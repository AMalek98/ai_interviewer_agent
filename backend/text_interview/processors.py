"""
Text Interview - Response Processing

Handles:
- User response processing
- QCM answer validation
- Interview flow control (should_continue logic)
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import from shared module
from shared.models import InterviewState, InterviewResponse

# Import from sibling modules
from .utils import extract_technologies_from_answer, extract_key_topics_from_answer


def process_response(state: InterviewState, user_response: str, qcm_selected: str = None, qcm_selected_multiple: List[str] = None) -> Dict[str, Any]:
    """Process user response and update interview state (job-focused tracking)"""

    if not state.get("current_question"):
        return {"error": "No current question to respond to"}

    current_question = state["current_question"]

    # Get current technology focus from state
    technology_focus = state.get("current_technology_focus")

    # Extract technologies and topics from the response (still useful for analysis)
    extracted_technologies = extract_technologies_from_answer(user_response, [])
    key_topics = extract_key_topics_from_answer(user_response)

    # Build follow-up context for future questions
    follow_up_context = ""
    if extracted_technologies or key_topics:
        follow_up_context = f"Tech: {', '.join(extracted_technologies[:3])}; Topics: {', '.join(key_topics[:3])}"

    # Create response object (job-focused)
    response = InterviewResponse(
        question_id=current_question.question_id,
        response_text=user_response,
        qcm_selected=qcm_selected,
        qcm_selected_multiple=qcm_selected_multiple,
        is_correct=None,
        timestamp=datetime.now().isoformat(),
        # Job-focused fields
        technology_focus=technology_focus,
        follow_up_context=follow_up_context,
        extracted_technologies=extracted_technologies,
        key_topics=key_topics,
        # DEPRECATED (kept for backward compatibility)
        related_experience=None,
        experience_index=None
    )

    # For QCM questions, check if answer is correct
    if current_question.question_type == "qcm" and current_question.qcm_data:
        if current_question.qcm_data.is_multiple_choice:
            # Multiple-choice question: check if all correct answers are selected
            if qcm_selected_multiple and current_question.qcm_data.correct_answers:
                selected_set = set(qcm_selected_multiple)
                correct_set = set(current_question.qcm_data.correct_answers)
                response.is_correct = selected_set == correct_set
        else:
            # Single-choice question: check single answer
            if qcm_selected:
                response.is_correct = qcm_selected == current_question.qcm_data.correct_answer

    # Add response to history
    state["responses_history"].append(response)

    # Phase 5: Update answer references for follow-up questions
    state["answer_references"][current_question.question_id] = user_response

    # Save to interview JSON file for backward compatibility
    try:
        interview_data = {}
        try:
            with open("interview.json", "r") as f:
                interview_data = json.load(f)
        except FileNotFoundError:
            pass

        # Use question text as key for compatibility
        question_key = current_question.question_text
        if current_question.question_type == "qcm":
            interview_data[question_key] = {
                "response": user_response,
                "selected_option": qcm_selected,
                "is_correct": response.is_correct
            }
        else:
            interview_data[question_key] = user_response

        with open("interview.json", "w") as f:
            json.dump(interview_data, f, indent=2)
    except Exception as e:
        print(f"Error saving to interview.json: {e}")

    return {"processed": True}


def should_continue(state: InterviewState) -> str:
    """Determine if interview should continue or end"""
    if state.get("complete", False):
        return "end_interview"

    # Check if all phases are complete
    current_phase = state["current_phase"]
    phase_count = state["phase_question_count"][current_phase]

    # PHASE 2: Updated phase completion logic (5 questions per phase)
    if (current_phase == "open" and phase_count >= 5) or \
       (current_phase == "qcm" and phase_count >= 5):
        # Try to move to next phase
        if current_phase == "open":
            return "generate_question"  # Move to QCM
        elif current_phase == "qcm":
            return "end_interview"  # Complete (coding moved to separate agent)
        else:
            return "end_interview"  # Complete

    return "generate_question"
