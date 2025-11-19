"""
Oral Interview Utilities
Helper functions for state management, validation, and file operations
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime


def validate_dialogue_state(state: Dict[str, Any]) -> bool:
    """
    Validate dialogue state dictionary

    Args:
        state: Dialogue state dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = [
        'complete',
        'job_description',
        'structured_cv',
        'difficulty_score',
        'conversation_history',
        'current_turn',
        'interview_start_time',
        'matched_technologies',
        'topics_covered',
        'depth_scores',
        'asked_question_categories',
        'current_section',
        'audio_files',
        'interview_filename'
    ]

    for key in required_keys:
        if key not in state:
            print(f"❌ Missing required key in dialogue state: {key}")
            return False

    return True


def load_interview_json(interview_path: str) -> Optional[Dict[str, Any]]:
    """
    Load oral interview JSON file

    Args:
        interview_path: Path to interview JSON file

    Returns:
        Interview data dictionary or None if error
    """
    try:
        if not os.path.exists(interview_path):
            print(f"❌ Interview file not found: {interview_path}")
            return None

        with open(interview_path, 'r', encoding='utf-8') as f:
            interview_data = json.load(f)

        return interview_data

    except Exception as e:
        print(f"❌ Error loading interview JSON: {e}")
        return None


def save_interview_json(interview_data: Dict[str, Any], output_path: str) -> bool:
    """
    Save interview data to JSON file

    Args:
        interview_data: Interview data dictionary
        output_path: Path to save JSON file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(interview_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Interview saved to: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error saving interview JSON: {e}")
        return False


def calculate_interview_duration(start_time_iso: str) -> float:
    """
    Calculate interview duration in minutes

    Args:
        start_time_iso: Start time in ISO format

    Returns:
        Duration in minutes
    """
    try:
        start_time = datetime.fromisoformat(start_time_iso)
        duration_seconds = (datetime.now() - start_time).total_seconds()
        duration_minutes = round(duration_seconds / 60, 1)
        return duration_minutes

    except Exception as e:
        print(f"❌ Error calculating duration: {e}")
        return 0.0


def extract_qa_pairs(conversation_history: list) -> list:
    """
    Extract Q&A pairs from conversation history

    Args:
        conversation_history: List of conversation entries

    Returns:
        List of Q&A pair dictionaries
    """
    qa_pairs = []
    current_question = None

    for entry in conversation_history:
        if entry["speaker"] == "interviewer":
            current_question = entry
        elif entry["speaker"] == "candidate" and current_question:
            qa_pairs.append({
                "question": current_question["text"],
                "question_turn": current_question["turn"],
                "answer": entry["text"],
                "answer_turn": entry["turn"],
                "audio_file": entry.get("audio_file"),
                "timestamp": entry.get("timestamp")
            })
            current_question = None

    return qa_pairs


def generate_interview_filename(candidate_name: str, prefix: str = "oral") -> str:
    """
    Generate interview filename with timestamp

    Args:
        candidate_name: Name of candidate
        prefix: File prefix (default: "oral")

    Returns:
        Formatted filename string
    """
    import re

    # Sanitize candidate name
    safe_name = re.sub(r'[^\w\s-]', '', candidate_name).strip().replace(' ', '-')

    if not safe_name:
        safe_name = "candidate"

    # Add timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')

    filename = f"{prefix}-{safe_name}-{timestamp}.json"

    return filename


def format_conversation_for_display(conversation_history: list) -> str:
    """
    Format conversation history for human-readable display

    Args:
        conversation_history: List of conversation entries

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("INTERVIEW CONVERSATION")
    lines.append("=" * 70)

    for entry in conversation_history:
        speaker = "INTERVIEWER" if entry["speaker"] == "interviewer" else "CANDIDATE"
        turn = entry.get("turn", "?")
        text = entry["text"]

        lines.append(f"\n[Turn {turn}] {speaker}:")
        lines.append(f"{text}")
        lines.append("-" * 70)

    return "\n".join(lines)


def validate_cv_session(cv_session: Dict[str, Any]) -> bool:
    """
    Validate CV session data

    Args:
        cv_session: CV session dictionary

    Returns:
        True if valid, False otherwise
    """
    if not cv_session:
        print("❌ CV session is None")
        return False

    required_keys = ['structured_cv', 'job_description', 'difficulty_score']

    for key in required_keys:
        if key not in cv_session:
            print(f"❌ Missing required key in CV session: {key}")
            return False

    return True


def get_interview_progress(current_turn: int, total_turns: int = 15) -> Dict[str, Any]:
    """
    Calculate interview progress

    Args:
        current_turn: Current turn number
        total_turns: Total number of turns (default: 15)

    Returns:
        Progress dictionary
    """
    percentage = round((current_turn / total_turns) * 100, 1)

    # Determine current section
    if current_turn == 0:
        section = "Opening"
    elif 1 <= current_turn <= 4:
        section = "HR Behavioral"
    elif current_turn == 5:
        section = "Transition to CV"
    elif 6 <= current_turn <= 9:
        section = "CV Experience"
    elif current_turn == 10:
        section = "Transition to Job"
    elif 11 <= current_turn <= 13:
        section = "Job Description"
    elif current_turn >= 14:
        section = "Closing"
    else:
        section = "Unknown"

    return {
        "current_turn": current_turn,
        "total_turns": total_turns,
        "percentage": percentage,
        "section": section,
        "questions_remaining": max(0, total_turns - current_turn)
    }
