"""
Shared utilities and models for the AI Interview System

This module contains common functionality used across all interview types:
- LLM setup and initialization
- Pydantic models and data structures
- Information extraction utilities
- CV analysis and scoring
- Speech processing (STT and TTS)
"""

from .models import (
    WorkExperience, Education, Skill, Project, PersonalInfo,
    StructuredCV, StructuredJobDescription,
    QCMOption, QCMQuestion, InterviewQuestion, InterviewResponse,
    InterviewState
)

from .llm_setup import (
    load_env, validate_api_key, get_llm, initialize_llm
)

from . import config

__all__ = [
    # Models
    'WorkExperience', 'Education', 'Skill', 'Project', 'PersonalInfo',
    'StructuredCV', 'StructuredJobDescription',
    'QCMOption', 'QCMQuestion', 'InterviewQuestion', 'InterviewResponse',
    'InterviewState',
    # LLM Setup
    'load_env', 'validate_api_key', 'get_llm', 'initialize_llm',
    # Configuration
    'config',
]
