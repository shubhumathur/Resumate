"""
ResumeParsingAgent - Extracts structured data from resume text using spaCy NER.
"""
import spacy
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ResumeParsingAgent:
    """
    Agent responsible for parsing resumes and extracting structured information.
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def parse(self, resume_text: str) -> Dict:
        """
        Parse resume text and extract structured information.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dictionary with parsed resume data
        """
        if self.nlp is None:
            # Fallback to regex-based parsing if spaCy is not available
            return self._parse_with_regex(resume_text)
        
        doc = self.nlp(resume_text)
        
        # Extract entities
        name = self._extract_name(resume_text, doc)
        skills = self._extract_skills(resume_text, doc)
        education = self._extract_education(resume_text, doc)
        experience_years = self._extract_experience_years(resume_text, doc)
        certifications = self._extract_certifications(resume_text, doc)
        email = self._extract_email(resume_text)
        phone = self._extract_phone(resume_text)
        
        return {
            "name": name,
            "skills": skills,
            "education": education,
            "experience_years": experience_years,
            "certifications": certifications,
            "email": email,
            "phone": phone,
            "raw_text": resume_text
        }
    
    def _extract_name(self, text: str, doc) -> Optional[str]:
        """Extract candidate name (usually at the beginning of resume)."""
        # Try to find PERSON entities
        if doc:
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    # Name is usually in the first few lines
                    lines = text.split('\n')[:5]
                    if any(ent.text in line for line in lines):
                        return ent.text.strip()
        
        # Fallback: First line that looks like a name
        lines = text.split('\n')[:3]
        for line in lines:
            line = line.strip()
            if len(line) > 0 and len(line.split()) <= 4:
                # Check if it contains title-like words
                if not any(word.lower() in line.lower() for word in ['resume', 'cv', 'email', 'phone', 'linkedin']):
                    return line
        
        return None
    
    def _extract_skills(self, text: str, doc) -> List[str]:
        """Extract skills from resume using master list and section parsing."""
        import json
        import os
        
        skills = []
        
        # Try to load skills master list
        skills_master_list = []
        try:
            skills_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'skills_master_list.json')
            if os.path.exists(skills_file):
                with open(skills_file, 'r', encoding='utf-8') as f:
                    skills_master_list = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load skills master list: {e}")
            # Fallback to hardcoded list
            skills_master_list = [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
                'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'machine learning',
                'deep learning', 'nlp', 'computer vision', 'aws', 'azure', 'gcp',
                'docker', 'kubernetes', 'jenkins', 'git', 'sql', 'nosql', 'mongodb',
                'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka', 'spark',
                'hadoop', 'tableau', 'power bi', 'agile', 'scrum', 'ci/cd'
            ]
        
        text_lower = text.lower()
        
        # Find skills mentioned in text using master list
        for skill in skills_master_list:
            skill_lower = skill.lower()
            if skill_lower in text_lower:
                # Format skill name
                if len(skill.split()) == 1:
                    skill_formatted = skill.title()
                else:
                    skill_formatted = skill.title()
                if skill_formatted not in skills:
                    skills.append(skill_formatted)
        
        # Look for "Skills:" section
        skills_section = self._extract_section(text, ['skills', 'technical skills', 'competencies'])
        if skills_section:
            # Extract words/phrases from skills section
            lines = skills_section.split('\n')
            for line in lines:
                # Split by common separators
                items = re.split(r'[,;|•]', line)
                for item in items:
                    item = item.strip()
                    # Remove trailing punctuation
                    item = item.rstrip('.,;:!?')
                    if len(item) > 2 and item not in skills:
                        skills.append(item)
        
        # Deduplicate and normalize
        from utils.scoring import normalize_skill
        seen_normalized = set()
        skills_deduped = []
        for skill in skills:
            normalized = normalize_skill(skill)
            if normalized and normalized not in seen_normalized:
                seen_normalized.add(normalized)
                skills_deduped.append(skill)
        
        return skills_deduped[:50]  # Limit to top 50 skills
    
    def _extract_education(self, text: str, doc) -> Optional[str]:
        """Extract education information."""
        education_section = self._extract_section(text, ['education', 'academic', 'qualifications'])
        
        if education_section:
            # Extract first significant line
            lines = education_section.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 10 and any(word in line.lower() for word in ['bachelor', 'master', 'phd', 'degree', 'diploma', 'university', 'college']):
                    return line
        
        # Fallback: Look for education patterns in full text
        education_patterns = [
            r'B\.?[Ss]\.?[Cc]\.?[Ss]\.?',
            r'M\.?[Ss]\.?[Cc]\.?[Ss]\.?',
            r'Ph\.?D\.?',
            r'Bachelor.*?Science',
            r'Master.*?Science',
            r'Bachelor.*?Engineering',
            r'Master.*?Engineering'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_experience_years(self, text: str, doc) -> float:
        """Extract years of experience using improved extraction logic."""
        # Use the improved experience extraction from scoring utils
        try:
            from utils.scoring import extract_experience_value, is_entry_level_role
            
            # Check if resume indicates entry-level/internship
            if is_entry_level_role(text):
                return 0.5  # Treat as entry-level
            
            # Look for experience patterns in the text
            patterns = [
                r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
                r'experience.*?(\d+)\+?\s*years?',
                r'(\d+)\+?\s*years?\s*in',
                r'(\d+)\s*[-–]\s*(\d+)\s*years?',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Use extract_experience_value for consistent parsing
                    if isinstance(matches[0], tuple):
                        # Range match
                        exp_text = f"{matches[0][0]}-{matches[0][1]} years"
                    else:
                        exp_text = f"{matches[0]} years"
                    
                    experience = extract_experience_value(exp_text)
                    if experience > 0:
                        return experience
            
            # Fallback: Count experience entries and estimate
            experience_section = self._extract_section(text, ['experience', 'work experience', 'employment'])
            if experience_section:
                # Count date ranges
                date_pattern = r'\d{4}\s*[-–]\s*\d{4}|\d{4}\s*[-–]\s*(?:present|current)'
                matches = re.findall(date_pattern, experience_section)
                if matches:
                    # Estimate: assume average 2-3 years per position
                    estimated = len(matches) * 2.5
                    # Use extract_experience_value for consistency
                    return extract_experience_value(f"{estimated} years")
        except ImportError:
            # Fallback to original logic if import fails
            pass
        
        # Original fallback logic
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience.*?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except (ValueError, IndexError):
                    continue
        
        return 0.0
    
    def _extract_certifications(self, text: str, doc) -> List[str]:
        """Extract certifications."""
        certifications = []
        
        # Look for certifications section
        cert_section = self._extract_section(text, ['certifications', 'certificates', 'licenses'])
        
        if cert_section:
            lines = cert_section.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 5 and any(word in line.lower() for word in ['certified', 'certification', 'certificate', 'aws', 'azure', 'google']):
                    certifications.append(line)
        
        # Look for common certification patterns
        cert_patterns = [
            r'AWS\s+Certified.*?',
            r'Azure\s+.*?Certified',
            r'Google\s+.*?Certified',
            r'PMP\s+Certified',
            r'CISSP',
            r'Cisco\s+.*?Certified'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)
        
        return list(set(certifications))[:20]  # Limit to 20 unique certifications
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number."""
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{10,15}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract a specific section from resume."""
        text_lower = text.lower()
        lines = text.split('\n')
        
        for section_name in section_names:
            section_name_lower = section_name.lower()
            
            # Find section header
            for i, line in enumerate(lines):
                if section_name_lower in line.lower() and len(line.strip()) < 50:
                    # Extract content until next section
                    section_lines = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Stop at next section header (all caps or short line)
                        if len(next_line) > 0 and (
                            next_line.isupper() or 
                            (len(next_line) < 30 and any(word in next_line.lower() for word in ['experience', 'education', 'skills', 'projects', 'certifications']))
                        ):
                            break
                        section_lines.append(lines[j])
                    
                    return '\n'.join(section_lines)
        
        return None
    
    def _parse_with_regex(self, resume_text: str) -> Dict:
        """Fallback parsing using regex when spaCy is not available."""
        return {
            "name": self._extract_name(resume_text, None),
            "skills": self._extract_skills(resume_text, None),
            "education": self._extract_education(resume_text, None),
            "experience_years": self._extract_experience_years(resume_text, None),
            "certifications": self._extract_certifications(resume_text, None),
            "email": self._extract_email(resume_text),
            "phone": self._extract_phone(resume_text),
            "raw_text": resume_text
        }

