"""
Pydantic models for oral interview evaluation
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# LLM Structured Output Models (for evaluation)
# ============================================================================

class OralResponseEvaluation(BaseModel):
    """Single-call LLM evaluation for one oral response"""
    relevance_score: float = Field(ge=0, le=10, description="How well answer addresses question")
    technical_score: float = Field(ge=0, le=10, description="Technical vocabulary quality")
    coherence_score: float = Field(ge=0, le=10, description="Logical flow and completeness")
    clarity_score: float = Field(ge=0, le=10, description="Communication clarity")

    relevance_phrase: str = Field(description="Brief relevance assessment (max 12 words)")
    technical_phrase: str = Field(description="Brief technical assessment (max 12 words)")
    coherence_phrase: str = Field(description="Brief coherence assessment (max 12 words)")


# ============================================================================
# Evaluation Report Models
# ============================================================================

class OralQuestionDetail(BaseModel):
    """Detailed evaluation for one Q&A pair"""
    turn: int
    question: str
    response: str
    audio_file: Optional[str]

    # Scores (0-10)
    relevance_score: float
    technical_vocab_score: float
    coherence_score: float
    clarity_score: float

    # Text metrics
    word_count: int
    sentence_count: int

    # Feedback
    feedback: str  # 3 phrases combined


class OralEvaluationReport(BaseModel):
    """Complete oral interview evaluation report"""
    # Metadata
    candidate_name: str
    interview_date: str
    duration_minutes: float
    total_turns: int
    difficulty_score: int

    # Final scores (0-10)
    overall_score: float
    technical_vocab_score: float  # 30% weight
    coherence_score: float  # 30% weight
    relevance_score: float  # 25% weight
    clarity_score: float  # 15% weight

    # Detailed feedback per question
    question_evaluations: List[OralQuestionDetail]

    # Summary
    evaluation_summary: str  # 2-3 sentences
