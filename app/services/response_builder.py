<<<<<<< HEAD
def build_response(columns, rows, insight=None):
=======
def build_response(columns, rows):
    """Return a structured response dict for the front-end from SQL results.

    Args:
     - columns: Iterable of column names returned by the DB.
     - rows: List of row tuples returned by the DB.

    Return:
     - A dict representing either a textual summary or a tabular payload.
    """
>>>>>>> main
    if not rows:
        return {
            "type": "text",
            "message": "No results found."
        }

    if len(columns) == 1 and len(rows) == 1:
        return {
            "type": "text",
            "message": f"The result is {rows[0][0]}."
        }

    return {
        "type": "table",
        "columns": list(columns),
        "rows": [list(row) for row in rows],
        "insight": insight  # 👈 NEW
    }
