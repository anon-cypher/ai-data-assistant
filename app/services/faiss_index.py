import faiss
import json
import numpy as np
from app.utils.utils import get_embedding_array
from app.utils.config import INDEX_PATH, TABLE_METADATA_PATH, DBConfig

def embed_text(text):
    """Return a float32 NumPy embedding for `text` using the LLM.

    Args:
     - text: The input text to embed (e.g., table description).

    Return:
     - A 1D NumPy array (dtype float32) representing the embedding vector.
    """
    return get_embedding_array(text)

def build_faiss_index():
    """Read schema metadata, compute embeddings, and write index+metadata.

    Args:
     - None

    Return:
     - None. Side effects: writes FAISS index to `INDEX_PATH` and table
       metadata JSON to `TABLE_METADATA_PATH`.
    """
    with open(DBConfig.SCHEMA_METADATA_PATH) as f:
        tables = json.load(f)

    embeddings = []
    metadata = []

    for table in tables:
        emb = embed_text(table["description"])
        embeddings.append(emb)
        metadata.append({
            "table_name": table["table"],
            "columns": table["columns"],
            "description": table["description"]
        })

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    faiss.write_index(index, INDEX_PATH)

    with open(TABLE_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ FAISS index built")

if __name__ == "__main__":
    build_faiss_index()
