# AI Interview System Enhancement Plan

## Overview
Transform the current interview system from generic questions to experience-focused, practical assessment with enhanced question generation based on CV analysis and job matching.

## Current Issues
- Questions only use partial CV content (first 3 responsibilities)
- No experience prioritization or scoring
- Algorithmic coding questions too complex for interviews
- Generic questions don't leverage full CV depth
- No answer-aware follow-up questioning

## New System Architecture

### Question Flow Structure (15 Total Questions)
```
Open Questions (5):
├── Q1: First experience (highest scored)
├── Q2: Follow-up on same experience (references Q1 answer)
├── Q3: Second experience (second highest scored)
├── Q4: Follow-up on same experience (references Q3 answer)
└── Q5: Job description requirements focus

QCM Questions (5): Technology rotation from experiences + job requirements
Coding Questions (5): Debug code + explain code from CV/job technologies
```

## PHASE 1: Experience Selection & Scoring System

### Step 1.1: Create `score_experiences()` function
**Purpose:** Rank CV experiences by job relevance
**Algorithm:**
```python
def score_experiences(experiences, job_description):
    for exp in experiences:
        # 50% technology/keyword matching
        tech_overlap_score = calculate_tech_overlap(exp.technologies, job_requirements)

        # 50% recency/duration scoring
        recency_score = calculate_recency_score(exp.start_date, exp.end_date)
        duration_score = calculate_duration_score(exp.duration)
        time_score = (recency_score + duration_score) / 2

        # Final weighted score
        final_score = (tech_overlap_score * 0.5) + (time_score * 0.5)

    return sorted_experiences_by_score
```

### Step 1.2: Create `select_top_experiences()` function
**Purpose:** Select top 2 experiences for questioning
**Logic:**
- Take top 2 from scoring
- Handle edge cases (1 experience CVs)
- Store selected experiences in interview state

## PHASE 2: Question Flow Structure Updates

### Step 2.1: Modify phase question counts
**Current:** 3 questions per phase
**New:** 5 questions per phase
**Changes:**
- Update `phase_question_count` initialization: `{"open": 0, "qcm": 0, "coding": 0}`
- Update phase transition logic in `generate_question()`:
  ```python
  if current_phase == "open" and phase_count >= 5:  # was 3
      state["current_phase"] = "qcm"
  elif current_phase == "qcm" and phase_count >= 5:  # was 3
      state["current_phase"] = "coding"
  elif current_phase == "coding" and phase_count >= 5:  # was 2
      return {"complete": True}
  ```

### Step 2.2: Update `generate_open_question()` flow
**New Question Mapping:**
- Q1: Focus on `selected_experiences[0]` (highest scored)
- Q2: Follow-up on same experience, reference Q1 answer
- Q3: Focus on `selected_experiences[1]` (second highest)
- Q4: Follow-up on same experience, reference Q3 answer
- Q5: Job requirements only (ignore CV experiences)

## PHASE 3: Enhanced Prompt System

### Step 3.1: Experience-specific prompt templates
**Current Approach:** Generic CV blob in prompts
**New Approach:** Targeted experience injection

**Individual Experience Context:**
```
FOCUSED EXPERIENCE:
Company: {company}
Position: {position}
Duration: {start_date} - {end_date} ({duration})
Key Achievements:
{all_responsibilities_without_truncation}
Technologies Used: {technologies}
Impact Metrics: {extract_metrics_from_responsibilities}
```

**Follow-up Question Prompt:**
```
CONTEXT: Candidate was asked about their {experience_company} {experience_position} role.

PREVIOUS QUESTION: "{previous_question}"
CANDIDATE'S RESPONSE: "{previous_answer}"

Generate a deeper follow-up question that:
1. References their specific answer
2. Explores technical implementation details
3. Asks about challenges and solutions
4. Focuses on {specific_technology} they mentioned

Question should be conversational and build on their response.
```

**Job-Focused Prompt (Q5):**
```
IGNORE THE CANDIDATE'S CV EXPERIENCES.

Focus ONLY on job requirements:
Required Skills: {job_technologies}
Company Context: {company_domain}
Role Expectations: {extracted_job_requirements}

Generate question about:
- How they would approach this role's challenges
- Their understanding of required technologies
- Fit for company's specific needs

Do not reference their past experiences.
```

### Step 3.2: Update context builders
**New Functions Needed:**
- `build_experience_context(experience)` - Single experience focus
- `build_followup_context(previous_q, previous_a, experience)` - Answer-aware
- `build_job_context(job_description)` - CV-independent

## PHASE 4: Coding Question Revolution

### Step 4.1: Debug code generation
**Replace:** Complex algorithmic challenges
**With:** Practical debugging tasks

**Debug Prompts by Difficulty:**
```python
# Easy (1 error) - Syntax/basic logic
debug_easy_prompt = """
Create a {language} code snippet (10-12 lines) using {cv_technology}.
Include exactly 1 logical error that would cause incorrect output.
Error should be: missing return, wrong operator, or off-by-one.
Code should solve a realistic problem from their experience domain.
"""

# Medium (2 errors) - Logic + edge case
debug_medium_prompt = """
Create a {language} code snippet (12-15 lines) using {cv_technology}.
Include exactly 2 errors: 1 logic error + 1 edge case handling.
Code should be more complex but still interview-appropriate.
"""

# Hard (3 errors) - Multiple logic issues
debug_hard_prompt = """
Create a {language} code snippet (15-20 lines) using {cv_technology}.
Include exactly 3 errors across logic, edge cases, and implementation.
Code should test deeper understanding but remain fixable in interview time.
"""
```

### Step 4.2: Code explanation prompts
**Replace:** "Implement algorithm X"
**With:** "Explain what this code does"

```python
explanation_prompt = """
Generate working {language} code (8-15 lines) using {cv_technology}.
Code should demonstrate a concept from their experience: {experience_context}.
Present code and ask:
1. "Explain what this code does step by step"
2. "What would happen if we change [specific line]?"
3. "How would you improve this code's performance/readability?"
"""
```

### Step 4.3: New parsing functions
**Replace:**
- `parse_algorithmic_response()`
- `parse_language_specific_response()`

**With:**
- `parse_debug_response()` - Extract code + errors + fixes
- `parse_explanation_response()` - Extract code + questions

## PHASE 5: Answer-Aware Follow-up System

### Step 5.1: Enhanced response storage
**Current:** Basic response tracking
**New:** Experience-mapped responses

```python
class EnhancedInterviewResponse(BaseModel):
    question_id: int
    response_text: str
    related_experience: Optional[str]  # Company + Position
    experience_index: Optional[int]   # 0 or 1 for top experiences
    question_type: str
    follow_up_context: Optional[str]  # For generating next question
```

### Step 5.2: Follow-up question logic
**Implementation:**
```python
def generate_followup_question(state, experience_index, previous_response):
    experience = state["selected_experiences"][experience_index]
    previous_answer = previous_response.response_text

    # Build context-aware prompt
    prompt = followup_prompt_template.format(
        experience_company=experience.company,
        experience_position=experience.position,
        previous_question=state["questions_history"][-1].question_text,
        previous_answer=previous_answer,
        specific_technology=get_relevant_technology(experience, previous_answer)
    )

    return llm.invoke(prompt)
```

## PHASE 6: Integration & Testing

### Step 6.1: Interview state management updates
**Add to InterviewState:**
```python
selected_experiences: List[WorkExperience]  # Top 2 experiences
experience_scores: Dict[str, float]         # Scoring results
current_experience_focus: Optional[int]     # 0, 1, or None (for job-focused)
answer_references: Dict[int, str]          # Question_id -> answer for follow-ups
```

### Step 6.2: Frontend updates for 15 questions
**Progress Indicators:**
- Update phase display: "Open Questions (3/5)" format
- Add experience focus indicators: "Focusing on: Metavoria Data Scientist role"
- Longer interview flow UX improvements

## Implementation Priority

### High Priority (Core Functionality)
1. ✅ Experience scoring and selection
2. ✅ Updated question flow (5 questions per phase)
3. ✅ Enhanced prompts with experience focus
4. ✅ Follow-up question logic with answer references

### Medium Priority (Quality Improvements)
5. ✅ Coding question transformation (debug + explain)
6. ✅ Job-focused questioning (CV-independent Q5)
7. ✅ Enhanced response tracking

### Low Priority (UX Polish)
8. ✅ Frontend progress indicators
9. ✅ Experience focus display
10. ✅ Interview summary enhancements

## Success Metrics
- Questions reference full CV content (not just first 3 responsibilities)
- Each of top 2 experiences gets focused attention (2 questions each)
- Follow-up questions meaningfully reference previous answers
- Coding questions are practical and completable in interview time
- Job description requirements are properly assessed independent of CV

## Progress Tracking
- [✅] Phase 1: Experience Selection & Scoring - COMPLETED
- [✅] Phase 2: Question Flow Updates - COMPLETED
- [✅] Phase 3: Enhanced Prompts - COMPLETED
- [✅] Phase 4: Coding Question Revolution - COMPLETED
- [ ] Phase 5: Answer-Aware Follow-ups
- [ ] Phase 6: Integration & Testing

---
*Last Updated: December 2024*
*Status: Phase 1-4 Complete, Ready for Phase 5-6 Implementation*

## IMPLEMENTATION NOTES - COMPLETED FEATURES

### ✅ Phase 1 Achievements:
- Experience scoring algorithm with 50% tech overlap + 50% time factors
- Intelligent top 2 experience selection
- Integration with interview initialization
- Comprehensive debug logging for scoring process

### ✅ Phase 2 Achievements:
- Extended interview from 8 to 15 questions (5 per phase)
- Experience-focused question mapping (Q1-Q2 on exp1, Q3-Q4 on exp2, Q5 job-focused)
- Answer-aware follow-up question infrastructure
- Enhanced context builders for single experience, follow-ups, and job-only focus
- Technology extraction from candidate responses

### ✅ Phase 3 Achievements:
- Enhanced interview_prompts.yaml with experience-focused templates
- New prompt templates: initial_experience_prompt, followup_experience_prompt, job_focused_prompt
- Updated debug_prompt and explanation_prompt for coding questions
- Enhanced technology extraction with domain-specific patterns (AI/ML, web dev, data science, etc.)
- Comprehensive technology categorization covering 8+ domains

### ✅ Phase 4 Achievements:
- Revolutionary coding question system replacing algorithmic challenges
- New Pydantic models: DebugCodingQuestion and ExplanationCodingQuestion
- Debug questions: inject 1-3 realistic bugs based on difficulty level
- Explanation questions: analyze working code from candidate's domain
- Technology-focused code generation using candidate's CV technologies
- Error injection system: syntax → logic → architecture based on difficulty
- Comprehensive parsing functions for new question formats
- Updated frontend response handling for coding_debug and coding_explain types