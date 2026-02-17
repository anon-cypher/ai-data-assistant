from app.db.schema_loader import get_schema_metadata
import json
from app.utils.config import DBConfig

def generate_metadata_file():
    """Generate and write the schema metadata JSON file.

    Args:
     - None

    Return:
     - None. Side effects: writes the metadata JSON to
       `DBConfig.SCHEMA_METADATA_PATH` and prints a confirmation line.
    """
    schema = get_schema_metadata()
    metadata = []

    for table, columns in schema.items():
        description = f"Table {table} containing columns: {', '.join(columns)}"
        metadata.append({
            "table": table,
            "description": description,
            "columns": columns
        })

    with open(DBConfig.SCHEMA_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ schema_metadata.json created")

if __name__ == "__main__":
    generate_metadata_file()
