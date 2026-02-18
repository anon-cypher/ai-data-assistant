"""Deep Agent integration using DeepAgents if available, with a fallback.

This module exposes:
- `DeepAgent`: lightweight in-process coordinator that authors/fixes/executes SQL
    using existing project services and the centralized LLM wrapper.
- `create_deep_agent(model=None)`: factory that builds a DeepAgents graph
    exposing internal tools to the agent (only if `deepagents` is installed).
- `get_agent()`: returns either the DeepAgents-backed agent (if enabled)
    or the lightweight `DeepAgent`.
"""

from typing import Optional, Dict, Any, List
import os
import logging

# Project utilities
from app.services.rule_engine import match_rule_based_query
from app.services.table_selector import select_relevant_tables
from app.services.metadata_loader import load_table_metadata
from app.services.sql_generator import generate_sql
from app.services.sql_validator import validate_sql
from app.services.db_executer import execute_sql
from app.utils.utils import llm_chat
from app.utils.config import DEEP_AGENT_ENABLED
from app.utils.utils import _load_lm_model
from app.utils.prompts import Prompts

# Optional deepagents import
try:
    from deepagents import create_deep_agent as _create_deep_agent
except Exception:  # pragma: no cover - optional dependency
    _create_deep_agent = None


class DeepAgent:
    """Lightweight coordinator that authors/fixes/executes SQL.

    This class exists as a fallback when the `deepagents` framework is not
    available or when the feature flag is disabled.
    """

    def __init__(self):
        self.metadata = load_table_metadata()

    def _attempt_fix_sql(self, bad_sql: str, selected_tables: List[str]) -> Optional[str]:
        """Ask the LLM to repair a broken SQL query given schema context.

        Args:
         - bad_sql: The SQL string that failed validation or execution.
         - selected_tables: Tables the agent is allowed to reference.

        Return:
         - A cleaned, repaired SQL string if the model returns one, else None.
        """
        schema_context = ""
        for table in self.metadata:
            if table["table_name"] in selected_tables:
                cols = ", ".join(table["columns"])
                schema_context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"

        prompt = (
            "You are an assistant that fixes SQL queries so they are valid SELECT queries.\n"
            "Only return the corrected SQL. Do not return any explanation.\n"
            f"Schema context:\n{schema_context}\n"
            "Broken SQL:\n" + bad_sql + "\n\n"
            "Return a corrected SELECT query using only the available tables."
        )

        fixed = llm_chat(prompt, model_key="small")
        return fixed.strip() if fixed else None

    def autonomous_run(self, question: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Autonomously author, validate, fix, and execute SQL for `question`.

        The agent will attempt up to `max_iterations` cycles of generate->validate->fix.
        If it cannot produce a valid SQL, it will return a `clarify` payload asking
        the caller to disambiguate (e.g., choose a table).

        Args:
         - question: Natural-language question to handle.
         - max_iterations: How many generate/fix cycles to attempt before asking for clarification.

        Return:
         - On success: dict containing `answer`, `sql_used`, `columns`, `rows`, `source`.
         - If clarification is required: dict with `clarify: True` and a `question` string.
         - On error: dict with `error` key.
        """
        # 1. Table selection
        selected_tables = select_relevant_tables(question)

        # If we couldn't pick any table, ask the user to choose from metadata
        if not selected_tables:
            table_names = [t["table_name"] for t in self.metadata]
            return {
                "clarify": True,
                "question": (
                    "I couldn't determine which table you meant. "
                    "Which of these tables should I use? " + ", ".join(table_names)
                ),
                "options": table_names,
                "source": "deep_agent"
            }

        sql_query = None
        for _ in range(max_iterations):
            # generate if we don't have a candidate
            if not sql_query:
                try:
                    sql_query = generate_sql(question, selected_tables, self.metadata)
                except Exception as e:
                    return {"error": f"SQL generation failed: {e}", "source": "llm_generation"}

            # try validate
            try:
                safe_sql = validate_sql(sql_query, selected_tables)
                # execute and return
                try:
                    columns, rows = execute_sql(safe_sql)
                except Exception as e:
                    return {"error": f"Execution failed: {e}", "source": "execution"}

                return {
                    "answer": "Query executed successfully.",
                    "sql_used": safe_sql,
                    "columns": columns,
                    "rows": rows,
                    "source": "deep_agent"
                }
            except Exception:
                # attempt fix and loop
                fixed = self._attempt_fix_sql(sql_query, selected_tables)
                if not fixed:
                    return {"clarify": True, "question": "I could not fix the SQL — can you clarify the desired columns or table?", "source": "deep_agent"}
                sql_query = fixed

        return {"error": "Unable to produce a valid SQL after multiple attempts.", "source": "deep_agent"}

    def run(self, question: str) -> Dict[str, Any]:
        """Process `question` and return a structured response dict.

        This method defaults to autonomous authoring: it will try to author,
        validate, fix, and execute SQL without further intervention. It falls
        back to the rule-based path when applicable.

        Args:
         - question: Natural-language user question.

        Return:
         - A dict with keys like `answer`, `sql_used`, `columns`, `rows`, and `source`.
        """
        # 1. Try rule-based fast path
        sql_query = match_rule_based_query(question)
        if sql_query:
            try:
                cols, rows = execute_sql(sql_query)
                return {
                    "answer": f"(Rule-based answer)\n{sql_query}",
                    "sql_used": sql_query,
                    "columns": cols,
                    "rows": rows,
                    "source": "rule_engine"
                }
            except Exception as e:
                return {"error": f"Rule-based execution failed: {e}", "source": "rule_engine"}

        # Delegate to autonomous authoring flow
        return self.autonomous_run(question)


def create_deep_agent(model: str | None = None):
    """Create a DeepAgents graph using our internal tools.

    This function adapts project utilities into callable tools consumable by
    the DeepAgents `create_deep_agent` factory. Tools exposed:
     - `get_schema`: returns table metadata
     - `validate_sql`: validates a SQL string for allowed tables
     - `fix_sql`: attempts to fix broken SQL via the LLM
     - `execute_sql`: executes a validated SELECT query and returns rows

    Args:
     - model: Optional model identifier passed to DeepAgents (provider:model).

    Return:
     - A compiled deep agent (state graph) instance.
    """
    if _create_deep_agent is None:
        raise RuntimeError("deepagents package is not available in the environment")

    metadata = load_table_metadata()

    model = _load_lm_model(model)

    def get_schema() -> List[Dict[str, Any]]:
        """Return JSON-serializable schema metadata."""
        return metadata

    def validate_sql_tool(sql: str, allowed_tables=None) -> str:
        """Validate SQL against allowed tables and return cleaned SQL or raise."""
        # allow passing allowed_tables as comma-separated string
        if isinstance(allowed_tables, str):
            allowed = [t.strip() for t in allowed_tables.split(",") if t.strip()]
        else:
            allowed = allowed_tables or []
        return validate_sql(sql, allowed)

    def fix_sql_tool(bad_sql: str, allowed_tables=None) -> str:
        """Attempt to fix `bad_sql` using the LLM and schema context."""
        schema_context = ""
        for table in metadata:
            if not allowed_tables or table["table_name"] in (allowed_tables or []):
                cols = ", ".join(table["columns"])
                schema_context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"

        prompt = (
            "You are an assistant that fixes SQL queries so they are valid SELECT queries.\n"
            "Only return the corrected SQL. Do not return any explanation.\n"
            f"Schema context:\n{schema_context}\n"
            "Broken SQL:\n" + bad_sql + "\n\n"
            "Return a corrected SELECT query using only the available tables."
        )

        fixed = llm_chat(prompt, model_key="small")
        return fixed.strip() if fixed else ""

    def execute_sql_tool(sql: str):
        """Validate and execute a SQL string, return (columns, rows)."""
        safe = validate_sql(sql, [t["table_name"] for t in metadata])
        cols, rows = execute_sql(safe)
        return {"columns": list(cols), "rows": [list(r) for r in rows]}

    # Provide plain callables as tools; deepagents will wrap them appropriately.
    tools = [get_schema, validate_sql_tool, fix_sql_tool, execute_sql_tool]

    agent = _create_deep_agent(model=model, tools=tools, system_prompt=Prompts.DEEP_AGENT_SYSTEM)
    return agent


def get_agent(model: str) -> Optional[DeepAgent]:
    """Return a `DeepAgent` instance if enabled, otherwise `None`.

    Args:
     - None

    Return:
     - A `DeepAgent` object or `None`.
    """
    if not DEEP_AGENT_ENABLED:
        return None

    # If deepagents framework is available, prefer it only when LLM credentials
    # are present to avoid runtime authentication errors (e.g. Anthropic/OpenAI).

    if _create_deep_agent is not None:
        has_openai = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ANTHROPIC_AUTH_TOKEN")
            or os.getenv("AUTHORIZATION")
        )

        if not (has_openai or has_anthropic):
            logging.warning("DeepAgents available but no LLM credentials found; using fallback DeepAgent.")
            return DeepAgent()

        try:
            return create_deep_agent(model=model)
        except Exception:
            logging.exception("Failed to create DeepAgents graph; falling back to lightweight DeepAgent.")
            return DeepAgent()

    # Fallback: return the lightweight in-process agent
    return DeepAgent()
