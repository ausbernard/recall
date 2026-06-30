"""Local vector search with sentence-transformers + numpy"""

from sentence_transformers import SentenceTransformer
import numpy as np
from src.config import get_embedding_model

_model = None   # Lazy loaded

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(get_embedding_model())
    return _model

def embed(text):
    return get_model().encode(text)

def search_chunks(query, chunks, top_k=3):
    """only public function"""
    query_vec = embed(query)
    similarities = [
        (chunk, _cosine(query_vec), chunk['embedding']) for chunk in chunks
    ]
    
    return [c for c, _ in sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]]

def _cosine(a,b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
