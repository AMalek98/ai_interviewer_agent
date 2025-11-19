"""
Output Comparison Utility for Code Evaluation
Provides intelligent comparison between expected and actual code outputs
"""

from pydantic import BaseModel, Field
from typing import Optional
import re


class ExecutionComparison(BaseModel):
    """Structured comparison of code execution results"""
    expected_output: str = Field(description="Expected output from question")
    actual_output: str = Field(description="Actual output from Piston execution")
    exit_code: int = Field(description="Exit code from execution")
    stderr: str = Field(default="", description="Standard error output")
    compilation_success: bool = Field(description="Whether code compiled/ran successfully")
    match_status: str = Field(description="EXACT_MATCH | PARTIAL_MATCH | NO_MATCH | EXECUTION_ERROR")
    match_confidence: float = Field(description="Confidence score 0.0-1.0")
    comparison_notes: str = Field(default="", description="Additional comparison details")


def normalize_output(output: str) -> str:
    """
    Normalize output for comparison

    Args:
        output: Raw output string

    Returns:
        Normalized output string
    """
    # Strip whitespace
    normalized = output.strip()
    # Normalize line endings
    normalized = normalized.replace('\r\n', '\n')
    # Remove trailing whitespace from each line
    normalized = '\n'.join(line.rstrip() for line in normalized.split('\n'))
    return normalized


def compare_outputs(
    expected: str,
    actual: str,
    exit_code: int,
    stderr: str
) -> ExecutionComparison:
    """
    Intelligent comparison between expected and actual outputs

    Performs:
    - Execution error detection
    - Exact string matching (with normalization)
    - Numeric comparison (with floating point tolerance)
    - Partial/substring matching

    Args:
        expected: Expected output string
        actual: Actual output from code execution
        exit_code: Exit code from execution (0 = success)
        stderr: Standard error output

    Returns:
        ExecutionComparison with match status and confidence
    """
    # IMPORTANT: Include stderr in actual output for comparison
    # Runtime errors should be considered as incorrect output
    actual_with_errors = actual
    if stderr.strip():
        # Append stderr to actual output so errors are visible in comparison
        actual_with_errors = (actual + "\n" + stderr).strip() if actual.strip() else stderr.strip()

    # Check for execution errors first
    if exit_code != 0 or stderr.strip():
        return ExecutionComparison(
            expected_output=expected,
            actual_output=actual_with_errors,  # Include errors in output
            exit_code=exit_code,
            stderr=stderr,
            compilation_success=False,
            match_status="EXECUTION_ERROR",
            match_confidence=0.0,
            comparison_notes=f"Code failed with exit code {exit_code}: {stderr[:100]}"
        )

    # Normalize both outputs
    expected_norm = normalize_output(expected)
    actual_norm = normalize_output(actual)

    # Exact match check
    if expected_norm == actual_norm:
        return ExecutionComparison(
            expected_output=expected,
            actual_output=actual,
            exit_code=exit_code,
            stderr=stderr,
            compilation_success=True,
            match_status="EXACT_MATCH",
            match_confidence=1.0,
            comparison_notes="Output matches exactly"
        )

    # Try numeric comparison (handle floating point tolerance)
    try:
        expected_float = float(expected_norm)
        actual_float = float(actual_norm)
        diff = abs(expected_float - actual_float)

        if diff < 0.001:
            return ExecutionComparison(
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                compilation_success=True,
                match_status="EXACT_MATCH",
                match_confidence=1.0,
                comparison_notes=f"Numeric match within tolerance (diff: {diff:.6f})"
            )
    except ValueError:
        # Not numeric, continue with other checks
        pass

    # Partial match detection - substring matching
    if actual_norm and expected_norm:
        if actual_norm in expected_norm or expected_norm in actual_norm:
            # Calculate confidence based on string length ratio
            confidence = min(len(actual_norm), len(expected_norm)) / max(len(actual_norm), len(expected_norm))
            return ExecutionComparison(
                expected_output=expected,
                actual_output=actual,
                exit_code=exit_code,
                stderr=stderr,
                compilation_success=True,
                match_status="PARTIAL_MATCH",
                match_confidence=confidence,
                comparison_notes="Output partially matches (substring detected)"
            )

        # Check for similar words/tokens (for more complex partial matching)
        expected_words = set(expected_norm.lower().split())
        actual_words = set(actual_norm.lower().split())

        if expected_words and actual_words:
            common_words = expected_words & actual_words
            if common_words:
                confidence = len(common_words) / len(expected_words | actual_words)
                if confidence > 0.3:  # At least 30% word overlap
                    return ExecutionComparison(
                        expected_output=expected,
                        actual_output=actual,
                        exit_code=exit_code,
                        stderr=stderr,
                        compilation_success=True,
                        match_status="PARTIAL_MATCH",
                        match_confidence=confidence,
                        comparison_notes=f"Output partially matches (word overlap: {confidence*100:.1f}%)"
                    )

    # No match found
    return ExecutionComparison(
        expected_output=expected,
        actual_output=actual,
        exit_code=exit_code,
        stderr=stderr,
        compilation_success=True,
        match_status="NO_MATCH",
        match_confidence=0.0,
        comparison_notes="Output does not match expected result"
    )


# Test function for development
if __name__ == "__main__":
    print("=== Output Comparator Test Suite ===\n")

    # Test 1: Exact match
    print("Test 1: Exact match")
    result = compare_outputs("Hello, World!", "Hello, World!", 0, "")
    print(f"Status: {result.match_status}, Confidence: {result.match_confidence}")

    # Test 2: Numeric match
    print("\nTest 2: Numeric match with tolerance")
    result = compare_outputs("3.14159", "3.14158", 0, "")
    print(f"Status: {result.match_status}, Confidence: {result.match_confidence}")

    # Test 3: Execution error
    print("\nTest 3: Execution error")
    result = compare_outputs("15", "", 1, "NameError: name 'x' is not defined")
    print(f"Status: {result.match_status}, Confidence: {result.match_confidence}")

    # Test 4: No match
    print("\nTest 4: No match")
    result = compare_outputs("Expected output", "Completely different", 0, "")
    print(f"Status: {result.match_status}, Confidence: {result.match_confidence}")

    # Test 5: Partial match
    print("\nTest 5: Partial match")
    result = compare_outputs("Total: 42", "Total: 42\nExtra line here", 0, "")
    print(f"Status: {result.match_status}, Confidence: {result.match_confidence}")

    print("\n=== Tests Complete ===")
