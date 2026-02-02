import re

FORBIDDEN_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter", "truncate", "create"
]

MAX_LIMIT = 1000


def is_select_query(sql: str) -> bool:
    sql_clean = sql.strip().lower()
    return sql_clean.startswith("select") or sql_clean.startswith("with")


def contains_forbidden_keywords(sql: str) -> bool:
    sql_lower = sql.lower()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql_lower):
            return True
    return False


def enforce_limit(sql: str) -> str:
    if "limit" not in sql.lower():
        return sql.rstrip(";") + f" LIMIT {MAX_LIMIT};"
    return sql


def validate_sql(sql: str, allowed_tables: list[str]) -> str:
    if not is_select_query(sql):
        raise ValueError("Only SELECT queries are allowed.")

    if contains_forbidden_keywords(sql):
        raise ValueError("Query contains forbidden operations.")

    # Check table usage
    for word in re.findall(r"\bfrom\s+(\w+)|\bjoin\s+(\w+)", sql.lower()):
        table = next(filter(None, word))
        if table not in [t.lower() for t in allowed_tables]:
            raise ValueError(f"Unauthorized table used: {table}")

    sql = enforce_limit(sql)
    return sql
