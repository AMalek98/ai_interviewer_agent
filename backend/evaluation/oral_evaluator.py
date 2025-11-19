"""
Main oral interview evaluation engine
Orchestrates complete evaluation process for oral interviews
"""
import os
import json
import yaml
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from .evaluation_models import OralEvaluationReport
from .oral_response_evaluator import evaluate_all_oral_responses


# Load environment
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
load_dotenv(env_path)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.2)


def load_prompts():
    """Load oral evaluation prompts"""
    prompts_path = os.path.join(
        os.path.dirname(__file__),
        'oral_evaluation_prompts.yaml'
    )
    with open(prompts_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_oral_summary(
    candidate_name: str,
    interview_date: str,
    duration_minutes: float,
    total_turns: int,
    overall_score: float,
    technical_score: float,
    coherence_score: float,
    relevance_score: float,
    clarity_score: float
) -> str:
    """Generate overall summary using LLM"""
    prompts = load_prompts()

    summary_prompt = prompts["oral_summary_prompt"].format(
        candidate_name=candidate_name,
        interview_date=interview_date,
        duration_minutes=duration_minutes,
        total_turns=total_turns,
        overall_score=overall_score,
        technical_score=technical_score,
        coherence_score=coherence_score,
        relevance_score=relevance_score,
        clarity_score=clarity_score
    )

    response = llm.invoke(summary_prompt)
    return response.content.strip()


def evaluate_oral_interview(interview_json_path: str) -> OralEvaluationReport:
    """
    Main evaluation function for oral interviews

    Process:
    1. Load oral interview JSON
    2. Extract Q&A pairs from conversation
    3. Evaluate each response (LLM-based)
    4. Calculate aggregate scores
    5. Apply weights: Technical 30%, Coherence 30%, Relevance 25%, Clarity 15%
    6. Generate summary
    7. Save report

    Args:
        interview_json_path: Path to oral interview JSON file

    Returns:
        OralEvaluationReport object
    """
    print(f"\n{'='*70}")
    print(f"STARTING ORAL INTERVIEW EVALUATION")
    print(f"{'='*70}")
    print(f"Interview file: {interview_json_path}")

    # ========================================
    # STEP 1: Load Interview Data
    # ========================================
    if not os.path.exists(interview_json_path):
        raise FileNotFoundError(f"Interview file not found: {interview_json_path}")

    with open(interview_json_path, 'r', encoding='utf-8') as f:
        interview_data = json.load(f)

    metadata = interview_data["metadata"]
    conversation = interview_data["conversation"]

    print(f"\nCandidate: {metadata['candidate_name']}")
    print(f"Date: {metadata['date']}")
    print(f"Duration: {metadata['duration_minutes']} minutes")
    print(f"Total Turns: {metadata['total_turns']}")
    print(f"Difficulty: {metadata['difficulty_score']}/10")

    # ========================================
    # STEP 2: Evaluate All Q&A Pairs
    # ========================================
    print(f"\n{'='*70}")
    print("EVALUATING ORAL RESPONSES")
    print(f"{'='*70}")

    evaluations = evaluate_all_oral_responses(
        conversation=conversation,
        difficulty_level=metadata['difficulty_score'],
        topics_covered=metadata.get('topics_covered', [])
    )

    # ========================================
    # STEP 3: Calculate Aggregate Scores
    # ========================================
    if evaluations:
        avg_technical = sum(e.technical_vocab_score for e in evaluations) / len(evaluations)
        avg_coherence = sum(e.coherence_score for e in evaluations) / len(evaluations)
        avg_relevance = sum(e.relevance_score for e in evaluations) / len(evaluations)
        avg_clarity = sum(e.clarity_score for e in evaluations) / len(evaluations)
    else:
        avg_technical = avg_coherence = avg_relevance = avg_clarity = 0.0

    print(f"\n{'='*70}")
    print("AGGREGATE SCORES")
    print(f"{'='*70}")
    print(f"Technical Vocabulary: {avg_technical:.2f}/10")
    print(f"Coherence: {avg_coherence:.2f}/10")
    print(f"Relevance: {avg_relevance:.2f}/10")
    print(f"Clarity: {avg_clarity:.2f}/10")

    # ========================================
    # STEP 4: Calculate Final Score
    # ========================================
    # Weights: Technical 30%, Coherence 30%, Relevance 25%, Clarity 15%
    final_score = (
        (avg_technical * 0.30) +
        (avg_coherence * 0.30) +
        (avg_relevance * 0.25) +
        (avg_clarity * 0.15)
    )

    print(f"\n{'='*70}")
    print("FINAL SCORE CALCULATION")
    print(f"{'='*70}")
    print(f"Formula: (Tech × 0.30) + (Coherence × 0.30) + (Relevance × 0.25) + (Clarity × 0.15)")
    print(f"Calculation: ({avg_technical:.2f} × 0.30) + ({avg_coherence:.2f} × 0.30) + ({avg_relevance:.2f} × 0.25) + ({avg_clarity:.2f} × 0.15)")
    print(f"Final Score: {final_score:.2f}/10")

    # ========================================
    # STEP 5: Generate Summary
    # ========================================
    print(f"\n{'='*70}")
    print("GENERATING EVALUATION SUMMARY")
    print(f"{'='*70}")

    summary = generate_oral_summary(
        candidate_name=metadata["candidate_name"],
        interview_date=metadata["date"],
        duration_minutes=metadata["duration_minutes"],
        total_turns=metadata["total_turns"],
        overall_score=final_score,
        technical_score=avg_technical,
        coherence_score=avg_coherence,
        relevance_score=avg_relevance,
        clarity_score=avg_clarity
    )

    print(f"Summary: {summary}")

    # ========================================
    # STEP 6: Build Report
    # ========================================
    report = OralEvaluationReport(
        candidate_name=metadata["candidate_name"],
        interview_date=metadata["date"],
        duration_minutes=metadata["duration_minutes"],
        total_turns=metadata["total_turns"],
        difficulty_score=metadata["difficulty_score"],
        overall_score=round(final_score, 2),
        technical_vocab_score=round(avg_technical, 2),
        coherence_score=round(avg_coherence, 2),
        relevance_score=round(avg_relevance, 2),
        clarity_score=round(avg_clarity, 2),
        question_evaluations=evaluations,
        evaluation_summary=summary
    )

    # ========================================
    # STEP 7: Save Report
    # ========================================
    # Extract filename parts: oral-MALEK-AJMI-2025-10-07-111358.json
    interview_filename = os.path.basename(interview_json_path)
    report_filename = interview_filename.replace("oral-", "oral_evaluation_report-")

    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "oral_evaluation_reports")
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("EVALUATION COMPLETE")
    print(f"{'='*70}")
    print(f"Report saved to: {report_path}")

    return report


# CLI Tool for testing
if __name__ == "__main__":
    interview_path = r"C:\Users\Mega-PC\Desktop\ai_interviewer\backend\interviews\oral-MALEK-AJMI-2025-10-07-111358.json"

    try:
        report = evaluate_oral_interview(interview_path)
        print(f"\n✅ Evaluation completed successfully!")
        print(f"Overall Score: {report.overall_score}/10")
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
