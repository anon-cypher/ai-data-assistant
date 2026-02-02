import json

def load_table_metadata():
    with open("app/vector_store/table_metadata.json") as f:
        return json.load(f)
