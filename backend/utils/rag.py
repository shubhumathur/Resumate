"""
RAG (Retrieval-Augmented Generation) utilities for knowledge graph integration.
"""
from typing import List, Dict, Any
from pymongo import MongoClient
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class RAGKnowledgeGraph:
    """
    RAG system using MongoDB for knowledge graph storage.
    """
    
    def __init__(self, mongo_uri: str = None, db_name: str = None):
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "resumate")
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
    
    def store_skill_relationship(
        self,
        skill: str,
        role: str,
        importance: float = 1.0
    ):
        """
        Store a skill-role relationship in the knowledge graph.
        
        Args:
            skill: Skill name
            role: Role/job title
            importance: Importance score (0-1)
        """
        if not self.db:
            return
        
        collection = self.db.skill_relationships
        collection.update_one(
            {"skill": skill.lower(), "role": role.lower()},
            {
                "$set": {
                    "skill": skill.lower(),
                    "role": role.lower(),
                    "importance": importance,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
    
    def retrieve_related_skills(self, role: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve skills related to a role from the knowledge graph.
        
        Args:
            role: Job role/title
            limit: Maximum number of skills to return
            
        Returns:
            List of related skills with importance scores
        """
        if not self.db:
            return []
        
        collection = self.db.skill_relationships
        results = collection.find(
            {"role": role.lower()}
        ).sort("importance", -1).limit(limit)
        
        return list(results)
    
    def store_certification_relationship(
        self,
        certification: str,
        role: str,
        relevance: float = 1.0
    ):
        """
        Store a certification-role relationship.
        
        Args:
            certification: Certification name
            role: Role/job title
            relevance: Relevance score (0-1)
        """
        if not self.db:
            return
        
        collection = self.db.certification_relationships
        collection.update_one(
            {"certification": certification.lower(), "role": role.lower()},
            {
                "$set": {
                    "certification": certification.lower(),
                    "role": role.lower(),
                    "relevance": relevance,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
    
    def retrieve_related_certifications(self, role: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve certifications related to a role.
        
        Args:
            role: Job role/title
            limit: Maximum number of certifications to return
            
        Returns:
            List of related certifications
        """
        if not self.db:
            return []
        
        collection = self.db.certification_relationships
        results = collection.find(
            {"role": role.lower()}
        ).sort("relevance", -1).limit(limit)
        
        return list(results)
    
    def store_resume_match(
        self,
        candidate_name: str,
        job_title: str,
        suitability_score: float,
        match_data: Dict
    ):
        """
        Store a resume-match result for learning.
        
        Args:
            candidate_name: Candidate name
            job_title: Job title
            suitability_score: Suitability score
            match_data: Full match data
        """
        if not self.db:
            return
        
        collection = self.db.resume_matches
        collection.insert_one({
            "candidate_name": candidate_name,
            "job_title": job_title,
            "suitability_score": suitability_score,
            "match_data": match_data,
            "created_at": datetime.now()
        })
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global RAG instance
rag_kg = RAGKnowledgeGraph()
