from fastapi import APIRouter
import hashlib
import uuid
from typing import Optional
from langsmith import traceable

from app.services.cache_service import get_cache, set_cache
from app.services.rule_engine import match_rule_based_query
from app.services.table_selector import select_relevant_tables
from app.services.sql_generator import generate_sql
from app.services.metadata_loader import load_table_metadata
from app.services.db_executer import execute_sql
from app.services.response_builder import build_response
from app.services.insight_agent import generate_insight
from app.agents.deep_agent import get_agent
from app.utils.config import DEEP_AGENT_ENABLED, LLMConfig
from app.utils.logging import get_logger, log_exception

router = APIRouter()
metadata = load_table_metadata()
model = LLMConfig.MODELS.get("small")
_agent = get_agent(model) if DEEP_AGENT_ENABLED else None
logger = get_logger(__name__)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()

@traceable(name="agent_call")
def _agent_call(question: str, history: Optional[list] = None) -> dict:
    if not _agent:
        return {"error": "agent_not_configured"}
    # prefer invoke if available (deepagents/langgraph), otherwise fallback to run()
    try:
        if hasattr(_agent, "invoke"):
            messages = history or [{"role": "user", "content": question}]
            logger.debug("Invoking agent with messages: %s", messages)
            return _agent.invoke({"messages": messages})
        if hasattr(_agent, "run"):
            return _agent.run(question)
        return {"error": "unsupported_agent_interface"}
    except Exception as e:
        log_exception(logger, e, "agent call failed")
        return {"error": str(e)}


@router.post("/ask")
async def ask_question(payload: dict) -> dict:
    question = payload.get("question")
    if not question:
        return {"error": "question is required"}

    conv_id: Optional[str] = payload.get("conversation_id")
    followup = payload.get("followup")

    key = hashlib.md5(_normalize(question).encode()).hexdigest()
    cached = get_cache(key)
    if cached:
        return {"answer": cached, "source": "cache"}

    # rule-based short-circuit
    rule_sql = match_rule_based_query(question)
    if rule_sql:
        set_cache(key, rule_sql)
        return {"answer": rule_sql, "sql_used": rule_sql, "source": "rule_engine"}

    selected_tables = select_relevant_tables(question)

    # Agent path
    if _agent:
        # resume conversation if followup provided
        history = None
        if conv_id and followup:
            conv_key = f"conv:{conv_id}"
            state = get_cache(conv_key) or {}
            history = state.get("history", [])
            history.append({"role": "user", "content": followup})
            state["history"] = history
            state["turns"] = state.get("turns", 0) + 1
            set_cache(conv_key, state)

        result = _agent_call(question if not history else None, history)
        logger.debug("Agent result: %s", result)
        if result.get("error"):
            return {"error": result["error"]}

        # If agent explicitly asks for clarification or returns messages,
        # return a clarify payload for the frontend to handle.
        # if result.get("clarify"):
        #     conv_id = conv_id or uuid.uuid4().hex
        #     conv_key = f"conv:{conv_id}"
        #     state = get_cache(conv_key) or {}
        #     state.setdefault("history", [{"role": "user", "content": question}])
        #     state.setdefault("turns", 0)
        #     state["last_clarify"] = result.get("question")
        #     set_cache(conv_key, state)
        #     return {"clarify": True, "conversation_id": conv_id, "question": result.get("question"), "source": "deep_agent"}

        messages = result.get("messages")
        # Handle chat-style messages (langchain objects)
        if messages:
            def _get_msg_content(m):
                if m is None:
                    return ""
                if isinstance(m, dict):
                    return m.get("content") or m.get("text") or ""
                # LangChain message objects usually have `content` attribute
                txt = getattr(m, "content", None) or getattr(m, "text", None)
                if txt:
                    return txt
                try:
                    return str(m)
                except Exception:
                    return ""

            def _infer_role(m):
                if isinstance(m, dict):
                    return m.get("role") or ("assistant" if m.get("author") == "ai" else "user")
                cls = getattr(m, "__class__", None)
                if cls is not None:
                    name = cls.__name__.lower()
                    if "ai" in name or "assistant" in name:
                        return "assistant"
                # default
                return "user"

            def _is_clarifying(text: str) -> bool:
                if not text:
                    return False
                low = text.lower()
                triggers = [
                    "please specify",
                    "could you",
                    "which",
                    "do you mean",
                    "clarify",
                    "could you please",
                    "which metric",
                    "do you want",
                    "would you like",
                    "which of the following",
                ]
                if "?" in text:
                    return True
                return any(t in low for t in triggers)

            last = messages[-1]
            last_text = _get_msg_content(last).strip()
            logger.debug("Last agent message: %s", last_text)
            logger.debug("Is clarifying? %s", _is_clarifying(last_text))
            if _is_clarifying(last_text):
                conv_id = conv_id or uuid.uuid4().hex
                conv_key = f"conv:{conv_id}"
                # normalize history
                hist = []
                for m in messages:
                    hist.append({"role": _infer_role(m), "content": _get_msg_content(m)})

                state = get_cache(conv_key) or {}
                state["history"] = hist
                state["turns"] = state.get("turns", 0) + 1
                state["last_clarify"] = last_text
                state["options"] = result.get("options") or []
                set_cache(conv_key, state)
                return {"clarify": True, "conversation_id": conv_id, "question": last_text, "options": state["options"], "source": "deep_agent"}
            # If messages exist but aren't a clarifying question, return the
            # assistant's last message content as a textual answer.
            assistant_texts = [ _get_msg_content(m) for m in messages if _infer_role(m) == "assistant" ]
            if assistant_texts:
                final_text = assistant_texts[-1].strip()
                set_cache(key, final_text)
                # clear conversation state if present
                if conv_id:
                    set_cache(f"conv:{conv_id}", {})
                return {"answer": {"type": "text", "message": final_text}, "source": "deep_agent"}

        # Otherwise expect final result with columns/rows
        columns = result.get("columns")
        rows = result.get("rows")
        sql_used = result.get("sql_used")
        insight = None
        if rows and len(rows) > 1:
            try:
                insight = generate_insight(question, columns, rows)
            except Exception as e:
                log_exception(logger, e, "generate_insight failed")
                insight = None
        answer = build_response(columns, rows, insight)
        set_cache(key, answer)
        # clear conversation state if present
        if conv_id:
            set_cache(f"conv:{conv_id}", {})
        return {"answer": answer, "sql_used": sql_used, "tables_used": selected_tables, "source": "deep_agent"}

    # Fallback LLM SQL generation path
    try:
        sql_query = generate_sql(question, selected_tables, metadata)
    except Exception as e:
        log_exception(logger, e, "SQL generation failed in /ask")
        return {"error": f"sql generation failed: {e}"}

    try:
        columns, rows = execute_sql(sql_query)
    except Exception as e:
        log_exception(logger, e, "DB execution failed in /ask")
        return {"error": f"db execution failed: {e}"}

    insight = None
    if rows and len(rows) > 1:
        try:
            insight = generate_insight(question, columns, rows)
        except Exception:
            insight = None

    answer = build_response(columns, rows, insight)
    set_cache(key, answer)
    return {"answer": answer, "sql_used": sql_query, "tables_used": selected_tables, "source": "llm_sql_generator"}

