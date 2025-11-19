"""
Test Case Generator for Coding Interview Questions
Uses LLM to automatically generate test cases for debug, explain, and database questions
"""

import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import from shared modules
from shared.llm_setup import get_llm

# Import question types
from .question_generator import (
    InterviewQuestion, DebugCodingQuestion,
    ExplanationCodingQuestion, DatabaseSchemaQuestion
)

# Directory for storing test cases
TEST_CASES_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_cases')


class TestCase(BaseModel):
    """Pydantic model for a single test case"""
    input: str = Field(description="Input data (stdin format)")
    expected_output: str = Field(description="Expected output (exact match)")
    description: str = Field(description="Brief description of what this test validates")
    difficulty: str = Field(description="Test difficulty: easy/medium/hard")


class TestCaseSet(BaseModel):
    """Collection of test cases for a question"""
    question_id: str = Field(description="Unique question identifier")
    question_type: str = Field(description="Type: coding_debug, coding_explain, db_schema")
    question_title: str = Field(description="Question title")
    test_cases: List[TestCase] = Field(description="List of test cases")


def ensure_test_cases_directory():
    """Create test_cases directory if it doesn't exist"""
    os.makedirs(TEST_CASES_DIR, exist_ok=True)
    print(f"[INFO] Test cases directory: {TEST_CASES_DIR}")


def generate_debug_test_cases(
    question: InterviewQuestion,
    debug_data: DebugCodingQuestion
) -> List[TestCase]:
    """
    Generate test cases for a debug coding question

    Args:
        question: InterviewQuestion object
        debug_data: DebugCodingQuestion details

    Returns:
        List of TestCase objects
    """
    prompt = f"""
You are generating test cases for a debugging coding interview question.

**Question Type:** Debug Challenge
**Title:** {debug_data.title}
**Language:** {debug_data.target_language}
**Buggy Code:**
```
{debug_data.buggy_code}
```

**Context:** {debug_data.context_paragraph}
**Task:** {debug_data.task_instruction}
**Expected Outcome:** {debug_data.expected_outcome}
**Number of Bugs:** {debug_data.error_count}

**YOUR TASK:**
Generate 3-5 test cases that will:
1. FAIL on the buggy code (expose the bugs)
2. PASS on the corrected code (after fixing the bugs)
3. Cover different scenarios: basic functionality, edge cases, and error handling

For each test case, provide:
- Input data (in stdin format - use \\n for newlines)
- Expected output (the CORRECT output after code is fixed)
- Description of what this test validates
- Difficulty level (easy/medium/hard)

**IMPORTANT FORMAT RULES:**
- Input and expected_output should be EXACT strings that can be used for stdin/stdout comparison
- If the code doesn't use stdin, leave input as empty string ""
- For code that prints output, expected_output should be the exact print output (including newlines)
- Be specific and realistic based on the code's purpose

Return ONLY a valid JSON array in this exact format:
```json
[
  {{
    "input": "test input here",
    "expected_output": "expected output here",
    "description": "Brief description",
    "difficulty": "easy"
  }}
]
```

Return ONLY the JSON array, nothing else.
"""

    try:
        print(f"[INFO] Generating debug test cases for: {debug_data.title}")
        llm = get_llm()
        response = llm.invoke(prompt)
        test_cases_json = response.content.strip()

        # Clean the response
        if test_cases_json.startswith("```json"):
            test_cases_json = test_cases_json.replace("```json", "").replace("```", "").strip()
        elif test_cases_json.startswith("```"):
            test_cases_json = test_cases_json.replace("```", "").strip()

        # Parse JSON
        test_cases_data = json.loads(test_cases_json)

        # Convert to TestCase objects
        test_cases = [TestCase(**tc) for tc in test_cases_data]
        print(f"[OK] Generated {len(test_cases)} test cases")

        return test_cases

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse test cases JSON: {e}")
        print(f"[ERROR] LLM response: {test_cases_json[:500]}")
        # Return fallback test cases
        return create_fallback_debug_test_cases(debug_data)

    except Exception as e:
        print(f"[ERROR] Error generating test cases: {e}")
        return create_fallback_debug_test_cases(debug_data)


def generate_explain_test_cases(
    question: InterviewQuestion,
    explain_data: ExplanationCodingQuestion
) -> List[TestCase]:
    """
    Generate test cases for a code explanation question

    For explain questions, test cases verify the code works correctly
    and can be used to validate any improvements suggested by the candidate.

    Args:
        question: InterviewQuestion object
        explain_data: ExplanationCodingQuestion details

    Returns:
        List of TestCase objects
    """
    prompt = f"""
You are generating test cases for a code explanation/analysis coding interview question.

**Question Type:** Code Analysis
**Title:** {explain_data.title}
**Language:** {explain_data.target_language}
**Working Code:**
```
{explain_data.working_code}
```

**Context:** {explain_data.context_paragraph}
**Task:** {explain_data.task_instruction}
**Expected Outcome:** {explain_data.expected_outcome}

**YOUR TASK:**
Generate 3-4 test cases that verify this code works correctly. These test cases will:
1. Validate the code's basic functionality
2. Test edge cases and boundary conditions
3. Demonstrate the algorithm's behavior

For each test case, provide:
- Input data (in stdin format - use \\n for newlines)
- Expected output (exact output the code should produce)
- Description of what scenario is being tested
- Difficulty level (easy/medium/hard)

**IMPORTANT FORMAT RULES:**
- Input and expected_output should be EXACT strings for stdin/stdout comparison
- If the code doesn't use stdin, leave input as empty string ""
- Be specific based on what the code actually does

Return ONLY a valid JSON array in this exact format:
```json
[
  {{
    "input": "test input here",
    "expected_output": "expected output here",
    "description": "Brief description",
    "difficulty": "easy"
  }}
]
```

Return ONLY the JSON array, nothing else.
"""

    try:
        print(f"[INFO] Generating explanation test cases for: {explain_data.title}")
        llm = get_llm()
        response = llm.invoke(prompt)
        test_cases_json = response.content.strip()

        # Clean the response
        if test_cases_json.startswith("```json"):
            test_cases_json = test_cases_json.replace("```json", "").replace("```", "").strip()
        elif test_cases_json.startswith("```"):
            test_cases_json = test_cases_json.replace("```", "").strip()

        # Parse JSON
        test_cases_data = json.loads(test_cases_json)
        test_cases = [TestCase(**tc) for tc in test_cases_data]

        print(f"[OK] Generated {len(test_cases)} test cases")
        return test_cases

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse test cases JSON: {e}")
        return create_fallback_explain_test_cases(explain_data)

    except Exception as e:
        print(f"[ERROR] Error generating test cases: {e}")
        return create_fallback_explain_test_cases(explain_data)


def generate_db_schema_test_cases(
    question: InterviewQuestion,
    db_data: DatabaseSchemaQuestion
) -> List[TestCase]:
    """
    Generate test cases for a database schema question

    For DB questions, test cases are SQL validation scenarios.
    We'll generate sample data insertion and query examples.

    Args:
        question: InterviewQuestion object
        db_data: DatabaseSchemaQuestion details

    Returns:
        List of TestCase objects
    """
    prompt = f"""
You are generating SQL syntax validation test cases for a database schema design question.

**Question Type:** Database Schema Design
**Title:** {db_data.title}
**Database Technology:** {db_data.db_technology}
**Context:** {db_data.context_paragraph}
**Task:** {db_data.task_instruction}
**Requirements:** {', '.join(db_data.requirements)}

**YOUR TASK:**
Generate 2-3 simple SQL validation test cases. These will be used to check if the candidate's SQL has valid syntax.

For each test case:
- Input: A sample CREATE TABLE or INSERT statement to validate syntax
- Expected_output: "VALID" if syntax is correct, or the error message if invalid
- Description: What is being validated
- Difficulty: easy (we're only checking syntax, not logic)

**IMPORTANT:**
- These are SYNTAX validation tests only
- Input should be valid SQL for {db_data.db_technology}
- Keep it simple - just verify the SQL can be parsed

Return ONLY a valid JSON array in this exact format:
```json
[
  {{
    "input": "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
    "expected_output": "VALID",
    "description": "Validate basic CREATE TABLE syntax",
    "difficulty": "easy"
  }}
]
```

Return ONLY the JSON array, nothing else.
"""

    try:
        print(f"[INFO] Generating DB schema test cases for: {db_data.title}")
        llm = get_llm()
        response = llm.invoke(prompt)
        test_cases_json = response.content.strip()

        # Clean the response
        if test_cases_json.startswith("```json"):
            test_cases_json = test_cases_json.replace("```json", "").replace("```", "").strip()
        elif test_cases_json.startswith("```"):
            test_cases_json = test_cases_json.replace("```", "").strip()

        # Parse JSON
        test_cases_data = json.loads(test_cases_json)
        test_cases = [TestCase(**tc) for tc in test_cases_data]

        print(f"[OK] Generated {len(test_cases)} test cases")
        return test_cases

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse test cases JSON: {e}")
        return create_fallback_db_test_cases(db_data)

    except Exception as e:
        print(f"[ERROR] Error generating test cases: {e}")
        return create_fallback_db_test_cases(db_data)


def create_fallback_debug_test_cases(debug_data: DebugCodingQuestion) -> List[TestCase]:
    """Create basic fallback test cases for debug questions"""
    return [
        TestCase(
            input="",
            expected_output="",
            description=f"Basic functionality test for {debug_data.target_language} code",
            difficulty="easy"
        ),
        TestCase(
            input="",
            expected_output="",
            description="Edge case validation",
            difficulty="medium"
        )
    ]


def create_fallback_explain_test_cases(explain_data: ExplanationCodingQuestion) -> List[TestCase]:
    """Create basic fallback test cases for explain questions"""
    return [
        TestCase(
            input="",
            expected_output="",
            description=f"Verify {explain_data.target_language} code runs correctly",
            difficulty="easy"
        )
    ]


def create_fallback_db_test_cases(db_data: DatabaseSchemaQuestion) -> List[TestCase]:
    """Create basic fallback test cases for database questions"""
    return [
        TestCase(
            input="SELECT 1;",
            expected_output="VALID",
            description="Basic SQL syntax validation",
            difficulty="easy"
        )
    ]


def generate_test_cases(
    question: InterviewQuestion
) -> TestCaseSet:
    """
    Main function to generate test cases based on question type

    Args:
        question: InterviewQuestion object

    Returns:
        TestCaseSet with generated test cases
    """
    # Generate unique question ID if not present
    question_id = f"q{question.question_id}_{question.question_type}_{question.technology_focus.lower().replace(' ', '_')}"

    # Route to appropriate generator based on question type
    if question.question_type == 'coding_debug' and question.debug_data:
        test_cases = generate_debug_test_cases(question, question.debug_data)
    elif question.question_type == 'coding_explain' and question.explanation_data:
        test_cases = generate_explain_test_cases(question, question.explanation_data)
    elif question.question_type == 'db_schema' and question.db_schema_data:
        test_cases = generate_db_schema_test_cases(question, question.db_schema_data)
    else:
        print(f"[WARNING] Unknown question type: {question.question_type}, using fallback")
        test_cases = [
            TestCase(
                input="",
                expected_output="",
                description="Fallback test case",
                difficulty="easy"
            )
        ]

    return TestCaseSet(
        question_id=question_id,
        question_type=question.question_type,
        question_title=question.question_text,
        test_cases=test_cases
    )


def save_test_cases(test_case_set: TestCaseSet) -> str:
    """
    Save test cases to JSON file

    Args:
        test_case_set: TestCaseSet object

    Returns:
        Path to saved file
    """
    ensure_test_cases_directory()

    filename = f"{test_case_set.question_id}.json"
    filepath = os.path.join(TEST_CASES_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_case_set.model_dump(), f, indent=2)

        print(f"[OK] Test cases saved to: {filepath}")
        return filepath

    except Exception as e:
        print(f"[ERROR] Failed to save test cases: {e}")
        return ""


def load_test_cases(question_id: str) -> Optional[TestCaseSet]:
    """
    Load test cases from JSON file

    Args:
        question_id: Question identifier

    Returns:
        TestCaseSet object or None if not found
    """
    filename = f"{question_id}.json"
    filepath = os.path.join(TEST_CASES_DIR, filename)

    if not os.path.exists(filepath):
        print(f"[WARNING] Test cases file not found: {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        test_case_set = TestCaseSet(**data)
        print(f"[OK] Loaded {len(test_case_set.test_cases)} test cases from: {filepath}")
        return test_case_set

    except Exception as e:
        print(f"[ERROR] Failed to load test cases: {e}")
        return None


# Test function
if __name__ == "__main__":
    print("=== Test Case Generator Test ===\n")

    # Create a sample debug question for testing
    from coding_question_generator import DebugCodingQuestion, InterviewQuestion

    sample_debug_data = DebugCodingQuestion(
        title="Fix the Sum Function",
        context_paragraph="This code calculates the sum of two numbers.",
        task_instruction="Fix the bug in the addition function.",
        expected_outcome="Function should return correct sum.",
        buggy_code="def add(a, b):\n    return a - b\n\nprint(add(5, 3))",
        error_count=1,
        error_types=["logic"],
        hints=[],
        target_language="Python",
        cv_technology="Python",
        description="Fix the addition",
        expected_behavior="Should return 8",
        context="Basic Python"
    )

    sample_question = InterviewQuestion(
        question_id=1,
        question_type="coding_debug",
        question_text="Debug Challenge: Fix the Sum Function",
        difficulty_level=3,
        technology_focus="Python",
        debug_data=sample_debug_data,
        timestamp="2025-01-21T00:00:00"
    )

    # Generate test cases
    print("Generating test cases...")
    test_case_set = generate_test_cases(sample_question)

    print(f"\nGenerated {len(test_case_set.test_cases)} test cases:")
    for i, tc in enumerate(test_case_set.test_cases, 1):
        print(f"  {i}. {tc.description} ({tc.difficulty})")

    # Save test cases
    print("\nSaving test cases...")
    filepath = save_test_cases(test_case_set)

    # Load test cases
    print("\nLoading test cases...")
    loaded = load_test_cases(test_case_set.question_id)
    if loaded:
        print(f"Successfully loaded {len(loaded.test_cases)} test cases")

    print("\n=== Test Complete ===")
