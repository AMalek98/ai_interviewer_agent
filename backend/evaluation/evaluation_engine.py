"""
Main evaluation engine - orchestrates the complete evaluation process
Called by app.py after interview completion
"""
import os
import json
import yaml
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from .evaluation_models import EvaluationReport
from .qcm_evaluator import evaluate_qcm_questions
from .open_question_evaluator import evaluate_all_open_questions


# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
load_dotenv(env_path)

# Initialize LLM for summary generation
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.2)


def load_prompts():
    """Load evaluation prompts"""
    prompts_path = os.path.join(os.path.dirname(__file__), 'evaluation_prompts.yaml')
    with open(prompts_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_evaluation_summary(
    overall_score: float,
    qcm_score: float,
    tech_vocab_score: float,
    grammar_flow_score: float,
    qcm_details: dict
) -> str:
    """
    Generate overall evaluation summary using LLM

    Args:
        overall_score: Final weighted score 0-10
        qcm_score: QCM score 0-10
        tech_vocab_score: Average technical vocabulary score 0-10
        grammar_flow_score: Average grammar/flow score 0-10
        qcm_details: QCM details dict

    Returns:
        2-3 sentence summary string
    """
    prompts = load_prompts()

    summary_prompt = prompts["evaluation_summary_prompt"].format(
        overall_score=overall_score,
        qcm_score=qcm_score,
        tech_vocab_score=tech_vocab_score,
        grammar_flow_score=grammar_flow_score,
        qcm_correct=qcm_details["correct_answers"],
        qcm_total=qcm_details["total_questions"],
        qcm_percentage=qcm_details["percentage"]
    )

    response = llm.invoke(summary_prompt)
    return response.content.strip()


def evaluate_interview(interview_json_path: str) -> EvaluationReport:
    """
    Main evaluation function - orchestrates complete evaluation process

    Process:
    1. Load interview data
    2. Evaluate QCM questions (rule-based)
    3. Evaluate open questions (LLM-based)
    4. Calculate aggregate scores
    5. Apply coefficients (QCM 30%, Tech 40%, Grammar 30%)
    6. Generate summary
    7. Save report

    Args:
        interview_json_path: Path to interview JSON file

    Returns:
        EvaluationReport object
    """
    print(f"\n{'='*70}")
    print(f"STARTING INTERVIEW EVALUATION")
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
    questions = interview_data["questions"]

    print(f"\nCandidate: {metadata['candidate_name']}")
    print(f"Job Title: {metadata['job_title']}")
    print(f"Difficulty Level: {metadata['difficulty_level']}")
    print(f"Total Questions: {len(questions)}")

    # ========================================
    # STEP 2: Evaluate QCM Questions
    # ========================================
    print(f"\n{'='*70}")
    print("EVALUATING QCM QUESTIONS")
    print(f"{'='*70}")

    qcm_score, qcm_details = evaluate_qcm_questions(questions)

    # ========================================
    # STEP 3: Evaluate Open Questions
    # ========================================
    print(f"\n{'='*70}")
    print("EVALUATING OPEN QUESTIONS")
    print(f"{'='*70}")

    open_evaluations = evaluate_all_open_questions(questions)

    # ========================================
    # STEP 4: Calculate Aggregate Scores
    # ========================================
    if open_evaluations:
        avg_tech_vocab = sum(e.technical_vocab_score for e in open_evaluations) / len(open_evaluations)
        avg_grammar_flow = sum(e.grammar_flow_score for e in open_evaluations) / len(open_evaluations)
    else:
        avg_tech_vocab = 0.0
        avg_grammar_flow = 0.0

    print(f"\n{'='*70}")
    print("AGGREGATE SCORES")
    print(f"{'='*70}")
    print(f"QCM Score: {qcm_score}/10")
    print(f"Average Technical Vocabulary: {avg_tech_vocab:.2f}/10")
    print(f"Average Grammar/Flow: {avg_grammar_flow:.2f}/10")

    # ========================================
    # STEP 5: Calculate Final Score with Coefficients
    # ========================================
    # Coefficients: QCM 30%, Tech Vocab 40%, Grammar/Flow 30%
    final_score = (qcm_score * 0.3) + (avg_tech_vocab * 0.4) + (avg_grammar_flow * 0.3)

    print(f"\n{'='*70}")
    print("FINAL SCORE CALCULATION")
    print(f"{'='*70}")
    print(f"Formula: (QCM × 0.3) + (Tech × 0.4) + (Grammar × 0.3)")
    print(f"Calculation: ({qcm_score} × 0.3) + ({avg_tech_vocab:.2f} × 0.4) + ({avg_grammar_flow:.2f} × 0.3)")
    print(f"Final Score: {final_score:.2f}/10")

    # ========================================
    # STEP 6: Generate Evaluation Summary
    # ========================================
    print(f"\n{'='*70}")
    print("GENERATING EVALUATION SUMMARY")
    print(f"{'='*70}")

    summary = generate_evaluation_summary(
        overall_score=final_score,
        qcm_score=qcm_score,
        tech_vocab_score=avg_tech_vocab,
        grammar_flow_score=avg_grammar_flow,
        qcm_details=qcm_details.model_dump()
    )

    print(f"Summary: {summary}")

    # ========================================
    # STEP 7: Build Evaluation Report
    # ========================================
    report = EvaluationReport(
        candidate_name=metadata["candidate_name"],
        job_title=metadata["job_title"],
        difficulty_level=metadata["difficulty_level"],
        interview_date=metadata["interview_start_time"],
        overall_score=round(final_score, 2),
        qcm_score=round(qcm_score, 2),
        technical_vocab_score=round(avg_tech_vocab, 2),
        grammar_flow_score=round(avg_grammar_flow, 2),
        qcm_details=qcm_details,
        open_question_feedback=open_evaluations,
        evaluation_summary=summary
    )

    # ========================================
    # STEP 8: Save Evaluation Report
    # ========================================
    # Extract candidate name and date from interview filename
    interview_filename = os.path.basename(interview_json_path)
    # interview-malek-ajmi-06-10-2025.json -> evaluation_report-malek-ajmi-06-10-2025.json
    report_filename = interview_filename.replace("interview-", "evaluation_report-")

    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation_reports")
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("EVALUATION COMPLETE")
    print(f"{'='*70}")
    print(f"Report saved to: {report_path}")

    return report


# CLI Tool for standalone evaluation
if __name__ == "__main__":
    # Hardcoded path for testing
    interview_path = r"C:\Users\Mega-PC\Desktop\ai_interviewer\backend\interviews\interview-test-candidate-14-01-2025.json"

    try:
        report = evaluate_interview(interview_path)
        print(f"\nEvaluation completed successfully!")
        print(f"Overall Score: {report.overall_score}/10")
    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
