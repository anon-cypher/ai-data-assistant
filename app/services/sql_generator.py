import os
import re
from langsmith import traceable
from app.utils.utils import llm_chat
from app.utils.prompts import Prompts


def build_schema_context(selected_tables, metadata):
    """Construct a textual schema context for `selected_tables` from `metadata`.

    Args:
     - selected_tables: Iterable of table names to include in the context.
     - metadata: Schema metadata list/dict containing table/column info.

    Return:
     - A formatted string describing the selected tables and their columns.
    """
    context = ""
    for table in metadata:
        if table["table_name"] in selected_tables:
            cols = ", ".join(table["columns"])
            context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"
    return context


def clean_llm_sql(output: str) -> str:
    """Clean LLM output by removing surrounding markdown fences and trimming.

    Args:
     - output: Raw string returned by the LLM.

    Return:
     - A cleaned SQL string suitable for execution.
    """
    output = output.strip()

    # Remove ```sql ... ``` or ``` ... ```
    output = re.sub(r"^```sql", "", output, flags=re.IGNORECASE).strip()
    output = re.sub(r"^```", "", output).strip()
    output = re.sub(r"```$", "", output).strip()

    return output.strip()


@traceable(name="sql_generation")
def generate_sql(question, selected_tables, metadata):
    """Generate a SQL query for `question` scoped to `selected_tables`.

    Args:
     - question: The user's natural language question.
     - selected_tables: List of table names to consider.
     - metadata: Schema metadata list/dict for those tables.

    Return:
     - A cleaned SQL string produced by the LLM.
    """
    schema_context = ""
    for table in metadata:
        if table["table_name"] in selected_tables:
            cols = ", ".join(table["columns"])
            schema_context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"

    prompt = Prompts.SQL_GENERATION
    prompt = prompt.format(schema_context=schema_context, question=question)

    res = llm_chat(prompt, model_key="small")

    return clean_llm_sql(res)