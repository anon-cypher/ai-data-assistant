def build_response(columns, rows):
    if not rows:
        return {
            "type": "text",
            "message": "No results found."
        }

    # Single value (COUNT, SUM etc.)
    if len(columns) == 1 and len(rows) == 1:
        return {
            "type": "text",
            "message": f"The result is {rows[0][0]}."
        }

    # Tabular response
    return {
        "type": "table",
        "columns": list(columns),
        "rows": [list(row) for row in rows]
    }
