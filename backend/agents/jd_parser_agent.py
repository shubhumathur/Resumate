"""
JDParsingAgent - Parses and vectorizes job descriptions.
"""
import re
import sys
import os
from typing import Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.sentence_transformer_model import generate_embeddings
import logging

logger = logging.getLogger(__name__)


class JDParsingAgent:
    """
    Agent responsible for parsing job descriptions and creating embeddings.
    """
    
    def __init__(self):
        self.required_skills_keywords = ['required', 'must have', 'essential', 'mandatory']
        self.preferred_skills_keywords = ['preferred', 'nice to have', 'bonus', 'plus']
    
    def parse(self, jd_text: str) -> Dict:
        """
        Parse job description and extract structured information.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Dictionary with parsed JD data including embeddings
        """
        # Extract structured components
        title = self._extract_job_title(jd_text)
        skills_required = self._extract_required_skills(jd_text)
        skills_preferred = self._extract_preferred_skills(jd_text)
        all_skills = list(set(skills_required + skills_preferred))
        
        experience_required = self._extract_experience_required(jd_text)
        responsibilities = self._extract_responsibilities(jd_text)
        requirements = self._extract_requirements(jd_text)
        
        # Generate embeddings
        embedding = generate_embeddings(jd_text)
        
        # Create a combined profile text for better matching
        profile_text = self._create_profile_text(
            title, skills_required, skills_preferred,
            experience_required, responsibilities, requirements
        )
        profile_embedding = generate_embeddings(profile_text)
        
        # Ensure skills_count is the length of unique skills
        skills_count = len(all_skills) if all_skills else 0
        
        return {
            "title": title,
            "skills_required": skills_required,
            "skills_preferred": skills_preferred,
            "all_skills": all_skills,
            "skills_count": skills_count,  # Add explicit skills count
            "experience_required": experience_required,
            "responsibilities": responsibilities,
            "requirements": requirements,
            "raw_text": jd_text,
            "embedding": embedding,
            "profile_embedding": profile_embedding,
            "profile_text": profile_text
        }
    
    def _extract_job_title(self, text: str) -> Optional[str]:
        """Extract job title from JD."""
        # Usually in the first few lines
        lines = text.split('\n')[:10]
        
        for line in lines:
            line = line.strip()
            # Job titles are usually short and contain keywords
            if 5 < len(line) < 100:
                if any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'scientist', 'specialist', 'architect', 'lead']):
                    return line
        
        # Fallback: Look for patterns
        title_patterns = [
            r'Job\s+Title[:\s]+(.+)',
            r'Position[:\s]+(.+)',
            r'(Senior|Junior|Lead)?\s*(Software|Data|ML|AI|DevOps|Cloud|Backend|Frontend)?\s*(Engineer|Developer|Scientist|Analyst|Architect|Manager)'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip() if isinstance(matches[0], str) else ' '.join(matches[0]).strip()
        
        return None
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from JD."""
        skills = []
        
        # Look for skills section
        skills_section = self._extract_section(text, ['required skills', 'must have', 'essential skills', 'requirements'])
        
        if skills_section:
            # Extract skills from section
            skills.extend(self._parse_skills_from_text(skills_section))
        
        # Also look in general text for common skills
        common_skills = self._extract_common_skills(text)
        skills.extend(common_skills)
        
        return list(set(skills))[:30]  # Limit to 30 unique skills
    
    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills from JD."""
        skills = []
        
        # Look for preferred skills section
        preferred_section = self._extract_section(text, ['preferred', 'nice to have', 'bonus', 'plus'])
        
        if preferred_section:
            skills.extend(self._parse_skills_from_text(preferred_section))
        
        return list(set(skills))[:20]
    
    def _extract_experience_required(self, text: str) -> float:
        """Extract required years of experience."""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience.*?(\d+)\+?\s*years?',
            r'minimum.*?(\d+)\+?\s*years?',
            r'at least\s+(\d+)\+?\s*years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return 0.0
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities."""
        responsibilities = []
        
        resp_section = self._extract_section(text, ['responsibilities', 'duties', 'what you will do'])
        
        if resp_section:
            # Extract bullet points
            lines = resp_section.split('\n')
            for line in lines:
                line = line.strip()
                # Remove bullet markers
                line = re.sub(r'^[•\-\*\d+\.]\s*', '', line)
                if len(line) > 10:
                    responsibilities.append(line)
        
        return responsibilities[:20]  # Limit to 20 responsibilities
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements."""
        requirements = []
        
        req_section = self._extract_section(text, ['requirements', 'qualifications', 'must have'])
        
        if req_section:
            lines = req_section.split('\n')
            for line in lines:
                line = line.strip()
                line = re.sub(r'^[•\-\*\d+\.]\s*', '', line)
                if len(line) > 10:
                    requirements.append(line)
        
        return requirements[:20]
    
    def _extract_common_skills(self, text: str) -> List[str]:
        """Extract common technical skills mentioned in text using master list."""
        import json
        import os
        
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
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'fastapi', 'spring',
                'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'machine learning',
                'deep learning', 'nlp', 'natural language processing', 'computer vision',
                'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
                'docker', 'kubernetes', 'jenkins', 'git', 'sql', 'nosql', 'mongodb',
                'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka', 'apache spark',
                'hadoop', 'tableau', 'power bi', 'agile', 'scrum', 'ci/cd', 'terraform',
                'ansible', 'linux', 'unix', 'rest api', 'graphql', 'microservices'
            ]
        
        skills_found = []
        text_lower = text.lower()
        
        # Use n-gram matching (1-3 grams) to capture multi-word skills
        for skill in skills_master_list:
            skill_lower = skill.lower()
            # Check for exact match or as part of a phrase
            if skill_lower in text_lower:
                # Format skill name (title case for single words, preserve case for multi-word)
                if len(skill.split()) == 1:
                    skill_formatted = skill.title()
                else:
                    skill_formatted = skill.title()  # Title case for multi-word
                if skill_formatted not in skills_found:
                    skills_found.append(skill_formatted)
        
        return skills_found
    
    def _parse_skills_from_text(self, text: str) -> List[str]:
        """Parse skills from a text block with normalization."""
        skills = []
        
        # Split by common separators
        items = re.split(r'[,;|•\n]', text)
        
        for item in items:
            item = item.strip()
            # Remove common prefixes/suffixes
            item = re.sub(r'^(required|preferred|must have|nice to have)[:\s]*', '', item, flags=re.IGNORECASE)
            # Remove trailing punctuation
            item = item.rstrip('.,;:!?')
            # Remove section prefixes like "Languages:", "Tools:", etc.
            item = re.sub(r'^(languages?|tools?|frameworks?|technologies?|databases?|platforms?|skills?)[:\s]*', '', item, flags=re.IGNORECASE)
            item = item.strip()
            if len(item) > 2 and len(item) < 100:
                skills.append(item)
        
        # Deduplicate using normalized form
        from utils.scoring import normalize_skill
        seen_normalized = set()
        skills_deduped = []
        for skill in skills:
            normalized = normalize_skill(skill)
            if normalized and normalized not in seen_normalized:
                seen_normalized.add(normalized)
                skills_deduped.append(skill)
        
        return skills_deduped
    
    def _extract_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract a specific section from JD."""
        text_lower = text.lower()
        lines = text.split('\n')
        
        for section_name in section_names:
            section_name_lower = section_name.lower()
            
            # Find section header
            for i, line in enumerate(lines):
                if section_name_lower in line.lower() and len(line.strip()) < 100:
                    # Extract content until next section
                    section_lines = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Stop at next major section
                        if len(next_line) > 0 and (
                            next_line.isupper() or 
                            (len(next_line) < 50 and any(word in next_line.lower() for word in ['experience', 'education', 'skills', 'responsibilities', 'requirements', 'qualifications', 'benefits', 'salary']))
                        ):
                            break
                        section_lines.append(lines[j])
                    
                    return '\n'.join(section_lines)
        
        return None
    
    def _create_profile_text(
        self,
        title: Optional[str],
        skills_required: List[str],
        skills_preferred: List[str],
        experience_required: float,
        responsibilities: List[str],
        requirements: List[str]
    ) -> str:
        """Create a combined profile text for better semantic matching."""
        parts = []
        
        if title:
            parts.append(f"Job Title: {title}")
        
        if skills_required:
            parts.append(f"Required Skills: {', '.join(skills_required)}")
        
        if skills_preferred:
            parts.append(f"Preferred Skills: {', '.join(skills_preferred)}")
        
        if experience_required > 0:
            parts.append(f"Experience Required: {experience_required} years")
        
        if responsibilities:
            parts.append(f"Responsibilities: {' '.join(responsibilities[:5])}")
        
        if requirements:
            parts.append(f"Requirements: {' '.join(requirements[:5])}")
        
        return " | ".join(parts)

