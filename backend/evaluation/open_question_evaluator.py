"""
LLM-based open question evaluator
Ultra-compact version: Single LLM call per question with 3-phrase output
Reduces token usage by 80% compared to previous 3-call approach
"""
import os
import time
import yaml
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from .evaluation_models import (
    CompactEvaluation,
    OpenQuestionDetail
)


# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
load_dotenv(env_path)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.2  # Low temperature for consistent evaluation
)


def load_prompts():
    """Load evaluation prompts from YAML file"""
    prompts_path = os.path.join(
        os.path.dirname(__file__),
        'evaluation_prompts.yaml'
    )
    with open(prompts_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def evaluate_open_question(question: dict, prompts: dict) -> OpenQuestionDetail:
    """
    Evaluate one open question using ultra-compact single LLM call

    OPTIMIZATION: Reduced from 3 LLM calls to 1 call
    - Old approach: Tech eval → Grammar eval → Feedback generation (3 calls, 30s wait)
    - New approach: Single combined evaluation (1 call, 10s wait)
    - Token savings: ~80% reduction (1,030 → 200 tokens per question)

    Args:
        question: Question dict with question_text, response, question_id, reference_answer
        prompts: Loaded prompt templates

    Returns:
        OpenQuestionDetail with scores and 3-phrase feedback
    """
    question_text = question["question_text"]
    response = question["response"]
    question_id = question["question_id"]
    reference_answer = question.get("reference_answer", "")

    print(f"\nEvaluating Open Question {question_id}...")

    # Check if reference answer exists
    if not reference_answer:
        print(f"  WARNING: No reference answer found for question {question_id}")
        reference_answer = "No reference answer available for comparison."

    # ========================================
    # Single Combined Evaluation Call
    # ========================================
    compact_prompt = prompts["compact_evaluation_prompt"].format(
        response=response,
        reference_answer=reference_answer
    )

    llm_with_structure = llm.with_structured_output(CompactEvaluation)
    evaluation = llm_with_structure.invoke(compact_prompt)

    print(f"  Technical Score: {evaluation.technical_score}/10")
    print(f"  Grammar Score: {evaluation.grammar_score}/10")
    print(f"  Grammar: {evaluation.grammar_phrase}")
    print(f"  Technical: {evaluation.technical_phrase}")
    print(f"  Missing: {evaluation.missing_phrase}")

    # Rate limiting: Wait 10 seconds to stay under 10 RPM (free tier limit)
    time.sleep(10)

    # Build 3-phrase feedback from compact evaluation
    feedback = f"{evaluation.grammar_phrase}. {evaluation.technical_phrase}. {evaluation.missing_phrase}."

    # Build result
    return OpenQuestionDetail(
        question_id=question_id,
        question=question_text,
        response=response,
        technical_vocab_score=round(evaluation.technical_score, 2),
        grammar_flow_score=round(evaluation.grammar_score, 2),
        feedback=feedback
    )


def evaluate_all_open_questions(questions: List[dict]) -> List[OpenQuestionDetail]:
    """
    Evaluate all open questions in the interview

    Args:
        questions: List of all interview questions (will filter for open)

    Returns:
        List of OpenQuestionDetail evaluations
    """
    # Filter only open questions
    open_questions = [q for q in questions if q.get("type") == "open"]

    if not open_questions:
        print("No open questions found to evaluate")
        return []

    print(f"\n{'='*60}")
    print(f"Evaluating {len(open_questions)} Open Questions")
    print(f"{'='*60}")

    # Load prompts once
    prompts = load_prompts()

    # Evaluate each question
    evaluations = []
    for question in open_questions:
        eval_result = evaluate_open_question(question, prompts)
        evaluations.append(eval_result)

    return evaluations


# Test function
if __name__ == "__main__":
    # Test with sample question
    test_question = {
        "question_id": 1,
        "type": "open",
        "question_text": "Explain how you implemented the LangChain agent.",
        "response": "We used structured output and high-quality prompts to improve efficiency."
    }

    result = evaluate_all_open_questions([test_question])
    print(f"\nTest Result: {result[0]}")
    print(f"\nScores:")
    print(f"  Technical Vocab: {result[0].technical_vocab_score}/10")
    print(f"  Grammar/Flow: {result[0].grammar_flow_score}/10")
    print(f"\nFeedback: {result[0].feedback}")
