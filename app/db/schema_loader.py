from sqlalchemy import inspect
from app.db.connection import engine

def get_schema_metadata():
    """Inspect the database and return a mapping of table -> column names.

    Args:
     - None

    Return:
     - A dict where keys are table names and values are lists of column name
       strings for that table.
    """
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        schema[table_name] = columns

    return schema
