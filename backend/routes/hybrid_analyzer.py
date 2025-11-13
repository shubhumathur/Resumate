from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.db.vector_client import add_document
from backend.utils.graph_engine import store_job_graph, store_resume_graph
from backend.utils.rag_engine import hybrid_retrieve_context
from backend.utils.llm import generate_analysis  # Assuming services.llm equivalent lives here


router = APIRouter(prefix="/hybrid", tags=["Hybrid Analyzer"])


class ResumePayload(BaseModel):
    id: str = Field(..., description="Unique identifier for the resume")
    text: str
    name: str | None = None
    skills: list[str] | None = None
    experiences: list[str] | None = None
    metadata: Dict[str, Any] | None = None


class JobPayload(BaseModel):
    id: str = Field(..., description="Unique identifier for the job description")
    text: str
    title: str | None = None
    skills: list[str] | None = None
    metadata: Dict[str, Any] | None = None


class HybridAnalyzeRequest(BaseModel):
    resume: ResumePayload
    job: JobPayload


@router.post("/analyze")
def hybrid_analyze(payload: HybridAnalyzeRequest):
    try:
        resume_data = payload.resume.dict()
        job_data = payload.job.dict()

        store_resume_graph(resume_data)
        store_job_graph(job_data)

        add_document(resume_data["text"], {"type": "resume", "id": resume_data["id"]})
        add_document(job_data["text"], {"type": "job", "id": job_data["id"]})

        context = hybrid_retrieve_context(resume_data["text"], job_data["text"])

        prompt = f"""
You are an AI hiring assistant analyzing resume-job fit.

Resume Text: {resume_data['text']}
Job Description: {job_data['text']}
Semantic Matches: {context['semantic_matches']}
Graph Context (Skills & Relations): {context['graph_context']}

Provide a clear analysis:
1. Overall suitability summary
2. Missing but related skills
3. Recommendations for resume improvement
4. Explain reasoning concisely
"""
        analysis = generate_analysis(prompt)

        return {"context": context, "analysis": analysis}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

