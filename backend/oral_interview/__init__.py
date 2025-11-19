"""
Oral Interview Module

Handles voice-based interviews with:
- Speech-to-text transcription
- Text-to-speech generation
- Real-time conversation flow
- Audio response evaluation
"""

from .routes import oral_bp
from .question_generator import (
    DialogueState,
    generate_dialogue_question,
    process_dialogue_turn,
    save_oral_interview,
    load_oral_prompts
)
from .evaluator import (
    evaluate_oral_interview,
    OralEvaluationReport
)
from .utils import (
    validate_dialogue_state,
    load_interview_json,
    save_interview_json,
    extract_qa_pairs,
    generate_interview_filename,
    get_interview_progress
)

__all__ = [
    # Blueprint
    'oral_bp',
    # Question generation
    'DialogueState',
    'generate_dialogue_question',
    'process_dialogue_turn',
    'save_oral_interview',
    'load_oral_prompts',
    # Evaluation
    'evaluate_oral_interview',
    'OralEvaluationReport',
    # Utilities
    'validate_dialogue_state',
    'load_interview_json',
    'save_interview_json',
    'extract_qa_pairs',
    'generate_interview_filename',
    'get_interview_progress'
]
