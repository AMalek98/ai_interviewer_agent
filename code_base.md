# AI Interviewer - Codebase Structure

```
ai_interviewer/
│
├── README.md
├── ARCHITECTURE.md
├── ARCHITECTURE_DIAGRAM.md
├── code_base.md
│
├── backend/
│   ├── main.py
│   │
│   ├── text_interview/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── managers.py
│   │   ├── generators.py
│   │   ├── processors.py
│   │   └── utils.py
│   │
│   ├── oral_interview/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── question_generator.py
│   │   ├── utils.py
│   │   └── evaluator/
│   │       ├── __init__.py
│   │       ├── engine.py
│   │       ├── models.py
│   │       └── response_evaluator.py
│   │
│   ├── coding_interview/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── question_generator.py
│   │   ├── job_skill_analyzer.py
│   │   ├── test_case_generator.py
│   │   ├── utils.py
│   │   └── evaluator/
│   │       ├── __init__.py
│   │       ├── engine.py
│   │       ├── piston_compiler.py
│   │       └── output_comparator.py
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── llm_setup.py
│   │   ├── information_extraction.py
│   │   ├── cv_analysis.py
│   │   └── config.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluation_engine.py
│   │   ├── evaluation_models.py
│   │   ├── qcm_evaluator.py
│   │   ├── open_question_evaluator.py
│   │   ├── oral_response_evaluator.py
│   │   └── oral_evaluator.py
│   │
│   ├── config/
│   │   ├── .env
│   │   ├── interview_prompts.yaml
│   │   ├── oral_system_prompts.yaml
│   │   ├── coding_prompts.yaml
│   │   ├── evaluation_prompts.yaml
│   │   └── oral_evaluation_prompts.yaml
│   │
│   └── data/
│       ├── uploads/
│       ├── interviews/
│       │   ├── text/
│       │   ├── oral/
│       │   └── coding/
│       ├── evaluation_reports/
│       │   ├── text/
│       │   ├── oral/
│       │   └── coding/
│       └── security_logs/
│
├── frontend/
│   ├── index.html
│   ├── coding.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── README.md
│   │
│   └── src/
│       ├── main.jsx
│       ├── Router.jsx
│       ├── App.jsx
│       ├── OralInterview.jsx
│       ├── CodingInterviewer.jsx
│       ├── coding-main.jsx
│       ├── index.css
│       ├── App.css
│       ├── components/
│       │   └── security/
│       │       ├── index.js
│       │       ├── SecurityMonitor.jsx
│       │       ├── WarningModal.jsx
│       │       ├── WarningBanner.jsx
│       │       └── DisqualificationScreen.jsx
│       └── utils/
│           └── languageMapper.js
│
├── uploads/
├── static/
├── docs/
├── tests/
└── archive/
```
