"""
Piston API Client for Code Compilation and Execution
Provides interface to execute code in multiple languages using Piston API
"""

import requests
import time
from typing import Dict, List, Optional, Any
import json

# Piston API Configuration
PISTON_BASE_URL = "https://emkc.org/api/v2/piston"
PISTON_RUNTIMES_URL = f"{PISTON_BASE_URL}/runtimes"
PISTON_EXECUTE_URL = f"{PISTON_BASE_URL}/execute"

# Rate limiting configuration
REQUEST_DELAY = 0.3  # 300ms delay between requests (safety margin for 5 req/s limit)
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10  # 10 seconds timeout per request

# Language mapping (user-friendly name -> Piston language identifier)
LANGUAGE_MAP = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'java': 'java',
    'c#': 'csharp',
    'csharp': 'csharp',
    'go': 'go',
    'rust': 'rust',
    'php': 'php',
    'ruby': 'ruby',
    'sql': 'sqlite3',  # For SQL validation
    'sqlite': 'sqlite3',
    'c': 'c',
    'c++': 'cpp',
    'cpp': 'cpp'
}

# Default file extensions for languages
FILE_EXTENSIONS = {
    'python': 'py',
    'javascript': 'js',
    'typescript': 'ts',
    'java': 'java',
    'csharp': 'cs',
    'go': 'go',
    'rust': 'rs',
    'php': 'php',
    'ruby': 'rb',
    'sqlite3': 'sql',
    'c': 'c',
    'cpp': 'cpp'
}


def get_available_runtimes() -> List[Dict[str, Any]]:
    """
    Fetch available programming language runtimes from Piston API

    Returns:
        List of runtime dictionaries with language, version, and aliases
    """
    try:
        response = requests.get(PISTON_RUNTIMES_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        runtimes = response.json()

        print(f"[OK] Fetched {len(runtimes)} available runtimes from Piston API")
        return runtimes

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching Piston runtimes: {e}")
        return []


def normalize_language(language: str) -> Optional[str]:
    """
    Normalize language name to Piston API format

    Args:
        language: Language name (case-insensitive)

    Returns:
        Normalized language name or None if not found
    """
    language_lower = language.lower().strip()
    return LANGUAGE_MAP.get(language_lower)


def execute_code(
    code: str,
    language: str,
    stdin: str = "",
    compile_timeout: int = 10000,
    run_timeout: int = 5000
) -> Dict[str, Any]:
    """
    Execute code via Piston API with retry logic and rate limiting

    Args:
        code: Source code to execute
        language: Programming language (e.g., 'python', 'javascript')
        stdin: Standard input data (optional)
        compile_timeout: Compilation timeout in milliseconds (default 10s)
        run_timeout: Execution timeout in milliseconds (default 5s)

    Returns:
        Dict with structure:
        {
            'success': bool,
            'stdout': str,
            'stderr': str,
            'exit_code': int,
            'output': str,
            'language': str,
            'version': str,
            'error': str (optional, if request failed)
        }
    """
    # Normalize language name
    normalized_language = normalize_language(language)
    if not normalized_language:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Unsupported language: {language}',
            'exit_code': 1,
            'output': '',
            'language': language,
            'version': '',
            'error': f'Language "{language}" is not supported. Supported: {", ".join(LANGUAGE_MAP.keys())}'
        }

    # Get file extension
    file_extension = FILE_EXTENSIONS.get(normalized_language, 'txt')
    filename = f"main.{file_extension}"

    # Prepare request payload
    payload = {
        "language": normalized_language,
        "version": "*",  # Use latest version
        "files": [
            {
                "name": filename,
                "content": code
            }
        ],
        "stdin": stdin,
        "compile_timeout": compile_timeout,
        "run_timeout": run_timeout
    }

    # Retry logic with exponential backoff
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Rate limiting delay
            time.sleep(REQUEST_DELAY)

            # Execute request
            response = requests.post(
                PISTON_EXECUTE_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            run_data = result.get('run', {})

            # Build standardized response
            return {
                'success': True,
                'stdout': run_data.get('stdout', ''),
                'stderr': run_data.get('stderr', ''),
                'exit_code': run_data.get('code', 0),
                'output': run_data.get('output', ''),
                'language': result.get('language', normalized_language),
                'version': result.get('version', 'unknown')
            }

        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] Timeout on attempt {attempt}/{MAX_RETRIES}")
            if attempt == MAX_RETRIES:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': 'Execution timed out',
                    'exit_code': 124,  # Timeout exit code
                    'output': '',
                    'language': normalized_language,
                    'version': '',
                    'error': 'Request timed out after multiple attempts'
                }
            # Exponential backoff: 1s, 2s, 4s
            time.sleep(2 ** (attempt - 1))

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt == MAX_RETRIES:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e),
                    'exit_code': 1,
                    'output': '',
                    'language': normalized_language,
                    'version': '',
                    'error': f'Network error: {str(e)}'
                }
            # Exponential backoff
            time.sleep(2 ** (attempt - 1))

        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON response: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Invalid API response',
                'exit_code': 1,
                'output': '',
                'language': normalized_language,
                'version': '',
                'error': f'Failed to parse API response: {str(e)}'
            }

    # Should not reach here, but safety fallback
    return {
        'success': False,
        'stdout': '',
        'stderr': 'Unknown error',
        'exit_code': 1,
        'output': '',
        'language': normalized_language,
        'version': '',
        'error': 'Failed after all retry attempts'
    }


def run_test_cases(
    code: str,
    language: str,
    test_cases: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Run code against multiple test cases

    Args:
        code: Source code to test
        language: Programming language
        test_cases: List of test case dicts with 'input', 'expected_output', 'description'

    Returns:
        List of test result dicts:
        [
            {
                'description': str,
                'input': str,
                'expected_output': str,
                'actual_output': str,
                'passed': bool,
                'error': str (optional)
            }
        ]
    """
    results = []

    for test_case in test_cases:
        test_input = test_case.get('input', '')
        expected_output = test_case.get('expected_output', '').strip()
        description = test_case.get('description', 'Test case')

        # Execute code with test input
        execution_result = execute_code(code, language, stdin=test_input)

        if not execution_result['success']:
            results.append({
                'description': description,
                'input': test_input,
                'expected_output': expected_output,
                'actual_output': '',
                'passed': False,
                'error': execution_result.get('error', 'Execution failed'),
                'stderr': execution_result.get('stderr', '')
            })
            continue

        # Get actual output
        actual_output = execution_result['stdout'].strip()

        # Compare outputs (simple string comparison)
        passed = actual_output == expected_output

        results.append({
            'description': description,
            'input': test_input,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'passed': passed,
            'exit_code': execution_result['exit_code']
        })

        # Add stderr if present
        if execution_result['stderr']:
            results[-1]['stderr'] = execution_result['stderr']

    return results


def compare_buggy_vs_fixed(
    buggy_code: str,
    fixed_code: str,
    language: str,
    test_cases: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Compare buggy code vs fixed code by running both through test cases

    Args:
        buggy_code: Original buggy code
        fixed_code: Candidate's fixed code
        language: Programming language
        test_cases: List of test cases

    Returns:
        Dict with structure:
        {
            'buggy_results': {
                'test_results': [...],
                'passed_count': int,
                'total_count': int,
                'compilation_error': bool
            },
            'fixed_results': {
                'test_results': [...],
                'passed_count': int,
                'total_count': int,
                'compilation_error': bool
            },
            'improvement': float (percentage of tests fixed)
        }
    """
    # Run buggy code through test cases
    print(f"[BUGGY] Running buggy code through {len(test_cases)} test cases...")
    buggy_test_results = run_test_cases(buggy_code, language, test_cases)
    buggy_passed = sum(1 for r in buggy_test_results if r.get('passed', False))
    buggy_compilation_error = any(r.get('error') for r in buggy_test_results)

    # Run fixed code through test cases
    print(f"[FIXED] Running fixed code through {len(test_cases)} test cases...")
    fixed_test_results = run_test_cases(fixed_code, language, test_cases)
    fixed_passed = sum(1 for r in fixed_test_results if r.get('passed', False))
    fixed_compilation_error = any(r.get('error') for r in fixed_test_results)

    # Calculate improvement
    total_tests = len(test_cases)
    improvement = 0.0
    if total_tests > 0:
        improvement = ((fixed_passed - buggy_passed) / total_tests) * 100

    return {
        'buggy_results': {
            'test_results': buggy_test_results,
            'passed_count': buggy_passed,
            'total_count': total_tests,
            'compilation_error': buggy_compilation_error
        },
        'fixed_results': {
            'test_results': fixed_test_results,
            'passed_count': fixed_passed,
            'total_count': total_tests,
            'compilation_error': fixed_compilation_error
        },
        'improvement': improvement,
        'tests_fixed': fixed_passed - buggy_passed
    }


# Test function for development
if __name__ == "__main__":
    print("=== Piston Compiler Test Suite ===\n")

    # Test 1: Get available runtimes
    print("Test 1: Fetching available runtimes...")
    runtimes = get_available_runtimes()
    if runtimes:
        print(f"Found {len(runtimes)} runtimes. Sample: {runtimes[0]}")

    # Test 2: Execute simple Python code
    print("\nTest 2: Executing simple Python code...")
    result = execute_code("print('Hello from Piston!')", "python")
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")

    # Test 3: Run test cases
    print("\nTest 3: Running test cases...")
    test_code = """
def add(a, b):
    return a + b

# Read two numbers from stdin
a = int(input())
b = int(input())
print(add(a, b))
"""

    test_cases = [
        {"input": "5\n10", "expected_output": "15", "description": "Basic addition"},
        {"input": "-3\n7", "expected_output": "4", "description": "Negative numbers"}
    ]

    test_results = run_test_cases(test_code, "python", test_cases)
    for result in test_results:
        print(f"  {result['description']}: {'PASSED' if result['passed'] else 'FAILED'}")

    print("\n=== Tests Complete ===")
