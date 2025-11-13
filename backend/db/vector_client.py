import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer


INDEX_PATH = Path(os.getenv("RAG_INDEX_PATH", "rag_index.faiss"))
DATA_PATH = Path(os.getenv("RAG_DATA_PATH", "rag_data.pkl"))

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"))
    return _model


def load_index() -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    model = _get_model()
    dim = model.get_sentence_embedding_dimension()

    if INDEX_PATH.exists() and DATA_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        with DATA_PATH.open("rb") as f:
            data = pickle.load(f)
        return index, data

    return faiss.IndexFlatL2(dim), []


def save_index(index: faiss.Index, data: List[Dict[str, Any]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))
    with DATA_PATH.open("wb") as f:
        pickle.dump(data, f)


def add_document(text: str, metadata: Dict[str, Any]) -> None:
    index, data = load_index()
    model = _get_model()
    embedding = model.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    index.add(embedding)
    data.append({"text": text, "metadata": metadata})
    save_index(index, data)


def query_similar(text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    index, data = load_index()
    if index.ntotal == 0:
        return []

    model = _get_model()
    query_vec = model.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    distances, indices = index.search(query_vec, top_k)
    results: List[Dict[str, Any]] = []

    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(data):
            item = data[idx].copy()
            item["score"] = float(dist)
            results.append(item)
    return results

