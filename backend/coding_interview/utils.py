"""
Coding Interview Utilities
Helper functions for response parsing, validation, and formatting
"""

import re
import json
from typing import Dict, Any, Tuple, Optional
from datetime import datetime


def parse_coding_response(response_text: str, question_type: str) -> Dict[str, str]:
    """
    Parse candidate code and explanation from response text

    Args:
        response_text: Raw candidate response
        question_type: Type of question ('coding_debug', 'coding_explain', 'db_schema')

    Returns:
        Dictionary with 'code' and 'explanation' keys
    """
    candidate_code = ""
    candidate_explanation = ""

    # Try to split by common delimiters
    if "FIXED CODE:" in response_text.upper():
        parts = re.split(r'(?i)FIXED CODE:\s*', response_text, maxsplit=1)
        if len(parts) > 1:
            remaining = parts[1]
            expl_parts = re.split(r'(?i)EXPLANATION:\s*', remaining, maxsplit=1)
            if len(expl_parts) > 1:
                candidate_code = expl_parts[0].strip()
                candidate_explanation = expl_parts[1].strip()
            else:
                candidate_code = remaining.strip()

    elif "CODE:" in response_text.upper():
        parts = re.split(r'(?i)CODE:\s*', response_text, maxsplit=1)
        if len(parts) > 1:
            remaining = parts[1]
            expl_parts = re.split(r'(?i)EXPLANATION:\s*', remaining, maxsplit=1)
            if len(expl_parts) > 1:
                candidate_code = expl_parts[0].strip()
                candidate_explanation = expl_parts[1].strip()
            else:
                candidate_code = remaining.strip()

    else:
        # No clear code/explanation split, use heuristics
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response_text, re.DOTALL)
        if code_blocks:
            candidate_code = code_blocks[0].strip()
            candidate_explanation = re.sub(r'```[\w]*\n.*?```', '', response_text, flags=re.DOTALL).strip()
        else:
            # For explanation questions, entire response is the explanation
            if question_type == 'coding_explain':
                candidate_explanation = response_text.strip()
            else:
                # For other types, assume entire response is code
                candidate_code = response_text.strip()

    return {
        'code': candidate_code,
        'explanation': candidate_explanation
    }


def extract_code_blocks(text: str) -> list:
    """
    Extract code blocks from markdown-formatted text

    Args:
        text: Text containing code blocks

    Returns:
        List of code block strings
    """
    code_blocks = re.findall(r'```[\w]*\n(.*?)```', text, re.DOTALL)
    return [block.strip() for block in code_blocks]


def validate_coding_session(session_data: Dict[str, Any]) -> bool:
    """
    Validate coding interview session data

    Args:
        session_data: Session data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = [
        'job_description',
        'difficulty_score',
        'current_question_count',
        'total_questions',
        'coding_test_filename'
    ]

    for key in required_keys:
        if key not in session_data:
            print(f"❌ Missing required key in coding session: {key}")
            return False

    return True


def generate_coding_filename(timestamp: Optional[str] = None) -> str:
    """
    Generate filename for coding test

    Args:
        timestamp: Optional timestamp string

    Returns:
        Formatted filename
    """
    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')

    return f"code-test-{timestamp}.json"


def calculate_coding_progress(current_question: int, total_questions: int = 5) -> Dict[str, Any]:
    """
    Calculate progress percentage and remaining questions

    Args:
        current_question: Current question number
        total_questions: Total number of questions

    Returns:
        Progress dictionary
    """
    percentage = round((current_question / total_questions) * 100, 1)

    return {
        "current_question": current_question,
        "total_questions": total_questions,
        "percentage": percentage,
        "questions_remaining": total_questions - current_question,
        "is_complete": current_question >= total_questions
    }


def format_test_results(results: Dict[str, Any]) -> str:
    """
    Format test execution results for display

    Args:
        results: Test execution results dictionary

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("TEST EXECUTION RESULTS")
    lines.append("=" * 60)

    if 'compilation_success' in results:
        status = "✅ SUCCESS" if results['compilation_success'] else "❌ FAILED"
        lines.append(f"Compilation: {status}")

    if 'exit_code' in results:
        lines.append(f"Exit Code: {results['exit_code']}")

    if 'match_status' in results:
        lines.append(f"Output Match: {results['match_status']}")

    if 'match_confidence' in results:
        lines.append(f"Match Confidence: {results['match_confidence']:.1%}")

    if 'expected_output' in results:
        lines.append(f"\nExpected Output:")
        lines.append(f"{results['expected_output']}")

    if 'actual_output' in results:
        lines.append(f"\nActual Output:")
        lines.append(f"{results['actual_output']}")

    if 'stderr' in results and results['stderr']:
        lines.append(f"\nError Output:")
        lines.append(f"{results['stderr']}")

    lines.append("=" * 60)

    return "\n".join(lines)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim underscores from ends
    sanitized = sanitized.strip('_')

    return sanitized


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON file safely

    Args:
        filepath: Path to JSON file

    Returns:
        JSON data as dictionary, or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data to JSON file

    Args:
        data: Data to save
        filepath: Output file path

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving to {filepath}: {e}")
        return False
