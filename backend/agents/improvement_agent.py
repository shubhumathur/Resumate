"""
ImprovementAgent - Generates explainable summaries using Gemini LLM.
"""
import os
import google.generativeai as genai
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ImprovementAgent:
    """
    Agent responsible for generating explainable summaries using Gemini.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            #genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not found. Summaries will use fallback method.")
        
        

    def generate_summary(self, match_result: Dict) -> str:
        """
        Generate an explainable summary for a candidate match.
        
        Args:
            match_result: Matching result from MatchingAgent
            
        Returns:
            Human-readable summary explaining the match
        """
        if self.model is None:
            return self._generate_fallback_summary(match_result)
        
        try:
            prompt = self._create_summary_prompt(match_result)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return self._generate_fallback_summary(match_result)
    
    def _create_summary_prompt(self, match_result: Dict) -> str:
        """Create prompt for Gemini to generate summary."""
        candidate_name = match_result.get("candidate_name", "Candidate")
        suitability_score = match_result.get("suitability_score", 0)
        semantic_similarity = match_result.get("semantic_similarity", 0)
        skill_overlap = match_result.get("skill_overlap", 0)
        experience_relevance = match_result.get("experience_relevance", 0)
        
        matching_skills = match_result.get("matching_skills", [])
        missing_skills = match_result.get("missing_skills", [])
        
        resume_data = match_result.get("resume_data", {})
        jd_data = match_result.get("jd_data", {})
        
        job_title = jd_data.get("title", "the position")
        resume_skills = resume_data.get("skills", [])
        resume_experience = resume_data.get("experience_years", 0)
        resume_education = resume_data.get("education", "Not specified")
        
        prompt = f"""You are an expert recruiter analyzing a candidate's fit for a job position. 
Generate a concise, professional summary explaining why this candidate received a suitability score of {suitability_score}% for {job_title}.

Candidate Information:
- Name: {candidate_name}
- Education: {resume_education}
- Years of Experience: {resume_experience}
- Skills: {', '.join(resume_skills[:20])}

Job Requirements:
- Title: {job_title}
- Required Skills: {', '.join(jd_data.get('skills_required', [])[:20])}
- Experience Required: {jd_data.get('experience_required', 0)} years

Matching Analysis:
- Semantic Similarity: {semantic_similarity}%
- Skill Overlap: {skill_overlap}%
- Experience Relevance: {experience_relevance}%

Matching Skills: {', '.join(matching_skills[:15]) if matching_skills else 'None'}
Missing Skills: {', '.join(missing_skills[:10]) if missing_skills else 'None'}

Generate a 2-3 paragraph summary that:
1. Highlights the candidate's strengths and relevant skills
2. Explains what skills or experience are missing
3. Provides a clear rationale for the {suitability_score}% suitability score
4. Mentions specific matching and missing skills
5. Is professional, concise, and actionable for recruiters
6. Use appropriate tone:
   - 80-100%: Strong fit, enthusiastic tone
   - 60-80%: Moderate fit, constructive tone
   - <60%: Unfit but with learning recommendations, encouraging tone

Summary:"""
        
        return prompt
    
    def _generate_fallback_summary(self, match_result: Dict) -> str:
        """Generate summary without LLM (fallback method)."""
        candidate_name = match_result.get("candidate_name", "The candidate")
        suitability_score = match_result.get("suitability_score", 0)
        
        matching_skills = match_result.get("matching_skills", [])
        missing_skills = match_result.get("missing_skills", [])
        
        resume_data = match_result.get("resume_data", {})
        jd_data = match_result.get("jd_data", {})
        
        job_title = jd_data.get("title", "the position")
        resume_experience = resume_data.get("experience_years", 0)
        jd_experience = jd_data.get("experience_required", 0)
        
        summary_parts = []
        
        # Introduction
        summary_parts.append(
            f"{candidate_name} has received a suitability score of {suitability_score}% for {job_title}."
        )
        
        # Strengths
        if matching_skills:
            summary_parts.append(
                f"The candidate demonstrates strong alignment with key requirements, particularly in: {', '.join(matching_skills[:10])}."
            )
        
        if resume_experience >= jd_experience:
            summary_parts.append(
                f"With {resume_experience} years of experience, the candidate meets the experience requirements."
            )
        else:
            summary_parts.append(
                f"However, the candidate has {resume_experience} years of experience, which is below the required {jd_experience} years."
            )
        
        # Gaps
        if missing_skills:
            summary_parts.append(
                f"Key areas for improvement include: {', '.join(missing_skills[:5])}."
            )
        
        # Conclusion with score-range-based tone
        if suitability_score >= 80:
            summary_parts.append("Overall, this candidate is a strong fit for the position.")
        elif suitability_score >= 60:
            summary_parts.append("This candidate shows potential but may require additional training or experience.")
        else:
            summary_parts.append("This candidate may not be the best fit for the current position, but could benefit from skill development in the identified areas.")
        
        return " ".join(summary_parts)

