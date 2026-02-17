from sqlalchemy import text
from app.db.connection import engine


def execute_sql(sql_query: str):
    """Execute `sql_query` and return `(columns, rows)` results.

    Args:
     - sql_query: The SQL string to execute.

    Return:
     - A tuple `(columns, rows)` where `columns` is an iterable of column names
       and `rows` is a list of result rows.
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()

    return columns, rows
