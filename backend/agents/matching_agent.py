"""
MatchingAgent - Computes semantic and explicit matching between resumes and job descriptions.
"""
import sys
import os
from typing import Dict, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.vector_ops import compute_cosine_similarity
from utils.scoring import (
    compute_skill_overlap_score,
    compute_experience_relevance,
    compute_suitability_score,
    extract_matching_skills,
    extract_missing_skills
)
import logging

logger = logging.getLogger(__name__)


class MatchingAgent:
    """
    Agent responsible for computing matching scores between resumes and job descriptions.
    """
    
    def __init__(self):
        self.default_weights = {
            "semantic": 0.6,
            "skills": 0.3,
            "experience": 0.1
        }
    
    def match(
        self,
        resume_data: Dict,
        jd_data: Dict,
        weights: Dict[str, float] = None
    ) -> Dict:
        """
        Compute matching score between a resume and job description.
        
        Args:
            resume_data: Parsed resume data from ResumeParsingAgent
            jd_data: Parsed JD data from JDParsingAgent
            weights: Optional weights for scoring components
            
        Returns:
            Dictionary with matching results
        """
        if weights is None:
            weights = self.default_weights
        
        # Extract components with graceful handling for missing data
        resume_skills = resume_data.get("skills", []) or []
        resume_experience = resume_data.get("experience_years", 0.0) or 0.0
        resume_text = resume_data.get("raw_text", "") or ""
        
        jd_skills = jd_data.get("all_skills", []) or []
        jd_required_skills = jd_data.get("skills_required", []) or []
        jd_experience_required = jd_data.get("experience_required", 0.0) or 0.0
        jd_text = jd_data.get("raw_text", "") or ""
        
        # Build context-aware text blobs for semantic similarity
        # Concatenate all major fields for better context understanding
        from models.sentence_transformer_model import generate_embeddings, get_sentence_transformer_model
        from utils.scoring import normalize_text, is_entry_level_role
        
        # Build comprehensive resume text blob
        if not resume_text or len(resume_text.strip()) < 50:
            resume_components = []
            resume_components.append(resume_data.get("name", ""))
            resume_components.append(resume_data.get("education", ""))
            resume_components.extend(resume_data.get("skills", []) or [])
            resume_components.append(str(resume_data.get("experience_years", "")))
            resume_components.extend(resume_data.get("certifications", []) or [])
            resume_text = " ".join(str(c) for c in resume_components if c)
        
        # Build comprehensive JD text blob
        if not jd_text or len(jd_text.strip()) < 50:
            jd_components = []
            jd_components.append(jd_data.get("title", ""))
            jd_components.append(" ".join(jd_data.get("skills_required", []) or []))
            jd_components.append(" ".join(jd_data.get("skills_preferred", []) or []))
            jd_components.append(" ".join(jd_data.get("responsibilities", []) or []))
            jd_components.append(" ".join(jd_data.get("requirements", []) or []))
            jd_text = " ".join(str(c) for c in jd_components if c)
        
        # Normalize texts for better comparison
        resume_text_normalized = normalize_text(resume_text)
        jd_text_normalized = normalize_text(jd_text)
        
        # Get model for semantic skill matching
        try:
            model = get_sentence_transformer_model()
        except Exception as e:
            logger.warning(f"Failed to load model for semantic skill matching: {e}")
            model = None
        
        # Generate embeddings from full-document texts with chunking support
        # This prevents truncation issues with long resumes/JDs
        try:
            resume_embedding = generate_embeddings(resume_text_normalized, chunk_size=300)
            jd_embedding = generate_embeddings(jd_text_normalized, chunk_size=300)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            resume_embedding = None
            jd_embedding = None
        
        # Compute semantic similarity using full-document embeddings
        if jd_embedding and resume_embedding:
            semantic_similarity = compute_cosine_similarity(resume_embedding, jd_embedding)
            # Ensure semantic similarity is in 0-1 range
            semantic_similarity = max(0.0, min(1.0, semantic_similarity))
        else:
            semantic_similarity = 0.0
            logger.warning("Missing embeddings for semantic similarity calculation - using fallback")
        
        # Compute skill overlap using semantic matching if model available
        # Falls back to keyword-based matching if semantic matching fails
        try:
            from utils.scoring import compute_skill_overlap_score
            skill_overlap = compute_skill_overlap_score(
                resume_skills,
                jd_skills,
                model=model,
                jd_text=jd_text_normalized,
                resume_text=resume_text_normalized
            )
        except Exception as e:
            logger.warning(f"Error computing skill overlap: {e}")
            skill_overlap = 0.0
        
        # Compute experience relevance with intelligent entry-level detection
        try:
            from utils.scoring import compute_experience_relevance
            experience_relevance = compute_experience_relevance(
                resume_experience,
                jd_experience_required,
                resume_text=resume_text,
                jd_text=jd_text
            )
        except Exception as e:
            logger.warning(f"Error computing experience relevance: {e}")
            experience_relevance = 0.5  # Default to 50% if calculation fails
        
        # Compute overall suitability score with adaptive weighting and normalization
        try:
            from utils.scoring import compute_suitability_score
            suitability_score = compute_suitability_score(
                semantic_similarity,
                skill_overlap,
                experience_relevance,
                weights,
                candidate_experience=resume_experience,
                jd_text=jd_text,
                normalize=True  # Apply human-like score normalization
            )
        except Exception as e:
            logger.error(f"Error computing suitability score: {e}")
            # Fallback: simple average if calculation fails
            suitability_score = (
                semantic_similarity * 0.5 +
                skill_overlap * 0.3 +
                experience_relevance * 0.2
            ) * 100
            suitability_score = max(0.0, min(100.0, suitability_score))
        
        # Extract matching and missing skills
        # Try semantic skill extraction first, fallback to keyword-based
        try:
            if model:
                from utils.scoring import compute_semantic_skill_overlap
                matched_skills_semantic, missing_skills_semantic, _ = compute_semantic_skill_overlap(
                    model, jd_text_normalized, resume_text_normalized
                )
                if matched_skills_semantic:
                    matching_skills = matched_skills_semantic
                    missing_skills = missing_skills_semantic[:10]
                else:
                    # Fallback to keyword-based
                    matching_skills = extract_matching_skills(resume_skills, jd_skills)
                    missing_skills = extract_missing_skills(resume_skills, jd_required_skills)[:10]
            else:
                matching_skills = extract_matching_skills(resume_skills, jd_skills)
                missing_skills = extract_missing_skills(resume_skills, jd_required_skills)[:10]
        except Exception as e:
            logger.warning(f"Error extracting skills: {e}")
            matching_skills = extract_matching_skills(resume_skills, jd_skills)
            missing_skills = extract_missing_skills(resume_skills, jd_required_skills)[:10]
        
        # Ensure all scores are in 0-100 range (already normalized)
        # suitability_score is already 0-100 from compute_suitability_score
        semantic_percent = round(max(0.0, min(100.0, semantic_similarity * 100)), 2)
        skill_percent = round(max(0.0, min(100.0, skill_overlap * 100)), 2)
        exp_percent = round(max(0.0, min(100.0, experience_relevance * 100)), 2)
        final_score = round(max(0.0, min(100.0, suitability_score)), 2)
        
        # Canonicalize and deduplicate skills
        from utils.scoring import normalize_skill
        
        # Clean matching skills
        matching_skills_clean = []
        seen_normalized = set()
        for skill in matching_skills:
            normalized = normalize_skill(skill)
            if normalized and normalized not in seen_normalized:
                seen_normalized.add(normalized)
                # Clean up skill display (remove trailing punctuation, title case)
                skill_clean = skill.strip().rstrip('.,;:!?')
                if skill_clean:
                    matching_skills_clean.append(skill_clean)
        
        # Clean missing skills
        missing_skills_clean = []
        seen_normalized_missing = set()
        for skill in missing_skills[:10]:  # Limit to top 10
            normalized = normalize_skill(skill)
            if normalized and normalized not in seen_normalized_missing:
                seen_normalized_missing.add(normalized)
                skill_clean = skill.strip().rstrip('.,;:!?')
                if skill_clean:
                    missing_skills_clean.append(skill_clean)
        
        # Log detailed scoring information with interpretable debug output
        candidate_name = resume_data.get("name", "Unknown")
        logger.info(
            f"[Analyzer] candidate={candidate_name} "
            f"semantic={semantic_percent:.2f}% "
            f"skills_matched={len(matching_skills_clean)} "
            f"jd_skills={len(jd_skills)} "
            f"skill_overlap={skill_percent:.2f}% "
            f"exp_rel={exp_percent:.2f}% "
            f"final={final_score:.2f}%"
        )
        
        return {
            "candidate_name": candidate_name,
            "suitability_score": final_score,  # Already 0-100
            "semantic_similarity": semantic_percent,  # 0-100
            "skill_overlap": skill_percent,  # 0-100
            "experience_relevance": exp_percent,  # 0-100
            "matching_skills": matching_skills_clean,
            "missing_skills": missing_skills_clean,
            "resume_data": resume_data,
            "jd_data": jd_data
        }
    
    def batch_match(
        self,
        resumes_data: List[Dict],
        jd_data: Dict,
        weights: Dict[str, float] = None
    ) -> List[Dict]:
        """
        Compute matching scores for multiple resumes.
        
        Args:
            resumes_data: List of parsed resume data
            jd_data: Parsed JD data
            weights: Optional weights for scoring components
            
        Returns:
            List of matching results, sorted by suitability score (descending)
        """
        results = []
        
        for resume_data in resumes_data:
            try:
                match_result = self.match(resume_data, jd_data, weights)
                results.append(match_result)
            except Exception as e:
                logger.error(f"Error matching resume: {e}")
                continue
        
        # Sort by suitability score (descending)
        results.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        return results
    
    @staticmethod
    def test_matching_cases() -> None:
        """
        Test function that tests 4 predefined JD-resume pairs:
        1. Identical match (expected: 95-100%)
        2. Partial match (expected: 70-90%)
        3. Related domain (expected: 50-70%)
        4. Unrelated domain (expected: <40%)
        
        Prints all sub-scores for debugging.
        """
        from agents.resume_parser_agent import ResumeParsingAgent
        from agents.jd_parser_agent import JDParsingAgent
        
        # Initialize agents
        resume_parser = ResumeParsingAgent()
        jd_parser = JDParsingAgent()
        matching_agent = MatchingAgent()
        
        # Test Case 1: Identical Match
        print("=" * 80)
        print("TEST CASE 1: IDENTICAL MATCH (Expected: 95-100%)")
        print("=" * 80)
        
        jd1_text = """
        Job Title: Machine Learning Engineer
        
        Required Skills: Python, Machine Learning, TensorFlow, Deep Learning, NLP, AWS
        
        Experience Required: 3-5 years
        
        Responsibilities:
        - Develop and deploy ML models
        - Work with NLP and computer vision
        - Manage cloud infrastructure on AWS
        """
        
        resume1_text = """
        John Doe
        Machine Learning Engineer
        
        Skills: Python, Machine Learning, TensorFlow, Deep Learning, NLP, AWS
        
        Experience: 4 years of machine learning experience
        
        Responsibilities:
        - Developed and deployed ML models
        - Worked with NLP and computer vision
        - Managed cloud infrastructure on AWS
        """
        
        jd1_data = jd_parser.parse(jd1_text)
        resume1_data = resume_parser.parse(resume1_text)
        result1 = matching_agent.match(resume1_data, jd1_data)
        
        print(f"Candidate: {result1['candidate_name']}")
        print(f"Suitability Score: {result1['suitability_score']}%")
        print(f"  - Semantic Similarity: {result1['semantic_similarity']}%")
        print(f"  - Skill Overlap: {result1['skill_overlap']}%")
        print(f"  - Experience Relevance: {result1['experience_relevance']}%")
        print(f"Status: {'✅ PASS' if result1['suitability_score'] >= 95 else '❌ FAIL'}")
        print()
        
        # Test Case 2: Partial Match
        print("=" * 80)
        print("TEST CASE 2: PARTIAL MATCH (Expected: 70-90%)")
        print("=" * 80)
        
        jd2_text = """
        Job Title: Senior Software Engineer
        
        Required Skills: Python, Django, PostgreSQL, Docker, Kubernetes, AWS
        
        Experience Required: 5-7 years
        
        Responsibilities:
        - Design and develop web applications
        - Manage database systems
        - Deploy applications using Docker and Kubernetes
        """
        
        resume2_text = """
        Jane Smith
        Software Engineer
        
        Skills: Python, Flask, MySQL, Docker, AWS
        
        Experience: 3 years of software development experience
        
        Responsibilities:
        - Developed web applications
        - Worked with databases
        - Deployed applications using Docker
        """
        
        jd2_data = jd_parser.parse(jd2_text)
        resume2_data = resume_parser.parse(resume2_text)
        result2 = matching_agent.match(resume2_data, jd2_data)
        
        print(f"Candidate: {result2['candidate_name']}")
        print(f"Suitability Score: {result2['suitability_score']}%")
        print(f"  - Semantic Similarity: {result2['semantic_similarity']}%")
        print(f"  - Skill Overlap: {result2['skill_overlap']}%")
        print(f"  - Experience Relevance: {result2['experience_relevance']}%")
        print(f"Status: {'✅ PASS' if 70 <= result2['suitability_score'] <= 90 else '⚠️  CHECK'}")
        print()
        
        # Test Case 3: Related Domain
        print("=" * 80)
        print("TEST CASE 3: RELATED DOMAIN (Expected: 50-70%)")
        print("=" * 80)
        
        jd3_text = """
        Job Title: Data Scientist
        
        Required Skills: Python, Machine Learning, SQL, Statistics, Data Analysis
        
        Experience Required: 2-4 years
        
        Responsibilities:
        - Analyze large datasets
        - Build predictive models
        - Create data visualizations
        """
        
        resume3_text = """
        Bob Johnson
        Machine Learning Engineer
        
        Skills: Python, TensorFlow, Deep Learning, AWS
        
        Experience: 2 years of ML engineering experience
        
        Responsibilities:
        - Built ML models
        - Deployed models to production
        - Optimized model performance
        """
        
        jd3_data = jd_parser.parse(jd3_text)
        resume3_data = resume_parser.parse(resume3_text)
        result3 = matching_agent.match(resume3_data, jd3_data)
        
        print(f"Candidate: {result3['candidate_name']}")
        print(f"Suitability Score: {result3['suitability_score']}%")
        print(f"  - Semantic Similarity: {result3['semantic_similarity']}%")
        print(f"  - Skill Overlap: {result3['skill_overlap']}%")
        print(f"  - Experience Relevance: {result3['experience_relevance']}%")
        print(f"Status: {'✅ PASS' if 50 <= result3['suitability_score'] <= 70 else '⚠️  CHECK'}")
        print()
        
        # Test Case 4: Unrelated Domain
        print("=" * 80)
        print("TEST CASE 4: UNRELATED DOMAIN (Expected: <40%)")
        print("=" * 80)
        
        jd4_text = """
        Job Title: Marketing Manager
        
        Required Skills: Digital Marketing, SEO, Social Media, Content Marketing, Analytics
        
        Experience Required: 3-5 years
        
        Responsibilities:
        - Develop marketing strategies
        - Manage social media campaigns
        - Analyze marketing metrics
        """
        
        resume4_text = """
        Alice Brown
        Software Developer
        
        Skills: Java, Spring Boot, MySQL, REST APIs
        
        Experience: 4 years of backend development
        
        Responsibilities:
        - Developed REST APIs
        - Designed database schemas
        - Implemented microservices
        """
        
        jd4_data = jd_parser.parse(jd4_text)
        resume4_data = resume_parser.parse(resume4_text)
        result4 = matching_agent.match(resume4_data, jd4_data)
        
        print(f"Candidate: {result4['candidate_name']}")
        print(f"Suitability Score: {result4['suitability_score']}%")
        print(f"  - Semantic Similarity: {result4['semantic_similarity']}%")
        print(f"  - Skill Overlap: {result4['skill_overlap']}%")
        print(f"  - Experience Relevance: {result4['experience_relevance']}%")
        print(f"Status: {'✅ PASS' if result4['suitability_score'] < 40 else '⚠️  CHECK'}")
        print()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Test 1 (Identical): {result1['suitability_score']}% - {'✅ PASS' if result1['suitability_score'] >= 95 else '❌ FAIL'}")
        print(f"Test 2 (Partial): {result2['suitability_score']}% - {'✅ PASS' if 70 <= result2['suitability_score'] <= 90 else '⚠️  CHECK'}")
        print(f"Test 3 (Related): {result3['suitability_score']}% - {'✅ PASS' if 50 <= result3['suitability_score'] <= 70 else '⚠️  CHECK'}")
        print(f"Test 4 (Unrelated): {result4['suitability_score']}% - {'✅ PASS' if result4['suitability_score'] < 40 else '⚠️  CHECK'}")
        print("=" * 80)

