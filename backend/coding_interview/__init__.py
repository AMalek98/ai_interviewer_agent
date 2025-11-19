"""
Coding Interview Module

Handles code-based technical challenges with:
- Algorithm and data structure problems
- Code debugging challenges
- Database schema questions
- Live code execution and testing
- Test case generation and validation
"""

from .routes import coding_bp
from .question_generator import (
    generate_coding_question,
    CodingInterviewState,
    InterviewQuestion,
    DebugCodingQuestion,
    ExplanationCodingQuestion,
    DatabaseSchemaQuestion
)
from .job_skill_analyzer import (
    analyze_job_description_skills,
    JobSkillAnalysis,
    SkillImportance
)
from .evaluator import (
    evaluate_coding_interview,
    EvaluationResult
)
from .utils import (
    parse_coding_response,
    calculate_coding_progress,
    format_test_results,
    generate_coding_filename
)

__all__ = [
    # Blueprint
    'coding_bp',
    # Question generation
    'generate_coding_question',
    'CodingInterviewState',
    'InterviewQuestion',
    'DebugCodingQuestion',
    'ExplanationCodingQuestion',
    'DatabaseSchemaQuestion',
    # Job skill analysis
    'analyze_job_description_skills',
    'JobSkillAnalysis',
    'SkillImportance',
    # Evaluation
    'evaluate_coding_interview',
    'EvaluationResult',
    # Utilities
    'parse_coding_response',
    'calculate_coding_progress',
    'format_test_results',
    'generate_coding_filename'
]
