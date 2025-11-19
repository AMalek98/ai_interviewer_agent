"""
Pydantic models for interview evaluation system
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# LLM Structured Output Models (for evaluation)
# ============================================================================

class TechnicalVocabEval(BaseModel):
    """LLM output for technical vocabulary evaluation - DEPRECATED"""
    score: float = Field(ge=0, le=10, description="Technical vocabulary score 0-10")
    justification: str = Field(description="1-2 sentence justification")


class GrammarFlowEval(BaseModel):
    """LLM output for grammar/flow evaluation - DEPRECATED"""
    score: float = Field(ge=0, le=10, description="Grammar and coherence score 0-10")
    justification: str = Field(description="1-2 sentence justification")


class CompactEvaluation(BaseModel):
    """Ultra-compact evaluation model - Single LLM call with 3 required phrases"""
    technical_score: float = Field(ge=0, le=10, description="Technical quality score 0-10")
    grammar_score: float = Field(ge=0, le=10, description="Grammar and communication score 0-10")
    grammar_phrase: str = Field(description="Brief phrase on grammar quality (max 10 words)")
    technical_phrase: str = Field(description="Brief phrase on technical quality (max 10 words)")
    missing_phrase: str = Field(description="Brief phrase on what's missing (max 10 words)")


# ============================================================================
# Evaluation Report Models
# ============================================================================

class OpenQuestionDetail(BaseModel):
    """Detailed evaluation for one open question"""
    question_id: int
    question: str
    response: str
    technical_vocab_score: float  # 0-10
    grammar_flow_score: float     # 0-10
    feedback: str                 # 2-3 sentences


class QCMDetails(BaseModel):
    """QCM evaluation summary"""
    total_questions: int
    correct_answers: int
    percentage: float  # 0-100


class EvaluationReport(BaseModel):
    """Complete evaluation report for one candidate"""
    # Metadata
    candidate_name: str
    job_title: str
    difficulty_level: int
    interview_date: str

    # Final scores (0-10 scale)
    overall_score: float
    qcm_score: float              # 0-10
    technical_vocab_score: float  # 0-10 (average across open questions)
    grammar_flow_score: float     # 0-10 (average across open questions)

    # Detailed breakdowns
    qcm_details: QCMDetails
    open_question_feedback: List[OpenQuestionDetail]

    # Summary
    evaluation_summary: str  # 2-3 sentence overall assessment


# ============================================================================
# Oral Interview Evaluation Models
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
