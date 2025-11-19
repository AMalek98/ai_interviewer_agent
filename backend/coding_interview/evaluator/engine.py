"""
Code Evaluator for Coding Interview Responses
Orchestrates code compilation, testing, and LLM-based evaluation with scoring
"""

import json
import os
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared modules
from shared.llm_setup import get_llm

# Import utilities
from .piston_compiler import execute_code, run_test_cases, compare_buggy_vs_fixed
from ..test_case_generator import load_test_cases, TestCaseSet
from .output_comparator import ExecutionComparison, compare_outputs


class EvaluationResult(BaseModel):
    """Evaluation result for a single question"""
    question_title: str = Field(description="Question title")
    question_type: str = Field(description="Question type")
    score: int = Field(description="Score 0-10")
    feedback: List[str] = Field(description="3-phrase feedback")
    details: Dict[str, Any] = Field(default={}, description="Additional evaluation details")


class CodingInterviewEvaluation(BaseModel):
    """Complete evaluation results for coding interview"""
    candidate_name: str = Field(description="Candidate name")
    interview_date: str = Field(description="Interview date")
    overall_score: float = Field(description="Overall average score")
    overall_feedback: str = Field(description="Overall feedback summary")
    questions: List[EvaluationResult] = Field(description="Per-question results")
    evaluation_timestamp: str = Field(description="ISO timestamp of evaluation")


def parse_candidate_response(response_text: str, question_type: str) -> Dict[str, str]:
    """
    Parse candidate response based on question type

    Args:
        response_text: Raw response from candidate
        question_type: Type of question (coding_debug, coding_explain, db_schema)

    Returns:
        Dict with parsed components: {code: str, explanation: str, queries: str}
    """
    if question_type == 'coding_debug':
        # Parse debug response format: "FIXED CODE:\n{code}\n\nEXPLANATION:\n{explanation}"
        code_match = re.search(r'FIXED CODE:\s*\n(.*?)(?:\n\nEXPLANATION:|$)', response_text, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'EXPLANATION:\s*\n(.*)', response_text, re.DOTALL | re.IGNORECASE)

        code = code_match.group(1).strip() if code_match else response_text.strip()
        explanation = explanation_match.group(1).strip() if explanation_match else ""

        return {
            'code': code,
            'explanation': explanation,
            'queries': ''
        }

    elif question_type == 'coding_explain':
        # For explanation questions, the entire response is the analysis
        return {
            'code': '',
            'explanation': response_text.strip(),
            'queries': ''
        }

    elif question_type == 'db_schema':
        # Parse DB schema format: "SQL SCHEMA:\n{schema}\n\nDESIGN EXPLANATION:\n{explanation}\n\nEXAMPLE QUERIES:\n{queries}"
        schema_match = re.search(r'SQL SCHEMA:\s*\n(.*?)(?:\n\nDESIGN EXPLANATION:|$)', response_text, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'DESIGN EXPLANATION:\s*\n(.*?)(?:\n\nEXAMPLE QUERIES:|$)', response_text, re.DOTALL | re.IGNORECASE)
        queries_match = re.search(r'EXAMPLE QUERIES:\s*\n(.*)', response_text, re.DOTALL | re.IGNORECASE)

        # Fallback: if structured format not found, treat entire response as schema
        schema = schema_match.group(1).strip() if schema_match else response_text.strip()
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        queries = queries_match.group(1).strip() if queries_match else ""

        return {
            'code': schema,
            'explanation': explanation,
            'queries': queries
        }

    else:
        # Fallback: return entire response as code
        return {
            'code': response_text.strip(),
            'explanation': '',
            'queries': ''
        }


def evaluate_with_llm(
    question_data: Dict[str, Any],
    candidate_response: Dict[str, str],
    compilation_results: Optional[Dict[str, Any]] = None,
    test_results: Optional[List[Dict[str, Any]]] = None,
    execution_comparison: Optional[ExecutionComparison] = None
) -> Tuple[int, List[str]]:
    """
    Use LLM to evaluate response and provide score + feedback

    Args:
        question_data: Original question details
        candidate_response: Parsed candidate response
        compilation_results: Results from code compilation (optional)
        test_results: Results from test cases (optional)
        execution_comparison: Structured comparison of expected vs actual output (optional)

    Returns:
        Tuple of (score: int, feedback: List[str])
    """
    question_type = question_data.get('question_type', 'unknown')
    question_text = question_data.get('question_text', '')

    # Build compilation summary
    compilation_summary = "No compilation performed"
    if compilation_results:
        if 'fixed_results' in compilation_results:
            fixed = compilation_results['fixed_results']
            passed = fixed.get('passed_count', 0)
            total = fixed.get('total_count', 0)
            compilation_summary = f"Code compiled and tested: {passed}/{total} test cases passed"
            if fixed.get('compilation_error'):
                compilation_summary += " (compilation errors present)"
        else:
            compilation_summary = f"Compilation success: {compilation_results.get('success', False)}"

    # Build test results summary
    test_summary = "No test results"
    if test_results:
        passed = sum(1 for t in test_results if t.get('passed', False))
        total = len(test_results)
        test_summary = f"{passed}/{total} tests passed"

    # Build execution comparison summary (for structured output comparison)
    execution_summary = ""
    if execution_comparison:
        execution_summary = f"""

**Code Execution Comparison:**
Expected Output: {execution_comparison.expected_output}
Actual Output: {execution_comparison.actual_output}
Match Status: {execution_comparison.match_status}
Output Correctness: {execution_comparison.match_confidence * 100:.1f}%
Exit Code: {execution_comparison.exit_code}
Compilation Success: {'Yes' if execution_comparison.compilation_success else 'No'}
Notes: {execution_comparison.comparison_notes}
"""

    prompt = f"""
You are evaluating a candidate's coding interview response. Be objective and constructive.

**Question Type:** {question_type}
**Question:** {question_text}

**Candidate's Code/Response:**
{candidate_response.get('code', 'N/A')}

**Candidate's Explanation:**
{candidate_response.get('explanation', 'N/A')}

**Compilation Results:**
{compilation_summary}

**Test Results:**
{test_summary}{execution_summary}

**Evaluation Criteria:**

**CRITICAL: SEQUENTIAL EVALUATION PRIORITY FOR DEBUG QUESTIONS:**

**1. OUTPUT CORRECTNESS (Primary - This determines max possible score):**
   - **EXECUTION_ERROR** → Code has runtime/syntax errors → **MAX SCORE = 2**
     - Score 2: Has errors but explanation shows some understanding
     - Score 1: Has errors with poor explanation
     - Score 0: Complete failure

   - **NO_MATCH** → Wrong output produced → **MAX SCORE = 3**
     - Score 3: Wrong output but explanation shows understanding of what was needed
     - Score 2: Wrong output with limited understanding
     - Score 1: Wrong output and poor explanation

   - **PARTIAL_MATCH** → Partially correct output → **MAX SCORE = 6**
     - Score 6: Output mostly correct + good explanation
     - Score 5: Output partially correct + adequate explanation
     - Score 4: Output partially correct + weak explanation

   - **EXACT_MATCH** → Perfect output → **FULL RANGE 7-10**
     - Score 9-10: Perfect output + excellent explanation + optimal code quality
     - Score 8: Perfect output + good explanation + decent code
     - Score 7: Perfect output + minimal but correct explanation

**2. EXPLANATION QUALITY (Secondary - Only matters if output is correct):**
   - Did they identify the actual bugs correctly?
   - Did they explain why the bugs caused incorrect behavior?
   - Did they explain their fix properly?

**3. CODE QUALITY (Tertiary - Only considered for EXACT_MATCH):**
   - Code efficiency and best practices
   - Error handling and edge cases
   - Code readability and style

**For Explain Questions:**
- Focus on explanation quality, code understanding, and analysis depth
- Output correctness is secondary (only if code includes test execution)
- 9-10: Deep understanding, excellent complexity analysis, insightful improvements
- 7-8: Good understanding, correct analysis, reasonable improvements
- 5-6: Basic understanding, partial analysis, simple improvements
- 3-4: Limited understanding, weak analysis
- 0-2: Poor understanding, incorrect analysis

**For Database Questions:**
- **Syntax Validation (Automatic):** Pass/Fail based on SQL execution
- **Schema Design Evaluation (LLM):**
  - 9-10: All requirements met, optimal design, proper normalization, appropriate constraints
  - 7-8: Most requirements met, good design, minor improvements possible
  - 5-6: Basic requirements met, design needs improvement, missing some constraints
  - 3-4: Missing key requirements, poor design, major issues
  - 0-2: Invalid syntax OR missing critical tables/columns

**CRITICAL**: If SQL has syntax errors, max score = 2. LLM should verify:
1. Are all required tables present?
2. Are all required columns present with correct types?
3. Are relationships (foreign keys) properly defined?
4. Are constraints (PRIMARY KEY, UNIQUE, NOT NULL) appropriate?

**YOUR TASK:**
Provide EXACTLY 3 short feedback phrases (one sentence each) and a numerical score.

**Return ONLY valid JSON in this exact format:**
```json
{{
  "score": 7,
  "feedback": [
    "First observation about what they did well",
    "Main issue or area for improvement",
    "Overall assessment or recommendation"
  ]
}}
```

Return ONLY the JSON object, nothing else.
"""

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        evaluation_json = response.content.strip()

        # Clean response
        if evaluation_json.startswith("```json"):
            evaluation_json = evaluation_json.replace("```json", "").replace("```", "").strip()
        elif evaluation_json.startswith("```"):
            evaluation_json = evaluation_json.replace("```", "").strip()

        # Parse JSON
        evaluation_data = json.loads(evaluation_json)
        score = evaluation_data.get('score', 5)
        feedback = evaluation_data.get('feedback', [])

        # Validate score range
        score = max(0, min(10, score))

        # STRICT OUTPUT-BASED SCORING: Apply hard caps based on match_status
        # This ensures output correctness is the primary factor for debug questions
        if execution_comparison:
            original_score = score
            match_status = execution_comparison.match_status

            if match_status == "EXECUTION_ERROR":
                # Code has syntax/runtime errors - max score 2/10
                if score > 2:
                    print(f"[SCORING] Score capped from {original_score} to 2 due to EXECUTION_ERROR (code has runtime/syntax errors)")
                    score = min(score, 2)
                    # Update feedback to reflect the error
                    if "runtime error" not in feedback[0].lower() and "syntax error" not in feedback[0].lower():
                        feedback[0] = f"Code has execution errors: {execution_comparison.comparison_notes[:80]}"

            elif match_status == "NO_MATCH":
                # Wrong output - max score 3/10
                if score > 3:
                    print(f"[SCORING] Score capped from {original_score} to 3 due to NO_MATCH (wrong output produced)")
                    score = min(score, 3)
                    # Update feedback to reflect incorrect output
                    if "output" not in feedback[0].lower() or "correct" in feedback[0].lower():
                        feedback[0] = f"Output is incorrect: expected '{execution_comparison.expected_output[:50]}...', got '{execution_comparison.actual_output[:50]}...'"

            elif match_status == "PARTIAL_MATCH":
                # Partially correct output - max score 6/10
                if score > 6:
                    print(f"[SCORING] Score capped from {original_score} to 6 due to PARTIAL_MATCH (output partially correct)")
                    score = min(score, 6)

            # EXACT_MATCH: No cap, allow full range 7-10 based on explanation and code quality
            elif match_status == "EXACT_MATCH":
                # Ensure minimum score of 7 for perfect output
                if score < 7:
                    print(f"[SCORING] Score bumped from {original_score} to 7 due to EXACT_MATCH (perfect output)")
                    score = max(score, 7)

        # Ensure exactly 3 feedback phrases
        if len(feedback) < 3:
            feedback.extend(["Additional feedback needed"] * (3 - len(feedback)))
        elif len(feedback) > 3:
            feedback = feedback[:3]

        return score, feedback

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse LLM evaluation: {e}")
        return 5, ["Unable to parse evaluation", "Please review manually", "Default score assigned"]

    except Exception as e:
        print(f"[ERROR] Error in LLM evaluation: {e}")
        return 5, ["Evaluation error occurred", "Please review manually", "Default score assigned"]


def evaluate_debug_question(
    question_data: Dict[str, Any],
    candidate_response: str,
    test_cases: Optional[TestCaseSet] = None
) -> EvaluationResult:
    """
    Evaluate a debug coding question

    Process:
    1. Parse fixed code from response
    2. Compile buggy code (should fail/produce wrong output)
    3. Compile fixed code (should pass test cases)
    4. Compare outputs
    5. LLM evaluates code quality

    Args:
        question_data: Original question details
        candidate_response: Candidate's response text
        test_cases: Test cases for validation

    Returns:
        EvaluationResult object
    """
    print(f"[DEBUG] Evaluating debug question: {question_data.get('question_text', 'Unknown')}")

    # Parse response
    parsed_response = parse_candidate_response(candidate_response, 'coding_debug')
    fixed_code = parsed_response['code']
    explanation = parsed_response['explanation']

    # Get buggy code and language from question
    buggy_code = question_data.get('buggy_code', '')
    language = question_data.get('target_language', 'python')

    evaluation_details = {}

    # If test cases available (DB questions), compile and test both versions
    if test_cases and test_cases.test_cases:
        print(f"[INFO] Running code through {len(test_cases.test_cases)} test cases...")

        # Convert test cases to format expected by piston_compiler
        test_case_list = [
            {
                'input': tc.input,
                'expected_output': tc.expected_output,
                'description': tc.description
            }
            for tc in test_cases.test_cases
        ]

        # Rate limiting delay before compilation
        time.sleep(0.3)

        # Compare buggy vs fixed code
        comparison = compare_buggy_vs_fixed(buggy_code, fixed_code, language, test_case_list)
        evaluation_details['compilation'] = comparison
        evaluation_details['test_results'] = comparison['fixed_results']['test_results']

        # Get score and feedback from LLM
        score, feedback = evaluate_with_llm(
            question_data,
            parsed_response,
            compilation_results=comparison,
            test_results=comparison['fixed_results']['test_results']
        )

    else:
        # No test cases (coding questions): Use simple execution with embedded test data and compare outputs
        print("🎯 Using embedded test data for code execution with output comparison...")

        expected_output = question_data.get('expected_output', '')

        print(f"[INFO] Expected output: '{expected_output}'")

        # Rate limiting delay before execution
        time.sleep(0.3)

        try:
            # Execute the fixed code (test data is embedded in the code itself)
            execution_result = execute_code(fixed_code, language, stdin='')

            # Create structured comparison using output_comparator
            execution_comparison = compare_outputs(
                expected=expected_output,
                actual=execution_result.get('stdout', '').strip(),
                exit_code=execution_result.get('exit_code', 1),
                stderr=execution_result.get('stderr', '')
            )

            # Store comparison in evaluation details
            evaluation_details['execution_comparison'] = execution_comparison.model_dump()

            print(f"[INFO] Match Status: {execution_comparison.match_status}")
            print(f"[INFO] Confidence: {execution_comparison.match_confidence * 100:.1f}%")
            print(f"[INFO] Expected: '{expected_output}'")
            print(f"[INFO] Actual: '{execution_comparison.actual_output}'")

            # Get score and feedback from LLM with structured comparison
            score, feedback = evaluate_with_llm(
                question_data,
                parsed_response,
                execution_comparison=execution_comparison
            )

        except Exception as e:
            print(f"[ERROR] Code execution error: {e}")
            evaluation_details['execution_error'] = str(e)
            # Fallback to LLM-only evaluation
            score, feedback = evaluate_with_llm(question_data, parsed_response)
            evaluation_details['note'] = "Execution failed - evaluated based on code review only"

    return EvaluationResult(
        question_title=question_data.get('question_text', 'Unknown'),
        question_type='coding_debug',
        score=score,
        feedback=feedback,
        details=evaluation_details
    )


def evaluate_explain_question(
    question_data: Dict[str, Any],
    candidate_response: str,
    test_cases: Optional[TestCaseSet] = None
) -> EvaluationResult:
    """
    Evaluate a code explanation question

    Process:
    1. Parse explanation from response
    2. LLM evaluates explanation quality:
       - Understanding of code functionality
       - Complexity analysis accuracy
       - Edge case identification
       - Improvement suggestions

    Args:
        question_data: Original question details
        candidate_response: Candidate's response text
        test_cases: Test cases (not used for explain questions)

    Returns:
        EvaluationResult object
    """
    print(f"[EXPLAIN] Evaluating explanation question: {question_data.get('question_text', 'Unknown')}")

    # Parse response (entire response is the explanation)
    parsed_response = parse_candidate_response(candidate_response, 'coding_explain')

    # LLM evaluation (no compilation for explain questions)
    score, feedback = evaluate_with_llm(question_data, parsed_response)

    return EvaluationResult(
        question_title=question_data.get('question_text', 'Unknown'),
        question_type='coding_explain',
        score=score,
        feedback=feedback,
        details={
            'analysis_quality': 'LLM-evaluated based on understanding and insight',
            'explanation_length': len(parsed_response['explanation'])
        }
    )


def evaluate_db_schema_question(
    question_data: Dict[str, Any],
    candidate_response: str,
    test_cases: Optional[TestCaseSet] = None
) -> EvaluationResult:
    """
    Evaluate a database schema question

    Process:
    1. Parse SQL schema from response
    2. Validate SQL syntax using Piston (SQLite)
    3. LLM evaluates (syntax validation only, not deep design)

    Args:
        question_data: Original question details
        candidate_response: Candidate's response text
        test_cases: Test cases for SQL validation

    Returns:
        EvaluationResult object
    """
    print(f"[DB] Evaluating database schema question: {question_data.get('question_text', 'Unknown')}")

    # Parse response
    parsed_response = parse_candidate_response(candidate_response, 'db_schema')
    sql_schema = parsed_response['code']

    evaluation_details = {}

    # Try to validate SQL syntax
    if sql_schema.strip():
        print("[INFO] Validating SQL syntax...")
        time.sleep(0.3)  # Rate limiting

        # Execute SQL to check syntax (using SQLite)
        result = execute_code(sql_schema, 'sql', stdin='')

        evaluation_details['sql_validation'] = {
            'valid_syntax': result['success'] and result['exit_code'] == 0,
            'stderr': result.get('stderr', ''),
            'error': result.get('error', '') if not result['success'] else None
        }
    else:
        evaluation_details['sql_validation'] = {
            'valid_syntax': False,
            'error': 'No SQL schema provided'
        }

    # LLM evaluation
    score, feedback = evaluate_with_llm(
        question_data,
        parsed_response,
        compilation_results=evaluation_details.get('sql_validation')
    )

    return EvaluationResult(
        question_title=question_data.get('question_text', 'Unknown'),
        question_type='db_schema',
        score=score,
        feedback=feedback,
        details=evaluation_details
    )


def evaluate_coding_interview(
    coding_test_filename: str,
    uploads_folder: str,
    interviews_folder: str
) -> Dict[str, Any]:
    """
    Main orchestrator for evaluating a complete coding interview

    Process:
    1. Load code-test-{name}-{date}.json
    2. For each question:
       - Load test cases
       - Determine question type
       - Call appropriate evaluator
       - time.sleep(0.3) between compilations
    3. Calculate overall score
    4. Save to code-evaluation-{name}-{date}.json

    Args:
        coding_test_filename: Name of coding test file (e.g., "code-test-malek-ajmi-10-10-2025.json")
        uploads_folder: Path to uploads folder
        interviews_folder: Path to interviews folder

    Returns:
        Dict with evaluation results
    """
    print("=" * 60)
    print("STARTING CODING INTERVIEW EVALUATION")
    print("=" * 60)

    # Load coding test responses
    test_filepath = os.path.join(interviews_folder, coding_test_filename)
    if not os.path.exists(test_filepath):
        return {
            'success': False,
            'error': f'Coding test file not found: {coding_test_filename}'
        }

    try:
        with open(test_filepath, 'r', encoding='utf-8') as f:
            coding_responses = json.load(f)
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to load coding test file: {str(e)}'
        }

    # Extract candidate info from structured JSON
    candidate_name = coding_responses.get('candidate_name', 'Unknown Candidate')
    interview_date = coding_responses.get('interview_date', datetime.now().strftime('%d-%m-%Y'))
    questions_list = coding_responses.get('questions', [])

    print(f"\nCandidate: {candidate_name}")
    print(f"Interview Date: {interview_date}")
    print(f"Total Questions: {len(questions_list)}")
    print()

    # Evaluate each question
    evaluation_results = []
    total_score = 0

    for question_entry in questions_list:
        # Extract question data from structured format
        question_id = question_entry.get('question_id', 0)
        question_title = question_entry.get('question_title', 'Unknown Question')
        question_type = question_entry.get('question_type', 'coding_debug')
        technology = question_entry.get('technology', 'python')
        candidate_code = question_entry.get('candidate_code', '')
        candidate_explanation = question_entry.get('candidate_explanation', '')
        response_text = question_entry.get('candidate_full_response', '')

        print(f"\n{'='*60}")
        print(f"Evaluating Q{question_id}: {question_title}")
        print(f"{'='*60}")
        print(f"Type: {question_type} | Technology: {technology}")

        # Build question data using structured info
        question_data = {
            'question_text': question_title,
            'question_type': question_type,
            'buggy_code': '',  # Original buggy code not stored in responses
            'target_language': technology.lower(),
            'expected_output': question_entry.get('expected_output', '')  # Include expected output
        }

        # Test cases not used in current evaluation approach
        # - Coding questions (Python, JS, etc.): Use embedded test data + output comparison
        # - DB questions: Use syntax validation + LLM schema evaluation
        test_cases = None

        if question_type == 'db_schema':
            print(f"🗄️  Database question detected ({technology}) - will use syntax validation + LLM schema evaluation")
        else:
            print(f"💻 Coding question detected ({technology}) - will use embedded test data for simple execution")
            print(f"🎯 Expected Output: '{question_data.get('expected_output', '')}'")

        # Rate limiting delay
        if len(evaluation_results) > 0:
            time.sleep(0.3)

        # Call appropriate evaluator
        try:
            if question_type == 'coding_debug':
                result = evaluate_debug_question(question_data, response_text, test_cases=None)
            elif question_type == 'coding_explain':
                result = evaluate_explain_question(question_data, response_text, test_cases=None)
            elif question_type == 'db_schema':
                result = evaluate_db_schema_question(question_data, response_text, test_cases=None)
            else:
                # Fallback to explain evaluation
                result = evaluate_explain_question(question_data, response_text, test_cases=None)

            evaluation_results.append(result)
            total_score += result.score

            print(f"Score: {result.score}/10")
            print(f"Feedback:")
            for i, phrase in enumerate(result.feedback, 1):
                print(f"  {i}. {phrase}")

        except Exception as e:
            print(f"[ERROR] Failed to evaluate question: {e}")
            # Add error result
            evaluation_results.append(EvaluationResult(
                question_title=question_title,
                question_type=question_type,
                score=0,
                feedback=[
                    "Evaluation failed due to error",
                    f"Error: {str(e)}",
                    "Manual review required"
                ],
                details={'error': str(e)}
            ))

    # Calculate overall score
    overall_score = total_score / len(evaluation_results) if evaluation_results else 0

    # Generate overall feedback
    if overall_score >= 8:
        overall_feedback = "Excellent performance across coding challenges"
    elif overall_score >= 6:
        overall_feedback = "Good performance with room for improvement"
    elif overall_score >= 4:
        overall_feedback = "Average performance, needs development in key areas"
    else:
        overall_feedback = "Needs significant improvement in coding skills"

    # Create evaluation object
    evaluation = CodingInterviewEvaluation(
        candidate_name=candidate_name,
        interview_date=interview_date,
        overall_score=round(overall_score, 2),
        overall_feedback=overall_feedback,
        questions=[result for result in evaluation_results],
        evaluation_timestamp=datetime.now().isoformat()
    )

    # Save evaluation results
    evaluation_filename = coding_test_filename.replace('code-test-', 'code-evaluation-')
    evaluation_filepath = os.path.join(interviews_folder, evaluation_filename)

    try:
        with open(evaluation_filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation.model_dump(), f, indent=2)
        print(f"\n[OK] Evaluation saved to: {evaluation_filepath}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save evaluation: {e}")

    print("\n" + "=" * 60)
    print(f"EVALUATION COMPLETE")
    print(f"Overall Score: {overall_score:.1f}/10")
    print("=" * 60)

    return {
        'success': True,
        'evaluation_results': evaluation.model_dump()  # FIXED: Changed from 'evaluation' to match frontend expectation
    }


def detect_question_type(question_title: str) -> str:
    """
    Detect question type from title

    Args:
        question_title: Question title string

    Returns:
        Question type: 'coding_debug', 'coding_explain', or 'db_schema'
    """
    title_lower = question_title.lower()

    if 'debug' in title_lower or 'fix' in title_lower or 'bug' in title_lower:
        return 'coding_debug'
    elif 'analysis' in title_lower or 'analyze' in title_lower or 'explain' in title_lower:
        return 'coding_explain'
    elif 'database' in title_lower or 'schema' in title_lower or 'sql' in title_lower:
        return 'db_schema'
    else:
        # Default to debug
        return 'coding_debug'


# Example usage
if __name__ == "__main__":
    print("=== Code Evaluator Test ===\n")

    # This would normally be called from the Flask route
    # Example: evaluate_coding_interview("code-test-malek-ajmi-10-10-2025.json", "../uploads", "../interviews")

    print("Code evaluator module loaded successfully")
    print("Use evaluate_coding_interview() to evaluate a complete interview")
