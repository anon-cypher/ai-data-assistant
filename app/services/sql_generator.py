import os
from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
    )

MODEL_SMALL = "openai/gpt-4o-mini"  # cheap + good for structured tasks


def build_schema_context(selected_tables, metadata):
    context = ""
    for table in metadata:
        if table["table_name"] in selected_tables:
            cols = ", ".join(table["columns"])
            context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"
    return context

import re

def clean_llm_sql(output: str) -> str:
    output = output.strip()

    # Remove ```sql ... ``` or ``` ... ```
    output = re.sub(r"^```sql", "", output, flags=re.IGNORECASE).strip()
    output = re.sub(r"^```", "", output).strip()
    output = re.sub(r"```$", "", output).strip()

    return output.strip()


@traceable(name="sql_generation")
def generate_sql(question, selected_tables, metadata):
    schema_context = ""
    for table in metadata:
        if table["table_name"] in selected_tables:
            cols = ", ".join(table["columns"])
            schema_context += f"Table: {table['table_name']}\nColumns: {cols}\n\n"

    prompt = f"""
Generate PostgreSQL SQL.

Use only these tables:

{schema_context}

Return only SQL.

Question: {question}
"""

    response = client.chat.completions.create(
        model=MODEL_SMALL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300
    )

    res = response.choices[0].message.content.strip()

    return clean_llm_sql(res)