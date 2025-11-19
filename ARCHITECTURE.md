# Clean AI Interviewer Architecture

## 📁 Directory Structure

```
ai_interviewer/
├── backend/                    # Python Flask Backend
│   ├── app.py                 # Main Flask application
│   ├── config/                # Configuration files
│   │   ├── .env              # Environment variables
│   │   └── interview_prompts.yaml # AI prompts
│   └── utils/                 # Utility modules
│       ├── speech_to_text.py  # Voice recognition
│       └── text_to_speech.py  # Voice synthesis
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── App.css           # Styles
│   │   └── main.jsx          # Entry point
│   ├── package.json          # Dependencies
│   └── vite.config.js        # Build configuration
├── tests/                      # Test files
├── docs/                       # Documentation
├── archive/                    # Legacy files (archived)
├── uploads/                    # Runtime CV uploads
├── static/                     # Audio files
├── start_backend.bat          # Backend startup script
├── start_frontend.bat         # Frontend startup script
└── interview.json             # Session data
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt  # If requirements.txt exists
python app.py
```
OR use the batch file:
```
start_backend.bat
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
OR use the batch file:
```
start_frontend.bat
```

## 🔧 Configuration

- **Environment**: `backend/config/.env` - Contains API keys
- **Prompts**: `backend/config/interview_prompts.yaml` - AI interview prompts
- **Frontend**: `frontend/vite.config.js` - Dev server on port 5173
- **Backend**: Flask app on port 5000

## 📊 Tech Stack

### Backend
- **Flask** - Web framework
- **LangChain** - LLM integration
- **Google Gemini 2.5** - AI model
- **PyPDF** - CV parsing
- **Pydantic** - Data validation

### Frontend
- **React 19.1.0** - UI framework
- **Vite** - Build tool
- **TailwindCSS 4.1.6** - Styling
- **Axios** - HTTP client
- **Speech Recognition** - Voice input

## 🔄 Data Flow

1. **CV Upload** → PDF parsed → Structured data extraction
2. **Interview Init** → Experience scoring → Question generation
3. **Voice Interaction** → Speech-to-text → AI processing → Text-to-speech
4. **3-Phase Flow** → Open (5) → QCM (5) → Coding (5) questions

## 🗂️ Archived

- `archive/templates/` - Legacy HTML interface
- Legacy folders moved out of main structure

## 🧪 Testing

All test files are in the `tests/` directory:
- `test_complete_workflow.py`
- `test_cv_parsing.py`
- `test_phase5.py`
- `test_question_generation.py`

## 📖 Documentation

All docs are in the `docs/` directory:
- System enhancement docs
- Current state documentation
- Multi-language documentation