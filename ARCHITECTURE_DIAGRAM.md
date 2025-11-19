# Job-Centric Coding Interview System - Architecture

## System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          1. CV UPLOAD & PARSING                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                        ┌──────────────────────────┐
                        │  Parse CV using LLM      │
                        │  Extract:                │
                        │  - Skills                │
                        │  - Technologies          │
                        │  - Experience            │
                        └──────────────────────────┘
                                      │
                                      ▼
                        ┌──────────────────────────┐
                        │  Save structured_cv.json │
                        └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    2. JOB DESCRIPTION ANALYSIS (NEW!)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  analyze_job_description_skills()      │
                  │  (job_skill_analyzer.py)               │
                  │                                        │
                  │  LLM extracts and ranks skills:        │
                  │  ┌──────────────────────────────────┐ │
                  │  │ Skill: SQL                       │ │
                  │  │ Rank: 1 (critical)               │ │
                  │  │ Proficiency: expert              │ │
                  │  │ Category: database               │ │
                  │  │ Context: "must have expert SQL"  │ │
                  │  └──────────────────────────────────┘ │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  JobSkillAnalysis Object:              │
                  │  - primary_skills: [SQL, Python]       │
                  │  - secondary_skills: [Docker]          │
                  │  - database_requirement: {             │
                  │      has_db_requirement: True          │
                  │      db_technologies: [SQL, Postgres]  │
                  │      complexity_level: expert          │
                  │    }                                   │
                  │  - job_level: senior                   │
                  │  - overall_difficulty: 8               │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  Save structured_skills.json           │
                  └────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    3. QUESTION DISTRIBUTION PLANNING (NEW!)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  build_skill_difficulty_map()          │
                  │                                        │
                  │  Maps each skill to job-required       │
                  │  difficulty level:                     │
                  │                                        │
                  │  {                                     │
                  │    "sql": 10,  ← expert level required │
                  │    "python": 5, ← intermediate         │
                  │    "docker": 2  ← basic familiarity    │
                  │  }                                     │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  create_question_distribution_plan()   │
                  │                                        │
                  │  2-1-1-1 Distribution Strategy:        │
                  │                                        │
                  │  Q1: SQL (diff 10, type: db_schema)    │
                  │  Q2: SQL (diff 10, type: debug)        │
                  │  Q3: Python (diff 5, type: debug)      │
                  │  Q4: Docker (diff 2, type: explain)    │
                  │  Q5: SQL (diff 10, type: db_schema)    │
                  │      ↑ CV verification question        │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  CodingInterviewState created with:    │
                  │  - job_skill_analysis                  │
                  │  - question_distribution plan          │
                  │  - skill_difficulty_map                │
                  └────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    4. QUESTION GENERATION (ENHANCED!)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  generate_coding_question(state, n)    │
                  │                                        │
                  │  Gets plan for question N:             │
                  │  question_distribution[N]              │
                  └────────────────────────────────────────┘
                                      │
                        ┌─────────────┴──────────────┐
                        │                            │
                        ▼                            ▼
        ┌───────────────────────────┐   ┌───────────────────────────┐
        │  Question Type: db_schema │   │  Question Type: debug     │
        └───────────────────────────┘   │  or explain               │
                        │                └───────────────────────────┘
                        ▼                            │
        ┌───────────────────────────┐               │
        │  generate_db_schema_      │               ▼
        │  question()               │   ┌───────────────────────────┐
        │                           │   │  generate_debug_question()│
        │  Uses db_schema_prompt:   │   │  or                       │
        │  - Scenario-based         │   │  generate_explanation_    │
        │  - Schema design          │   │  question()               │
        │  - Query optimization     │   │                           │
        │  - Complexity based on    │   │  Uses enhanced prompts:   │
        │    job difficulty         │   │  - Skill importance       │
        └───────────────────────────┘   │  - Proficiency level      │
                                        │  - Job-centric difficulty │
                                        └───────────────────────────┘
                        │                            │
                        └─────────────┬──────────────┘
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  InterviewQuestion object:             │
                  │  - question_type                       │
                  │  - difficulty_level (from job needs)   │
                  │  - technology_focus (from job ranking) │
                  │  - question_data (debug/explain/db)    │
                  └────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         5. RESPONSE HANDLING                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  Frontend receives question with:      │
                  │                                        │
                  │  For db_schema:                        │
                  │  - scenario                            │
                  │  - requirements                        │
                  │  - task_description                    │
                  │  - expected_deliverable                │
                  │  - db_technology                       │
                  │                                        │
                  │  For debug:                            │
                  │  - buggy_code                          │
                  │  - expected_behavior                   │
                  │                                        │
                  │  For explain:                          │
                  │  - working_code                        │
                  │  - analysis_questions                  │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  User submits response                 │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  Save to code-test-{name}-{date}.json  │
                  └────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │  Generate next question (repeat from 4)│
                  └────────────────────────────────────────┘
```

## Key Components

### Job Skill Analyzer (`job_skill_analyzer.py`)
```python
analyze_job_description_skills(job_desc) → JobSkillAnalysis
    ↓
    Uses LLM to extract:
    - Skill names
    - Importance rankings (1-5)
    - Required proficiency levels
    - Database requirements
    - Job level (junior/mid/senior/principal)
    ↓
    Returns structured analysis
```

### Question Planner (`coding_question_generator.py`)
```python
create_question_distribution_plan(job_analysis, cv_techs)
    ↓
    Implements 2-1-1-1 strategy:
    Q1-Q2: Top skill (importance rank 1)
    Q3: Second skill (importance rank 2)
    Q4: Third/fourth skill
    Q5: Job+CV intersection (verify claims)
    ↓
    Returns {1: {skill, difficulty, type}, ...}
```

### Question Generator (`coding_question_generator.py`)
```python
generate_coding_question(state, question_num)
    ↓
    Gets plan: question_distribution[question_num]
    ↓
    Routes based on type:
    - db_schema → generate_db_schema_question()
    - debug → generate_debug_question()
    - explain → generate_explanation_question()
    ↓
    Each uses job-centric difficulty
    ↓
    Returns InterviewQuestion
```

## Data Flow Example

### Input: Job Description
```
Senior Backend Developer - SQL Focus

Required:
- Expert-level SQL (PostgreSQL)
- Strong Python for backend services
- Docker knowledge is a plus
```

### Step 1: Skill Analysis Output
```json
{
  "primary_skills": [
    {
      "skill_name": "SQL",
      "importance_rank": 1,
      "required_proficiency_level": "expert",
      "category": "database"
    },
    {
      "skill_name": "Python",
      "importance_rank": 2,
      "required_proficiency_level": "advanced",
      "category": "programming_language"
    }
  ],
  "database_requirement": {
    "has_db_requirement": true,
    "db_technologies": ["SQL", "PostgreSQL"],
    "complexity_level": "expert"
  },
  "job_level": "senior",
  "overall_difficulty": 8
}
```

### Step 2: Skill Difficulty Map
```json
{
  "sql": 10,      // expert level (9) + critical rank (1) = 10
  "python": 7,    // advanced level (7)
  "docker": 2     // basic level (3) - nice-to-have (4) = 2
}
```

### Step 3: Question Distribution Plan
```json
{
  "1": {
    "skill_name": "SQL",
    "difficulty": 10,
    "question_type": "db_schema",
    "importance_rank": 1
  },
  "2": {
    "skill_name": "SQL",
    "difficulty": 10,
    "question_type": "debug",
    "importance_rank": 1
  },
  "3": {
    "skill_name": "Python",
    "difficulty": 7,
    "question_type": "debug",
    "importance_rank": 2
  },
  "4": {
    "skill_name": "Docker",
    "difficulty": 2,
    "question_type": "explain",
    "importance_rank": 4
  },
  "5": {
    "skill_name": "SQL",
    "difficulty": 10,
    "question_type": "db_schema",
    "cv_verification": true
  }
}
```

### Step 4: Generated Question Example (Q1)
```json
{
  "question_id": 1,
  "question_type": "db_schema",
  "question_text": "Database Challenge: E-commerce Order Management System",
  "difficulty_level": 10,
  "technology_focus": "SQL",
  "db_schema_data": {
    "title": "E-commerce Order Management System",
    "scenario": "Design a database for an e-commerce platform...",
    "requirements": [
      "Track customers, orders, products, and inventory",
      "Handle complex queries for order history",
      "Optimize for high-volume transactions"
    ],
    "task_description": "Design a normalized schema with proper constraints...",
    "expected_deliverable": "SQL CREATE statements with indexes and foreign keys",
    "db_technology": "SQL",
    "complexity_level": "expert"
  }
}
```

## Benefits Visualization

```
Traditional Approach (CV-Based):
┌────────────────────────────────────────┐
│ Candidate CV: Junior in SQL            │
│ Job Needs: Expert SQL                  │
│                                        │
│ ❌ Questions: Easy SQL (3/10)          │
│ ❌ Result: Can't assess true capability│
└────────────────────────────────────────┘

New Approach (Job-Based):
┌────────────────────────────────────────┐
│ Candidate CV: Junior in SQL            │
│ Job Needs: Expert SQL                  │
│                                        │
│ ✅ Questions: Expert SQL (10/10)       │
│ ✅ Result: True capability revealed     │
│ ✅ Tests if CV claims are accurate     │
└────────────────────────────────────────┘
```
