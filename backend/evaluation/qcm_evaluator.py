"""
Rule-based QCM question evaluator
Simple correct/incorrect scoring
"""
from typing import List, Tuple
from .evaluation_models import QCMDetails


def evaluate_qcm_questions(questions: List[dict]) -> Tuple[float, QCMDetails]:
    """
    Evaluate QCM questions using simple rule-based scoring

    Args:
        questions: List of all interview questions (will filter for QCM)

    Returns:
        Tuple of (score_out_of_10, QCMDetails)
    """
    # Filter only QCM questions
    qcm_questions = [q for q in questions if q.get("type") == "qcm"]

    if not qcm_questions:
        return 0.0, QCMDetails(
            total_questions=0,
            correct_answers=0,
            percentage=0.0
        )

    # Count correct answers
    total = len(qcm_questions)
    correct = sum(1 for q in qcm_questions if q.get("is_correct", False))

    # Calculate scores
    percentage = (correct / total * 100) if total > 0 else 0.0
    score_out_of_10 = (correct / total * 10) if total > 0 else 0.0

    # Build details object
    details = QCMDetails(
        total_questions=total,
        correct_answers=correct,
        percentage=round(percentage, 2)
    )

    print(f"QCM Evaluation: {correct}/{total} correct ({percentage:.1f}%) - Score: {score_out_of_10:.2f}/10")

    return round(score_out_of_10, 2), details


# Test function
if __name__ == "__main__":
    # Test data
    test_questions = [
        {"type": "qcm", "is_correct": True},
        {"type": "qcm", "is_correct": False},
        {"type": "qcm", "is_correct": True},
        {"type": "qcm", "is_correct": True},
        {"type": "qcm", "is_correct": False},
        {"type": "open", "response": "..."}  # Should be ignored
    ]

    score, details = evaluate_qcm_questions(test_questions)
    print(f"\nTest Score: {score}/10")
    print(f"Details: {details}")

    # Verify calculations
    assert score == 6.0, f"Expected 6.0, got {score}"
    assert details.correct_answers == 3, f"Expected 3 correct, got {details.correct_answers}"
    assert details.total_questions == 5, f"Expected 5 total, got {details.total_questions}"
    assert details.percentage == 60.0, f"Expected 60.0%, got {details.percentage}"

    print("\nAll tests passed!")
