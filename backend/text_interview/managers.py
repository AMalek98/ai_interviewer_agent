"""
Text Interview - State and Interview Management

Handles:
- Global state management (current_interview, interview_lock)
- Interview lifecycle (initialize_interview, end_interview)
- Prompt loading and template retrieval
"""

import threading
import json
import os
import yaml
from datetime import datetime
from typing import Optional, Dict, Any

# Import from shared module
from shared.models import (
    InterviewState, StructuredCV, StructuredJobDescription,
    PersonalInfo, WorkExperience, Education, Skill, Project
)
from shared.cv_analysis import calculate_difficulty_from_job


# ============================================================================
# Global State Variables
# ============================================================================

# Thread-safe interview state management
current_interview = None  # Stores active InterviewState
interview_lock = threading.RLock()  # Reentrant lock for nested acquisition support

# Cached prompts from YAML
interview_prompts = None  # Loaded from YAML, cached in memory


# ============================================================================
# State Access Functions (Thread-Safe)
# ============================================================================

def get_current_interview():
    """Get current interview state (thread-safe)"""
    with interview_lock:
        return current_interview


def set_current_interview(state: Optional[Dict[str, Any]]):
    """Set current interview state (thread-safe)"""
    global current_interview
    with interview_lock:
        current_interview = state


def clear_current_interview():
    """Clear current interview state (thread-safe)"""
    global current_interview
    with interview_lock:
        current_interview = None


# ============================================================================
# Prompt Management
# ============================================================================

def load_interview_prompts():
    """Load interview prompts from YAML file"""
    global interview_prompts
    try:
        # Use relative path from this module
        prompts_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'interview_prompts.yaml'
        )
        with open(prompts_path, 'r', encoding='utf-8') as f:
            interview_prompts = yaml.safe_load(f)
        print("Interview prompts loaded successfully")
        return interview_prompts
    except Exception as e:
        print(f"Error loading interview prompts: {e}")
        return None


def get_prompt_template(prompt_type: str, prompt_key: str) -> str:
    """Get a specific prompt template from loaded prompts"""
    global interview_prompts
    if not interview_prompts:
        interview_prompts = load_interview_prompts()

    if not interview_prompts:
        return ""

    try:
        return interview_prompts.get(prompt_type, {}).get(prompt_key, "")
    except Exception as e:
        print(f"Error getting prompt template {prompt_type}.{prompt_key}: {e}")
        return ""


# ============================================================================
# Interview Lifecycle Management
# ============================================================================

def initialize_interview(structured_job: StructuredJobDescription, structured_cv: Optional[StructuredCV] = None) -> InterviewState:
    """Initialize a new interview state - job-focused approach (CV-independent questioning)"""

    # Extract technologies from structured job description
    job_technologies = structured_job.technologies

    # Calculate difficulty based ONLY on job description (no CV needed)
    difficulty_score = calculate_difficulty_from_job(structured_job)

    # Create dummy CV if not provided (for backward compatibility)
    if structured_cv is None:
        structured_cv = StructuredCV(
            personal_info=PersonalInfo(name="Candidate"),
            experiences=[],
            education=[],
            skills=[],
            projects=[]
        )

    # Technology matching is now simplified (no CV comparison needed)
    matched_technologies = []  # Not used in job-only mode

    print("=== Initializing Job-Focused Interview ===")
    print(f"Job Title: {structured_job.job_title}")
    print(f"Seniority: {structured_job.seniority_level}")
    print(f"Industry: {structured_job.industry or 'General'}")
    print(f"Domain: {structured_job.domain}")
    print(f"Technologies: {len(structured_job.technologies)} required")
    if structured_job.business_context:
        print(f"Business Context: {', '.join(structured_job.business_context[:3])}")

    # Preferred languages not used in job-only mode
    preferred_languages = []

    # Generate CV summary (minimal for job-only mode)
    name = structured_cv.personal_info.name if structured_cv.personal_info.name else "Candidate"
    cv_summary = f"Name: {name} (Job-only interview mode)"

    # Generate job description summary
    job_description_summary = f"Position: {structured_job.job_title}, Level: {structured_job.seniority_level}, Technologies: {len(structured_job.technologies)}, Domain: {structured_job.domain}"

    # DEPRECATED: No CV-based experience scoring in job-only mode
    scored_experiences = []
    selected_experiences = []
    experience_scores = {}

    return InterviewState(
        complete=False,
        job_description=job_description_summary,
        structured_job=structured_job,
        cv_summary=cv_summary,
        structured_cv=structured_cv,
        difficulty_score=difficulty_score,
        current_phase="open",
        phase_question_count={"open": 0, "qcm": 0},
        total_question_count=0,
        current_question=None,
        questions_history=[],
        responses_history=[],
        matched_technologies=matched_technologies,
        preferred_languages=preferred_languages,
        # Job-focused questioning
        current_technology_focus=None,
        # DEPRECATED (kept for backward compatibility)
        selected_experiences=selected_experiences,
        experience_scores=experience_scores,
        current_experience_focus=None,
        # Answer-aware follow-ups
        answer_references={},
        # Evaluation tracking
        start_time=datetime.now().isoformat()
    )


def end_interview(state: InterviewState) -> Dict[str, Any]:
    """End the interview, save enhanced JSON, and trigger evaluation"""
    print("=== Interview Completed ===")
    state["complete"] = True

    # ========================================
    # Build Enhanced Interview JSON
    # ========================================
    # Handle potential missing/dummy CV gracefully
    try:
        candidate_name = state["structured_cv"].personal_info.name or "Candidate"
    except:
        candidate_name = "Candidate"

    job_title = state["structured_job"].job_title or "Unknown Position"

    # Format candidate name for filename (lowercase, replace spaces with hyphens)
    candidate_name_formatted = candidate_name.lower().replace(" ", "-")

    # Get current date for filename
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Build metadata
    interview_data = {
        "metadata": {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "difficulty_level": state["difficulty_score"],
            "interview_start_time": state.get("start_time", datetime.now().isoformat())
        },
        "questions": []
    }

    # Add all questions with responses
    for question, response in zip(state["questions_history"], state["responses_history"]):
        q_data = {
            "question_id": question.question_id,
            "type": question.question_type,
            "question_text": question.question_text,
            "response": response.response_text,
            "technology_focus": question.technology_focus or ""
        }

        # Add reference answer for open questions
        if question.question_type == "open" and question.reference_answer:
            q_data["reference_answer"] = question.reference_answer

        # Add QCM-specific fields
        if question.question_type == "qcm" and question.qcm_data:
            q_data.update({
                "options": [f"{opt.option}) {opt.text}" for opt in question.qcm_data.options],
                "correct_answer": question.qcm_data.correct_answer,
                "correct_answers": question.qcm_data.correct_answers or [],
                "is_multiple_choice": question.qcm_data.is_multiple_choice,
                "selected_answer": response.qcm_selected or response.qcm_selected_multiple,
                "is_correct": response.is_correct if response.is_correct is not None else False
            })

        interview_data["questions"].append(q_data)

    # ========================================
    # Save Enhanced Interview JSON
    # ========================================
    interviews_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "interviews")
    os.makedirs(interviews_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    interview_filename = f"interview-{candidate_name_formatted}-{timestamp}.json"
    interview_path = os.path.join(interviews_dir, interview_filename)

    with open(interview_path, 'w', encoding='utf-8') as f:
        json.dump(interview_data, f, indent=2, ensure_ascii=False)

    print(f"Interview data saved: {interview_path}")

    # ========================================
    # Trigger Evaluation
    # ========================================
    print("\n" + "="*70)
    print("STARTING POST-INTERVIEW EVALUATION")
    print("="*70)

    evaluation_filename = f"evaluation_report-{candidate_name_formatted}-{timestamp}.json"

    try:
        # Import from parent directory's evaluation module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from evaluation.evaluation_engine import evaluate_interview

        evaluation_report = evaluate_interview(interview_path)

        print("\nEvaluation completed successfully!")
        print(f"Overall Score: {evaluation_report.overall_score}/10")
        print(f"Report saved to: evaluation_reports/{evaluation_filename}")

    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()

    # Store filenames in state for later retrieval
    state["interview_filename"] = interview_filename
    state["evaluation_filename"] = evaluation_filename

    # ========================================
    # Return Summary (for backward compatibility)
    # ========================================
    total_questions = len(state["questions_history"])
    qcm_correct = sum(1 for resp in state["responses_history"]
                      if resp.is_correct is True)
    qcm_total = sum(1 for q in state["questions_history"]
                    if q.question_type == "qcm")

    summary = {
        "total_questions": total_questions,
        "qcm_score": f"{qcm_correct}/{qcm_total}" if qcm_total > 0 else "N/A",
        "difficulty_level": state["difficulty_score"],
        "completed": True,
        "interview_file": interview_filename,
        "evaluation_file": evaluation_filename
    }

    print(f"\nInterview Summary: {summary}")
    return summary
