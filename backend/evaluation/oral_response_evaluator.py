"""
LLM-based oral interview response evaluator
Evaluates Q&A pairs from oral interview transcriptions
"""
import os
import time
import yaml
import re
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from .evaluation_models import (
    OralResponseEvaluation,
    OralQuestionDetail
)


# Load environment
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
load_dotenv(env_path)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.2
)


def load_prompts():
    """Load oral evaluation prompts"""
    prompts_path = os.path.join(
        os.path.dirname(__file__),
        'oral_evaluation_prompts.yaml'
    )
    with open(prompts_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def calculate_text_metrics(response: str) -> Tuple[int, int]:
    """Calculate word count and sentence count"""
    words = response.split()
    word_count = len(words)

    # Simple sentence count (count periods, exclamation, question marks)
    sentences = re.split(r'[.!?]+', response)
    sentence_count = len([s for s in sentences if s.strip()])

    return word_count, sentence_count


def evaluate_oral_response(
    question: str,
    response: str,
    turn: int,
    audio_file: str,
    difficulty_level: int,
    topics_covered: List[str],
    prompts: dict
) -> OralQuestionDetail:
    """
    Evaluate one oral interview Q&A pair using single LLM call

    Args:
        question: The question asked
        response: Candidate's spoken response (transcription)
        turn: Turn number
        audio_file: Audio filename (for reference)
        difficulty_level: Interview difficulty 1-10
        topics_covered: Topics discussed so far
        prompts: Loaded prompt templates

    Returns:
        OralQuestionDetail with scores and feedback
    """
    print(f"\n📝 Evaluating Turn {turn}...")
    print(f"   Question: {question[:60]}...")
    print(f"   Response: {response[:60]}...")

    # Calculate text metrics
    word_count, sentence_count = calculate_text_metrics(response)

    # Format prompt
    eval_prompt = prompts["oral_response_evaluation_prompt"].format(
        question=question,
        response=response,
        difficulty_level=difficulty_level,
        topics_covered=", ".join(topics_covered) if topics_covered else "None yet"
    )

    # Call LLM with structured output
    llm_with_structure = llm.with_structured_output(OralResponseEvaluation)
    evaluation = llm_with_structure.invoke(eval_prompt)

    print(f"   ✅ Relevance: {evaluation.relevance_score}/10")
    print(f"   ✅ Technical: {evaluation.technical_score}/10")
    print(f"   ✅ Coherence: {evaluation.coherence_score}/10")
    print(f"   ✅ Clarity: {evaluation.clarity_score}/10")

    # Rate limiting (10 RPM for free tier)
    time.sleep(10)

    # Combine phrases into feedback
    feedback = f"{evaluation.relevance_phrase}. {evaluation.technical_phrase}. {evaluation.coherence_phrase}."

    return OralQuestionDetail(
        turn=turn,
        question=question,
        response=response,
        audio_file=audio_file,
        relevance_score=round(evaluation.relevance_score, 2),
        technical_vocab_score=round(evaluation.technical_score, 2),
        coherence_score=round(evaluation.coherence_score, 2),
        clarity_score=round(evaluation.clarity_score, 2),
        word_count=word_count,
        sentence_count=sentence_count,
        feedback=feedback
    )


def evaluate_all_oral_responses(
    conversation: List[dict],
    difficulty_level: int,
    topics_covered: List[str]
) -> List[OralQuestionDetail]:
    """
    Evaluate all Q&A pairs in oral interview

    Args:
        conversation: Full conversation history from JSON
        difficulty_level: Interview difficulty score
        topics_covered: Topics covered in interview

    Returns:
        List of OralQuestionDetail evaluations
    """
    # Extract Q&A pairs
    qa_pairs = []
    current_question = None

    for entry in conversation:
        if entry["speaker"] == "interviewer":
            current_question = entry
        elif entry["speaker"] == "candidate" and current_question:
            qa_pairs.append({
                "question": current_question["text"],
                "response": entry["text"],
                "turn": entry["turn"],
                "audio_file": entry.get("audio_file")
            })

    print(f"\n{'='*60}")
    print(f"Evaluating {len(qa_pairs)} Q&A Pairs")
    print(f"{'='*60}")

    # Load prompts
    prompts = load_prompts()

    # Evaluate each pair
    evaluations = []
    for qa in qa_pairs:
        eval_result = evaluate_oral_response(
            question=qa["question"],
            response=qa["response"],
            turn=qa["turn"],
            audio_file=qa["audio_file"],
            difficulty_level=difficulty_level,
            topics_covered=topics_covered,
            prompts=prompts
        )
        evaluations.append(eval_result)

    return evaluations
