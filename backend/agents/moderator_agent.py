"""
ModeratorAgent - Manages global state and coordinates between agents.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ModeratorAgent:
    """
    Central agent that maintains global state and context between agents.
    Ensures consistent data flow and logging.
    """
    
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.resume_cache: Dict[str, Dict] = {}
        self.jd_cache: Dict[str, Dict] = {}
        self.processing_log: List[Dict] = []
        
    def initialize_session(self, session_id: str) -> None:
        """
        Initialize a new processing session.
        
        Args:
            session_id: Unique session identifier
        """
        self.state[session_id] = {
            "created_at": datetime.now().isoformat(),
            "resumes": [],
            "job_description": None,
            "results": [],
            "status": "initialized"
        }
        logger.info(f"Initialized session: {session_id}")
    
    def update_session(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> None:
        """
        Update session state.
        
        Args:
            session_id: Session identifier
            key: State key to update
            value: Value to set
        """
        if session_id not in self.state:
            self.initialize_session(session_id)
        
        self.state[session_id][key] = value
        logger.debug(f"Updated session {session_id}: {key}")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session state.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session state dictionary or None
        """
        return self.state.get(session_id)
    
    def cache_resume(self, resume_id: str, parsed_data: Dict) -> None:
        """
        Cache parsed resume data.
        
        Args:
            resume_id: Resume identifier
            parsed_data: Parsed resume data
        """
        self.resume_cache[resume_id] = parsed_data
        logger.debug(f"Cached resume: {resume_id}")
    
    def get_cached_resume(self, resume_id: str) -> Optional[Dict]:
        """
        Get cached resume data.
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            Cached resume data or None
        """
        return self.resume_cache.get(resume_id)
    
    def cache_jd(self, jd_id: str, parsed_data: Dict) -> None:
        """
        Cache parsed job description data.
        
        Args:
            jd_id: Job description identifier
            parsed_data: Parsed JD data
        """
        self.jd_cache[jd_id] = parsed_data
        logger.debug(f"Cached JD: {jd_id}")
    
    def get_cached_jd(self, jd_id: str) -> Optional[Dict]:
        """
        Get cached job description data.
        
        Args:
            jd_id: Job description identifier
            
        Returns:
            Cached JD data or None
        """
        return self.jd_cache.get(jd_id)
    
    def log_processing(
        self,
        agent_name: str,
        action: str,
        details: Dict = None
    ) -> None:
        """
        Log agent processing activity.
        
        Args:
            agent_name: Name of the agent
            action: Action performed
            details: Optional details dictionary
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        self.processing_log.append(log_entry)
        logger.info(f"{agent_name}: {action}")
    
    def get_processing_log(self, limit: int = 100) -> List[Dict]:
        """
        Get recent processing log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries
        """
        return self.processing_log[-limit:]
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear session data.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.state:
            del self.state[session_id]
        logger.info(f"Cleared session: {session_id}")


# Global moderator instance
moderator = ModeratorAgent()

