# AI Interviewer - API Documentation

**Version:** 2.0.0
**Server:** `http://127.0.0.1:5000`
**Last Updated:** 2025-10-28

## Overview

The AI Interviewer is a unified backend system that conducts three types of technical interviews:
- **Text Interview**: Traditional Q&A with open and multiple-choice questions
- **Oral Interview**: Voice-based conversational interview with audio recording
- **Coding Interview**: Technical coding challenges with automated evaluation

All three interview types run on a single Flask server with lazy loading for optimal performance.

---

## Quick Start

### Start the Server
```bash
cd backend
python main.py
```

Server runs on **port 5000** with all three interview types available.

### Health Check
```bash
curl http://127.0.0.1:5000/health
```

---

## API Routes

### System Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message with version info |
| GET | `/health` | Health check - shows module availability |
| GET | `/api/info` | Detailed API information and available endpoints |

**Example Response (`/health`):**
```json
{
  "status": "healthy",
  "modules": {
    "text": true,
    "oral": true,
    "coding": true
  },
  "version": "2.0.0"
}
```

---

### Text Interview Routes

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/start_interview` | Start new text interview | None |
| POST | `/submit_response` | Submit answer to current question | `{ response, qcm_selected?, qcm_selected_multiple? }` |
| POST | `/record` | Handle audio transcription | `{ transcription }` |

**Start Interview Response:**
```json
{
  "question_id": 1,
  "question_type": "open",
  "question": "Tell me about your experience with...",
  "difficulty_level": 5,
  "phase": "open",
  "question_count": 1,
  "complete": false
}
```

**Submit Response:**
```json
{
  "question_id": 2,
  "question_type": "qcm",
  "question": "Which of the following...",
  "options": [
    { "option": "A", "text": "Option A text" },
    { "option": "B", "text": "Option B text" }
  ],
  "is_multiple_choice": false,
  "complete": false
}
```

**Completion Response:**
```json
{
  "complete": true,
  "evaluation": {
    "overall_score": 7.5,
    "qcm_score": 8.0,
    "technical_vocab_score": 7.2,
    "grammar_flow_score": 7.8,
    "evaluation_summary": "Strong technical knowledge..."
  }
}
```

---

### Oral Interview Routes

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| POST | `/oral/upload_cv` | Upload CV (PDF only) | Form-data: `cv` file |
| GET | `/oral/start` | Initialize oral interview | None |
| POST | `/oral/continue` | Submit response, get next question | `{ response }` |
| POST | `/oral/complete` | Save interview dialogue | None |
| POST | `/oral/upload_audio` | Upload audio recording | Form-data: `audio`, `turn`, `timestamp` |
| POST | `/oral/evaluate` | Evaluate completed interview | `{ interview_filename }` |

**Upload CV Response:**
```json
{
  "success": true,
  "experiences_count": 3,
  "education_count": 2,
  "skills_count": 15,
  "projects_count": 4
}
```

**Start Interview Response:**
```json
{
  "success": true,
  "question": "Hello! Let's start with...",
  "turn": 1
}
```

**Continue Interview Response:**
```json
{
  "question": "That's interesting. Can you elaborate on...",
  "turn": 5,
  "complete": false
}
```

**Evaluation Response:**
```json
{
  "success": true,
  "overall_score": 7.8,
  "report": {
    "technical_vocab_score": 8.2,
    "coherence_score": 7.5,
    "relevance_score": 7.9,
    "clarity_score": 7.6
  }
}
```

---

### Coding Interview Routes

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/coding/` | API info for coding interview | None |
| GET | `/coding/start` | Start coding interview | None |
| POST | `/coding/submit` | Submit code solution | `{ response }` |
| POST | `/coding/evaluate` | Manually trigger evaluation | `{ coding_test_filename }` |
| GET | `/coding/status` | Get current interview status | None |

**Start Interview Response:**
```json
{
  "question_id": 1,
  "question_type": "debug",
  "title": "Fix the Authentication Bug",
  "context_paragraph": "A user authentication function...",
  "task_instruction": "Debug the code and fix all errors",
  "buggy_code": "def authenticate(user):\n    ...",
  "error_types": ["logic", "syntax"],
  "difficulty_level": 6,
  "question_count": 1,
  "total_questions": 5
}
```

**Submit Response (during interview):**
```json
{
  "question_id": 2,
  "question_type": "explanation",
  "title": "Explain the Caching Mechanism",
  "working_code": "def cache_result(fn):\n    ...",
  "question_count": 2,
  "total_questions": 5
}
```

**Completion Response:**
```json
{
  "complete": true,
  "message": "Interview completed",
  "evaluation_results": {
    "total_score": 8.2,
    "question_scores": [...]
  }
}
```

---

### Legacy Redirect Routes

For backward compatibility, the following routes redirect to new endpoints:

| Old Route | New Route |
|-----------|-----------|
| `/upload_cv` | `/oral/upload_cv` |
| `/oral_interview/start` | `/oral/start` |
| `/oral_interview/continue` | `/oral/continue` |
| `/oral_interview/complete` | `/oral/complete` |
| `/oral_interview/upload_audio` | `/oral/upload_audio` |
| `/oral_interview/evaluate` | `/oral/evaluate` |
| `/start_coding_interview` | `/coding/start` |
| `/submit_coding_response` | `/coding/submit` |
| `/evaluate_coding` | `/coding/evaluate` |

---

## Data Models

### CV & Job Models

**StructuredCV**
```python
{
  personal_info: PersonalInfo,
  experiences: List[WorkExperience],
  education: List[Education],
  skills: List[Skill],
  projects: List[Project],
  achievements: List[str],
  languages: List[str]
}
```

**WorkExperience**
```python
{
  company: str,
  position: str,
  start_date: str,
  end_date: str,
  responsibilities: List[str],
  technologies: List[str]
}
```

**StructuredJobDescription**
```python
{
  job_title: str,
  seniority_level: str,
  required_skills: List[str],
  preferred_skills: List[str],
  responsibilities: List[str],
  experience_years: int,
  technologies: List[str],
  domain: str  # ai_ml, web_development, data_science, general
}
```

---

### Question Models

**InterviewQuestion** (Text/Oral)
```python
{
  question_id: int,
  question_type: str,  # "open" or "qcm"
  question_text: str,
  difficulty_level: int,  # 1-10
  technology_focus: str,
  qcm_data?: QCMQuestion
}
```

**QCMQuestion**
```python
{
  question: str,
  options: List[QCMOption],
  correct_answer: str,  # Single choice
  correct_answers: List[str],  # Multiple choice
  is_multiple_choice: bool,
  explanation: str
}
```

**CodingInterviewQuestion**
```python
{
  question_id: int,
  question_type: str,  # "debug", "explanation", "db_schema"
  question_text: str,
  difficulty_level: int,
  technology_focus: str,
  debug_data?: DebugCodingQuestion,
  explanation_data?: ExplanationCodingQuestion,
  db_schema_data?: DatabaseSchemaQuestion
}
```

---

### State Models

**InterviewState** (Text Interview)
```python
{
  complete: bool,
  difficulty_score: int,  # 1-10
  current_phase: str,  # "open", "qcm"
  current_question: InterviewQuestion,
  questions_history: List[InterviewQuestion],
  responses_history: List[InterviewResponse],
  matched_technologies: List[str]
}
```

**DialogueState** (Oral Interview)
```python
{
  complete: bool,
  difficulty_score: int,
  conversation_history: List[Dict],
  current_turn: int,
  matched_technologies: List[str],
  topics_covered: List[str],
  current_section: str  # "opening", "hr", "cv", "job", "closing"
}
```

**CodingInterviewState**
```python
{
  difficulty_score: int,
  matched_technologies: List[str],
  current_question_count: int,
  total_questions: int,
  current_question: CodingInterviewQuestion,
  question_distribution: Dict[int, Dict]
}
```

---

### Evaluation Models

**EvaluationReport** (Text Interview)
```python
{
  candidate_name: str,
  job_title: str,
  overall_score: float,  # 0-10
  qcm_score: float,
  technical_vocab_score: float,
  grammar_flow_score: float,
  qcm_details: {
    total_questions: int,
    correct_answers: int,
    percentage: float
  },
  open_question_feedback: List[OpenQuestionDetail],
  evaluation_summary: str
}
```

**OralEvaluationReport**
```python
{
  candidate_name: str,
  duration_minutes: float,
  overall_score: float,  # 0-10
  technical_vocab_score: float,  # 30% weight
  coherence_score: float,  # 30% weight
  relevance_score: float,  # 25% weight
  clarity_score: float,  # 15% weight
  question_evaluations: List[OralQuestionDetail],
  evaluation_summary: str
}
```

---

## Architecture

### Directory Structure

```
backend/
├── main.py                          # Unified server (entry point)
├── app.py                           # Legacy text interview
├── shared/
│   ├── models.py                    # Pydantic models
│   ├── llm_setup.py                 # LLM initialization
│   ├── information_extraction.py    # CV/Job parsing
│   ├── cv_analysis.py               # CV analysis
│   └── speech_processing.py         # Speech utilities
├── text_interview/
│   └── evaluator/                   # Text evaluation modules
├── oral_interview/
│   ├── routes.py                    # Oral routes (blueprint)
│   ├── question_generator.py        # Question generation
│   └── evaluator/                   # Oral evaluation modules
├── coding_interview/
│   ├── routes.py                    # Coding routes (blueprint)
│   ├── question_generator.py        # Question generation
│   ├── job_skill_analyzer.py        # Skill analysis
│   └── evaluator/                   # Coding evaluation modules
├── config/
│   ├── .env                         # API keys
│   ├── interview_prompts.yaml       # Text prompts
│   ├── evaluation_prompts.yaml      # Text evaluation
│   ├── oral_system_prompts.yaml     # Oral prompts
│   └── coding_prompts.yaml          # Coding prompts
└── data/
    ├── uploads/                     # CV & job uploads
    ├── interviews/
    │   ├── text/                    # Text interview records
    │   ├── oral/                    # Oral interview records
    │   └── coding/                  # Coding interview records
    └── evaluation_reports/
        ├── text/                    # Text evaluations
        ├── oral/                    # Oral evaluations
        └── coding/                  # Coding evaluations
```

---

### Module Integration

**Blueprint Pattern** (Modern Approach):
- **Oral Interview**: Blueprint registered at startup (`/oral/*` routes)
- **Coding Interview**: Blueprint registered at startup (`/coding/*` routes)

**Legacy Integration**:
- **Text Interview**: Routes registered via `register_text_routes(app)` from `app.py`
- Preserves original route paths (`/start_interview`, `/submit_response`)
- Maintains backward compatibility

**Lazy Loading**:
- Each module initializes LLM and prompts only on first request
- Global state management per module (thread-safe)
- Optimizes startup time and memory usage

---

## Configuration

### Environment Variables

Required in `backend/config/.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### LLM Configuration

- **Model**: Gemini 2.0 Flash (Google Generative AI)
- **Temperature**: 0.3 (consistent, low randomness)
- **Provider**: `langchain_google_genai`
- **Usage**: Question generation, response evaluation, CV/job parsing

### CORS Configuration

```python
Origins: http://localhost:5173
Headers: Content-Type, Accept, Authorization, X-Requested-With
Methods: GET, POST, OPTIONS
Credentials: Enabled
```

### Prompt Files (YAML)

- `interview_prompts.yaml` - Text interview question generation
- `evaluation_prompts.yaml` - Text interview evaluation
- `oral_system_prompts.yaml` - Oral interview system prompts
- `oral_evaluation_prompts.yaml` - Oral interview evaluation
- `coding_prompts.yaml` - Coding interview question generation

---

## Data Flow

### Text Interview Flow
1. **Start**: `GET /start_interview` → parses job, generates Q1
2. **Submit**: `POST /submit_response` → evaluates answer, generates next Q
3. **Complete**: Final submission triggers evaluation
4. **Result**: Returns evaluation report with scores

### Oral Interview Flow
1. **Upload CV**: `POST /oral/upload_cv` → parses CV
2. **Start**: `GET /oral/start` → generates opening question
3. **Continue**: `POST /oral/continue` → dialogue loop (Q&A)
4. **Audio**: `POST /oral/upload_audio` → saves audio files
5. **Complete**: `POST /oral/complete` → saves dialogue JSON
6. **Evaluate**: `POST /oral/evaluate` → generates evaluation report

### Coding Interview Flow
1. **Start**: `GET /coding/start` → analyzes job skills, generates Q1
2. **Submit**: `POST /coding/submit` → evaluates code, generates next Q
3. **Complete**: Final submission triggers evaluation
4. **Result**: Returns evaluation with code analysis

---

## Storage Conventions

### File Naming

- **Text Interview**: `text-{candidate}-{timestamp}.json`
- **Oral Interview**: `oral-{candidate}-{timestamp}.json`
- **Coding Interview**: `code-test-{timestamp}.json`
- **Audio Files**: `oral-interview-q{turn}-{timestamp}.webm`
- **Evaluations**: `evaluation_report-{candidate}-{timestamp}.json`

### Data Persistence

All interview data and evaluations are saved to JSON files in the `data/` directory structure for:
- Record keeping
- Manual review
- Analytics and reporting
- Re-evaluation if needed

---

## Error Handling

### Global Handlers
- **404 Not Found**: Endpoint doesn't exist
- **500 Internal Server Error**: Unexpected error with traceback

### Module-Level Errors
- Try-catch blocks in all route handlers
- Detailed logging to console
- Graceful error responses with error messages

---

## Feature Matrix

| Feature | Text | Oral | Coding |
|---------|------|------|--------|
| CV Upload | ✅ | ✅ | ❌ (Job-only) |
| Job Description | ✅ | ✅ | ✅ |
| Question Generation | ✅ | ✅ | ✅ |
| Audio Recording | ❌ | ✅ | ❌ |
| Code Execution | ❌ | ❌ | ✅ (Piston) |
| Progressive Difficulty | ✅ | ✅ | ✅ |
| Automated Evaluation | ✅ | ✅ | ✅ |
| Question Types | Open, QCM | Conversational | Debug, Explain, DB |

---

## Testing

### Test System Routes
```bash
# Health check
curl http://127.0.0.1:5000/health

# API info
curl http://127.0.0.1:5000/api/info
```

### Test Text Interview
```bash
# Start interview
curl http://127.0.0.1:5000/start_interview

# Submit response
curl -X POST http://127.0.0.1:5000/submit_response \
  -H "Content-Type: application/json" \
  -d '{"response": "Your answer here"}'
```

### Test Oral Interview
```bash
# Upload CV
curl -X POST http://127.0.0.1:5000/oral/upload_cv \
  -F "cv=@path/to/cv.pdf"

# Start interview
curl http://127.0.0.1:5000/oral/start

# Continue interview
curl -X POST http://127.0.0.1:5000/oral/continue \
  -H "Content-Type: application/json" \
  -d '{"response": "Your answer here"}'
```

### Test Coding Interview
```bash
# Start interview
curl http://127.0.0.1:5000/coding/start

# Submit code
curl -X POST http://127.0.0.1:5000/coding/submit \
  -H "Content-Type: application/json" \
  -d '{"response": "def solution():\n    return True"}'
```

---

## Notes

- **Port 5000**: All three interview types run on the same port
- **Stateful**: Each interview maintains state during active session
- **Thread-Safe**: Global state protected with locks (text interview)
- **Modular**: Easy to add new interview types or question formats
- **Scalable**: Lazy loading minimizes resource usage

---

## Support

For issues or questions:
- Check server logs for detailed error messages
- Verify `.env` file contains valid `GOOGLE_API_KEY`
- Ensure YAML prompt files are present in `config/` directory
- Review uploaded files in `data/uploads/` directory

---

**Last Updated**: 2025-10-28
**Maintained By**: AI Interviewer Team
