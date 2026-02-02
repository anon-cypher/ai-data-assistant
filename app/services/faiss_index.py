import faiss
import json
import numpy as np
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
    )

INDEX_PATH = "app/vector_store/faiss.index"
META_PATH = "app/vector_store/table_metadata.json"

def embed_text(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype="float32")

def build_faiss_index():
    with open("app/db/schema_metadata.json") as f:
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

    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ FAISS index built")

if __name__ == "__main__":
    build_faiss_index()
