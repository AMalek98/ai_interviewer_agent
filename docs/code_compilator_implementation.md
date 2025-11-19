# **Code Compilator Implementation Plan**

## **Overview**
Automated evaluation system for coding interviews that compiles and tests candidate code using Piston API, then provides AI-based evaluation with numerical scores (0-10) and concise feedback (3 phrases).

---

## **Architecture Summary**

### **Current State Analysis**
Based on `code-test-malek-ajmi-10-10-2025.json`, the system currently stores:
- Question titles as keys
- Raw candidate responses as values (mix of code + explanations)
- Format: `"Debug Challenge: Title": "FIXED CODE:\n{code}\n\nEXPLANATION:\n{text}"`

### **Evaluation Flow**
```
Interview Complete → Load JSON → Parse Responses → Compile Code (Piston) →
Run Test Cases → LLM Evaluation → Score (0-10) + Feedback (3 phrases) →
Save Results → Display to Candidate
```

---

## **Piston API Integration Details**

### **API Endpoints**
- **Base URL**: `https://emkc.org/api/v2/piston`
- **Get Runtimes**: `GET /runtimes`
- **Execute Code**: `POST /execute`

### **Rate Limits**
- 5 requests/second on public API
- **Solution**: Add `time.sleep(0.3)` between compilations (safety margin)

### **Request Format**
```json
POST https://emkc.org/api/v2/piston/execute
{
  "language": "python",
  "version": "3.10.0",
  "files": [{"name": "main.py", "content": "print('test')"}],
  "stdin": "input data",
  "compile_timeout": 10000,
  "run_timeout": 5000
}
```

### **Response Format**
```json
{
  "language": "python",
  "version": "3.10.0",
  "run": {
    "stdout": "output\n",
    "stderr": "",
    "code": 0,
    "signal": null,
    "output": "output\n"
  }
}
```

### **Language Mapping**
```python
LANGUAGE_MAP = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'java': 'java',
    'c#': 'csharp',
    'go': 'go',
    'rust': 'rust',
    'php': 'php',
    'ruby': 'ruby',
    'sql': 'sqlite3'  # For SQL validation
}
```

---

## **Implementation Components**

### **1. File: `backend/utils/piston_compiler.py`**

**Purpose**: Piston API client with retry logic and rate limiting

**Key Functions**:
```python
def get_available_runtimes() -> List[Dict]
    """Fetch available languages from Piston API"""

def execute_code(code: str, language: str, stdin: str = "",
                 timeout: int = 5000) -> Dict
    """
    Execute code via Piston API
    - 3 retry attempts with exponential backoff
    - 10s timeout per request
    - 0.3s delay between requests
    Returns: {success: bool, stdout: str, stderr: str, exit_code: int}
    """

def run_test_cases(code: str, language: str,
                   test_cases: List[Dict]) -> List[Dict]
    """
    Run code against multiple test cases
    Returns: [
        {
            input: str,
            expected_output: str,
            actual_output: str,
            passed: bool,
            error: str (if any)
        }
    ]
    """

def compare_buggy_vs_fixed(buggy_code: str, fixed_code: str,
                           language: str, test_cases: List[Dict]) -> Dict
    """
    For debug questions: compile both versions and compare
    Returns: {
        buggy_results: {...},
        fixed_results: {...},
        test_comparison: [...]
    }
    """
```

**Error Handling**:
- Network errors → Retry 3 times with 1s, 2s, 4s delays
- Timeout errors → Return error dict with timeout flag
- API rate limit → Wait and retry
- Invalid language → Return validation error

---

### **2. File: `backend/utils/test_case_generator.py`**

**Purpose**: Generate test cases during question creation using LLM

**Key Functions**:
```python
def generate_test_cases(question: InterviewQuestion,
                        question_type: str) -> List[TestCase]
    """
    Use LLM to generate 3-5 test cases based on question
    For debug/explain: Create input/output pairs
    For db_schema: Generate sample data insertion scenarios

    Returns: [
        {
            input: str,
            expected_output: str,
            description: str,
            difficulty: str (easy/medium/hard)
        }
    ]
    """

def save_test_cases(question_id: str, test_cases: List[TestCase])
    """Save to backend/test_cases/{question_id}.json"""

def load_test_cases(question_id: str) -> List[TestCase]
    """Load test cases from file"""
```

**Test Case Generation Prompt Template**:
```
You are generating test cases for a coding interview question.

Question Type: {question_type}
Question: {question_text}
Code: {code_snippet}

Generate 3-5 test cases with:
1. Input data (stdin format)
2. Expected output (exact match)
3. Brief description of what this test validates
4. Difficulty level (easy/medium/hard)

For debug questions: Ensure test cases fail on buggy code, pass on correct code
For explain questions: Generate representative inputs that test edge cases

Return JSON array of test cases.
```

**Storage Location**: `backend/test_cases/`
- Format: `{question_id}.json`
- Structure: `{"question_id": "...", "question_type": "...", "test_cases": [...]}`

---

### **3. File: `backend/utils/code_evaluator.py`**

**Purpose**: Main evaluation orchestrator with LLM-based scoring

**Key Functions**:
```python
def parse_candidate_response(response_text: str,
                             question_type: str) -> Dict
    """
    Parse response from JSON format:
    - Debug: Extract FIXED CODE and EXPLANATION
    - Explain: Extract analysis text
    - DB Schema: Extract SQL SCHEMA, DESIGN EXPLANATION, EXAMPLE QUERIES

    Returns: {code: str, explanation: str, queries: str (optional)}
    """

def evaluate_debug_question(question_data: Dict,
                            candidate_response: str,
                            test_cases: List[Dict]) -> Dict
    """
    1. Parse fixed code from response
    2. Compile buggy code (from question) → should fail/produce wrong output
    3. Compile fixed code (from candidate) → should pass test cases
    4. Compare outputs
    5. LLM evaluates code quality (readability, efficiency, correctness)

    Returns: {
        score: int (0-10),
        feedback: [phrase1, phrase2, phrase3],
        compilation: {
            buggy_results: {...},
            fixed_results: {...}
        },
        test_results: [{test, passed, ...}],
        code_quality_analysis: str
    }
    """

def evaluate_explain_question(question_data: Dict,
                              candidate_response: str) -> Dict
    """
    1. No compilation (text-only analysis)
    2. LLM evaluates explanation quality:
       - Understanding of code functionality
       - Complexity analysis accuracy
       - Edge case identification
       - Improvement suggestions

    Returns: {
        score: int (0-10),
        feedback: [phrase1, phrase2, phrase3],
        analysis_quality: str
    }
    """

def evaluate_db_schema_question(question_data: Dict,
                                candidate_response: str) -> Dict
    """
    1. Parse SQL schema from response
    2. Validate SQL syntax using Piston (SQLite)
    3. LLM evaluates (no deep design analysis, just syntax)

    Returns: {
        score: int (0-10),
        feedback: [phrase1, phrase2, phrase3],
        sql_validation: {
            valid_syntax: bool,
            error: str (if any)
        }
    }
    """

def evaluate_coding_interview(coding_test_filename: str,
                              uploads_folder: str,
                              interviews_folder: str) -> Dict
    """
    MAIN ORCHESTRATOR

    1. Load code-test-{name}-{date}.json
    2. For each question:
       - Load test cases from test_cases/{question_id}.json
       - Determine question type from title/metadata
       - Call appropriate evaluator
       - time.sleep(0.3) between compilations
    3. Calculate overall score (average)
    4. Save to code-evaluation-{name}-{date}.json

    Returns: {
        candidate_name: str,
        interview_date: str,
        overall_score: float (0-10),
        overall_feedback: str,
        questions: [
            {
                question_title: str,
                question_type: str,
                score: int,
                feedback: [str, str, str],
                details: {...}
            }
        ],
        evaluation_timestamp: str
    }
    """
```

**LLM Evaluation Prompt Template**:
```
You are evaluating a candidate's coding interview response.

Question Type: {question_type}
Question: {question_text}

Candidate's Code:
{code}

Candidate's Explanation:
{explanation}

Compilation Results:
{compilation_results}

Test Cases Results:
{test_results}

Provide:
1. Score (0-10):
   - 0-3: Poor (major issues, doesn't work)
   - 4-6: Fair (works partially, has issues)
   - 7-8: Good (works well, minor issues)
   - 9-10: Excellent (perfect solution)

2. Feedback (exactly 3 short phrases):
   - Phrase 1: What they did well
   - Phrase 2: Main issue or improvement area
   - Phrase 3: Overall assessment

Return JSON:
{
  "score": 7,
  "feedback": [
    "Fixed the core bug correctly",
    "Could improve variable naming",
    "Good understanding of the problem"
  ]
}
```

---

### **4. File: `backend/coding_agent.py` - Updates**

**New Route**: `/evaluate_coding_interview`
```python
@app.route('/evaluate_coding_interview', methods=['POST'])
def evaluate_coding_interview_route():
    """
    Automatically triggered after last question submission

    Request body: {coding_test_filename: str}

    Process:
    1. Call code_evaluator.evaluate_coding_interview()
    2. Return evaluation results

    Response: {
        success: bool,
        evaluation_results: {...},
        error: str (if any)
    }
    """
```

**Update**: `/submit_coding_response`
```python
# After saving response
if state.current_question_count >= state.total_questions:
    # Interview complete - trigger evaluation
    evaluation_results = evaluate_coding_interview(
        state.coding_test_filename,
        app.config['UPLOAD_FOLDER'],
        app.config['INTERVIEWS_FOLDER']
    )

    return jsonify({
        'complete': True,
        'evaluation_results': evaluation_results,
        'message': 'Interview complete! Evaluating your responses...'
    })
```

**Update**: Question generation to include test cases
```python
# In start_coding_interview route
first_question = generate_coding_question(state, 1)

# Generate test cases
test_cases = generate_test_cases(first_question, first_question.question_type)
save_test_cases(first_question.question_id, test_cases)

# Include test cases in response
response_data = {
    ...existing fields...,
    'test_cases': test_cases  # NEW: Show to candidate
}
```

---

### **5. File: `frontend/src/CodingInterviewer.jsx` - Updates**

**New State Variables**:
```javascript
const [evaluationResults, setEvaluationResults] = useState(null);
const [isEvaluating, setIsEvaluating] = useState(false);
const [currentTestCases, setCurrentTestCases] = useState([]);
```

**Display Test Cases in Question UI**:
```jsx
{/* NEW: Test Cases Section */}
{currentTestCases && currentTestCases.length > 0 && (
  <div className="mb-4 p-4 bg-green-50 border border-green-300 rounded">
    <details className="cursor-pointer">
      <summary className="font-semibold text-green-800">
        📝 Test Cases You Need to Pass ({currentTestCases.length})
      </summary>
      <div className="mt-3 space-y-2">
        {currentTestCases.map((tc, idx) => (
          <div key={idx} className="p-3 bg-white border border-green-200 rounded">
            <p className="text-sm text-gray-600 mb-1">{tc.description}</p>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <strong>Input:</strong>
                <pre className="bg-gray-50 p-1 rounded">{tc.input}</pre>
              </div>
              <div>
                <strong>Expected Output:</strong>
                <pre className="bg-gray-50 p-1 rounded">{tc.expected_output}</pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    </details>
  </div>
)}
```

**Handle Evaluation Response**:
```javascript
const submitCodingAnswer = async () => {
  // ...existing submission logic...

  const data = submitRes.data;

  if (data.complete) {
    setIsEvaluating(true);

    // Evaluation results already returned by backend
    if (data.evaluation_results) {
      setEvaluationResults(data.evaluation_results);
      setInterviewComplete(true);
    }

    setIsEvaluating(false);
  }
};
```

**Evaluation Loading State**:
```jsx
{isEvaluating && (
  <div className="w-full max-w-2xl mx-auto">
    <div className="bg-white rounded-2xl shadow-2xl p-12 text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">
        Evaluating Your Code...
      </h2>
      <p className="text-gray-600">
        Compiling and testing your solutions. This may take a minute.
      </p>
    </div>
  </div>
)}
```

**Evaluation Results Display**:
```jsx
{interviewComplete && evaluationResults && (
  <div className="w-full max-w-4xl mx-auto space-y-6">
    {/* Overall Score Card */}
    <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-xl p-6 text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-2">
        🎉 Interview Complete!
      </h2>
      <div className="text-6xl font-bold text-green-600 my-4">
        {evaluationResults.overall_score.toFixed(1)}/10
      </div>
      <p className="text-lg text-gray-700">
        {evaluationResults.overall_feedback}
      </p>
    </div>

    {/* Per-Question Results */}
    <div className="space-y-4">
      <h3 className="text-2xl font-semibold text-gray-800 text-center">
        Question-by-Question Breakdown
      </h3>

      {evaluationResults.questions.map((q, idx) => {
        const scoreColor = q.score >= 8 ? 'green' : q.score >= 5 ? 'yellow' : 'red';
        return (
          <div key={idx} className={`bg-white border-2 border-${scoreColor}-300 rounded-lg p-6 shadow-md`}>
            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="font-bold text-lg text-gray-800">
                  Q{idx + 1}: {q.question_title}
                </h4>
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                  {q.question_type.toUpperCase()}
                </span>
              </div>
              <div className={`text-3xl font-bold text-${scoreColor}-600`}>
                {q.score}/10
              </div>
            </div>

            {/* Feedback Phrases */}
            <div className="space-y-1 mb-4">
              {q.feedback.map((phrase, i) => (
                <p key={i} className="text-sm text-gray-700">
                  {i === 0 ? '✅' : i === 1 ? '💡' : '📊'} {phrase}
                </p>
              ))}
            </div>

            {/* Test Results (for debug questions) */}
            {q.details?.test_results && (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-medium text-gray-700">
                  View Test Results ({q.details.test_results.filter(t => t.passed).length}/{q.details.test_results.length} passed)
                </summary>
                <div className="mt-2 space-y-1">
                  {q.details.test_results.map((test, i) => (
                    <div key={i} className={`text-xs p-2 rounded ${test.passed ? 'bg-green-50' : 'bg-red-50'}`}>
                      {test.passed ? '✅' : '❌'} {test.description}
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* Compilation Errors (if any) */}
            {q.details?.compilation?.fixed_results?.stderr && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                <strong className="text-red-800 text-sm">Compilation Error:</strong>
                <pre className="text-xs text-red-700 mt-1 overflow-x-auto">
                  {q.details.compilation.fixed_results.stderr}
                </pre>
              </div>
            )}
          </div>
        );
      })}
    </div>
  </div>
)}
```

---

## **File Structure**

```
backend/
├── coding_agent.py (UPDATED)
├── utils/
│   ├── piston_compiler.py (NEW)
│   ├── test_case_generator.py (NEW)
│   ├── code_evaluator.py (NEW)
│   └── coding_question_generator.py (UPDATED)
├── interviews/
│   ├── code-test-{name}-{date}.json (existing)
│   └── code-evaluation-{name}-{date}.json (NEW)
└── test_cases/
    └── {question_id}.json (NEW)

frontend/src/
└── CodingInterviewer.jsx (UPDATED)
```

---

## **Data Schemas**

### **Test Case JSON** (`test_cases/{question_id}.json`)
```json
{
  "question_id": "q1_debug_python_2024",
  "question_type": "coding_debug",
  "test_cases": [
    {
      "input": "5\n10\n",
      "expected_output": "15\n",
      "description": "Basic addition test",
      "difficulty": "easy"
    },
    {
      "input": "-3\n7\n",
      "expected_output": "4\n",
      "description": "Negative number handling",
      "difficulty": "medium"
    }
  ]
}
```

### **Evaluation Results JSON** (`interviews/code-evaluation-{name}-{date}.json`)
```json
{
  "candidate_name": "Malek Ajmi",
  "interview_date": "10-10-2025",
  "overall_score": 7.2,
  "overall_feedback": "Strong debugging skills with room for improvement in code documentation",
  "questions": [
    {
      "question_title": "Debug Challenge: Restaurant Order Intent Classification",
      "question_type": "coding_debug",
      "score": 8,
      "feedback": [
        "Successfully fixed the core bug",
        "Code could use better variable names",
        "Good understanding of the problem"
      ],
      "details": {
        "compilation": {
          "buggy_results": {
            "stdout": "",
            "stderr": "NameError...",
            "exit_code": 1
          },
          "fixed_results": {
            "stdout": "Expected output",
            "stderr": "",
            "exit_code": 0
          }
        },
        "test_results": [
          {
            "input": "test input",
            "expected_output": "expected",
            "actual_output": "expected",
            "passed": true,
            "description": "Basic functionality test"
          }
        ],
        "code_quality_analysis": "Clean implementation with proper error handling"
      }
    }
  ],
  "evaluation_timestamp": "2025-10-10T15:30:00Z"
}
```

---

## **Implementation Checklist**

### **Phase 1: Piston Integration**
- [ ] Create `piston_compiler.py` with retry logic
- [ ] Test language mapping (Python, JS, Java, SQL)
- [ ] Test timeout handling (5s run, 10s compile)
- [ ] Verify rate limiting with sleep(0.3)

### **Phase 2: Test Case Generation**
- [ ] Create `test_case_generator.py`
- [ ] Design LLM prompts for test case generation
- [ ] Create `test_cases/` directory
- [ ] Test generating 3-5 test cases per question

### **Phase 3: Evaluation Logic**
- [ ] Create `code_evaluator.py`
- [ ] Implement `evaluate_debug_question()` with both code compilations
- [ ] Implement `evaluate_explain_question()` (LLM only, no compilation)
- [ ] Implement `evaluate_db_schema_question()` (SQL syntax validation)
- [ ] Implement scoring algorithm (0-10 scale)
- [ ] Create 3-phrase feedback generator

### **Phase 4: Backend Integration**
- [ ] Update `coding_question_generator.py` to call test generator
- [ ] Add `/evaluate_coding_interview` route
- [ ] Update `/submit_coding_response` to trigger evaluation
- [ ] Include test_cases in question response
- [ ] Test full flow: question → test cases → evaluation

### **Phase 5: Frontend Display**
- [ ] Add test cases display component
- [ ] Add evaluation loading state
- [ ] Create evaluation results UI with color-coded scores
- [ ] Test complete interview flow

### **Phase 6: Testing & Validation**
- [ ] Test with debug questions (buggy vs fixed code)
- [ ] Test with explain questions (text-only)
- [ ] Test with DB schema questions (SQL validation)
- [ ] Test error handling (compilation errors, timeouts)
- [ ] Test rate limiting behavior
- [ ] Validate scoring consistency

---

## **Key Implementation Notes**

### **Parsing Candidate Responses**
Current format from JSON:
```
"FIXED CODE:\n{code}\n\nEXPLANATION:\n{explanation}"
```

Parser regex:
```python
import re

def parse_debug_response(response_text):
    code_match = re.search(r'FIXED CODE:\s*\n(.*?)\n\nEXPLANATION:', response_text, re.DOTALL)
    explanation_match = re.search(r'EXPLANATION:\s*\n(.*)', response_text, re.DOTALL)

    return {
        'code': code_match.group(1).strip() if code_match else '',
        'explanation': explanation_match.group(1).strip() if explanation_match else ''
    }
```

### **Question Type Detection**
From existing JSON structure:
```python
def detect_question_type(question_title):
    if 'Debug Challenge' in question_title:
        return 'coding_debug'
    elif 'Code Analysis' in question_title:
        return 'coding_explain'
    elif 'Database Design' in question_title or 'Schema' in question_title:
        return 'db_schema'
    else:
        return 'coding_debug'  # default
```

### **Error Handling Strategy**
1. **Network errors**: Retry 3 times, then return error score (0) with feedback
2. **Compilation errors**: Include in evaluation (partial credit possible)
3. **Timeout errors**: Score based on what completed
4. **Missing test cases**: Skip compilation, use LLM-only evaluation

---

## **Future Enhancements** (Not in this phase)
- Self-hosted Piston instance for unlimited requests
- Code plagiarism detection
- Performance benchmarking (execution time, memory)
- Advanced test case generation with edge cases
- Role-based access (recruiter vs candidate results)
- Evaluation analytics dashboard

---

**End of Implementation Plan**
