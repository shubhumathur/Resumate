"""
Scoring utilities for candidate matching.
"""
import re
import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

# Enhanced synonym expansion for better skill matching
SYNONYMS = {
    "rest api": ["restful api", "restful apis", "rest apis", "api development", "rest services"],
    "nosql": ["no sql", "mongodb", "mongo", "non-relational", "document database"],
    "llm": ["large language model", "language model", "llms", "transformer model", "generative ai"],
    "nlp": ["natural language processing", "text processing", "language understanding"],
    "ml": ["machine learning", "ml algorithms", "predictive modeling"],
    "deep learning": ["neural networks", "cnn", "rnn", "lstm", "neural net"],
    "ai": ["artificial intelligence", "intelligent systems"],
    "aws": ["amazon web services", "amazon aws", "ec2", "s3", "lambda"],
    "gcp": ["google cloud platform", "google cloud", "gcp services"],
    "azure": ["microsoft azure", "azure cloud"],
    "ci/cd": ["continuous integration", "continuous deployment", "cicd", "devops"],
    "api": ["apis", "application programming interface", "web api", "rest api"],
    "docker": ["containerization", "containers", "docker containers"],
    "kubernetes": ["k8s", "container orchestration", "kube"],
    "python": ["python programming", "python3", "python development"],
    "javascript": ["js", "node.js", "nodejs", "typescript"],
    "java": ["java programming", "java development", "spring boot"],
    "sql": ["database", "relational database", "mysql", "postgresql"],
    "git": ["version control", "github", "gitlab", "source control"],
}

# Section prefixes to remove from skills/responsibilities
SECTION_PREFIXES = [
    "ai/ml tools:",
    "frameworks & tools:",
    "languages:",
    "technologies:",
    "skills:",
    "technical skills:",
    "programming languages:",
    "tools:",
    "software:",
    "platforms:",
]


def normalize_text(text: str) -> str:
    """
    Comprehensive text normalization for fairness in comparisons.
    - Lowercases everything
    - Removes punctuation and special characters
    - Normalizes plurals and hyphens
    - Strips section prefixes
    - Normalizes whitespace
    
    Args:
        text: Text string to normalize
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove section prefixes (e.g., "AI/ML Tools:", "Languages:")
    for prefix in SECTION_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Normalize hyphens and slashes to spaces (e.g., "REST-API" -> "rest api")
    text = re.sub(r'[-/]', ' ', text)
    
    # Remove punctuation and special characters, keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Normalize whitespace (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill string for comparison.
    Removes prefixes (e.g., "Databases: MySQL" -> "MySQL") and standardizes format.
    
    Args:
        skill: Skill string to normalize (e.g., "Databases: MySQL", "Agentic AI: CrewAI")
        
    Returns:
        Normalized skill string (lowercase, no prefix, trimmed)
    """
    if not skill:
        return ""
    
    # Remove section prefixes (e.g., "Databases: MySQL" -> "MySQL")
    # Pattern matches "Category: Skill" or "Category - Skill" or "Category | Skill"
    # More aggressive: match any text before colon/dash/pipe followed by whitespace
    skill = re.sub(r'^[^:|\-]+[:|\-|]\s*', '', skill, flags=re.IGNORECASE)
    skill = skill.strip()
    
    # Remove any remaining prefixes like "Skills:", "Technologies:", etc.
    skill = re.sub(r'^(skills?|technologies?|tools?|languages?|frameworks?|databases?|platforms?|agentic\s+ai|ai/ml\s+tools?):\s*', '', skill, flags=re.IGNORECASE)
    skill = skill.strip()
    
    # Apply standard normalization (lowercase, remove punctuation, trim)
    normalized = skill.lower().strip()
    normalized = re.sub(r'[.,:;!?()\[\]{}]', '', normalized)
    normalized = normalized.strip()
    
    return normalized


def expand_skill_synonyms(skill: str) -> Set[str]:
    """
    Expand a skill with its synonyms for flexible matching.
    
    Args:
        skill: Skill string
        
    Returns:
        Set of normalized skill variations (original normalized + synonyms)
    """
    normalized = normalize_skill(skill)
    variations = {normalized}
    
    # Check if normalized skill matches any synonym key or value
    for key, synonyms in SYNONYMS.items():
        key_normalized = normalize_skill(key)
        synonyms_normalized = [normalize_skill(s) for s in synonyms]
        
        # If our skill matches the key or any synonym, add all related variations
        if normalized == key_normalized or normalized in synonyms_normalized:
            variations.add(key_normalized)
            variations.update(synonyms_normalized)
    
    return variations


def extract_skills_dynamic(text: str) -> List[str]:
    """
    Extract skills dynamically from text using pattern matching.
    Works for any domain without requiring predefined skill lists.
    
    Args:
        text: Text containing skills
        
    Returns:
        List of extracted skills
    """
    if not text:
        return []
    
    text_lower = text.lower()
    # Remove special characters but keep alphanumeric, spaces, and common separators
    text_clean = re.sub(r'[^a-z0-9\s,\.\-\&\+/]', ' ', text_lower)
    
    # Split by common separators
    parts = re.split(r'[,\n;•|]', text_clean)
    
    skills = []
    for part in parts:
        part = part.strip()
        # Filter out very short or very long parts, and common non-skill words
        if 2 < len(part) < 50:
            # Remove common prefixes and section headers
            part = re.sub(r'^(skills?|technologies?|tools?|languages?|frameworks?):\s*', '', part)
            part = part.strip()
            if part and part not in ['and', 'or', 'the', 'a', 'an', 'with', 'using']:
                skills.append(part)
    
    return skills


def compute_semantic_skill_overlap(
    model,
    jd_text: str,
    resume_text: str,
    threshold: float = 0.75
) -> Tuple[List[str], List[str], float]:
    """
    Compute semantic skill overlap using embeddings (fully generalized, domain-agnostic).
    Works automatically for any skills without predefined lists.
    
    Args:
        model: SentenceTransformer model for embeddings
        jd_text: Job description text
        resume_text: Resume text
        threshold: Similarity threshold for matching (default: 0.75)
        
    Returns:
        Tuple of (matched_skills, missing_skills, overlap_score)
    """
    # Extract skills dynamically
    jd_skills = extract_skills_dynamic(jd_text)
    resume_skills = extract_skills_dynamic(resume_text)
    
    if not jd_skills:
        return [], [], 0.0
    
    if not resume_skills:
        return [], jd_skills, 0.0
    
    try:
        # Generate embeddings for skills
        jd_emb = model.encode(jd_skills, convert_to_numpy=True)
        res_emb = model.encode(resume_skills, convert_to_numpy=True)
        
        # Compute similarity matrix
        sim_matrix = cosine_similarity(jd_emb, res_emb)
        
        # Find matches
        matched = []
        missing = []
        
        for i, skill in enumerate(jd_skills):
            max_sim = np.max(sim_matrix[i])
            if max_sim >= threshold:
                matched.append(skill)
            else:
                missing.append(skill)
        
        # Calculate overlap score
        overlap = len(matched) / len(jd_skills) if jd_skills else 0.0
        
        return matched, missing, overlap
    except Exception as e:
        # Fallback to keyword-based matching if embedding fails
        return compute_skill_overlap_fallback(jd_skills, resume_skills)


def compute_skill_overlap_fallback(
    jd_skills: List[str],
    resume_skills: List[str]
) -> Tuple[List[str], List[str], float]:
    """
    Fallback keyword-based skill matching if semantic matching fails.
    
    Args:
        jd_skills: Job description skills
        resume_skills: Resume skills
        
    Returns:
        Tuple of (matched_skills, missing_skills, overlap_score)
    """
    # Normalize skills
    jd_normalized = {normalize_skill(s) for s in jd_skills}
    resume_normalized = {normalize_skill(s) for s in resume_skills}
    
    matched_normalized = jd_normalized & resume_normalized
    missing_normalized = jd_normalized - resume_normalized
    
    # Map back to original skills
    jd_skill_map = {normalize_skill(s): s for s in jd_skills}
    matched = [jd_skill_map[s] for s in matched_normalized if s in jd_skill_map]
    missing = [jd_skill_map[s] for s in missing_normalized if s in jd_skill_map]
    
    overlap = len(matched) / len(jd_skills) if jd_skills else 0.0
    
    return matched, missing, overlap


def compute_skill_overlap_score(
    resume_skills: List[str],
    job_skills: List[str],
    model=None,
    jd_text: str = "",
    resume_text: str = ""
) -> float:
    """
    Compute skill overlap score using semantic matching if model provided,
    otherwise falls back to keyword-based matching with synonyms.
    Skills are normalized (prefixes removed) before comparison.
    
    Args:
        resume_skills: List of skills from resume
        job_skills: List of required/preferred skills from JD
        model: Optional SentenceTransformer model for semantic matching
        jd_text: Job description text for dynamic skill extraction
        resume_text: Resume text for dynamic skill extraction
        
    Returns:
        Skill overlap score (0-1)
    """
    # Normalize all skills first to remove prefixes (e.g., "Databases: MySQL" -> "mysql")
    resume_skills_normalized = [normalize_skill(s) for s in resume_skills if s and normalize_skill(s)]
    job_skills_normalized = [normalize_skill(s) for s in job_skills if s and normalize_skill(s)]
    
    # Try semantic matching if model and texts provided
    if model and jd_text and resume_text:
        try:
            _, _, overlap = compute_semantic_skill_overlap(model, jd_text, resume_text, threshold=0.75)
            if overlap > 0:
                return min(1.0, max(0.0, overlap))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Semantic skill matching failed, using keyword-based: {e}")
            pass  # Fallback to keyword-based
    
    # Fallback to keyword-based matching with synonyms
    if not job_skills_normalized:
        return 0.0
    
    # Expand skills with synonyms (use normalized versions)
    resume_skill_set = set()
    for skill in resume_skills_normalized:
        if skill:
            resume_skill_set.add(skill)
            # Add synonym variations for normalized skill
            resume_skill_set.update(expand_skill_synonyms(skill))
    
    job_skill_set = set()
    for skill in job_skills_normalized:
        if skill:
            job_skill_set.add(skill)
            # Add synonym variations for normalized skill
            job_skill_set.update(expand_skill_synonyms(skill))
    
    # Calculate overlap using intersection (fuzzy matching with synonyms)
    intersection = resume_skill_set & job_skill_set
    
    if not job_skill_set:
        return 0.0
    
    # Calculate match ratio: how many job skills are matched
    # This gives higher weight to matching all required skills
    match_ratio = len(intersection) / len(job_skill_set)
    
    # Use weighted overlap score
    overlap_score = match_ratio
    
    # Additional boost for high match ratios
    if match_ratio >= 0.9:
        overlap_score = min(1.0, overlap_score * 1.05)  # 5% boost for 90%+ matches
    elif match_ratio >= 0.7:
        overlap_score = min(1.0, overlap_score * 1.02)  # 2% boost for 70%+ matches
    
    # Ensure score is between 0 and 1
    return min(1.0, max(0.0, overlap_score))


def extract_experience_value(experience_text: str) -> float:
    """
    Robust experience extraction handling ranges, internships, freshers, and missing data.
    Intelligently interprets entry-level roles.
    
    Args:
        experience_text: Text containing experience information
        
    Returns:
        Extracted experience value as float (years)
    """
    if not experience_text:
        return 0.0
    
    text_lower = str(experience_text).lower()
    
    # Handle special cases: internships, freshers, trainees, students
    if any(term in text_lower for term in ['intern', 'internship', 'fresher', 'fresh', 'trainee', 
                                           'entry level', 'entry-level', 'student', 'training']):
        return 0.5  # Give 0.5 years for internships/entry-level
    
    # Handle "no experience" or similar
    if any(word in text_lower for word in ['no experience', '0 years', 'zero experience']):
        return 0.0
    
    # Try to extract range (e.g., "0-2 years", "1-3 years", "3–5 years")
    range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', text_lower)
    if range_match:
        min_exp = float(range_match.group(1))
        max_exp = float(range_match.group(2))
        # For entry-level ranges (0-2, 1-3), return lower end to be more inclusive
        if max_exp <= 3:
            return min_exp + 0.5
        return (min_exp + max_exp) / 2.0
    
    # Try to extract single number (e.g., "5 years", "5+ years", "5+")
    single_match = re.search(r'(\d+)\+?', text_lower)
    if single_match:
        return float(single_match.group(1))
    
    # Fallback: look for any number in the text
    any_number = re.search(r'\d+', text_lower)
    if any_number:
        return float(any_number.group(0))
    
    return 0.0


def is_entry_level_role(text: str) -> bool:
    """
    Determine if a role is entry-level based on text content.
    
    Args:
        text: Job description or resume text
        
    Returns:
        True if role appears to be entry-level
    """
    if not text:
        return False
    
    text_lower = str(text).lower()
    entry_level_indicators = [
        'intern', 'internship', 'fresher', 'fresh', 'trainee',
        'entry level', 'entry-level', 'junior', '0-2', '0–2',
        '1-2', '1–2', '1-3', '1–3', 'student', 'graduate',
        'new grad', 'new graduate'
    ]
    
    return any(term in text_lower for term in entry_level_indicators)


def compute_experience_relevance(
    resume_experience_years: float,
    job_required_experience: float,
    resume_text: str = "",
    jd_text: str = ""
) -> float:
    """
    Compute experience relevance score with intelligent handling for entry-level roles.
    If both JD and resume indicate entry-level, set experience_relevance = 100%.
    
    Args:
        resume_experience_years: Years of experience from resume (can be float from range)
        job_required_experience: Required years of experience from JD
        resume_text: Resume text for context (optional)
        jd_text: Job description text for context (optional)
        
    Returns:
        Experience relevance score (0-1)
    """
    # Check if both are entry-level roles
    if resume_text and jd_text:
        resume_is_entry = is_entry_level_role(resume_text)
        jd_is_entry = is_entry_level_role(jd_text)
        
        if resume_is_entry and jd_is_entry:
            return 1.0  # Perfect match for entry-level roles
    
    # Handle missing or zero experience requirement - don't penalize
    if job_required_experience == 0 or job_required_experience is None:
        return 1.0
    
    # Handle missing candidate experience - graceful degradation
    if resume_experience_years is None:
        resume_experience_years = 0.0
    
    # If candidate meets or exceeds requirement, full score
    if resume_experience_years >= job_required_experience:
        return 1.0
    
    # For entry-level JDs (0-2 years), be more forgiving
    if job_required_experience <= 2:
        # If candidate has any experience (even 0.5), give good score
        if resume_experience_years > 0:
            return min(1.0, 0.7 + (resume_experience_years / job_required_experience) * 0.3)
        else:
            return 0.6  # Still give decent score for no experience in entry-level role
    
    # Proportional scoring with fair curve for mid/senior roles
    if job_required_experience > 0:
        ratio = resume_experience_years / job_required_experience
        # Use a square root curve to be more forgiving
        # This gives: 0.8 ratio -> ~0.89 score, 0.5 ratio -> ~0.71 score
        relevance = ratio ** 0.7  # Square root-like curve (0.7 exponent)
    else:
        relevance = 1.0
    
    # Ensure minimum score for candidates with any experience
    if resume_experience_years > 0:
        relevance = max(0.3, relevance)  # Minimum 30% if they have some experience
    
    return max(0.0, min(1.0, relevance))


def normalize_score_for_human_distribution(score: float) -> float:
    """
    Normalize score to human-like distribution (40-95% range for most cases).
    Interpolates from [30%, 80%] to [40%, 95%] as specified.
    Makes scores more realistic and recruiter-aligned.
    Perfect matches will be boosted later to reach 95-100%.
    
    Args:
        score: Raw score (0-1)
        
    Returns:
        Normalized score (0.0-0.95, with most scores in 0.4-0.95 range)
    """
    # Convert to percentage for interpolation
    score_percent = score * 100
    
    # Interpolate from [30, 80] to [40, 95] as specified by user
    if score_percent >= 30:
        if score_percent <= 80:
            normalized_percent = np.interp(score_percent, [30, 80], [40, 95])
        else:
            # For scores > 80%, allow them to go up to 95% (perfect matches boosted later)
            normalized_percent = min(95, 40 + (score_percent - 30) * (55 / 50))
    elif score_percent > 0:
        # For low but non-zero scores, scale proportionally from 0-30% to 0-40%
        normalized_percent = np.interp(score_percent, [0, 30], [0, 40])
    else:
        normalized_percent = 0.0
    
    # Convert back to 0-1 range
    normalized = normalized_percent / 100.0
    
    # Clamp to 0.0-0.95 range (perfect matches will be boosted later)
    return max(0.0, min(0.95, normalized))


def compute_suitability_score(
    semantic_similarity: float,
    skill_overlap: float,
    experience_relevance: float,
    weights: Dict[str, float] = None,
    candidate_experience: float = None,
    jd_text: str = "",
    normalize: bool = True
) -> float:
    """
    Compute overall suitability score with adaptive weighting based on job seniority.
    Uses domain penalty/bonus logic and fallback for perfect matches.
    Applies human-like score normalization.
    
    Args:
        semantic_similarity: Cosine similarity score (0-1)
        skill_overlap: Skill overlap score (0-1)
        experience_relevance: Experience relevance score (0-1)
        weights: Optional weights for each factor (overrides adaptive logic)
        candidate_experience: Candidate experience in years (for adaptive weighting)
        jd_text: Job description text (for detecting entry-level roles)
        normalize: Whether to apply human-like score normalization (default: True)
        
    Returns:
        Overall suitability score (0-100)
    """
    # Handle missing values gracefully
    semantic_similarity = max(0.0, min(1.0, semantic_similarity or 0.0))
    skill_overlap = max(0.0, min(1.0, skill_overlap or 0.0))
    experience_relevance = max(0.0, min(1.0, experience_relevance or 0.0))
    
    # Adaptive weighting based on job seniority (not just candidate experience)
    if weights is None:
        is_entry_level_jd = is_entry_level_role(jd_text) if jd_text else False
        
        if is_entry_level_jd:
            # Entry-level role: don't penalize lack of experience
            # Use exact weights as specified: 0.65 semantic + 0.35 skills
            weights = {
                "semantic": 0.65,
                "skills": 0.35,
                "experience": 0.0  # Don't weight experience for entry-level
            }
        else:
            # Non-entry-level: use standard weights
            # Use exact weights as specified: 0.55 semantic + 0.30 skills + 0.15 experience
            weights = {
                "semantic": 0.55,
                "skills": 0.30,
                "experience": 0.15
            }
    else:
        # Normalize provided weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calculate weighted score using exact weights
    score = (
        weights.get("semantic", 0.55) * semantic_similarity +
        weights.get("skills", 0.30) * skill_overlap +
        weights.get("experience", 0.15) * experience_relevance
    )
    
    # Domain penalty: if semantic similarity is very low (<40%), cap score at 40%
    # This prevents false positives when domains completely mismatch
    semantic_percent = semantic_similarity * 100
    skill_percent = skill_overlap * 100
    
    if semantic_percent < 40:
        score = min(score, 0.40)  # Cap at 40% for domain mismatches
    
    # Apply human-like score normalization first (before perfect match boosts)
    if normalize:
        score = normalize_score_for_human_distribution(score)
    
    # Domain bonus: if both semantic > 85% and skill > 70%, add bonus
    if semantic_percent > 85 and skill_percent > 70:
        score = min(1.0, score + 0.05)  # +5% bonus for strong contextual match
    
    # Fallback for identical matches: if semantic > 90% AND skill overlap > 80%,
    # force score to be at least 95% (after normalization, so it can exceed 95%)
    if semantic_percent > 90 and skill_percent > 80:
        score = max(score, 0.95)  # Ensure at least 95% for perfect matches
        # Allow perfect matches to reach 100%
        if score >= 0.95 and semantic_percent > 95:
            score = min(1.0, score * 1.02)  # Slight boost for extremely high matches
    
    # Additional boost for extremely high semantic similarity (after normalization)
    if semantic_percent > 95 and score < 1.0:
        score = min(1.0, score * 1.01)  # Small boost for extremely high semantic match
    
    # Convert to percentage and clamp to 0-100
    final_score = round(score * 100, 2)
    return max(0.0, min(100.0, final_score))


def extract_matching_skills(
    resume_skills: List[str],
    job_skills: List[str]
) -> List[str]:
    """
    Extract skills that match between resume and job description.
    Uses normalized skills and synonym expansion.
    
    Args:
        resume_skills: List of skills from resume
        job_skills: List of required/preferred skills from JD
        
    Returns:
        List of matching skills (original format from resume)
    """
    # Create mapping of normalized -> original skills
    resume_normalized_to_original = {}
    resume_skill_set = set()
    
    for skill in resume_skills:
        normalized = normalize_skill(skill)
        resume_normalized_to_original[normalized] = skill
        resume_skill_set.add(normalized)
        resume_skill_set.update(expand_skill_synonyms(skill))
    
    job_skill_set = set()
    for skill in job_skills:
        normalized = normalize_skill(skill)
        job_skill_set.add(normalized)
        job_skill_set.update(expand_skill_synonyms(skill))
    
    # Find matching normalized skills
    matching_normalized = resume_skill_set & job_skill_set
    
    # Convert back to original skill names (prefer resume format)
    matching_skills = []
    for normalized in matching_normalized:
        if normalized in resume_normalized_to_original:
            original = resume_normalized_to_original[normalized]
            if original not in matching_skills:
                matching_skills.append(original)
    
    return sorted(matching_skills)


def extract_missing_skills(
    resume_skills: List[str],
    job_skills: List[str]
) -> List[str]:
    """
    Extract skills required by job but missing in resume.
    Uses normalized skills and synonym expansion.
    
    Args:
        resume_skills: List of skills from resume
        job_skills: List of required/preferred skills from JD
        
    Returns:
        List of missing skills (original format from job description)
    """
    # Create mapping of normalized -> original skills for job
    job_normalized_to_original = {}
    resume_skill_set = set()
    
    for skill in resume_skills:
        normalized = normalize_skill(skill)
        resume_skill_set.add(normalized)
        resume_skill_set.update(expand_skill_synonyms(skill))
    
    job_skill_set = set()
    for skill in job_skills:
        normalized = normalize_skill(skill)
        job_normalized_to_original[normalized] = skill
        job_skill_set.add(normalized)
        job_skill_set.update(expand_skill_synonyms(skill))
    
    # Find missing skills
    missing_normalized = job_skill_set - resume_skill_set
    
    # Convert back to original skill names (prefer job description format)
    missing_skills = []
    for normalized in missing_normalized:
        if normalized in job_normalized_to_original:
            original = job_normalized_to_original[normalized]
            if original not in missing_skills:
                missing_skills.append(original)
    
    return sorted(missing_skills)

