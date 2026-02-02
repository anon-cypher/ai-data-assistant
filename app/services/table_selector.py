import faiss
import json
import numpy as np
import os
from openai import OpenAI
from langsmith import traceable
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
    )

INDEX_PATH = "app/vector_store/faiss.index"
META_PATH = "app/vector_store/table_metadata.json"

index = faiss.read_index(INDEX_PATH)

with open(META_PATH) as f:
    metadata = json.load(f)

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)

@traceable(name="table_selection")
def select_relevant_tables(question, top_k=2):
    q_emb = get_embedding(question)
    distances, indices = index.search(q_emb, top_k)
    return [metadata[i]["table_name"] for i in indices[0]]
