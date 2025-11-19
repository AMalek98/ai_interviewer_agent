"""
CV Analysis and Scoring Module for AI Interview System

This module contains functions for analyzing CVs and calculating scores:
- Difficulty score calculation based on CV experience and job requirements
- Experience scoring and ranking by job relevance
- Duration and recency analysis for work experiences
- Technology overlap calculation between CV and job
- Experience selection for targeted interview questioning

Functions can be reused across different interview agents and systems.
"""

from typing import List, Optional, Tuple
from shared.models import WorkExperience, StructuredCV, StructuredJobDescription
import re
from datetime import datetime
import dateutil.parser


# ============================================================================
# Difficulty Calculation Functions
# ============================================================================

def calculate_difficulty_from_job(structured_job: StructuredJobDescription) -> int:
    """
    Calculate difficulty score (1-10) based ONLY on job requirements.
    No CV parsing needed - reduces token usage significantly.

    Args:
        structured_job: Parsed job description with requirements

    Returns:
        int: Difficulty score from 1 (easiest) to 10 (hardest)

    Scoring Factors:
        - Seniority level (50% weight)
        - Required experience years (30% weight)
        - Technology complexity (20% weight)
    """
    try:
        difficulty_factors = []

        # Factor 1: Seniority level (50% weight)
        seniority_score = 5  # Default mid-level
        seniority_lower = structured_job.seniority_level.lower()

        if any(keyword in seniority_lower for keyword in ["intern", "internship", "entry", "junior", "graduate"]):
            seniority_score = 2
        elif any(keyword in seniority_lower for keyword in ["mid", "intermediate", "associate"]):
            seniority_score = 5
        elif any(keyword in seniority_lower for keyword in ["senior", "sr"]):
            seniority_score = 7
        elif any(keyword in seniority_lower for keyword in ["lead", "staff", "principal", "architect", "head", "chief"]):
            seniority_score = 9

        difficulty_factors.append(seniority_score * 0.5)

        # Factor 2: Required experience years (30% weight)
        experience_score = 5  # Default
        if structured_job.experience_years:
            years = structured_job.experience_years
            if years < 1:
                experience_score = 2
            elif years < 3:
                experience_score = 4
            elif years < 5:
                experience_score = 6
            elif years < 8:
                experience_score = 8
            else:
                experience_score = 10

        difficulty_factors.append(experience_score * 0.3)

        # Factor 3: Technology complexity (20% weight)
        tech_score = 5  # Default

        # Advanced technologies that indicate higher difficulty
        advanced_tech = [
            "machine learning", "ml", "ai", "artificial intelligence", "deep learning",
            "kubernetes", "k8s", "microservices", "system design", "distributed systems",
            "architecture", "aws", "azure", "gcp", "cloud", "devops", "ci/cd",
            "data science", "big data", "spark", "hadoop", "kafka"
        ]

        # Intermediate technologies
        intermediate_tech = [
            "react", "angular", "vue", "node", "python", "java", "javascript",
            "typescript", "docker", "sql", "mongodb", "postgresql", "api", "rest"
        ]

        # Combine all required skills and technologies
        all_tech = (structured_job.required_skills + structured_job.technologies)
        all_tech_lower = [tech.lower() for tech in all_tech]

        # Count advanced technologies
        advanced_count = sum(1 for tech in all_tech_lower if any(adv in tech for adv in advanced_tech))
        intermediate_count = sum(1 for tech in all_tech_lower if any(inter in tech for inter in intermediate_tech))

        if advanced_count >= 3:
            tech_score = 9
        elif advanced_count >= 2:
            tech_score = 8
        elif advanced_count >= 1:
            tech_score = 7
        elif intermediate_count >= 5:
            tech_score = 6
        elif intermediate_count >= 3:
            tech_score = 5
        elif intermediate_count >= 1:
            tech_score = 4

        difficulty_factors.append(tech_score * 0.2)

        # Calculate final score
        final_score = sum(difficulty_factors)

        # Ensure score is between 1 and 10
        final_score = max(1, min(10, round(final_score)))

        print(f"Job-only difficulty calculation - Seniority: {seniority_score}, Experience: {experience_score}, Tech: {tech_score} -> Final: {final_score}")
        return int(final_score)

    except Exception as e:
        print(f"Error calculating job-only difficulty score: {e}")
        return 5  # Default to mid-level


def calculate_difficulty_score(structured_cv: StructuredCV, structured_job: StructuredJobDescription) -> int:
    """
    Calculate difficulty score (1-10) based on CV experience and job requirements

    Args:
        structured_cv: Parsed CV data with experiences, education, and skills
        structured_job: Parsed job description with requirements and seniority

    Returns:
        int: Difficulty score from 1 (easiest) to 10 (hardest)

    Scoring Factors:
        - Years of experience (40% weight)
        - Education level (10% weight)
        - Technical skills complexity (25% weight)
        - Job requirements complexity (25% weight)
    """
    try:
        difficulty_factors = []

        # Factor 1: Years of experience (40% weight)
        experience_score = 0
        if structured_cv.experiences:
            total_months = 0
            for exp in structured_cv.experiences:
                months = estimate_duration_months(exp.duration or "")
                if months > 0:
                    total_months += months
                else:
                    # If no duration, estimate based on dates or assume 12 months
                    total_months += 12

            years_experience = total_months / 12
            if years_experience < 1:
                experience_score = 1
            elif years_experience < 2:
                experience_score = 3
            elif years_experience < 4:
                experience_score = 5
            elif years_experience < 7:
                experience_score = 7
            else:
                experience_score = 9

        difficulty_factors.append(experience_score * 0.4)

        # Factor 2: Education level (20% weight)
        education_score = 1
        if structured_cv.education:
            degrees = [edu.degree.lower() for edu in structured_cv.education if edu.degree]
            if any("phd" in degree or "doctorate" in degree for degree in degrees):
                education_score = 10
            elif any("master" in degree or "msc" in degree or "mba" in degree for degree in degrees):
                education_score = 7
            elif any("bachelor" in degree or "bsc" in degree or "ba" in degree for degree in degrees):
                education_score = 5
            elif any("associate" in degree or "diploma" in degree for degree in degrees):
                education_score = 3

        difficulty_factors.append(education_score * 0.1)

        # Factor 3: Technical skills complexity (25% weight)
        skills_score = 1
        if structured_cv.skills:
            advanced_skills = [
                "machine learning", "ai", "kubernetes", "microservices",
                "system design", "architecture", "devops", "cloud", "aws", "azure"
            ]
            intermediate_skills = [
                "react", "angular", "vue", "node.js", "python", "java", "sql"
            ]

            skill_names = [skill.name.lower() for skill in structured_cv.skills]
            advanced_count = sum(1 for skill in skill_names if any(adv in skill for adv in advanced_skills))
            intermediate_count = sum(1 for skill in skill_names if any(inter in skill for inter in intermediate_skills))

            if advanced_count >= 3:
                skills_score = 9
            elif advanced_count >= 1:
                skills_score = 7
            elif intermediate_count >= 5:
                skills_score = 6
            elif intermediate_count >= 2:
                skills_score = 4

        difficulty_factors.append(skills_score * 0.25)

        # Factor 4: Job requirements complexity (15% weight) - Use structured job data
        job_score = 5  # Default mid-level
        seniority_lower = structured_job.seniority_level.lower()

        if any(indicator in seniority_lower for indicator in ["senior", "lead", "principal", "architect"]):
            job_score = 8
        elif any(indicator in seniority_lower for indicator in ["junior", "entry", "intern", "graduate"]):
            job_score = 3
        elif "mid" in seniority_lower:
            job_score = 5

        # Also consider experience_years if specified
        if structured_job.experience_years:
            if structured_job.experience_years >= 7:
                job_score = max(job_score, 8)
            elif structured_job.experience_years >= 4:
                job_score = max(job_score, 6)
            elif structured_job.experience_years >= 2:
                job_score = max(job_score, 4)

        difficulty_factors.append(job_score * 0.25)

        # Calculate final score
        final_score = sum(difficulty_factors)

        # Ensure score is between 1 and 10
        final_score = max(1, min(10, round(final_score)))

        print(f"Difficulty calculation - Experience: {experience_score}, Education: {education_score}, Skills: {skills_score}, Job: {job_score} -> Final: {final_score}")
        return int(final_score)

    except Exception as e:
        print(f"Error calculating difficulty score: {e}")
        return 5  # Default to mid-level


def estimate_duration_months(duration_str: str) -> int:
    """
    Estimate duration in months from various string formats

    Args:
        duration_str: Duration string like "2 years", "6 months", "1.5 years", etc.

    Returns:
        int: Estimated duration in months, or 0 if unable to parse

    Examples:
        "2 years" -> 24
        "6 months" -> 6
        "1.5 years" -> 18
    """
    if not duration_str:
        return 0

    duration_lower = duration_str.lower()

    # Look for year patterns
    year_match = re.search(r'(\d+\.?\d*)\s*(?:year|yr)', duration_lower)
    if year_match:
        return int(float(year_match.group(1)) * 12)

    # Look for month patterns
    month_match = re.search(r'(\d+)\s*(?:month|mo)', duration_lower)
    if month_match:
        return int(month_match.group(1))

    # Look for patterns like "6 months", "2 years"
    if "month" in duration_lower:
        nums = re.findall(r'\d+', duration_str)
        if nums:
            return int(nums[0])

    if "year" in duration_lower:
        nums = re.findall(r'\d+', duration_str)
        if nums:
            return int(nums[0]) * 12

    return 0


# ============================================================================
# Experience Scoring Functions
# ============================================================================

def calculate_tech_overlap(exp_technologies: List[str], job_technologies: List[str]) -> float:
    """
    Calculate technology overlap score between experience and job requirements

    Args:
        exp_technologies: List of technologies from candidate's experience
        job_technologies: List of technologies required by the job

    Returns:
        float: Overlap score from 0.0 to 1.0 (percentage of job requirements covered)
    """
    if not exp_technologies or not job_technologies:
        return 0.0

    # Normalize to lowercase for comparison
    exp_tech_set = set(tech.lower().strip() for tech in exp_technologies)
    job_tech_set = set(tech.lower().strip() for tech in job_technologies)

    # Calculate overlap
    overlap = exp_tech_set.intersection(job_tech_set)

    # Score as percentage of job requirements covered
    overlap_score = len(overlap) / len(job_tech_set) if job_tech_set else 0.0

    return min(1.0, overlap_score)  # Cap at 1.0


def calculate_recency_score(start_date: Optional[str], end_date: Optional[str]) -> float:
    """
    Calculate recency score based on how recent the experience is

    Args:
        start_date: Start date of experience (optional)
        end_date: End date of experience ("Present" for current roles)

    Returns:
        float: Recency score from 0.1 to 1.0
               1.0 = current role
               ~0.8 = ended 1 year ago
               ~0.5 = ended 3 years ago
    """
    if not end_date:
        return 0.5  # Default score for missing data

    try:
        # Handle "Present" or current roles
        if end_date.lower() in ['present', 'current', 'now']:
            return 1.0  # Maximum score for current roles

        # Parse end date
        try:
            end_date_obj = dateutil.parser.parse(end_date, fuzzy=True)
        except:
            # If parsing fails, try simple year extraction
            year_match = re.search(r'(\d{4})', end_date)
            if year_match:
                end_date_obj = datetime(int(year_match.group(1)), 12, 31)
            else:
                return 0.5  # Default score

        # Calculate months since end date
        current_date = datetime.now()
        months_since_end = (current_date.year - end_date_obj.year) * 12 + (current_date.month - end_date_obj.month)

        # Apply decay function - more recent = higher score
        # Score decreases exponentially: 1.0 for current, ~0.8 for 1 year ago, ~0.5 for 3 years ago
        recency_score = max(0.1, 1.0 / (1.0 + months_since_end * 0.05))

        return recency_score

    except Exception as e:
        print(f"Error calculating recency score: {e}")
        return 0.5  # Default score


def calculate_duration_score(duration: Optional[str]) -> float:
    """
    Calculate duration score based on length of experience

    Args:
        duration: Duration string (e.g., "2 years", "6 months")

    Returns:
        float: Duration score from 0.3 to 1.0
               < 6 months = 0.3-0.6
               6-12 months = 0.6-0.8
               1-2 years = 0.8-0.9
               2+ years = 0.9-1.0
    """
    if not duration:
        return 0.5  # Default score for missing data

    try:
        # Use existing function to get months
        months = estimate_duration_months(duration)

        if months == 0:
            return 0.3  # Low score for unknown duration

        # Score based on duration - longer is generally better but with diminishing returns
        # 6 months = 0.6, 1 year = 0.8, 2 years = 0.9, 3+ years = 1.0
        if months < 6:
            duration_score = 0.3 + (months / 6) * 0.3  # 0.3 to 0.6
        elif months < 12:
            duration_score = 0.6 + ((months - 6) / 6) * 0.2  # 0.6 to 0.8
        elif months < 24:
            duration_score = 0.8 + ((months - 12) / 12) * 0.1  # 0.8 to 0.9
        else:
            duration_score = min(1.0, 0.9 + ((months - 24) / 24) * 0.1)  # 0.9 to 1.0

        return duration_score

    except Exception as e:
        print(f"Error calculating duration score: {e}")
        return 0.5  # Default score


def score_experiences(experiences: List[WorkExperience], job_technologies: List[str]) -> List[Tuple[WorkExperience, float]]:
    """
    Score CV experiences by job relevance and return sorted list

    Args:
        experiences: List of candidate's work experiences
        job_technologies: List of technologies required by the job

    Returns:
        List of tuples: (experience, score) sorted by score (highest first)

    Scoring Algorithm:
        - 50% technology overlap (how many job technologies are in experience)
        - 25% recency (how recent the experience is)
        - 25% duration (how long they worked in this role)
    """
    if not experiences:
        return []

    scored_experiences = []

    for exp in experiences:
        try:
            # Extract technologies from experience (technologies field + responsibilities)
            exp_technologies = list(exp.technologies) if exp.technologies else []

            # Also extract technologies from responsibilities text
            if exp.responsibilities:
                responsibilities_text = ' '.join(exp.responsibilities).lower()
                # Add basic tech extraction from responsibilities
                tech_keywords = ['python', 'java', 'javascript', 'react', 'angular', 'sql', 'mongodb',
                               'aws', 'docker', 'kubernetes', 'git', 'machine learning', 'ai', 'nlp']
                for keyword in tech_keywords:
                    if keyword in responsibilities_text:
                        exp_technologies.append(keyword)

            # Calculate component scores
            tech_overlap_score = calculate_tech_overlap(exp_technologies, job_technologies)
            recency_score = calculate_recency_score(exp.start_date, exp.end_date)
            duration_score = calculate_duration_score(exp.duration)

            # Combine time scores
            time_score = (recency_score + duration_score) / 2

            # Final weighted score (50% tech overlap, 50% time factors)
            final_score = (tech_overlap_score * 0.5) + (time_score * 0.5)

            scored_experiences.append((exp, final_score))

            # Debug logging
            print(f"Experience: {exp.position} at {exp.company}")
            print(f"  Tech overlap: {tech_overlap_score:.2f}, Recency: {recency_score:.2f}, Duration: {duration_score:.2f}")
            print(f"  Final score: {final_score:.2f}")

        except Exception as e:
            print(f"Error scoring experience {exp.position}: {e}")
            scored_experiences.append((exp, 0.5))  # Default score

    # Sort by score (highest first)
    scored_experiences.sort(key=lambda x: x[1], reverse=True)
    return scored_experiences


def select_top_experiences(scored_experiences: List[Tuple[WorkExperience, float]]) -> List[WorkExperience]:
    """
    Select top 2 experiences for focused questioning

    Args:
        scored_experiences: List of (experience, score) tuples sorted by score

    Returns:
        List of top 2 WorkExperience objects (or 1 if only one experience available)
    """
    if not scored_experiences:
        return []

    if len(scored_experiences) == 1:
        # Only one experience - use it twice or handle in questioning logic
        return [scored_experiences[0][0]]

    # Take top 2 experiences
    top_experiences = [exp for exp, score in scored_experiences[:2]]

    print(f"Selected top experiences:")
    for i, exp in enumerate(top_experiences):
        score = scored_experiences[i][1]
        print(f"  {i+1}. {exp.position} at {exp.company} (score: {score:.2f})")

    return top_experiences


# ============================================================================
# Utility Functions
# ============================================================================

def load_text_file(file_path: str) -> str:
    """
    Load text content from a file

    Args:
        file_path: Path to the text file

    Returns:
        str: File content, or empty string if error occurs
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return ""
