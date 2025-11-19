# AI Interviewer - Intelligent Multi-Modal Interview System

An advanced AI-powered interview platform supporting text-based, oral, and coding assessments. The system uses Google Gemini for intelligent question generation and evaluation, with a focus on job-centric skill assessment rather than CV-based questioning.

## 🎯 Key Features

### Multi-Modal Interview Types

1. **Text Interview**
   - 5 open-ended questions
   - 5 QCM/MCQ questions
   - Real-time evaluation
   - Job-focused questioning

2. **Oral Interview**
   - Voice-based interaction
   - Speech-to-text transcription (Whisper)
   - Text-to-speech questions (Kokoro)
   - Audio recording and storage

3. **Coding Interview**
   - Debug challenges
   - Code explanation tasks
   - Database schema design
   - Skill-weighted question distribution
   - Progressive difficulty (50% → 100%)

### Job-Centric Approach

- **Skill Importance Ranking**: Automatically analyzes job descriptions to identify critical skills
- **2-1-1-1 Distribution Strategy**:
  - 2 questions on the most important skill
  - 1 question on the second most important skill
  - 1 question on another important skill
  - 1 question to verify CV claims (skill intersection test)
- **Job-Based Difficulty**: Questions match job requirements, not candidate's claimed experience
- **CV Verification**: Tests actual proficiency vs. claimed skills

### Security Features

- Fullscreen enforcement
- Tab switching detection
- Violation logging
- Progressive warning system
- Automatic disqualification after threshold

### Intelligent Evaluation

- Automated evaluation using Google Gemini
- QCM auto-scoring
- Open question evaluation with detailed feedback
- Comprehensive evaluation reports

## 🛠️ Tech Stack

### Backend

- **Framework**: Flask 3.0+
- **AI/LLM**:
  - LangChain
  - Google Gemini 2.0 Flash (langchain-google-genai)
- **Audio Processing**:
  - Faster Whisper (speech-to-text)
  - Kokoro TTS (text-to-speech)
  - PyAudio, Soundfile
- **Utilities**:
  - Pydantic (data validation)
  - PyYAML (configuration)
  - python-dotenv (environment management)

### Frontend

- **Framework**: React 19.1.0
- **Build Tool**: Vite 6.3.5
- **Styling**: TailwindCSS 4.1.6
- **Key Libraries**:
  - Axios 1.9.0 (HTTP client)
  - React Speech Recognition 4.0.1
  - Monaco Editor 0.59.0 (code editor)
- **Dev Tools**: ESLint 9.25.0

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **Google Gemini API Key**: Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AMalek98/ai_interviewer_agent.git
cd ai_interviewer_agent
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Note: PyAudio on Windows may require additional steps:
# pip install pipwin
# pipwin install pyaudio

# Set up environment variables
# Create/edit backend/config/.env and add:
echo "GOOGLE_API_KEY=your_google_api_key_here" > backend/config/.env
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## 🎬 How to Launch

### Start the Backend Server

```bash
cd backend
python main.py
```

The backend server will start on **http://127.0.0.1:5000**

You should see output like:
```
======================================================================
🚀 AI INTERVIEWER - UNIFIED SERVER
======================================================================

📦 Available Modules:
   ✅ Text Interview      → /start_interview, /submit_response, /record
   ✅ Oral Interview      → /oral/
   ✅ Coding Interview    → /coding/

📍 Server Configuration:
   - URL: http://127.0.0.1:5000
   - Frontend Origin: http://localhost:5173
```

### Start the Frontend Server (New Terminal)

```bash
cd frontend
npm run dev
```

The frontend will start on **http://localhost:5173**

### Access the Application

Open your browser and navigate to: **http://localhost:5173**

## 📁 Project Structure

```
ai_interviewer/
│
├── README.md
├── ARCHITECTURE.md
├── ARCHITECTURE_DIAGRAM.md
├── code_base.md
├── requirements.txt
│
├── backend/
│   ├── main.py                      # Unified Flask server (Port 5000)
│   │
│   ├── text_interview/              # Text interview module
│   │   ├── routes.py
│   │   ├── managers.py
│   │   ├── generators.py
│   │   ├── processors.py
│   │   └── utils.py
│   │
│   ├── oral_interview/              # Oral interview module
│   │   ├── routes.py
│   │   ├── question_generator.py
│   │   ├── utils.py
│   │   └── evaluator/
│   │       ├── engine.py
│   │       ├── models.py
│   │       └── response_evaluator.py
│   │
│   ├── coding_interview/            # Coding interview module
│   │   ├── routes.py
│   │   ├── question_generator.py
│   │   ├── job_skill_analyzer.py
│   │   ├── test_case_generator.py
│   │   ├── utils.py
│   │   └── evaluator/
│   │       ├── engine.py
│   │       ├── piston_compiler.py
│   │       └── output_comparator.py
│   │
│   ├── shared/                      # Shared utilities
│   │   ├── models.py
│   │   ├── llm_setup.py
│   │   ├── information_extraction.py
│   │   ├── cv_analysis.py
│   │   ├── speech_processing.py
│   │   └── config.py
│   │
│   ├── evaluation/                  # Evaluation engine
│   │   ├── evaluation_engine.py
│   │   ├── evaluation_models.py
│   │   ├── qcm_evaluator.py
│   │   ├── open_question_evaluator.py
│   │   ├── oral_response_evaluator.py
│   │   └── oral_evaluator.py
│   │
│   ├── config/
│   │   ├── .env                     # Environment variables
│   │   ├── interview_prompts.yaml
│   │   ├── oral_system_prompts.yaml
│   │   ├── coding_prompts.yaml
│   │   ├── evaluation_prompts.yaml
│   │   └── oral_evaluation_prompts.yaml
│   │
│   └── data/
│       ├── uploads/                 # CV and job description uploads
│       ├── interviews/
│       │   ├── text/               # Text interview transcripts
│       │   ├── oral/               # Oral interview recordings
│       │   └── coding/             # Coding interview responses
│       ├── evaluation_reports/
│       │   ├── text/
│       │   ├── oral/
│       │   └── coding/
│       └── security_logs/          # Security violation logs
│
├── frontend/
│   ├── index.html
│   ├── coding.html
│   ├── package.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   │
│   └── src/
│       ├── main.jsx
│       ├── Router.jsx
│       ├── App.jsx                 # Text interview UI
│       ├── OralInterview.jsx       # Oral interview UI
│       ├── CodingInterviewer.jsx   # Coding interview UI
│       ├── coding-main.jsx
│       ├── index.css
│       ├── App.css
│       ├── components/
│       │   └── security/           # Security monitoring components
│       │       ├── SecurityMonitor.jsx
│       │       ├── WarningModal.jsx
│       │       ├── WarningBanner.jsx
│       │       └── DisqualificationScreen.jsx
│       └── utils/
│           └── languageMapper.js
│
├── docs/                            # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── TESTING_GUIDE.md
│   └── evaluation_steps.md
│
├── tests/                           # Test files
└── archive/                         # Archived files
```

## 🔧 API Endpoints

### Core Endpoints

**Health & Info:**
- `GET /health` - Server health check
- `GET /api/info` - API information and available modules
- `GET /` - Root endpoint

### Text Interview

- `POST /start_interview` - Initialize text interview
  - Body: `{ "cv_file": file, "job_description": file }`
- `POST /submit_response` - Submit answer and get next question
  - Body: `{ "response": "answer text" }`
- `POST /record` - Get interview transcript

### Oral Interview

- `POST /oral/upload_cv` - Upload CV for oral interview
- `GET /oral/start` - Start oral interview
- `POST /oral/continue` - Continue to next question
- `POST /oral/upload_audio` - Upload audio response
- `POST /oral/complete` - Complete interview
- `POST /oral/evaluate` - Get evaluation report

### Coding Interview

- `POST /coding/start` - Start coding interview
  - Body: `{ "cv_file": file, "job_description": file }`
- `POST /coding/submit` - Submit coding response
  - Body: `{ "response": "code solution" }`
- `POST /coding/evaluate` - Get evaluation report

### Security

- `POST /api/security/violation` - Log security violation
  - Body: `{ "type": "tab_switch", "interview_type": "coding" }`
- `GET /api/security/stats` - Get violation statistics

## 🎓 Interview Question Types

### Text Interview

1. **Open-Ended Questions**:
   - Technical depth assessment
   - Problem-solving scenarios
   - Real-world application

2. **QCM/MCQ Questions**:
   - Quick knowledge verification
   - Multiple choice format
   - Auto-scored

### Oral Interview

- Voice-based questions
- Natural conversation flow
- Speech pattern analysis
- Pronunciation and fluency assessment

### Coding Interview

1. **Debug Questions**: Find and fix bugs in provided code
2. **Explanation Questions**: Analyze and explain working code
3. **Database Schema Questions**:
   - Schema design challenges
   - Complex SQL query writing
   - Performance optimization
   - Only generated when job requires database skills

## 🎯 How It Works

### 1. CV & Job Description Upload

Upload candidate's CV and job description (PDF/TXT format):
- System parses documents using LLM
- Extracts skills, technologies, and experience
- Saves structured data for analysis

### 2. Skill Analysis

System analyzes the job description:
```
🔍 ANALYZING JOB DESCRIPTION FOR SKILL REQUIREMENTS
✅ Job Skill Analysis Complete:
   - Primary Skills: 2
   - Job Level: senior
   - Overall Difficulty: 8/10
   - Database Required: True

   Top 3 Skills:
      1. SQL (Rank 1, expert)
      2. Python (Rank 2, intermediate)
      3. Docker (Rank 4, basic)
```

### 3. Question Distribution Planning

Creates strategic question plan:
```
📋 Question Distribution Plan:
   Q1: SQL (Difficulty 10/10, Type: db_schema)
   Q2: SQL (Difficulty 10/10, Type: debug)
   Q3: Python (Difficulty 5/10, Type: debug)
   Q4: Docker (Difficulty 2/10, Type: explain)
   Q5: SQL (Difficulty 10/10, Type: db_schema) - CV Verification
```

### 4. Question Generation

Each question generated based on:
- Skill importance from job description
- Required proficiency level
- Job-centric difficulty (not CV-based)
- Appropriate question type for the skill

### 5. Response Collection & Evaluation

- Real-time response submission
- Automated evaluation using Gemini
- Detailed feedback and scoring
- Comprehensive evaluation reports

## 🔒 Security Monitoring

The system includes comprehensive security features:

- **Fullscreen Enforcement**: Interview must be in fullscreen mode
- **Tab Switch Detection**: Detects when user switches tabs/windows
- **Copy/Paste Monitoring**: Tracks clipboard usage
- **Violation Logging**: All violations saved to `backend/data/security_logs/`
- **Progressive Warnings**:
  - Warning 1-2: Modal warning
  - Warning 3+: Disqualification
- **Automatic Disqualification**: Interview terminated after threshold violations

## ⚙️ Configuration

### Environment Variables

Create `backend/config/.env`:

```env
# Google Gemini API Key (Required)
GOOGLE_API_KEY=your_google_api_key_here
```

### Prompt Customization

Prompts can be customized in:
- `backend/config/interview_prompts.yaml` - Text interview prompts
- `backend/config/oral_system_prompts.yaml` - Oral interview prompts
- `backend/config/coding_prompts.yaml` - Coding interview prompts
- `backend/config/evaluation_prompts.yaml` - Evaluation prompts

## 📊 Example Scenarios

### Scenario 1: SQL-Focused Job

**Job Description:** "Senior Backend Developer requiring expert SQL skills..."

**Result:**
- Q1-Q2: Expert-level SQL questions (difficulty 10/10)
- Q3: Secondary skill question
- Q4: Tertiary skill question
- Q5: SQL question to verify CV claims

### Scenario 2: Frontend Developer

**Job Description:** "Frontend Developer with React and TypeScript..."

**Result:**
- No database questions generated
- Focus on React, TypeScript, JavaScript
- Questions distributed across frontend skills
- Progressive difficulty based on seniority level

### Scenario 3: CV Mismatch Detection

**Job:** Requires expert SQL
**CV:** Claims "proficient in SQL"
**Q5:** Expert-level SQL question to verify actual proficiency

## 🎯 Key Advantages

### Traditional Approach ❌

- Questions based on CV experience level
- Junior developer gets junior questions
- Can't assess true capability for senior roles
- Skills equally weighted regardless of job needs

### Our Approach ✅

- Questions based on job requirements
- Junior developer gets senior-level questions if job needs senior skills
- Reveals true capability and skill gaps
- Skills weighted by importance in job description
- Tests CV accuracy with verification questions

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- Additional question types (algorithm, system design)
- Framework-specific questions (React, Django, etc.)
- Dynamic question count based on skill complexity
- Integration with job posting APIs
- Multi-language support
- Video interview capabilities

## 📚 Documentation

- **ARCHITECTURE.md**: System architecture overview
- **ARCHITECTURE_DIAGRAM.md**: Visual architecture and data flow
- **docs/API_DOCUMENTATION.md**: Detailed API reference
- **docs/TESTING_GUIDE.md**: Testing procedures
- **docs/IMPLEMENTATION_SUMMARY.md**: Implementation details
- **code_base.md**: Codebase structure reference

## 🐛 Troubleshooting

### PyAudio Installation Issues (Windows)

```bash
pip install pipwin
pipwin install pyaudio
```

Or download the appropriate wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

### Port Already in Use

**Backend (Port 5000):**
Change in `backend/main.py` (line ~405):
```python
app.run(host='127.0.0.1', port=5001, debug=True)  # Change 5000 to 5001
```

**Frontend (Port 5173):**
Change in `frontend/vite.config.js`:
```javascript
server: {
  port: 5174  // Change 5173 to 5174
}
```

### CORS Issues

Ensure frontend origin is correctly set in `backend/main.py`:
```python
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
```

## 📄 License

MIT License - See LICENSE file for details

## 👥 Authors

Malek Ajmi - [@AMalek98](https://github.com/AMalek98)

## 🌟 Acknowledgments

- Google Gemini for AI capabilities
- OpenAI Whisper for speech recognition
- LangChain for LLM framework
- React and Vite communities
