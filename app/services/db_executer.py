from sqlalchemy import text
from app.db.connection import engine


def execute_sql(sql_query: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()

    return columns, rows
