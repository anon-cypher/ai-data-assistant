import re
from app.utils.config import SQLValidatorConfig

def is_select_query(sql: str) -> bool:
    """Return True if `sql` appears to be a SELECT (or WITH) query.

    Args:
     - sql: The SQL string to inspect.

    Return:
     - `True` if the SQL starts with SELECT or WITH, otherwise `False`.
    """
    sql_clean = sql.strip().lower()
    return sql_clean.startswith("select") or sql_clean.startswith("with")


def contains_forbidden_keywords(sql: str) -> bool:
    """Detect any forbidden DDL/DML keywords in `sql`.

    Args:
     - sql: The SQL string to check.

    Return:
     - `True` if a forbidden keyword is present, otherwise `False`.
    """
    sql_lower = sql.lower()
    for keyword in SQLValidatorConfig.FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql_lower):
            return True
    return False


def enforce_limit(sql: str) -> str:
    """Ensure `sql` includes a `LIMIT` clause, appending a default if missing.

    Args:
     - sql: The SQL string to potentially modify.

    Return:
     - The SQL string guaranteed to contain a LIMIT clause.
    """
    if "limit" not in sql.lower():
        return sql.rstrip(";") + f" LIMIT {SQLValidatorConfig.MAX_LIMIT};"
    return sql


def validate_sql(sql: str, allowed_tables: list[str]) -> str:
    """Validate `sql` is SELECT-only, uses allowed tables, and enforces limits.

    Args:
     - sql: The SQL string to validate.
     - allowed_tables: A list of authorized table names (case-insensitive).

    Return:
     - The possibly-modified SQL string (with a LIMIT appended).

    Raises:
     - ValueError: if the SQL is not allowed or references unauthorized tables.
    """
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
