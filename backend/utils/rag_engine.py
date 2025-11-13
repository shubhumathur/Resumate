from __future__ import annotations

from typing import Any, Dict

from backend.db.vector_client import query_similar
from backend.utils.graph_engine import fetch_shared_skills


def hybrid_retrieve_context(resume_text: str, jd_text: str, top_k: int = 5) -> Dict[str, Any]:
    semantic_matches = query_similar(jd_text, top_k=top_k)
    graph_context = list(fetch_shared_skills(limit=top_k * 2))

    return {
        "semantic_matches": semantic_matches,
        "graph_context": graph_context,
    }

