import faiss
import json
import numpy as np
import os
from langsmith import traceable
from app.utils.utils import get_embedding_array
from app.utils.config import INDEX_PATH, TABLE_METADATA_PATH

index = faiss.read_index(INDEX_PATH)

with open(TABLE_METADATA_PATH) as f:
    metadata = json.load(f)

def get_embedding(text):
    """Return a 2D embedding array for `text` shaped (1, dim).

    Args:
     - text: The input text to embed.

    Return:
     - A NumPy array shaped (1, embedding_dim) of type float32.
    """
    arr = get_embedding_array(text)
    return arr.reshape(1, -1)

@traceable(name="table_selection")
def select_relevant_tables(question, top_k=2):
    """Return the top_k most relevant table names for `question`.

    Uses FAISS nearest-neighbor search on the question embedding.

    Args:
     - question: The user question to find relevant tables for.
     - top_k: Number of top results to return (default 2).

    Return:
     - A list of table name strings ordered by relevance.
    """
    q_emb = get_embedding(question)
    distances, indices = index.search(q_emb, top_k)
    return [metadata[i]["table_name"] for i in indices[0]]
