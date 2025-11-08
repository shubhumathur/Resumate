"""
QuestionAgent - Generates personalized interview questions based on resume.
"""
import os
import re
import google.generativeai as genai
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class QuestionAgent:
    """
    Agent responsible for generating personalized interview questions.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            #genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not found. Questions will use fallback method.")
    
    def generate_questions(
        self,
        resume_data: Dict,
        jd_data: Dict,
        num_questions: int = 5
    ) -> List[str]:
        """
        Generate personalized interview questions.
        
        Args:
            resume_data: Parsed resume data
            jd_data: Parsed JD data
            num_questions: Number of questions to generate
            
        Returns:
            List of interview questions
        """
        if self.model is None:
            return self._generate_fallback_questions(resume_data, jd_data, num_questions)
        
        try:
            prompt = self._create_question_prompt(resume_data, jd_data, num_questions)
            response = self.model.generate_content(prompt)
            questions_text = response.text
            
            # Parse questions from response
            questions = self._parse_questions(questions_text)
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"Error generating questions with Gemini: {e}")
            return self._generate_fallback_questions(resume_data, jd_data, num_questions)
    
    def _create_question_prompt(self, resume_data: Dict, jd_data: Dict, num_questions: int) -> str:
        """Create prompt for Gemini to generate questions."""
        candidate_name = resume_data.get("name", "Candidate")
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience_years", 0)
        education = resume_data.get("education", "Not specified")
        certifications = resume_data.get("certifications", [])
        
        job_title = jd_data.get("title", "the position")
        jd_skills = jd_data.get("skills_required", [])
        responsibilities = jd_data.get("responsibilities", [])
        
        prompt = f"""Generate {num_questions} personalized interview questions for {candidate_name} applying for {job_title}.

Candidate Profile:
- Education: {education}
- Experience: {experience} years
- Key Skills: {', '.join(skills[:20])}
- Certifications: {', '.join(certifications[:10]) if certifications else 'None'}

Job Requirements:
- Title: {job_title}
- Required Skills: {', '.join(jd_skills[:20])}
- Key Responsibilities: {', '.join(responsibilities[:5]) if responsibilities else 'Not specified'}

Generate {num_questions} specific, technical interview questions that:
1. Relate to the candidate's specific skills and experience
2. Test their knowledge relevant to the job requirements
3. Are tailored to their background (not generic)
4. Include both technical and behavioral aspects
5. Are professional and appropriate

Format each question on a new line, numbered 1-{num_questions}.

Questions:"""
        
        return prompt
    
    def _parse_questions(self, questions_text: str) -> List[str]:
        """Parse questions from LLM response."""
        questions = []
        lines = questions_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove numbering
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            # Remove markdown formatting
            line = re.sub(r'^[-*]\s*', '', line)
            
            if len(line) > 20 and line.endswith('?'):
                questions.append(line)
            elif len(line) > 20 and '?' in line:
                questions.append(line)
        
        return questions
    
    def _generate_fallback_questions(
        self,
        resume_data: Dict,
        jd_data: Dict,
        num_questions: int
    ) -> List[str]:
        """Generate fallback questions without LLM."""
        questions = []
        
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience_years", 0)
        job_title = jd_data.get("title", "this position")
        
        # Generate skill-based questions
        if skills:
            for skill in skills[:min(3, num_questions)]:
                questions.append(
                    f"Can you describe a project where you used {skill}? What challenges did you face?"
                )
        
        # Generate experience-based questions
        if experience > 0 and len(questions) < num_questions:
            questions.append(
                f"With {experience} years of experience, what has been your biggest professional achievement?"
            )
        
        # Generate role-specific questions
        if len(questions) < num_questions:
            questions.append(
                f"Why are you interested in {job_title}? What unique value do you bring?"
            )
        
        # Fill remaining with generic questions
        generic_questions = [
            "How do you stay updated with the latest technologies in your field?",
            "Can you walk me through a challenging problem you solved recently?",
            "How do you handle tight deadlines and multiple priorities?",
            "What is your approach to learning new technologies?"
        ]
        
        while len(questions) < num_questions and generic_questions:
            questions.append(generic_questions.pop(0))
        
        return questions[:num_questions]
