from schema_loader import get_schema_metadata
import json

def generate_metadata_file():
    schema = get_schema_metadata()
    metadata = []

    for table, columns in schema.items():
        description = f"Table {table} containing columns: {', '.join(columns)}"
        metadata.append({
            "table": table,
            "description": description,
            "columns": columns
        })

    with open("app/db/schema_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ schema_metadata.json created")

if __name__ == "__main__":
    generate_metadata_file()
