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


def validate_sql(sql: str, allowed_tables: list[str] | None) -> str:
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

    # Normalize allowed_tables to a list of lowercase table names. Accept
    # strings, lists of strings, or lists of dicts containing table metadata.
    allowed = []
    if allowed_tables:
        # If a single comma-separated string was passed, split it
        if isinstance(allowed_tables, str):
            allowed_iter = [t.strip() for t in allowed_tables.split(",") if t.strip()]
        else:
            allowed_iter = allowed_tables

        for t in allowed_iter:
            if isinstance(t, dict):
                # common keys for table name
                name = t.get("table_name") or t.get("name") or t.get("table")
                if name:
                    allowed.append(name.lower())
                    continue
                # fall back to stringifying the dict
                allowed.append(str(t).lower())
            else:
                allowed.append(str(t).lower())

    # Check table usage
    for word in re.findall(r"\bfrom\s+(\w+)|\bjoin\s+(\w+)", sql.lower()):
        table = next(filter(None, word))
        if allowed and table not in allowed:
            raise ValueError(f"Unauthorized table used: {table}")

    sql = enforce_limit(sql)
    return sql
