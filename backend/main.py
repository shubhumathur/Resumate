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

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials



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
from routes.hybrid_analyzer import router as hybrid_analyzer_router

# Import auth
try:
    from auth import (
        create_user,
        authenticate_user,
        create_access_token,
        decode_token,
        get_user_by_id,
        get_db,
        ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    AUTH_AVAILABLE = True
except ImportError:
    logger.warning("Auth module not available. Install passlib and bcrypt for authentication.")
    AUTH_AVAILABLE = False

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

app.include_router(hybrid_analyzer_router)

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
    user_id: Optional[str] = None  # Optional user_id for auto-saving
    auto_save: Optional[bool] = False  # Whether to auto-save result


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


class EnhanceResumeRequest(BaseModel):
    text: str
    style: Optional[str] = "ats-friendly"  # "ats-friendly", "professional", "concise"


class MockInterviewRequest(BaseModel):
    message: str
    resume_data: Optional[Dict[str, Any]] = None
    jd_data: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, str]]] = None


# Auth models
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SaveResultRequest(BaseModel):
    user_id: str
    resume_id: Optional[str] = None
    jd_id: Optional[str] = None
    scores: Dict[str, float]
    summary: Optional[str] = None
    questions: Optional[List[str]] = None
    matching_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    resume_data: Optional[Dict[str, Any]] = None
    jd_data: Optional[Dict[str, Any]] = None


# Security
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=501, detail="Authentication not configured")
    
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


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
    Optionally auto-saves result to MongoDB if user_id and auto_save are provided.
    """
    try:
        match_result = matching_agent.match(
            request.resume_data,
            request.jd_data,
            request.weights
        )
        
        # Auto-save result if requested
        if request.auto_save and request.user_id:
            try:
                db = get_db()
                if db is not None:
                    # Generate questions and summary for saved result
                    questions = []
                    summary = ""
                    
                    try:
                        questions = question_agent.generate_questions(
                            request.resume_data,
                            request.jd_data,
                            num_questions=10
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate questions during auto-save: {e}")
                    
                    try:
                        summary = improvement_agent.generate_summary(match_result)
                    except Exception as e:
                        logger.warning(f"Failed to generate summary during auto-save: {e}")
                    
                    # Prepare result document
                    result_doc = {
                        "user_id": request.user_id,
                        "scores": {
                            "suitability": match_result.get("suitability_score", 0),
                            "semantic_similarity": match_result.get("semantic_similarity", 0),
                            "skill_overlap": match_result.get("skill_overlap", 0),
                            "experience_relevance": match_result.get("experience_relevance", 0),
                        },
                        "summary": summary,
                        "questions": questions,
                        "resume_data": request.resume_data,
                        "jd_data": request.jd_data,
                        "matching_skills": match_result.get("matching_skills", []),
                        "missing_skills": match_result.get("missing_skills", []),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    
                    # Use upsert to replace existing result for this user (keep only latest)
                    # Find existing result for this user
                    existing = db.match_results.find_one(
                        {"user_id": request.user_id},
                        sort=[("created_at", -1)]
                    )
                    
                    if existing:
                        # Update existing result
                        db.match_results.update_one(
                            {"_id": existing["_id"]},
                            {"$set": result_doc}
                        )
                        logger.info(f"Updated existing analysis result for user {request.user_id}")
                    else:
                        # Insert new result
                        db.match_results.insert_one(result_doc)
                        logger.info(f"Auto-saved new analysis result for user {request.user_id}")
                    # Also upsert an interview session with this context
                    try:
                        role = request.jd_data.get("title", "General Role") if request.jd_data else "General Role"
                        jd_summary = ""
                        if request.jd_data:
                            if request.jd_data.get("raw_text"):
                                jd_summary = request.jd_data["raw_text"][:500]
                            elif request.jd_data.get("profile_text"):
                                jd_summary = request.jd_data["profile_text"][:500]
                            elif request.jd_data.get("responsibilities"):
                                jd_summary = " | ".join(request.jd_data["responsibilities"][:3])
                        session_doc = {
                            "user_id": request.user_id,
                            "session_id": str(uuid4()),
                            "role": role,
                            "resume_summary": request.resume_data.get("summary", None) if request.resume_data else None,
                            "jd_summary": jd_summary,
                            "questions": questions or [],
                            "chat_history": [],
                            "resume_data": request.resume_data,
                            "jd_data": request.jd_data,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        # Save session
                        db.interview_sessions.insert_one(session_doc)
                        # Enforce retention
                        sessions = list(db.interview_sessions.find({"user_id": request.user_id}).sort("timestamp", -1))
                        if len(sessions) > 5:
                            for s in sessions[5:]:
                                db.interview_sessions.delete_one({"_id": s["_id"]})
                    except Exception as e:
                        logger.warning(f"Failed to upsert interview session during auto-save: {e}")
            except Exception as e:
                logger.error(f"Failed to auto-save result: {e}")
                # Don't fail the match request if save fails
        
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


@app.post("/enhance_resume")
async def enhance_resume(request: EnhanceResumeRequest):
    """
    Enhance resume text using Gemini LLM for ATS optimization.
    """
    try:
        if not improvement_agent.model:
            raise HTTPException(status_code=503, detail="Gemini API not configured")
        
        # Create enhancement prompt
        style_instructions = {
            "ats-friendly": "Optimize for Applicant Tracking Systems (ATS). Use standard keywords, clear formatting, and industry-standard terminology.",
            "professional": "Enhance for professional tone and clarity. Maintain formality while improving readability.",
            "concise": "Make the text more concise while preserving all key information. Remove redundancy."
        }
        
        instruction = style_instructions.get(request.style, style_instructions["ats-friendly"])
        
        prompt = f"""You are an expert resume writer. Enhance the following resume section to make it more {request.style}.

Instructions:
{instruction}

Original text:
{request.text}

Enhanced text (return only the enhanced version, no explanations):"""

        response = improvement_agent.model.generate_content(prompt)
        enhanced_text = response.text.strip()
        
        moderator.log_processing("ImprovementAgent", "enhance_resume")
        return {"success": True, "enhanced_text": enhanced_text}
    except Exception as e:
        logger.error(f"Error enhancing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mock_interview")
async def mock_interview(request: MockInterviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Chat endpoint for mock interview practice.
    Automatically fetches latest analysis context if resume_data/jd_data not provided.
    """
    try:
        if not question_agent.model:
            raise HTTPException(status_code=503, detail="Gemini API not configured")
        
        # Try to fetch latest context from MongoDB if not provided
        resume_data = request.resume_data
        jd_data = request.jd_data
        
        if not resume_data or not jd_data:
            # Fetch from MongoDB using user_id
            user_id = request.user_id or current_user.get("_id")
            if user_id:
                try:
                    db = get_db()
                    if db is not None:
                        result = db.match_results.find_one(
                            {"user_id": user_id},
                            sort=[("created_at", -1)]
                        )
                        if result:
                            resume_data = result.get("resume_data", {}) or resume_data
                            jd_data = result.get("jd_data", {}) or jd_data
                            logger.info(f"Auto-loaded context from MongoDB for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to fetch context from MongoDB: {e}")
        
        # Build context from resume and JD
        context = ""
        if resume_data:
            skills = resume_data.get("skills", [])
            experience = resume_data.get("experience_years", 0)
            context += f"Candidate Skills: {', '.join(skills[:15]) if isinstance(skills, list) else 'Not specified'}\n"
            if experience:
                context += f"Experience: {experience} years\n"
        
        if jd_data:
            job_title = jd_data.get("title", "the position")
            jd_skills = jd_data.get("skills_required", []) or jd_data.get("all_skills", [])
            context += f"Job Title: {job_title}\n"
            if isinstance(jd_skills, list):
                context += f"Required Skills: {', '.join(jd_skills[:15])}\n"
        
        # Build conversation history
        history_text = ""
        if request.chat_history:
            for msg in request.chat_history[-5:]:  # Last 5 messages for context
                role = "Interviewer" if msg.get("role") == "assistant" else "Candidate"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        # Enhanced prompt with better context and intent parsing
        # Parse user intent
        message_lower = request.message.lower()
        intent = "general"
        topic = None
        
        # Detect topic-specific requests
        if any(word in message_lower for word in ["oops", "object-oriented", "object oriented"]):
            intent = "technical_topic"
            topic = "OOPS (Object-Oriented Programming)"
        elif any(word in message_lower for word in ["dsa", "data structure", "algorithm"]):
            intent = "technical_topic"
            topic = "Data Structures and Algorithms"
        elif any(word in message_lower for word in ["system design", "architecture", "scalability"]):
            intent = "technical_topic"
            topic = "System Design"
        elif any(word in message_lower for word in ["behavioral", "tell me about", "experience"]):
            intent = "behavioral"
        elif any(word in message_lower for word in ["practice", "ask me", "question"]):
            intent = "practice_request"
        
        # Build enhanced context from resume_data and jd_data (now fetched above)
        skills_list = resume_data.get("skills", []) if resume_data else []
        jd_skills_list = (jd_data.get("skills_required", []) or jd_data.get("all_skills", [])) if jd_data else []
        job_title = jd_data.get("title", "the position") if jd_data else "the position"
        
        # Create JD summary
        jd_summary = ""
        if jd_data:
            responsibilities = jd_data.get("responsibilities", [])
            if responsibilities:
                jd_summary = " | ".join(responsibilities[:3])
            elif jd_data.get("raw_text"):
                jd_summary = jd_data["raw_text"][:500]
            elif jd_data.get("profile_text"):
                jd_summary = jd_data["profile_text"][:500]
            else:
                jd_summary = f"Role: {job_title}"
        
        prompt = f"""You are an AI interview coach conducting a realistic mock interview. 

Candidate Context:
- Skills: {', '.join(skills_list[:15]) if skills_list else 'Not specified'}
- Job Description Summary: {jd_summary}
- Target Role: {job_title}
- Required Skills: {', '.join(jd_skills_list[:15]) if jd_skills_list else 'Not specified'}

Conversation History:
{history_text if history_text else "No previous conversation."}

Current User Message: "{request.message}"

Instructions:
1. If the user requests to practice a specific topic (e.g., "practice OOPS", "ask me DSA questions"), immediately start asking relevant technical questions in that domain.
2. If the user provides an answer to a question, give constructive feedback (1-2 sentences) evaluating their response, then ask a follow-up question.
3. If the user asks a question, answer it professionally and then continue with interview practice.
4. Keep responses concise (2-3 sentences max).
5. Maintain a friendly but professional interviewer tone.
6. Focus on questions relevant to the candidate's skills and the job role.
7. Provide specific, actionable feedback when evaluating answers.

{"IMPORTANT: The user wants to practice " + topic + ". Start asking relevant technical questions immediately." if intent == "technical_topic" and topic else ""}

Response:"""

        response = question_agent.model.generate_content(prompt)
        reply = response.text.strip()
        
        moderator.log_processing("QuestionAgent", "mock_interview")
        return {"success": True, "reply": reply}
    except Exception as e:
        logger.error(f"Error in mock interview: {e}")
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


# Authentication endpoints
if AUTH_AVAILABLE:
    @app.post("/auth/signup")
    async def signup(request: SignupRequest):
        """Sign up a new user."""
        try:
            user = create_user(request.name, request.email, request.password)
            if not user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            access_token = create_access_token(
                data={"sub": user["_id"]},
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            return {
                "success": True,
                "user": user,
                "token": access_token,
                "token_type": "bearer"
            }
        except ConnectionError as e:
            logger.error(f"MongoDB connection error during signup: {e}")
            raise HTTPException(status_code=503, detail="Database connection failed. Please ensure MongoDB is running.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error signing up: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

    @app.post("/auth/login")
    async def login(request: LoginRequest):
        """Login a user."""
        try:
            logger.info(f"Login attempt for email: {request.email}")
            user = authenticate_user(request.email, request.password)
            if not user:
                logger.warning(f"Login failed for email: {request.email}")
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            
            access_token = create_access_token(
                data={"sub": user["_id"]},
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            logger.info(f"Login successful for user: {user.get('email')}")
            return {
                "success": True,
                "user": user,
                "token": access_token,
                "token_type": "bearer"
            }
        except ConnectionError as e:
            logger.error(f"MongoDB connection error during login: {e}")
            raise HTTPException(status_code=503, detail="Database connection failed. Please ensure MongoDB is running.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error logging in: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

    @app.get("/auth/me")
    async def get_current_user_info(current_user: dict = Depends(get_current_user)):
        """Get current user information."""
        return {"success": True, "user": current_user}


# MongoDB persistence endpoints
@app.post("/save_result")
async def save_result(request: SaveResultRequest, current_user: dict = Depends(get_current_user)):
    """Save a match result to MongoDB."""
    try:
        db = get_db()
        result = {
            "user_id": current_user["_id"],
            "resume_id": request.resume_id,
            "jd_id": request.jd_id,
            "scores": request.scores,
            "summary": request.summary,
            "questions": request.questions,
            "matching_skills": request.matching_skills or [],
            "missing_skills": request.missing_skills or [],
            "resume_data": request.resume_data,
            "jd_data": request.jd_data,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Also save resume and JD if provided
        if request.resume_data and not request.resume_id:
            resume_doc = {
                "user_id": current_user["_id"],
                "filename": request.resume_data.get("name", "resume.pdf"),
                "parsed_data": request.resume_data,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
            resume_result = db.resumes.insert_one(resume_doc)
            result["resume_id"] = str(resume_result.inserted_id)
        
        if request.jd_data and not request.jd_id:
            jd_doc = {
                "user_id": current_user["_id"],
                "title": request.jd_data.get("title", "Job Description"),
                "parsed_data": request.jd_data,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
            jd_result = db.job_descriptions.insert_one(jd_doc)
            result["jd_id"] = str(jd_result.inserted_id)
        
        result_id = db.match_results.insert_one(result)
        result["_id"] = str(result_id.inserted_id)
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error saving result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/interview_questions/{user_id}")
async def get_interview_questions(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Fetch interview questions from the most recent match result for a user.
    If questions don't exist, generate them from the last analysis.
    Returns structured context for Interview Prep page.
    """
    try:
        # Verify user can only access their own data
        if current_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Find the most recent match result for this user
        result = db.match_results.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        if not result:
            logger.info(f"No analysis found for user {user_id}")
            return {
                "success": False,
                "status": "no_context",
                "message": "No analysis found. Please run a resume-JD analysis first.",
                "questions": [],
                "context": None
            }
        
        # Extract context data
        resume_data = result.get("resume_data", {})
        jd_data = result.get("jd_data", {})
        matching_skills = result.get("matching_skills", [])
        missing_skills = result.get("missing_skills", [])
        role = jd_data.get("title", "General Role") if jd_data else "General Role"
        
        # Create JD summary
        jd_summary = ""
        if jd_data:
            if jd_data.get("raw_text"):
                jd_summary = jd_data["raw_text"][:500]
            elif jd_data.get("profile_text"):
                jd_summary = jd_data["profile_text"][:500]
            elif jd_data.get("responsibilities"):
                jd_summary = " | ".join(jd_data["responsibilities"][:3])
        
        # Check if questions already exist
        existing_questions = result.get("questions", [])
        if existing_questions and len(existing_questions) > 0:
            context = {
                "role": role,
                "matched_skills": matching_skills,
                "missing_skills": missing_skills,
                "jd_summary": jd_summary,
                "scores": result.get("scores", {}),
            }
            logger.info(f"Loaded last analysis for {user_id}: role={role}, matched_skills={len(matching_skills)}, questions={len(existing_questions)}")
            return {
                "success": True,
                "status": "success",
                "questions": existing_questions,
                "resume_data": resume_data,
                "jd_data": jd_data,
                "context": context,
                "result_id": str(result.get("_id"))
            }
        
        # Generate questions if they don't exist
        if not resume_data or not jd_data:
            return {
                "success": False,
                "status": "incomplete",
                "message": "Incomplete analysis data. Please run a new analysis.",
                "questions": [],
                "context": None
            }
        
        try:
            questions = question_agent.generate_questions(resume_data, jd_data, num_questions=10)
            
            # Update the result with generated questions
            db.match_results.update_one(
                {"_id": result.get("_id")},
                {"$set": {"questions": questions}}
            )
            
            context = {
                "role": role,
                "matched_skills": matching_skills,
                "missing_skills": missing_skills,
                "jd_summary": jd_summary,
                "scores": result.get("scores", {}),
            }
            
            logger.info(f"Generated and saved questions for {user_id}: role={role}, questions={len(questions)}")
            return {
                "success": True,
                "status": "success",
                "questions": questions,
                "resume_data": resume_data,
                "jd_data": jd_data,
                "context": context,
                "result_id": str(result.get("_id"))
            }
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return {
                "success": False,
                "status": "error",
                "message": f"Failed to generate questions: {str(e)}",
                "questions": [],
                "context": None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interview questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user_history/{user_id}")
async def get_user_history(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user's match history."""
    try:
        # Verify user can only access their own history
        if current_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db = get_db()
        from bson import ObjectId
        
        # Find all results for this user
        results_cursor = db.match_results.find({"user_id": user_id}).sort("created_at", -1).limit(100)
        results = list(results_cursor)
        
        # Convert ObjectId to string and fetch related data
        for result in results:
            result["_id"] = str(result["_id"])
            # Fetch resume filename if resume_id exists
            if result.get("resume_id"):
                try:
                    resume_obj_id = ObjectId(result["resume_id"])
                    resume = db.resumes.find_one({"_id": resume_obj_id})
                    if resume:
                        result["resume_filename"] = resume.get("filename", "resume.pdf")
                        result["resume_name"] = resume.get("parsed_data", {}).get("name", "Resume")
                except Exception as e:
                    logger.warning(f"Could not fetch resume {result['resume_id']}: {e}")
                    result["resume_filename"] = "resume.pdf"
            # Fetch JD title if jd_id exists
            if result.get("jd_id"):
                try:
                    jd_obj_id = ObjectId(result["jd_id"])
                    jd = db.job_descriptions.find_one({"_id": jd_obj_id})
                    if jd:
                        result["jd_title"] = jd.get("title", "Job Description")
                except Exception as e:
                    logger.warning(f"Could not fetch JD {result['jd_id']}: {e}")
                    result["jd_title"] = "Job Description"
        
        return {"success": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific analysis by ID."""
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        from bson import ObjectId
        
        try:
            result = db.match_results.find_one({"_id": ObjectId(analysis_id)})
        except Exception:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify user owns this analysis
        if result.get("user_id") != current_user["_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert ObjectId to string
        result["_id"] = str(result["_id"])
        
        # Fetch related data
        if result.get("resume_id"):
            try:
                resume_obj_id = ObjectId(result["resume_id"])
                resume = db.resumes.find_one({"_id": resume_obj_id})
                if resume:
                    result["resume_filename"] = resume.get("filename", "resume.pdf")
            except Exception:
                pass
        
        if result.get("jd_id"):
            try:
                jd_obj_id = ObjectId(result["jd_id"])
                jd = db.job_descriptions.find_one({"_id": jd_obj_id})
                if jd:
                    result["jd_title"] = jd.get("title", "Job Description")
            except Exception:
                pass
        
        # Extract resume and JD text
        resume_data = result.get("resume_data", {})
        jd_data = result.get("jd_data", {})
        
        resume_text = ""
        if resume_data:
            # Try to get raw text from resume data
            resume_text = resume_data.get("raw_text") or resume_data.get("text") or ""
            # If no raw text, try to reconstruct from parsed data
            if not resume_text:
                parts = []
                if resume_data.get("name"):
                    parts.append(f"Name: {resume_data['name']}")
                if resume_data.get("email"):
                    parts.append(f"Email: {resume_data['email']}")
                if resume_data.get("skills"):
                    parts.append(f"Skills: {', '.join(resume_data['skills'])}")
                if resume_data.get("experience"):
                    for exp in resume_data["experience"]:
                        if isinstance(exp, dict):
                            parts.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
                resume_text = "\n".join(parts)
        
        jd_text = ""
        if jd_data:
            jd_text = jd_data.get("raw_text") or jd_data.get("profile_text") or jd_data.get("description") or ""
        
        return {
            "success": True,
            "id": result["_id"],
            "user": result.get("user_id"),
            "resume_data": resume_data,
            "jd_data": jd_data,
            "resume_text": resume_text,
            "jd_text": jd_text,
            "scores": result.get("scores", {}),
            "matching_skills": result.get("matching_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "summary": result.get("summary", ""),
            "interview_questions": result.get("questions", []),
            "created_at": result.get("created_at"),
            "job_title": result.get("jd_title") or jd_data.get("title", "Job Description"),
            "resume_filename": result.get("resume_filename", "resume.pdf"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/summary")
async def get_analytics_summary(current_user: dict = Depends(get_current_user)):
    """Get aggregated analytics summary for the current user."""
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        user_id = current_user["_id"]
        
        # Fetch all analyses for this user
        results = list(db.match_results.find({"user_id": user_id}).sort("created_at", 1))
        
        if not results:
            return {
                "success": True,
                "total_analyses": 0,
                "latest_match_score": 0,
                "best_match_score": 0,
                "average_skill_overlap": 0,
                "most_matched_role": "N/A",
                "trend_data": [],
                "matching_skills_freq": {},
                "missing_skills_freq": {},
                "top_roles": [],
                "overall_average": {"suitability": 0, "semantic": 0, "skills": 0, "experience": 0},
                "ai_recommendation": "Run your first analysis to unlock personalized insights!"
            }
        
        # Calculate basic metrics
        total_analyses = len(results)
        
        # Get latest and best match scores
        latest_result = results[-1]
        latest_match_score = latest_result.get("scores", {}).get("suitability", 0)
        if not latest_match_score:
            latest_match_score = latest_result.get("suitability_score", 0)
        
        best_match_score = max(
            [r.get("scores", {}).get("suitability", 0) or r.get("suitability_score", 0) for r in results]
        )
        
        # Calculate average skill overlap
        skill_overlaps = [
            r.get("scores", {}).get("skill_overlap", 0) or r.get("skill_overlap", 0) for r in results
        ]
        average_skill_overlap = sum(skill_overlaps) / len(skill_overlaps) if skill_overlaps else 0
        
        # Find most matched role (role with highest average match)
        role_scores = {}
        for r in results:
            jd_data = r.get("jd_data", {})
            role_title = jd_data.get("title") or r.get("jd_title") or "Unknown Role"
            match_score = r.get("scores", {}).get("suitability", 0) or r.get("suitability_score", 0)
            
            if role_title not in role_scores:
                role_scores[role_title] = []
            role_scores[role_title].append(match_score)
        
        most_matched_role = "N/A"
        if role_scores:
            most_matched_role = max(role_scores.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]
        
        # Build trend data
        trend_data = []
        for r in results:
            created_at = r.get("created_at", "")
            date_str = created_at[:10] if created_at else ""
            
            scores = r.get("scores", {})
            trend_data.append({
                "date": date_str,
                "match": scores.get("suitability", 0) or r.get("suitability_score", 0),
                "semantic": scores.get("semantic_similarity", 0) or r.get("semantic_similarity", 0),
                "skills": scores.get("skill_overlap", 0) or r.get("skill_overlap", 0),
                "experience": scores.get("experience_relevance", 0) or r.get("experience_relevance", 0),
            })
        
        # Calculate skill frequencies
        matching_skills_freq = {}
        missing_skills_freq = {}
        
        for r in results:
            matching_skills = r.get("matching_skills", [])
            missing_skills = r.get("missing_skills", [])
            
            for skill in matching_skills:
                if skill:
                    matching_skills_freq[skill] = matching_skills_freq.get(skill, 0) + 1
            
            for skill in missing_skills:
                if skill:
                    missing_skills_freq[skill] = missing_skills_freq.get(skill, 0) + 1
        
        # Get top roles with details
        top_roles_data = {}
        for r in results:
            jd_data = r.get("jd_data", {})
            role_title = jd_data.get("title") or r.get("jd_title") or "Unknown Role"
            match_score = r.get("scores", {}).get("suitability", 0) or r.get("suitability_score", 0)
            matching_skills = r.get("matching_skills", [])
            
            if role_title not in top_roles_data:
                top_roles_data[role_title] = {
                    "scores": [],
                    "skills": set()
                }
            
            top_roles_data[role_title]["scores"].append(match_score)
            top_roles_data[role_title]["skills"].update(matching_skills)
        
        # Convert to list format
        top_roles = []
        for role_title, data in top_roles_data.items():
            scores = data["scores"]
            top_roles.append({
                "title": role_title,
                "best_match": max(scores) if scores else 0,
                "average_match": sum(scores) / len(scores) if scores else 0,
                "skills": list(data["skills"])[:5]  # Top 5 skills
            })
        
        # Sort by best_match descending
        top_roles.sort(key=lambda x: x["best_match"], reverse=True)
        top_roles = top_roles[:5]  # Top 5 roles
        
        # Calculate overall averages
        all_suitability = [r.get("scores", {}).get("suitability", 0) or r.get("suitability_score", 0) for r in results]
        all_semantic = [r.get("scores", {}).get("semantic_similarity", 0) or r.get("semantic_similarity", 0) for r in results]
        all_skills = [r.get("scores", {}).get("skill_overlap", 0) or r.get("skill_overlap", 0) for r in results]
        all_experience = [r.get("scores", {}).get("experience_relevance", 0) or r.get("experience_relevance", 0) for r in results]
        
        overall_average = {
            "suitability": sum(all_suitability) / len(all_suitability) if all_suitability else 0,
            "semantic": sum(all_semantic) / len(all_semantic) if all_semantic else 0,
            "skills": sum(all_skills) / len(all_skills) if all_skills else 0,
            "experience": sum(all_experience) / len(all_experience) if all_experience else 0,
        }
        
        # Generate AI recommendation using LLM
        ai_recommendation = "Your resume shows consistent performance. Continue refining your skills alignment with target roles."
        
        if improvement_agent.model:
            try:
                # Build context for LLM
                context = f"""
User has completed {total_analyses} resume analyses.
Latest match score: {latest_match_score:.0f}%
Best match score: {best_match_score:.0f}%
Average skill overlap: {average_skill_overlap:.0f}%
Most matched role: {most_matched_role}

Top matching skills: {', '.join(list(matching_skills_freq.keys())[:5])}
Top missing skills: {', '.join(list(missing_skills_freq.keys())[:5])}

Overall averages:
- Suitability: {overall_average['suitability']:.0f}%
- Semantic: {overall_average['semantic']:.0f}%
- Skills: {overall_average['skills']:.0f}%
- Experience: {overall_average['experience']:.0f}%
"""
                
                prompt = f"""You are a career coach analyzing resume performance data. Provide a concise, actionable recommendation (2-3 sentences) based on this data:

{context}

Focus on:
- Strengths to highlight
- Areas for improvement
- Specific actionable advice

Keep it professional and encouraging."""
                
                response = improvement_agent.model.generate_content(prompt)
                ai_recommendation = response.text.strip()
            except Exception as e:
                logger.warning(f"Failed to generate AI recommendation: {e}")
        
        return {
            "success": True,
            "total_analyses": total_analyses,
            "latest_match_score": latest_match_score,
            "best_match_score": best_match_score,
            "average_skill_overlap": average_skill_overlap,
            "most_matched_role": most_matched_role,
            "trend_data": trend_data,
            "matching_skills_freq": matching_skills_freq,
            "missing_skills_freq": missing_skills_freq,
            "top_roles": top_roles,
            "overall_average": overall_average,
            "ai_recommendation": ai_recommendation,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Interview Sessions (Persistent)
# ---------------------------
from pydantic import BaseModel
from typing import List as _List, Dict as _Dict, Any as _Any, Optional as _Optional


class InterviewSessionUpsert(BaseModel):
    session_id: _Optional[str] = None
    role: _Optional[str] = None
    resume_summary: _Optional[str] = None
    jd_summary: _Optional[str] = None
    questions: _Optional[_List[str]] = None
    chat_history: _Optional[_List[_Dict[str, str]]] = None  # [{role, content, ts?}]
    resume_data: _Optional[_Dict[str, _Any]] = None
    jd_data: _Optional[_Dict[str, _Any]] = None


class EnhancerRequest(BaseModel):
    user_id: str
    jd_id: _Optional[str] = None
    mode: str  # "jd-aligned" | "concise" | "professional" | "ats"
    resume_text: str


@app.post("/enhancer")
async def enhancer(request: EnhancerRequest, current_user: dict = Depends(get_current_user)):
    """
    JD-aware resume enhancement. For 'jd-aligned' mode, pulls JD text from MongoDB.
    Falls back to existing styles for other modes.
    """
    try:
        if current_user["_id"] != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if not improvement_agent.model:
            raise HTTPException(status_code=503, detail="Gemini API not configured")

        db = get_db()
        jd_text = ""
        # Resolve JD text by jd_id if provided
        if request.jd_id and db is not None:
            from bson import ObjectId
            try:
                jd_doc = db.job_descriptions.find_one({"_id": ObjectId(request.jd_id)})
                if jd_doc:
                    parsed = jd_doc.get("parsed_data", {}) or {}
                    jd_text = parsed.get("raw_text") or parsed.get("profile_text") or parsed.get("description") or ""
            except Exception:
                jd_text = ""
        # If no jd_text yet, try to use the latest match_results jd_data as fallback
        if not jd_text and db is not None:
            result = db.match_results.find_one({"user_id": request.user_id}, sort=[("created_at", -1)])
            if result:
                jd_data = result.get("jd_data", {}) or {}
                jd_text = jd_data.get("raw_text") or jd_data.get("profile_text") or jd_data.get("description") or ""

        mode = request.mode.lower()
        if mode == "jd-aligned":
            if not jd_text:
                raise HTTPException(status_code=400, detail="No job description found. Select a JD from your analyses.")
            prompt = f"""You are an expert resume optimization assistant.
Given the user's resume section and the target job description,
rewrite the section to be tailored for that specific job.
Ensure it’s:
- ATS-friendly,
- Matched to the JD’s tone, skills, and key requirements,
- Quantified where possible,
- Authentic and concise.

ORIGINAL RESUME:
{request.resume_text}

TARGET JOB DESCRIPTION:
{jd_text}

ENHANCED OUTPUT:
"""
            response = improvement_agent.model.generate_content(prompt)
            enhanced_text = (response.text or "").strip()
            # Simple keyword extraction heuristic (top skills words that also appear in JD)
            matched_keywords: _List[str] = []
            try:
                resume_words = set([w.strip(".,;:()[]").lower() for w in request.resume_text.split()])
                jd_words = set([w.strip(".,;:()[]").lower() for w in jd_text.split()])
                overlap = [w for w in jd_words if len(w) > 3 and w in resume_words]
                matched_keywords = list(dict.fromkeys(overlap))[:20]
            except Exception:
                matched_keywords = []
            return {"success": True, "enhanced_text": enhanced_text, "matched_keywords": matched_keywords}
        else:
            # Map other modes to existing enhance_resume styles
            style_map = {
                "ats": "ats-friendly",
                "ats-friendly": "ats-friendly",
                "professional": "professional",
                "concise": "concise",
            }
            style = style_map.get(mode, "ats-friendly")
            prompt = f"""You are an expert resume writer. Enhance the following resume section to make it more {style}.

Instructions:
{"Optimize for Applicant Tracking Systems (ATS). Use standard keywords, clear formatting, and industry-standard terminology." if style=="ats-friendly" else
"Enhance for professional tone and clarity. Maintain formality while improving readability." if style=="professional" else
"Make the text more concise while preserving all key information. Remove redundancy."}

Original text:
{request.resume_text}

Enhanced text (return only the enhanced version, no explanations):"""
            response = improvement_agent.model.generate_content(prompt)
            enhanced_text = (response.text or "").strip()
            return {"success": True, "enhanced_text": enhanced_text, "matched_keywords": []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhancer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interview_sessions/{user_id}")
async def list_interview_sessions(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    List interview sessions for a user, sorted newest first.
    """
    try:
        if current_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        db = get_db()
        sessions = list(db.interview_sessions.find({"user_id": user_id}).sort("timestamp", -1))
        for s in sessions:
            s["_id"] = str(s["_id"])
        return {"success": True, "sessions": [{"session_id": s.get("session_id"), "role": s.get("role"), "timestamp": s.get("timestamp")} for s in sessions]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing interview sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interview_sessions/{user_id}/{session_id}")
async def get_interview_session(user_id: str, session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get full interview session (questions, chat, context).
    """
    try:
        if current_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        db = get_db()
        session = db.interview_sessions.find_one({"user_id": user_id, "session_id": session_id})
        if not session:
            return {"success": False, "message": "Session not found"}
        session["_id"] = str(session["_id"])
        return {"success": True, "session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interview session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview_sessions/{user_id}")
async def upsert_interview_session(user_id: str, payload: InterviewSessionUpsert, current_user: dict = Depends(get_current_user)):
    """
    Save or update current interview session.
    Keeps only 5 most recent sessions per user.
    """
    try:
        if current_user["_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        db = get_db()
        from uuid import uuid4
        now_iso = datetime.utcnow().isoformat()
        session_id = payload.session_id or str(uuid4())
        update_doc = {
            "user_id": user_id,
            "session_id": session_id,
            "role": payload.role,
            "resume_summary": payload.resume_summary,
            "jd_summary": payload.jd_summary,
            "questions": payload.questions or [],
            "chat_history": payload.chat_history or [],
            "resume_data": payload.resume_data,
            "jd_data": payload.jd_data,
            "timestamp": now_iso,
        }
        db.interview_sessions.update_one(
            {"user_id": user_id, "session_id": session_id},
            {"$set": update_doc},
            upsert=True
        )
        # Enforce retention (keep 5 most recent)
        sessions = list(db.interview_sessions.find({"user_id": user_id}).sort("timestamp", -1))
        if len(sessions) > 5:
            for s in sessions[5:]:
                db.interview_sessions.delete_one({"_id": s["_id"]})
        return {"success": True, "session_id": session_id, "timestamp": now_iso}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting interview session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/result/{result_id}")
async def delete_result(result_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a match result."""
    try:
        db = get_db()
        from bson import ObjectId
        
        result = db.match_results.find_one({"_id": ObjectId(result_id)})
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Verify user owns this result
        if result["user_id"] != current_user["_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db.match_results.delete_one({"_id": ObjectId(result_id)})
        return {"success": True, "message": "Result deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

