# Code Compilator Testing Guide

## Quick Start Testing

### Prerequisites
```bash
# Install required dependencies
pip install requests langchain-google-genai

# Ensure .env file has GOOGLE_API_KEY set
```

### Test 1: Piston API Integration
```bash
cd backend/utils
python piston_compiler.py
```

**Expected Output**:
```
=== Piston Compiler Test Suite ===

Test 1: Fetching available runtimes...
[OK] Fetched 87 available runtimes from Piston API
Found 87 runtimes. Sample: {'language': 'python', ...}

Test 2: Executing simple Python code...
Success: True
Output: Hello from Piston!

Test 3: Running test cases...
  Basic addition: PASSED
  Negative numbers: PASSED

=== Tests Complete ===
```

---

### Test 2: Test Case Generator
```bash
cd backend/utils
python test_case_generator.py
```

**Expected**: Generates test cases for sample debug question and saves to `backend/test_cases/`

---

### Test 3: Full System Integration

#### Step 1: Start Backend
```bash
cd backend
python coding_agent.py
```

**Expected**: Server running on http://localhost:5001

#### Step 2: Start Frontend
```bash
cd frontend
npm run dev
```

**Expected**: Frontend running on http://localhost:5173

#### Step 3: Complete Interview
1. Navigate to http://localhost:5173
2. Upload a PDF CV
3. Start coding interview
4. Answer all 5 questions (any response works for testing)
5. Wait for evaluation to complete

**Expected Results**:
- Test cases displayed for each question
- Evaluation loading spinner appears
- Results page shows:
  - Overall score (0-10)
  - Per-question breakdown
  - 3-phrase feedback for each question
  - Test results (if compilation succeeded)

---

## Manual Testing Scenarios

### Scenario 1: Debug Question with Working Code
**Input**:
```
FIXED CODE:
def add(a, b):
    return a + b

a = int(input())
b = int(input())
print(add(a, b))

EXPLANATION:
Fixed the subtraction operator to use addition instead.
```

**Expected Evaluation**:
- Score: 8-10
- Feedback: Positive about fixing the bug
- Test cases: All passing

---

### Scenario 2: Debug Question with Broken Code
**Input**:
```
FIXED CODE:
def add(a, b)
    return a - b

EXPLANATION:
I tried to fix it.
```

**Expected Evaluation**:
- Score: 0-3
- Feedback: Mentions syntax error and wrong operator
- Compilation error shown

---

### Scenario 3: Explain Question
**Input**:
```
This code implements a binary search algorithm with O(log n) time complexity.
It works by repeatedly dividing the search space in half.
Improvements could include adding input validation and handling edge cases.
```

**Expected Evaluation**:
- Score: 6-9 (depending on quality)
- Feedback: Analyzes understanding and suggestions
- No compilation (text-only evaluation)

---

### Scenario 4: Database Schema Question
**Input**:
```
SQL SCHEMA:
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);

DESIGN EXPLANATION:
Simple users table with auto-incrementing ID and unique email constraint.

EXAMPLE QUERIES:
SELECT * FROM users WHERE email = 'test@example.com';
```

**Expected Evaluation**:
- Score: 6-8
- SQL Validation: Valid syntax
- Feedback: Comments on schema design

---

## Testing Checklist

### Functional Tests
- [ ] CV upload works
- [ ] Interview starts successfully
- [ ] Test cases display for each question
- [ ] All question types work (debug, explain, db_schema)
- [ ] Submission saves responses
- [ ] Evaluation triggers after final question
- [ ] Results display correctly

### Question Types
- [ ] Debug question: Code compiles and runs
- [ ] Debug question: Test cases execute
- [ ] Explain question: LLM evaluation works
- [ ] DB Schema: SQL validation works

### Error Handling
- [ ] Invalid code shows compilation error
- [ ] Timeout errors handled gracefully
- [ ] Network errors show appropriate message
- [ ] Missing test cases fallback to LLM-only

### UI/UX
- [ ] Test cases collapsible section works
- [ ] Evaluation loading spinner shows
- [ ] Overall score displays correctly
- [ ] Color coding works (green/yellow/red)
- [ ] Feedback phrases display (3 per question)
- [ ] Test results expandable section works

---

## Common Issues & Solutions

### Issue 1: "Module not found: langchain_google_genai"
**Solution**:
```bash
pip install langchain-google-genai
```

### Issue 2: Evaluation Stuck on Loading
**Possible Causes**:
- Piston API rate limit hit
- Network connectivity issues
- LLM API key invalid

**Debug**:
1. Check backend console for errors
2. Verify GOOGLE_API_KEY in .env
3. Test Piston API manually

### Issue 3: Test Cases Not Displaying
**Possible Causes**:
- Test case generation failed
- Frontend not receiving test_cases data

**Debug**:
1. Check backend console for test case generation logs
2. Inspect network tab for `/start_coding_interview` response
3. Verify `test_cases` array in response

### Issue 4: Compilation Errors for Valid Code
**Possible Causes**:
- Language mismatch
- Missing stdin handling
- Timeout too short

**Debug**:
1. Check language mapping in `piston_compiler.py`
2. Verify test case input format
3. Increase timeout if needed

---

## Performance Metrics

### Expected Timing
- **Test Case Generation**: 3-5 seconds per question
- **Code Compilation**: 1-2 seconds per test case
- **Full Evaluation**: 10-20 seconds for 5 questions
- **LLM Evaluation**: 2-3 seconds per question

### Rate Limiting
- Piston API: 3.3 req/s (with 0.3s delay)
- 5 questions × 3 test cases × 2 versions = 30 requests
- Total time: ~9 seconds minimum (compilation only)

---

## Validation Checklist

Before considering implementation complete:

### Backend
- [ ] All 3 new utility files created
- [ ] coding_agent.py updated with imports
- [ ] /evaluate_coding_interview route added
- [ ] Test case generation integrated
- [ ] Evaluation triggers on completion
- [ ] test_cases/ directory exists

### Frontend
- [ ] State variables added (currentTestCases, evaluationResults, isEvaluating)
- [ ] Test cases display component added
- [ ] Evaluation results UI implemented
- [ ] Loading state shows during evaluation
- [ ] Color-coded scores work
- [ ] Fallback UI for errors

### Integration
- [ ] End-to-end flow works
- [ ] Data persists to JSON files
- [ ] Evaluation results match expected format
- [ ] No console errors

---

## Sample Test Data

### Minimal CV for Testing
Create a simple PDF with:
- Name: Test Candidate
- Experience: Python Developer, 2 years
- Skills: Python, JavaScript, SQL

### Sample Job Description
```
Software Developer
Required: Python, JavaScript
Nice to have: SQL, React
Experience: 2+ years
```

This will generate Python/JavaScript coding questions.

---

## Troubleshooting Commands

### Check Test Cases Directory
```bash
ls backend/test_cases/
# Should show .json files after questions generated
```

### View Generated Test Cases
```bash
cat backend/test_cases/q1_coding_debug_python.json
```

### View Evaluation Results
```bash
cat backend/interviews/code-evaluation-test-candidate-21-01-2025.json
```

### Monitor Backend Logs
Watch for:
- "[INFO] Generating test cases for question..."
- "[OK] Generated X test cases"
- "[DEBUG] Evaluating debug question..."
- "[OK] Evaluation saved to..."

---

## Success Criteria

The implementation is successful if:

1. ✅ Test cases generate for all question types
2. ✅ Code compiles via Piston API
3. ✅ Test results show passed/failed accurately
4. ✅ LLM provides scores and feedback
5. ✅ Evaluation results save to JSON
6. ✅ Frontend displays results correctly
7. ✅ No critical errors in console
8. ✅ Rate limiting prevents API issues

---

**Ready to Test!**

Start with Test 1 (Piston API) to verify basic connectivity, then proceed to full system integration testing.

For issues, check the backend console logs first - they contain detailed debugging information.
