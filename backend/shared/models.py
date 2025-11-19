"""
State Classes and Pydantic Models for AI Interview System

This module contains all data structures used throughout the interview system:
- CV-related models (WorkExperience, Education, Skill, Project, PersonalInfo, StructuredCV)
- Job description models (StructuredJobDescription)
- Question/Response models (QCMOption, QCMQuestion, InterviewQuestion, InterviewResponse)
- Interview state management (InterviewState)
"""

from pydantic import BaseModel, Field
from typing import TypedDict, List, Optional, Dict


# ============================================================================
# CV-Related Pydantic Models
# ============================================================================

class WorkExperience(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job position/title")
    start_date: Optional[str] = Field(description="Start date of employment")
    end_date: Optional[str] = Field(description="End date of employment")
    duration: Optional[str] = Field(description="Duration of employment")
    responsibilities: List[str] = Field(description="List of responsibilities and achievements")
    technologies: List[str] = Field(default=[], description="Technologies used in this role")


class Education(BaseModel):
    institution: str = Field(description="Educational institution name")
    degree: str = Field(description="Degree or qualification obtained")
    field_of_study: Optional[str] = Field(description="Field of study")
    start_date: Optional[str] = Field(description="Start date")
    end_date: Optional[str] = Field(description="End date")
    grade: Optional[str] = Field(description="Grade or GPA if mentioned")


class Skill(BaseModel):
    name: str = Field(description="Skill name")
    category: str = Field(description="Skill category (e.g., programming, tool, framework)")
    proficiency: Optional[str] = Field(description="Proficiency level if mentioned")


class Project(BaseModel):
    name: str = Field(description="Project name")
    description: Optional[str] = Field(default="", description="Project description")
    technologies: List[str] = Field(default=[], description="Technologies used")
    duration: Optional[str] = Field(default=None, description="Project duration")
    achievements: List[str] = Field(default=[], description="Key achievements or metrics")


class PersonalInfo(BaseModel):
    name: Optional[str] = Field(default="", description="Full name")
    email: Optional[str] = Field(default="", description="Email address")
    phone: Optional[str] = Field(default="", description="Phone number")
    location: Optional[str] = Field(default="", description="Location/address")


class StructuredCV(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo, description="Personal information (name, contact, etc.)")
    experiences: List[WorkExperience] = Field(default=[], description="Work experiences")
    education: List[Education] = Field(default=[], description="Educational background")
    skills: List[Skill] = Field(default=[], description="Skills and competencies")
    projects: List[Project] = Field(default=[], description="Projects")
    achievements: List[str] = Field(default=[], description="Notable achievements")
    languages: List[str] = Field(default=[], description="Languages spoken")


# ============================================================================
# Job Description Pydantic Models
# ============================================================================

class StructuredJobDescription(BaseModel):
    job_title: str = Field(description="Job title/position")
    company_name: Optional[str] = Field(default="", description="Company name if mentioned")
    location: Optional[str] = Field(default="", description="Job location")
    job_type: Optional[str] = Field(default="", description="Full-time, Part-time, Contract, etc.")
    seniority_level: str = Field(description="Junior, Mid-level, Senior, Lead, Principal, etc.")
    required_skills: List[str] = Field(default=[], description="Required technical skills")
    preferred_skills: List[str] = Field(default=[], description="Preferred/nice-to-have skills")
    responsibilities: List[str] = Field(default=[], description="Job responsibilities and duties")
    requirements: List[str] = Field(default=[], description="Job requirements")
    experience_years: Optional[int] = Field(default=None, description="Years of experience required")
    education_requirements: List[str] = Field(default=[], description="Education requirements")
    domain: str = Field(description="Domain: ai_ml|web_development|data_science|general")
    technologies: List[str] = Field(default=[], description="All technologies, frameworks, tools mentioned")
    benefits: List[str] = Field(default=[], description="Benefits and perks offered")

    # Domain-technical question fields (optional for enhanced question generation)
    industry: Optional[str] = Field(default=None, description="Industry/vertical: banking, healthcare, e-commerce, fintech, insurance, retail, etc.")
    business_context: List[str] = Field(default=[], description="Business problems/context: fraud detection, recommendation systems, risk analysis, customer segmentation, etc.")
    domain_specific_challenges: List[str] = Field(default=[], description="Domain-specific challenges: regulatory compliance, data privacy, real-time processing, scalability, etc.")


# ============================================================================
# Question and Response Models
# ============================================================================

class QCMOption(BaseModel):
    option: str = Field(description="Option letter (A, B, C, D)")
    text: str = Field(description="Option text")


class QCMQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[QCMOption] = Field(description="Multiple choice options")
    correct_answer: str = Field(description="Correct option letter (for single-choice questions)")
    correct_answers: Optional[List[str]] = Field(default=None, description="Correct option letters (for multiple-choice questions)")
    is_multiple_choice: bool = Field(default=False, description="True if multiple answers are correct, False if only one answer is correct")
    explanation: str = Field(description="Explanation of correct answer(s)")
    technology_focus: str = Field(description="Technology this question focuses on")


class InterviewQuestion(BaseModel):
    question_id: int = Field(description="Question number")
    question_type: str = Field(description="Type: open or qcm")
    question_text: str = Field(description="The question text")
    difficulty_level: int = Field(description="Difficulty level 1-10")
    technology_focus: Optional[str] = Field(default="", description="Technology focus area")
    qcm_data: Optional[QCMQuestion] = Field(default=None, description="QCM specific data")
    reference_answer: Optional[str] = Field(default=None, description="Best possible response for open questions (used for evaluation)")
    timestamp: str = Field(description="When question was generated")


class InterviewResponse(BaseModel):
    question_id: int = Field(description="Question ID this responds to")
    response_text: str = Field(description="User's response text")
    qcm_selected: Optional[str] = Field(default=None, description="Selected QCM option (single-choice)")
    qcm_selected_multiple: Optional[List[str]] = Field(default=None, description="Selected QCM options (multiple-choice)")
    is_correct: Optional[bool] = Field(default=None, description="If QCM answer was correct")
    timestamp: str = Field(description="When response was submitted")

    # Job-focused response tracking
    technology_focus: Optional[str] = Field(default=None, description="Technology this question focused on")
    follow_up_context: Optional[str] = Field(default=None, description="Context for generating follow-up questions")
    extracted_technologies: List[str] = Field(default=[], description="Technologies mentioned in this response")
    key_topics: List[str] = Field(default=[], description="Key topics discussed in this response")

    # DEPRECATED (kept for backward compatibility)
    related_experience: Optional[str] = Field(default=None, description="DEPRECATED: No longer used")
    experience_index: Optional[int] = Field(default=None, description="DEPRECATED: No longer used")


# ============================================================================
# Interview State Management
# ============================================================================

class InterviewState(TypedDict):
    """
    TypedDict defining the complete interview state structure.

    This state tracks all aspects of an interview session including:
    - Candidate and job information
    - Current question and phase
    - Question/response history
    - Technology matching
    - Job-focused questioning (CV-independent)
    """
    # Basic state
    complete: bool
    job_description: str  # Keep as summary string for backward compatibility
    structured_job: Optional[StructuredJobDescription]  # Structured job description
    cv_summary: str  # Keep for backward compatibility
    structured_cv: Optional[StructuredCV]
    difficulty_score: int  # 1-10 difficulty level

    # Question tracking
    current_phase: str  # 'open', 'qcm' (coding moved to separate agent)
    phase_question_count: Dict[str, int]  # Count per phase
    total_question_count: int
    current_question: Optional[InterviewQuestion]

    # Response tracking
    questions_history: List[InterviewQuestion]
    responses_history: List[InterviewResponse]

    # Technology matching
    matched_technologies: List[str]
    preferred_languages: List[str]

    # Job-focused questioning (replaces CV experience tracking)
    current_technology_focus: Optional[str]  # Current technology being questioned about

    # DEPRECATED (kept for backward compatibility, no longer used)
    selected_experiences: List[WorkExperience]  # DEPRECATED: No longer used in question generation
    experience_scores: Dict[str, float]  # DEPRECATED: No longer used
    current_experience_focus: Optional[int]  # DEPRECATED: No longer used

    # Answer-aware follow-up system
    answer_references: Dict[int, str]  # Question_id -> answer text for follow-ups

    # Evaluation tracking
    start_time: str  # ISO format timestamp for interview start
