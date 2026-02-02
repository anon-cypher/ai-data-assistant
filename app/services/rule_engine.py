import re
from app.db.schema_loader import get_schema_metadata

schema_cache = get_schema_metadata()

def find_table_in_question(question: str):
    q = question.lower()
    for table in schema_cache.keys():
        if table.lower() in q:
            return table
    return None


def match_rule_based_query(question: str):
    q = question.lower()
    table = find_table_in_question(q)

    if not table:
        return None

    # COUNT
    if "how many" in q or "count" in q:
        return f"SELECT COUNT(*) FROM {table};"

    # LIST ALL
    if "list" in q or "show" in q:
        return f"SELECT * FROM {table} LIMIT 100;"

    # SUM
    if "total" in q or "sum" in q:
        # try to find numeric column
        numeric_cols = [col for col in schema_cache[table] if "amount" in col or "price" in col or "total" in col]
        if numeric_cols:
            return f"SELECT SUM({numeric_cols[0]}) FROM {table};"

    return None
