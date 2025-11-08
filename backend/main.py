"""
FastAPI main application for ResuMate backend.
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ✅ --- Global Gemini Configuration ---
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

# Configure Gemini API globally
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# ✅ --- End of Gemini Config ---

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime



# Import agents
from agents.file_input_agent import FileInputAgent
from agents.resume_parser_agent import ResumeParsingAgent
from agents.jd_parser_agent import JDParsingAgent
from agents.matching_agent import MatchingAgent
from agents.improvement_agent import ImprovementAgent
from agents.question_agent import QuestionAgent
from agents.moderator_agent import moderator

# Import utilities
from utils.rag import rag_kg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ResuMate API",
    description="Intelligent Resume Screening and Candidate Matching System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
file_input_agent = FileInputAgent()
resume_parser_agent = ResumeParsingAgent()
jd_parser_agent = JDParsingAgent()
matching_agent = MatchingAgent()
improvement_agent = ImprovementAgent()
question_agent = QuestionAgent()

# Preload SentenceTransformer model to avoid timeouts on first use
try:
    from models.sentence_transformer_model import generate_embeddings
    logger.info("Preloading SentenceTransformer model...")
    generate_embeddings("test")  # Dummy call to load model
    logger.info("SentenceTransformer model preloaded successfully.")
except Exception as e:
    logger.error(f"Failed to preload SentenceTransformer model: {e}")


# Pydantic models
class ResumeParseRequest(BaseModel):
    resume_text: str


class JDParseRequest(BaseModel):
    jd_text: str


class MatchRequest(BaseModel):
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]
    weights: Optional[Dict[str, float]] = None


class BatchMatchRequest(BaseModel):
    resumes_data: List[Dict[str, Any]]
    jd_data: Dict[str, Any]
    weights: Optional[Dict[str, float]] = None


class SummaryRequest(BaseModel):
    match_result: Dict[str, Any]


class QuestionsRequest(BaseModel):
    resume_data: Dict[str, Any]
    jd_data: Dict[str, Any]
    num_questions: Optional[int] = 5


# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ResuMate API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/parse_resume_text")
async def parse_resume_text(request: ResumeParseRequest):
    """
    Parse resume text and extract structured information.
    """
    try:
        parsed_data = resume_parser_agent.parse(request.resume_text)
        moderator.log_processing("ResumeParsingAgent", "parse_resume_text")
        return {"success": True, "data": parsed_data}
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse_resume_file")
async def parse_resume_file(file: UploadFile = File(...)):
    """
    Parse resume from uploaded file (PDF/DOCX/TXT).
    """
    try:
        if not file_input_agent.is_supported(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text
        text = file_input_agent.extract_text(
            file_content=file_content,
            filename=file.filename
        )
        
        # Parse resume
        parsed_data = resume_parser_agent.parse(text)
        
        moderator.log_processing("FileInputAgent", "extract_text", {"filename": file.filename})
        moderator.log_processing("ResumeParsingAgent", "parse_resume_file")
        
        return {"success": True, "data": parsed_data}
    except Exception as e:
        logger.error(f"Error parsing resume file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse_jd")
async def parse_jd(request: JDParseRequest):
    """
    Parse job description and create embeddings.
    """
    try:
        parsed_data = jd_parser_agent.parse(request.jd_text)
        moderator.log_processing("JDParsingAgent", "parse_jd")
        return {"success": True, "data": parsed_data}
    except Exception as e:
        logger.error(f"Error parsing JD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match")
async def match(request: MatchRequest):
    """
    Compute matching score between a resume and job description.
    """
    try:
        match_result = matching_agent.match(
            request.resume_data,
            request.jd_data,
            request.weights
        )
        moderator.log_processing("MatchingAgent", "match")
        return {"success": True, "data": match_result}
    except Exception as e:
        logger.error(f"Error matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_match")
async def batch_match(request: BatchMatchRequest):
    """
    Compute matching scores for multiple resumes.
    """
    try:
        match_results = matching_agent.batch_match(
            request.resumes_data,
            request.jd_data,
            request.weights
        )
        moderator.log_processing("MatchingAgent", "batch_match", {"count": len(match_results)})
        return {"success": True, "data": match_results}
    except Exception as e:
        logger.error(f"Error batch matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_summary")
async def generate_summary(request: SummaryRequest):
    """
    Generate explainable summary for a candidate match.
    """
    try:
        summary = improvement_agent.generate_summary(request.match_result)
        moderator.log_processing("ImprovementAgent", "generate_summary")
        return {"success": True, "summary": summary}
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_questions")
async def generate_questions(request: QuestionsRequest):
    """
    Generate personalized interview questions.
    """
    try:
        questions = question_agent.generate_questions(
            request.resume_data,
            request.jd_data,
            request.num_questions
        )
        moderator.log_processing("QuestionAgent", "generate_questions")
        return {"success": True, "questions": questions}
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_pipeline")
async def process_pipeline(
    resume_files: List[UploadFile] = File(...),
    jd_text: str = None,
    jd_file: UploadFile = None
):
    """
    Complete end-to-end pipeline: parse resumes, parse JD, match, and generate summaries.
    """
    try:
        session_id = str(uuid.uuid4())
        moderator.initialize_session(session_id)
        
        # Parse job description
        if jd_file:
            jd_content = await jd_file.read()
            jd_text = file_input_agent.extract_text(
                file_content=jd_content,
                filename=jd_file.filename
            )
        
        if not jd_text:
            raise HTTPException(status_code=400, detail="Job description text or file required")
        
        jd_data = jd_parser_agent.parse(jd_text)
        moderator.cache_jd(session_id, jd_data)
        
        # Parse all resumes
        resumes_data = []
        for resume_file in resume_files:
            if not file_input_agent.is_supported(resume_file.filename):
                continue
            
            resume_content = await resume_file.read()
            resume_text = file_input_agent.extract_text(
                file_content=resume_content,
                filename=resume_file.filename
            )
            
            resume_data = resume_parser_agent.parse(resume_text)
            resumes_data.append(resume_data)
        
        if not resumes_data:
            raise HTTPException(status_code=400, detail="No valid resumes provided")
        
        # Match all resumes
        match_results = matching_agent.batch_match(resumes_data, jd_data)
        
        # Generate summaries and questions
        results = []
        for match_result in match_results:
            summary = improvement_agent.generate_summary(match_result)
            questions = question_agent.generate_questions(
                match_result["resume_data"],
                jd_data,
                num_questions=5
            )
            
            results.append({
                **match_result,
                "summary": summary,
                "questions": questions
            })
        
        moderator.update_session(session_id, "results", results)
        moderator.log_processing("ModeratorAgent", "process_pipeline", {"session_id": session_id})
        
        return {
            "success": True,
            "session_id": session_id,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session data.
    """
    session_data = moderator.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "data": session_data}


@app.get("/logs")
async def get_logs(limit: int = 100):
    """
    Get recent processing logs.
    """
    logs = moderator.get_processing_log(limit)
    return {"success": True, "logs": logs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

