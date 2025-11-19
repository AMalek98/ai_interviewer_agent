"""
Coding Interview Evaluation System

Handles evaluation of coding solutions:
- Code compilation and execution
- Test case validation
- Code quality assessment
- Performance analysis
"""

from .engine import evaluate_coding_interview, EvaluationResult
from .piston_compiler import execute_code, run_test_cases, compare_buggy_vs_fixed
from .output_comparator import compare_outputs, ExecutionComparison

__all__ = [
    'evaluate_coding_interview',
    'EvaluationResult',
    'execute_code',
    'run_test_cases',
    'compare_buggy_vs_fixed',
    'compare_outputs',
    'ExecutionComparison'
]
