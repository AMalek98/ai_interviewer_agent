# Post-Interview Evaluation System - Implementation Steps

## Overview
Build an independent evaluation system that automatically runs after interview completion. The system evaluates both QCM questions (rule-based) and open questions (LLM-based) using coefficient-weighted scoring.

---

## Architecture Summary

```
Interview Completes
        ↓
app.py → end_interview()
        ↓
Saves Enhanced interview.json
        ↓
Calls evaluation_engine.evaluate_interview()
        ↓
    ┌───────┴────────┐
    │                │
QCM Eval        Open Question Eval
(Rule-based)    (LLM × 2 per question)
    │                │
    │         ┌──────┴──────┐
    │    Tech Vocab    Grammar/Flow
    │    (0-10)       (0-10)
    │         └──────┬──────┘
    │                │
    └───────┬────────┘
            ↓
    Calculate Final Score
    (Coefficients: QCM 30%, Tech 40%, Grammar 30%)
            ↓
    Generate Report
            ↓
evaluation_report-{name}-{date}.json
```

---

## Step-by-Step Implementation Plan

---

## **STEP 1: Create Directory Structure**

### Actions:
1. Create new folder: `backend/evaluation/`
2. Create new folder: `backend/evaluation_reports/`
3. Ensure folder exists: `backend/interviews/` (already exists)

### Files to create:
```
backend/
├── evaluation/
│   ├── __init__.py
│   ├── evaluation_models.py
│   ├── evaluation_prompts.yaml
│   ├── qcm_evaluator.py
│   ├── open_question_evaluator.py
│   └── evaluation_engine.py
└── evaluation_reports/
    └── (evaluation reports will be saved here)
```

### Verification:
- [x] Folders created
- [x] Empty `__init__.py` created in `evaluation/`

---

## **STEP 2: Create Pydantic Models**

### File: `backend/evaluation/evaluation_models.py`

### Implementation:
```python
"""
Pydantic models for interview evaluation system
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# LLM Structured Output Models (for evaluation)
# ============================================================================

class TechnicalVocabEval(BaseModel):
    """LLM output for technical vocabulary evaluation"""
    score: float = Field(ge=0, le=10, description="Technical vocabulary score 0-10")
    justification: str = Field(description="1-2 sentence justification")


class GrammarFlowEval(BaseModel):
    """LLM output for grammar/flow evaluation"""
    score: float = Field(ge=0, le=10, description="Grammar and coherence score 0-10")
    justification: str = Field(description="1-2 sentence justification")


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
```

### Verification:
- [x] File created with all models
- [x] Import test: `from evaluation.evaluation_models import EvaluationReport`

---

## **STEP 3: Create Evaluation Prompts**

### File: `backend/evaluation/evaluation_prompts.yaml`

### Implementation:
```yaml
# Evaluation Prompts for LLM-based Open Question Assessment
# Two separate evaluations per question: Technical Vocabulary + Grammar/Flow

technical_vocab_prompt: |
  You are evaluating a candidate's TECHNICAL VOCABULARY in their interview response.

  QUESTION ASKED:
  {question}

  CANDIDATE'S RESPONSE:
  {response}

  EVALUATION CRITERIA (Score 0-10):

  9-10 (Excellent):
    - Uses multiple relevant technical terms accurately
    - Demonstrates deep understanding through terminology
    - Technical language is precise and appropriate

  7-8 (Good):
    - Uses several relevant technical terms correctly
    - Shows solid technical understanding
    - Appropriate technical vocabulary for the question

  5-6 (Adequate):
    - Uses some technical terms
    - Basic technical vocabulary present
    - Could be more specific or detailed

  3-4 (Limited):
    - Few technical terms used
    - Mostly generic or vague language
    - Limited demonstration of technical knowledge

  0-2 (Poor):
    - No relevant technical terminology
    - Very generic response
    - Does not demonstrate technical understanding

  INSTRUCTIONS:
  1. Identify relevant technical terms in the response
  2. Evaluate if they are used correctly and appropriately
  3. Assess if the terminology demonstrates understanding of the subject
  4. Consider the question's technology focus and expected vocabulary

  Provide your evaluation with:
  - A score from 0-10
  - A brief justification (1-2 sentences) explaining the score

grammar_flow_prompt: |
  You are evaluating the COMMUNICATION QUALITY of a candidate's interview response.

  QUESTION ASKED:
  {question}

  CANDIDATE'S RESPONSE:
  {response}

  EVALUATION CRITERIA (Score 0-10):

  9-10 (Excellent):
    - Perfect or near-perfect grammar
    - Smooth, logical flow between ideas
    - Highly coherent and well-structured
    - Fully and directly answers the question
    - Complete explanation covering all aspects

  7-8 (Good):
    - Good grammar with minor errors
    - Clear structure and logical flow
    - Coherent explanation
    - Addresses the question well
    - Covers main aspects adequately

  5-6 (Adequate):
    - Acceptable grammar with some errors
    - Some flow issues or disorganization
    - Partially answers the question
    - Missing some aspects or lacks depth

  3-4 (Limited):
    - Poor grammar affecting clarity
    - Disjointed or unclear flow
    - Weak connection to the question
    - Incomplete or superficial answer

  0-2 (Poor):
    - Very poor grammar, hard to understand
    - Incoherent or no logical flow
    - Does not answer the question
    - Extremely incomplete or off-topic

  INSTRUCTIONS:
  1. Evaluate grammatical correctness and sentence structure
  2. Assess logical flow and coherence of the explanation
  3. Check if the response actually answers what was asked
  4. Evaluate completeness: Does it cover the main aspects of the question?
  5. Consider clarity: Is the explanation easy to understand?

  Provide your evaluation with:
  - A score from 0-10
  - A brief justification (1-2 sentences) explaining the score

feedback_generation_prompt: |
  Generate constructive feedback for the candidate based on these two evaluations:

  TECHNICAL VOCABULARY EVALUATION:
  Score: {tech_score}/10
  Justification: {tech_justification}

  GRAMMAR/COMMUNICATION EVALUATION:
  Score: {grammar_score}/10
  Justification: {grammar_justification}

  INSTRUCTIONS:
  Write 2-3 concise sentences of actionable feedback that:
  1. Highlights what the candidate did well (if applicable)
  2. Identifies the main area(s) for improvement
  3. Provides constructive guidance

  Be professional, balanced, and specific. Focus on both technical communication and general communication skills.

  Example format:
  "The response demonstrates [technical strength/weakness]. The explanation [communication strength/weakness]. Consider [specific actionable advice]."

evaluation_summary_prompt: |
  Generate an overall evaluation summary for this candidate's interview performance.

  SCORES:
  - Overall Score: {overall_score}/10
  - QCM Score: {qcm_score}/10 (30% weight)
  - Technical Vocabulary: {tech_vocab_score}/10 (40% weight)
  - Grammar/Flow: {grammar_flow_score}/10 (30% weight)

  QCM DETAILS:
  - Correct: {qcm_correct}/{qcm_total} ({qcm_percentage}%)

  INSTRUCTIONS:
  Write 2-3 sentences summarizing the candidate's overall performance:
  1. Start with the overall score and general assessment
  2. Highlight the strongest area
  3. Identify the area needing most improvement

  Be professional and constructive. This summary helps HR/hiring managers make decisions.

  Example format:
  "The candidate scored {overall_score}/10 overall, indicating [level] performance. [Strength observation]. [Improvement area observation]."
```

### Verification:
- [x] File created with all prompts
- [x] YAML syntax is valid (test with `yaml.safe_load()`)

---

## **STEP 4: Implement QCM Evaluator**

### File: `backend/evaluation/qcm_evaluator.py`

### Implementation:
```python
"""
Rule-based QCM question evaluator
Simple correct/incorrect scoring
"""
from typing import List, Tuple
from evaluation_models import QCMDetails


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

    print(f"QCM Evaluation: {correct}/{total} correct ({percentage:.1f}%) → Score: {score_out_of_10:.2f}/10")

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
    print(f"Test Score: {score}/10")
    print(f"Details: {details}")
```

### Verification:
- [x] File created
- [x] Test function runs successfully
- [x] Returns correct score (3/5 correct = 6.0/10)

---

## **STEP 5: Implement Open Question Evaluator**

### File: `backend/evaluation/open_question_evaluator.py`

### Implementation:
```python
"""
LLM-based open question evaluator
Uses structured output with separate calls for tech vocab and grammar/flow
"""
import os
import yaml
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from evaluation_models import (
    TechnicalVocabEval,
    GrammarFlowEval,
    OpenQuestionDetail
)


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
    Evaluate one open question using LLM with structured output
    Makes 3 LLM calls:
    1. Technical vocabulary evaluation
    2. Grammar/flow evaluation
    3. Combined feedback generation

    Args:
        question: Question dict with question_text, response, question_id
        prompts: Loaded prompt templates

    Returns:
        OpenQuestionDetail with scores and feedback
    """
    question_text = question["question_text"]
    response = question["response"]
    question_id = question["question_id"]

    print(f"\nEvaluating Open Question {question_id}...")

    # ========================================
    # Call 1: Technical Vocabulary Evaluation
    # ========================================
    tech_prompt = prompts["technical_vocab_prompt"].format(
        question=question_text,
        response=response
    )

    llm_with_structure = llm.with_structured_output(TechnicalVocabEval)
    tech_eval = llm_with_structure.invoke(tech_prompt)

    print(f"  Tech Vocab Score: {tech_eval.score}/10")
    print(f"  Justification: {tech_eval.justification}")

    # ========================================
    # Call 2: Grammar/Flow Evaluation
    # ========================================
    grammar_prompt = prompts["grammar_flow_prompt"].format(
        question=question_text,
        response=response
    )

    llm_with_structure = llm.with_structured_output(GrammarFlowEval)
    grammar_eval = llm_with_structure.invoke(grammar_prompt)

    print(f"  Grammar/Flow Score: {grammar_eval.score}/10")
    print(f"  Justification: {grammar_eval.justification}")

    # ========================================
    # Call 3: Generate Combined Feedback
    # ========================================
    feedback_prompt = prompts["feedback_generation_prompt"].format(
        tech_score=tech_eval.score,
        tech_justification=tech_eval.justification,
        grammar_score=grammar_eval.score,
        grammar_justification=grammar_eval.justification
    )

    feedback_response = llm.invoke(feedback_prompt)
    feedback = feedback_response.content.strip()

    print(f"  Feedback: {feedback}")

    # Build result
    return OpenQuestionDetail(
        question_id=question_id,
        question=question_text,
        response=response,
        technical_vocab_score=round(tech_eval.score, 2),
        grammar_flow_score=round(grammar_eval.score, 2),
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
```

### Verification:
- [x] File created
- [x] Test function runs successfully
- [x] LLM returns structured output correctly
- [x] All 3 LLM calls complete

---

## **STEP 6: Implement Main Evaluation Engine**

### File: `backend/evaluation/evaluation_engine.py`

### Implementation:
```python
"""
Main evaluation engine - orchestrates the complete evaluation process
Called by app.py after interview completion
"""
import os
import json
import yaml
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI

from evaluation_models import EvaluationReport
from qcm_evaluator import evaluate_qcm_questions
from open_question_evaluator import evaluate_all_open_questions


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
    # interview-malek-ajmi-06-10-2025.json → evaluation_report-malek-ajmi-06-10-2025.json
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
    import sys

    if len(sys.argv) < 2:
        print("Usage: python evaluation_engine.py <interview_filename>")
        print("Example: python evaluation_engine.py interview-malek-ajmi-06-10-2025.json")
        sys.exit(1)

    interview_filename = sys.argv[1]
    interview_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "interviews",
        interview_filename
    )

    try:
        report = evaluate_interview(interview_path)
        print(f"\n✅ Evaluation completed successfully!")
        print(f"Overall Score: {report.overall_score}/10")
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### Verification:
- [x] File created
- [x] Can be run standalone via CLI
- [x] Test with existing interview file

---

## **STEP 7: Modify app.py - Update Interview Data Structure**

### File: `backend/app.py`

### Location: `end_interview()` function (around line 1085)

### Changes Required:

**Before:**
```python
def end_interview(state: InterviewState) -> Dict[str, Any]:
    """End the interview and generate summary"""
    print("=== Interview Completed ===")
    state["complete"] = True

    # Generate simple summary
    total_questions = len(state["questions_history"])
    qcm_correct = sum(1 for resp in state["responses_history"]
                      if resp.is_correct is True)
    qcm_total = sum(1 for q in state["questions_history"]
                    if q.question_type == "qcm")

    summary = {
        "total_questions": total_questions,
        "qcm_score": f"{qcm_correct}/{qcm_total}" if qcm_total > 0 else "N/A",
        "difficulty_level": state["difficulty_score"],
        "completed": True
    }

    print(f"Interview Summary: {summary}")
    return summary
```

**After:**
```python
def end_interview(state: InterviewState) -> Dict[str, Any]:
    """End the interview, save enhanced JSON, and trigger evaluation"""
    print("=== Interview Completed ===")
    state["complete"] = True

    # ========================================
    # Build Enhanced Interview JSON
    # ========================================
    candidate_name = state["structured_cv"].personal_info.name or "Unknown"
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
    interviews_dir = os.path.join(os.path.dirname(__file__), "interviews")
    os.makedirs(interviews_dir, exist_ok=True)

    interview_filename = f"interview-{candidate_name_formatted}-{current_date}.json"
    interview_path = os.path.join(interviews_dir, interview_filename)

    with open(interview_path, 'w', encoding='utf-8') as f:
        json.dump(interview_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Interview data saved: {interview_path}")

    # ========================================
    # Trigger Evaluation
    # ========================================
    print("\n" + "="*70)
    print("STARTING POST-INTERVIEW EVALUATION")
    print("="*70)

    try:
        from evaluation.evaluation_engine import evaluate_interview

        evaluation_report = evaluate_interview(interview_path)

        print("\n✅ Evaluation completed successfully!")
        print(f"Overall Score: {evaluation_report.overall_score}/10")
        print(f"Report saved to: evaluation_reports/evaluation_report-{candidate_name_formatted}-{current_date}.json")

    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

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
        "interview_file": interview_filename
    }

    print(f"\nInterview Summary: {summary}")
    return summary
```

### Additional Imports Needed at Top of app.py:
```python
from datetime import datetime  # Should already exist
import os  # Should already exist
```

### Verification:
- [ ] Modified `end_interview()` function
- [ ] Imports added
- [ ] Test interview completion triggers evaluation

---

## **STEP 8: Add start_time Tracking to Interview State**

### File: `backend/app.py`

### Location: `initialize_interview()` function (around line 113)

### Add to the return statement:
```python
return InterviewState(
    # ... existing fields ...
    answer_references={},
    start_time=datetime.now().isoformat()  # ADD THIS LINE
)
```

### Also update state_classes.py:

### File: `backend/state_classes.py`

### Location: `InterviewState` TypedDict (around line 138)

### Add field:
```python
class InterviewState(TypedDict):
    # ... existing fields ...

    # Phase 5: Answer-aware follow-up system
    answer_references: Dict[int, str]

    # Evaluation tracking
    start_time: str  # ADD THIS LINE - ISO format timestamp
```

### Verification:
- [ ] `start_time` added to InterviewState
- [ ] `start_time` set in `initialize_interview()`
- [ ] Interview JSON includes correct timestamp

---

## **STEP 9: Testing & Verification**

### Test 1: Run Standalone Evaluation on Existing Interview
```bash
cd backend
python -m evaluation.evaluation_engine ../interviews/interview-malek-ajmi-06-10-2025.json
```

**Expected Output:**
- QCM evaluation completes
- 5 open questions evaluated (15 LLM calls total)
- Final score calculated
- Report saved to `evaluation_reports/`

### Test 2: Complete End-to-End Interview
1. Start interview via `/start_interview`
2. Answer all 10 questions
3. Complete interview
4. Verify:
   - [ ] Enhanced interview.json saved
   - [ ] Evaluation automatically triggered
   - [ ] Evaluation report generated
   - [ ] Console shows all evaluation steps

### Test 3: Verify Report Structure
```python
import json

# Load generated report
with open('backend/evaluation_reports/evaluation_report-malek-ajmi-06-10-2025.json', 'r') as f:
    report = json.load(f)

# Check structure
assert "overall_score" in report
assert "qcm_score" in report
assert "technical_vocab_score" in report
assert "grammar_flow_score" in report
assert len(report["open_question_feedback"]) == 5
assert report["qcm_details"]["total_questions"] == 5

print("✅ Report structure is valid!")
```

### Test 4: Score Calculation Verification
**Given:**
- QCM: 4/5 correct = 8.0/10
- Tech Vocab: avg 6.0/10
- Grammar: avg 4.0/10

**Expected:**
```
Final = (8.0 × 0.3) + (6.0 × 0.4) + (4.0 × 0.3)
      = 2.4 + 2.4 + 1.2
      = 6.0/10
```

### Verification Checklist:
- [ ] Standalone evaluation works
- [ ] End-to-end interview → evaluation works
- [ ] Report JSON structure is correct
- [ ] Score calculations are accurate
- [ ] All files saved to correct locations

---

## **STEP 10: Optional - Create Flask API Endpoint**

### File: `backend/app.py`

### Add Endpoint (optional, for manual evaluation trigger):
```python
@app.route('/evaluate_interview', methods=['POST'])
def evaluate_interview_endpoint():
    """
    Optional endpoint to manually trigger evaluation

    POST /evaluate_interview
    Body: { "interview_filename": "interview-malek-ajmi-06-10-2025.json" }
    """
    try:
        data = request.json
        interview_filename = data.get('interview_filename')

        if not interview_filename:
            return jsonify({'error': 'interview_filename is required'}), 400

        interview_path = os.path.join('backend/interviews', interview_filename)

        if not os.path.exists(interview_path):
            return jsonify({'error': 'Interview file not found'}), 404

        # Run evaluation
        from evaluation.evaluation_engine import evaluate_interview
        report = evaluate_interview(interview_path)

        return jsonify({
            'message': 'Evaluation completed successfully',
            'overall_score': report.overall_score,
            'report_file': f"evaluation_report-{interview_filename.replace('interview-', '')}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Verification:
- [ ] Endpoint created (if desired)
- [ ] Can manually trigger evaluation via POST

---

## **STEP 11: Documentation & Final Checks**

### Create README for Evaluation System

### File: `backend/evaluation/README.md`

```markdown
# Interview Evaluation System

## Overview
Automatic post-interview evaluation system using LLM-based assessment for open questions and rule-based scoring for QCM questions.

## Scoring System

### Final Score Calculation
```
Final Score = (QCM × 0.3) + (Tech Vocab × 0.4) + (Grammar × 0.3)
```

- **QCM**: 30% weight - Rule-based correct/incorrect
- **Technical Vocabulary**: 40% weight - LLM evaluation of technical terms
- **Grammar/Flow**: 30% weight - LLM evaluation of communication quality

All scores are 0-10 scale.

## Files

- `evaluation_models.py` - Pydantic models
- `evaluation_prompts.yaml` - LLM prompt templates
- `qcm_evaluator.py` - Rule-based QCM scoring
- `open_question_evaluator.py` - LLM-based open question evaluation
- `evaluation_engine.py` - Main orchestrator

## Usage

### Automatic (after interview)
Evaluation runs automatically when interview completes.

### Manual (CLI)
```bash
python -m evaluation.evaluation_engine interview-{name}-{date}.json
```

### Manual (API)
```bash
POST /evaluate_interview
{
  "interview_filename": "interview-malek-ajmi-06-10-2025.json"
}
```

## Output

Evaluation reports saved to: `backend/evaluation_reports/evaluation_report-{name}-{date}.json`

Report includes:
- Overall score and dimensional scores
- QCM details (correct/total)
- Per-question feedback (2-3 sentences each)
- Overall evaluation summary
```

---

## Final Verification Checklist

### Files Created:
- [ ] `backend/evaluation/__init__.py`
- [ ] `backend/evaluation/evaluation_models.py`
- [ ] `backend/evaluation/evaluation_prompts.yaml`
- [ ] `backend/evaluation/qcm_evaluator.py`
- [ ] `backend/evaluation/open_question_evaluator.py`
- [ ] `backend/evaluation/evaluation_engine.py`
- [ ] `backend/evaluation/README.md`
- [ ] `backend/evaluation_reports/` (folder)

### Files Modified:
- [ ] `backend/app.py` - `end_interview()` function updated
- [ ] `backend/app.py` - imports added
- [ ] `backend/state_classes.py` - `start_time` field added
- [ ] `backend/app.py` - `initialize_interview()` updated

### Functionality Tests:
- [ ] Standalone evaluation works
- [ ] End-to-end interview triggers evaluation
- [ ] Enhanced interview.json structure correct
- [ ] Evaluation report structure correct
- [ ] Score calculations accurate
- [ ] All LLM calls complete successfully

### Integration Tests:
- [ ] Interview saves enhanced JSON
- [ ] Evaluation runs automatically after interview
- [ ] Both files saved to correct directories
- [ ] No errors in console during process

---

## Implementation Order Summary

1. [x] Create directory structure
2. [x] Create Pydantic models
3. [x] Create evaluation prompts
4. [x] Implement QCM evaluator
5. [x] Implement open question evaluator
6. [x] Implement evaluation engine
7. [ ] Modify app.py - end_interview()
8. [ ] Add start_time tracking
9. [ ] Test everything
10. [ ] Optional API endpoint
11. [ ] Create documentation

---

## Estimated Time
- Steps 1-3: 30 minutes (setup + models + prompts)
- Steps 4-5: 1 hour (evaluators)
- Step 6: 1 hour (main engine)
- Step 7-8: 30 minutes (app.py modifications)
- Step 9: 1 hour (testing)
- Step 10-11: 30 minutes (optional + docs)

**Total: ~4.5 hours**

---

## Success Criteria

✅ Interview completes and saves enhanced JSON
✅ Evaluation runs automatically
✅ Report generated with all required fields
✅ Scores calculated correctly with coefficients
✅ LLM evaluations complete for all open questions
✅ 2-3 sentence feedback per question
✅ No errors in console

---

## Notes

- Evaluation is **independent** from interview (runs after completion)
- Human makes final pass/fail decision based on report
- System provides scores and feedback for decision support
- All scores are 0-10 scale for consistency
- Coefficient-based weighting ensures balanced assessment
