"""Text Interview - Question Generation

Handles:- Question generation orchestration- Open question generation- QCM/MCQ question generation- Reference answer generation- Context building (domain-technical and generic)"""

from datetime import datetime
from typing import Dict, Any, List, Optional

# Import from shared module
from shared.models import (
    InterviewState, InterviewQuestion, QCMQuestion, QCMOption,
    StructuredJobDescription, StructuredCV, WorkExperience
)

from shared.llm_setup import get_llm

# Import from sibling modules
from .managers import get_prompt_template
from .utils import (    get_difficulty_description, extract_technologies_from_answer,    extract_key_topics_from_answer, clean_generated_question,    extract_metrics_from_responsibilities)

# Get LLM instance
llm = get_llm()


def generate_question(state: InterviewState) -> Dict[str, Any]:
    """Generate the next interview question based on current phase and progress"""

    # Check if we should move to next phase or complete interview
    current_phase = state["current_phase"]
    phase_count = state["phase_question_count"][current_phase]

    # PHASE 2: Updated phase transition logic (5 questions per phase)
    if current_phase == "open" and phase_count >= 5:
        # Move to QCM phase
        state["current_phase"] = "qcm"
        current_phase = "qcm"
        phase_count = 0
        print("=== Transitioning to QCM Phase ===")
    elif current_phase == "qcm" and phase_count >= 5:
        # Complete interview after QCM (coding moved to separate agent)
        print("=== Interview Complete (Coding questions available in separate agent) ===")
        return {"complete": True}

    # Generate question based on current phase
    question_id = state["total_question_count"] + 1

    if current_phase == "open":
        question = generate_open_question(state, phase_count + 1)
    elif current_phase == "qcm":
        question = generate_qcm_question(state, phase_count + 1)
    else:
        return {"complete": True}

    # Update state
    state["phase_question_count"][current_phase] += 1
    state["total_question_count"] += 1
    state["current_question"] = question
    state["questions_history"].append(question)

    return {
        "current_question": question,
        "complete": False,
        "phase": current_phase,
        "question_count": question_id
    }
def generate_reference_answer(
    question_text: str,
    structured_job: StructuredJobDescription,
    technology_focus: str,
    difficulty_score: int,
    difficulty_desc: str
) -> str:
    """
    Generate a reference answer (best possible response) for an open question.
    This will be used during evaluation to compare against candidate's response.

    Args:
        question_text: The interview question
        structured_job: Job description with requirements
        technology_focus: Technology the question focuses on
        difficulty_score: Difficulty level 1-10
        difficulty_desc: Human-readable difficulty description

    Returns:
        Reference answer text (150-300 words)
    """
    # Build job context for reference answer
    if structured_job.industry and (structured_job.business_context or structured_job.domain_specific_challenges):
        # Domain-technical context
        job_context = build_domain_technical_context(structured_job, technology_focus)
    else:
        # Generic job context
        job_context = build_generic_job_technical_context(structured_job, technology_focus)

    # Get reference answer prompt template
    prompt_template = get_prompt_template("open_questions", "reference_answer_generation_prompt") or """
Generate the BEST POSSIBLE RESPONSE to this interview question.

QUESTION: {question_text}

JOB CONTEXT:
- Position: {job_title}
- Seniority: {seniority_level}
- Technology Focus: {technology_focus}
- Difficulty Level: {difficulty_level}/10 ({difficulty_description})

{job_context}

Generate a comprehensive, technically accurate reference answer (150-300 words) that demonstrates expert-level understanding appropriate for this difficulty level.
"""

    formatted_prompt = prompt_template.format(
        question_text=question_text,
        job_title=structured_job.job_title,
        seniority_level=structured_job.seniority_level,
        technology_focus=technology_focus,
        difficulty_level=difficulty_score,
        difficulty_description=difficulty_desc,
        job_context=job_context
    )

    # Generate reference answer using LLM
    response = llm.invoke(formatted_prompt)
    reference_answer = response.content.strip()

    return reference_answer
def generate_open_question(state: InterviewState, question_number: int) -> InterviewQuestion:
    """Generate a job-focused open-ended interview question (domain-technical when possible)"""

    difficulty_score = state["difficulty_score"]
    difficulty_desc = get_difficulty_description(difficulty_score)
    structured_job = state["structured_job"]

    # Select technology focus for this question
    technology_focus = select_technology_for_question(structured_job, question_number)
    state["current_technology_focus"] = technology_focus

    # Determine if we should use domain-technical or generic prompts
    has_industry_context = (structured_job.industry is not None and
                           (len(structured_job.business_context) > 0 or
                            len(structured_job.domain_specific_challenges) > 0))

    print(f"=== Generating Open Question {question_number}/5 ===")
    print(f"Technology Focus: {technology_focus}")
    print(f"Industry Context: {'Yes' if has_industry_context else 'No (Generic)'}")

    if question_number == 1:
        # Q1: Initial job-focused technical question
        print("Q1: Initial job-focused technical question")

        if has_industry_context:
            # Domain-technical question
            job_context = build_domain_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "domain_technical_question_prompt") or """
Generate a domain-specific technical question for a {job_title} in the {industry} industry.

{job_context}

Technology Focus: {technology_focus}
Difficulty: {difficulty_description}

Generate a question that:
- Combines {technology_focus} with {industry} real-world scenarios
- Tests practical knowledge needed for THIS role
- Does NOT reference candidate's CV
- Is appropriate for {difficulty_description} level

Example format: "How would you handle [specific challenge] using {technology_focus} in [industry context]?"
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                industry=structured_job.industry,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )
        else:
            # Generic technical question
            job_context = build_generic_job_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "generic_job_technical_prompt") or """
Generate a technical question about {technology_focus} for a {job_title} position.

{job_context}

Question should:
- Test {technology_focus} knowledge needed for THIS role
- Be appropriate for {difficulty_description} level
- Focus on practical application
- Does NOT reference candidate's CV
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )

    elif question_number == 2:
        # Q2: Follow-up on Q1 answer (job-focused)
        print("Q2: Follow-up on Q1 (job-focused)")

        if state["responses_history"]:
            previous_question = state["questions_history"][-1].question_text
            previous_answer = state["responses_history"][-1].response_text

            followup_context = build_job_focused_followup_context(
                previous_question, previous_answer, structured_job, technology_focus
            )

            prompt_template = get_prompt_template("open_questions", "followup_job_technical_prompt") or """
Generate a follow-up question based on their previous answer about THIS ROLE.

{followup_context}

Dig deeper into technical details they mentioned, but stay focused on the ROLE requirements.
"""
            formatted_prompt = prompt_template.format(followup_context=followup_context)
        else:
            formatted_prompt = f"Can you explain how you would implement {technology_focus} for this role?"

    elif question_number == 3:
        # Q3: Different technology/requirement focus
        print("Q3: Different technology focus")

        if has_industry_context:
            # Domain-technical question
            job_context = build_domain_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "domain_technical_question_prompt") or """
Generate a domain-specific technical question for a {job_title} in the {industry} industry.

{job_context}

Technology Focus: {technology_focus}
Difficulty: {difficulty_description}

Generate a question that combines {technology_focus} with {industry} scenarios.
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                industry=structured_job.industry,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )
        else:
            # Generic technical question
            job_context = build_generic_job_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "generic_job_technical_prompt") or """
Generate a technical question about {technology_focus} for a {job_title} position.

{job_context}

Test practical {technology_focus} knowledge for THIS role at {difficulty_description} level.
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )

    elif question_number == 4:
        # Q4: Follow-up on Q3 answer (job-focused)
        print("Q4: Follow-up on Q3 (job-focused)")

        if len(state["responses_history"]) >= 3:
            previous_question = state["questions_history"][-1].question_text
            previous_answer = state["responses_history"][-1].response_text

            followup_context = build_job_focused_followup_context(
                previous_question, previous_answer, structured_job, technology_focus
            )

            prompt_template = get_prompt_template("open_questions", "followup_job_technical_prompt") or """
Generate a follow-up question based on their previous answer about THIS ROLE.

{followup_context}

Explore deeper technical aspects related to the job requirements.
"""
            formatted_prompt = prompt_template.format(followup_context=followup_context)
        else:
            formatted_prompt = f"What challenges might you face implementing {technology_focus} in this role?"

    elif question_number == 5:
        # Q5: Job requirements focus (as before, but now consistent with Q1-Q4)
        print("Q5: Job requirements focus")

        if has_industry_context:
            job_context = build_domain_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "domain_technical_question_prompt") or """
Generate a domain-specific technical question for a {job_title} in the {industry} industry.

{job_context}

Focus on {technology_focus} and how they would approach this role's challenges.
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                industry=structured_job.industry,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )
        else:
            job_context = build_generic_job_technical_context(structured_job, technology_focus)
            prompt_template = get_prompt_template("open_questions", "generic_job_technical_prompt") or """
Generate a technical question about {technology_focus} for THIS {job_title} role.

{job_context}

Focus on practical problem-solving for this position.
"""
            formatted_prompt = prompt_template.format(
                job_title=structured_job.job_title,
                job_context=job_context,
                technology_focus=technology_focus,
                difficulty_level=difficulty_score,
                difficulty_description=difficulty_desc
            )

    else:
        # Fallback for unexpected question numbers
        formatted_prompt = f"How would you approach {technology_focus} challenges in a {structured_job.job_title} role?"

    # Generate question using LLM
    response = llm.invoke(formatted_prompt)
    question_text = clean_generated_question(response.content)

    # Generate reference answer (best possible response) for evaluation
    print(f"Generating reference answer for question...")
    reference_answer = generate_reference_answer(
        question_text=question_text,
        structured_job=structured_job,
        technology_focus=technology_focus,
        difficulty_score=difficulty_score,
        difficulty_desc=difficulty_desc
    )
    print(f"Reference answer generated ({len(reference_answer)} characters)")

    return InterviewQuestion(
        question_id=state["total_question_count"] + 1,
        question_type="open",
        question_text=question_text,
        difficulty_level=difficulty_score,
        technology_focus=technology_focus,  # Now tracks job technology focus
        reference_answer=reference_answer,  # Store reference answer for evaluation
        timestamp=datetime.now().isoformat()
    )
def generate_qcm_question(state: InterviewState, question_number: int) -> InterviewQuestion:
    """Generate a technical multiple choice question focused on job requirements

    Questions 1-2: Multiple-choice (MCQ) - multiple correct answers
    Questions 3-5: Single-choice (QCM) - one correct answer
    """

    difficulty_score = state["difficulty_score"]
    difficulty_desc = get_difficulty_description(difficulty_score)
    structured_job = state["structured_job"]

    # Determine if this should be a multiple-choice question
    is_multiple_choice = question_number <= 2  # Q1-Q2 are MCQ, Q3-Q5 are single-choice

    # Select technology focus from JOB requirements (not matched technologies)
    # Rotate through required_skills + technologies
    all_job_tech = structured_job.required_skills + structured_job.technologies

    # Remove duplicates while preserving order
    seen = set()
    unique_job_tech = []
    for tech in all_job_tech:
        tech_lower = tech.lower()
        if tech_lower not in seen:
            seen.add(tech_lower)
            unique_job_tech.append(tech)

    # Select technology for this question
    if unique_job_tech:
        tech_index = (question_number - 1) % len(unique_job_tech)
        technology_focus = unique_job_tech[tech_index]
    else:
        technology_focus = "general programming"

    # Build job-focused context (NO CV CONTEXT)
    job_context = build_qcm_job_context(structured_job)

    # Use appropriate prompt template based on question type
    if is_multiple_choice:
        prompt_template = get_prompt_template("qcm_questions", "multiple_choice_generation_prompt")
    else:
        prompt_template = get_prompt_template("qcm_questions", "job_focused_generation_prompt")

    formatted_prompt = prompt_template.format(
        job_title=structured_job.job_title,
        seniority_level=structured_job.seniority_level,
        domain=structured_job.domain,
        industry=structured_job.industry or "general",
        technology_focus=technology_focus,
        required_skills=", ".join(structured_job.required_skills[:10]) if structured_job.required_skills else "various skills",
        technologies=", ".join(structured_job.technologies[:15]) if structured_job.technologies else "various technologies",
        job_context=job_context,
        difficulty_level=difficulty_score,
        difficulty_description=difficulty_desc
    )

    question_type_label = "MCQ (Multiple-Choice)" if is_multiple_choice else "QCM (Single-Choice)"
    print(f"=== Generating {question_type_label} Question {question_number}/5 ===")
    print(f"Technology Focus: {technology_focus}")
    print(f"Difficulty: {difficulty_score} ({difficulty_desc})")

    # Generate QCM/MCQ using LLM with STRUCTURED OUTPUT
    # This forces the LLM to return data in our exact QCMQuestion schema
    try:
        llm_with_structure = llm.with_structured_output(QCMQuestion)
        qcm_data = llm_with_structure.invoke(formatted_prompt)

        # Set technology_focus and is_multiple_choice since they may not be in the prompt
        qcm_data.technology_focus = technology_focus
        qcm_data.is_multiple_choice = is_multiple_choice

        # For MCQ, ensure correct_answers is populated
        if is_multiple_choice and qcm_data.correct_answers:
            print(f"✅ MCQ generated successfully with {len(qcm_data.options)} options and {len(qcm_data.correct_answers)} correct answers")
        else:
            print(f"✅ QCM generated successfully with {len(qcm_data.options)} options")

    except Exception as e:
        print(f"❌ Error generating structured {'MCQ' if is_multiple_choice else 'QCM'}: {e}")
        print("Falling back to default question")

        # Fallback question based on question type
        if is_multiple_choice:
            qcm_data = QCMQuestion(
                question=f"Which of the following are important aspects of {technology_focus}? (Select ALL that apply)",
                options=[
                    QCMOption(option="A", text="Following best practices and design patterns"),
                    QCMOption(option="B", text="Writing comprehensive documentation"),
                    QCMOption(option="C", text="Implementing proper error handling"),
                    QCMOption(option="D", text="Skipping code reviews to save time")
                ],
                correct_answer="A",  # Kept for backward compatibility
                correct_answers=["A", "B", "C"],
                is_multiple_choice=True,
                explanation="Options A, B, and C are all important aspects of professional development. Code reviews (option D) should not be skipped.",
                technology_focus=technology_focus
            )
        else:
            qcm_data = QCMQuestion(
                question=f"What is a key concept in {technology_focus}?",
                options=[
                    QCMOption(option="A", text="Following best practices and design patterns"),
                    QCMOption(option="B", text="Ignoring code quality standards"),
                    QCMOption(option="C", text="Writing code without documentation"),
                    QCMOption(option="D", text="Avoiding testing and validation")
                ],
                correct_answer="A",
                is_multiple_choice=False,
                explanation="Following best practices and design patterns is essential for maintainable, scalable code.",
                technology_focus=technology_focus
            )

    return InterviewQuestion(
        question_id=state["total_question_count"] + 1,
        question_type="qcm",
        question_text=qcm_data.question,
        difficulty_level=difficulty_score,
        technology_focus=technology_focus,
        qcm_data=qcm_data,
        timestamp=datetime.now().isoformat()
    )
def build_single_experience_context(experience: WorkExperience) -> str:
    """Build focused context for a single experience with full details"""
    context = "=== FOCUSED EXPERIENCE ===\n"

    context += f"Company: {experience.company}\n"
    context += f"Position: {experience.position}\n"

    # Duration information
    if experience.start_date or experience.end_date:
        context += f"Duration: {experience.start_date or 'Unknown'} - {experience.end_date or 'Unknown'}"
        if experience.duration:
            context += f" ({experience.duration})\n"
        else:
            context += "\n"
    elif experience.duration:
        context += f"Duration: {experience.duration}\n"

    # All responsibilities without truncation
    if experience.responsibilities:
        context += "\nKey Achievements & Responsibilities:\n"
        for i, responsibility in enumerate(experience.responsibilities, 1):
            context += f"{i}. {responsibility}\n"

        # Extract metrics from responsibilities
        metrics = extract_metrics_from_responsibilities(experience.responsibilities)
        if metrics:
            context += f"\nImpact Metrics: {', '.join(metrics)}\n"

    # Technologies used
    if experience.technologies:
        context += f"\nTechnologies Used: {', '.join(experience.technologies)}\n"

    return context
def build_followup_context(previous_question: str, previous_answer: str, experience: WorkExperience) -> str:
    """Build context for answer-aware follow-up questions"""
    context = "=== FOLLOW-UP CONTEXT ===\n"

    context += f"EXPERIENCE FOCUS: {experience.position} role at {experience.company}\n\n"
    context += f"PREVIOUS QUESTION: \"{previous_question}\"\n\n"
    context += f"CANDIDATE'S RESPONSE: \"{previous_answer}\"\n\n"

    # Extract technologies mentioned in the previous answer
    mentioned_technologies = extract_technologies_from_answer(previous_answer, experience.technologies)
    if mentioned_technologies:
        context += f"TECHNOLOGIES MENTIONED: {', '.join(mentioned_technologies)}\n\n"

    # Provide guidance for follow-up
    context += "FOLLOW-UP GUIDANCE:\n"
    context += "1. Reference their specific answer\n"
    context += "2. Explore technical implementation details\n"
    context += "3. Ask about challenges and solutions\n"
    context += "4. Focus on technologies they mentioned\n"
    context += "5. Keep question conversational and build on their response\n"

    return context
def build_job_only_context_from_structured(structured_job: StructuredJobDescription) -> str:
    """Build context focusing purely on job requirements using structured job description"""
    context = "=== JOB-FOCUSED CONTEXT ===\n"
    context += "IGNORE THE CANDIDATE'S CV EXPERIENCES.\n\n"

    context += f"ROLE REQUIREMENTS:\n"
    context += f"Job Title: {structured_job.job_title}\n"

    if structured_job.required_skills:
        context += f"Required Skills: {', '.join(structured_job.required_skills)}\n"

    if structured_job.preferred_skills:
        context += f"Preferred Skills: {', '.join(structured_job.preferred_skills)}\n"

    context += f"Seniority Level: {structured_job.seniority_level}\n"
    context += f"Domain: {structured_job.domain}\n"

    if structured_job.experience_years:
        context += f"Required Experience: {structured_job.experience_years} years\n"

    if structured_job.responsibilities:
        context += f"\nKEY RESPONSIBILITIES:\n"
        for resp in structured_job.responsibilities[:5]:  # Limit to top 5
            context += f"- {resp}\n"

    if structured_job.technologies:
        context += f"\nTECHNOLOGIES: {', '.join(structured_job.technologies)}\n"

    context += "\nQUESTION FOCUS:\n"
    context += "- How they would approach this role's challenges\n"
    context += "- Their understanding of required technologies\n"
    context += "- Fit for company's specific needs\n"
    context += "- Problem-solving approach for this domain\n"
    context += "\nDo NOT reference their past experiences.\n"

    return context
def build_qcm_job_context(structured_job: StructuredJobDescription) -> str:
    """Build context for QCM questions from job description only"""
    context = "=== JOB REQUIREMENTS FOR QCM ===\n"
    context += f"Position: {structured_job.job_title}\n"
    context += f"Seniority: {structured_job.seniority_level}\n"
    context += f"Domain: {structured_job.domain}\n\n"

    if structured_job.required_skills:
        context += "REQUIRED SKILLS:\n"
        for skill in structured_job.required_skills[:10]:
            context += f"- {skill}\n"
        context += "\n"

    if structured_job.technologies:
        context += "TECHNOLOGIES:\n"
        for tech in structured_job.technologies[:15]:
            context += f"- {tech}\n"
        context += "\n"

    if structured_job.responsibilities:
        context += "KEY RESPONSIBILITIES:\n"
        for resp in structured_job.responsibilities[:5]:
            context += f"- {resp}\n"
        context += "\n"

    return context
def select_technology_for_question(structured_job: StructuredJobDescription, question_number: int) -> str:
    """
    Select technology focus for open question based on job requirements.
    Rotates through required_skills and technologies based on importance.

    Args:
        structured_job: Job description with requirements
        question_number: 1-5 for open questions

    Returns:
        Technology name to focus on
    """
    # Combine required_skills and technologies (required_skills have priority)
    all_techs = structured_job.required_skills + structured_job.technologies

    # Remove duplicates while preserving order
    seen = set()
    unique_techs = []
    for tech in all_techs:
        tech_lower = tech.lower()
        if tech_lower not in seen:
            seen.add(tech_lower)
            unique_techs.append(tech)

    if not unique_techs:
        return "general technical skills"

    # Select technology based on question number (rotate through)
    # Q1 and Q2 use same tech, Q3 and Q4 use same tech, Q5 uses another
    if question_number in [1, 2]:
        tech_index = 0
    elif question_number in [3, 4]:
        tech_index = 1 if len(unique_techs) > 1 else 0
    else:  # Q5
        tech_index = 2 if len(unique_techs) > 2 else 0

    return unique_techs[tech_index]
def build_domain_technical_context(structured_job: StructuredJobDescription, technology_focus: str) -> str:
    """
    Build domain-technical context combining technology + industry + business problems.
    Used when industry/business_context are available.

    Args:
        structured_job: Job description with optional industry/business_context
        technology_focus: Technology to focus the question on

    Returns:
        Formatted context string for domain-technical prompts
    """
    context = "=== DOMAIN-TECHNICAL JOB CONTEXT ===\n"
    context += f"Position: {structured_job.job_title}\n"
    context += f"Seniority: {structured_job.seniority_level}\n"
    context += f"Industry: {structured_job.industry}\n"
    context += f"Domain: {structured_job.domain}\n"
    context += f"Technology Focus: {technology_focus}\n\n"

    if structured_job.business_context:
        context += "BUSINESS PROBLEMS/CONTEXT:\n"
        for problem in structured_job.business_context:
            context += f"- {problem}\n"
        context += "\n"

    if structured_job.domain_specific_challenges:
        context += "DOMAIN-SPECIFIC CHALLENGES:\n"
        for challenge in structured_job.domain_specific_challenges:
            context += f"- {challenge}\n"
        context += "\n"

    if structured_job.responsibilities:
        context += "KEY RESPONSIBILITIES:\n"
        for resp in structured_job.responsibilities[:5]:
            context += f"- {resp}\n"
        context += "\n"

    if structured_job.required_skills:
        context += f"REQUIRED SKILLS: {', '.join(structured_job.required_skills[:8])}\n\n"

    return context
def build_generic_job_technical_context(structured_job: StructuredJobDescription, technology_focus: str) -> str:
    """
    Build generic job-technical context (no industry/business context).
    Fallback when industry is not specified.

    Args:
        structured_job: Job description
        technology_focus: Technology to focus the question on

    Returns:
        Formatted context string for generic technical prompts
    """
    context = "=== JOB REQUIREMENTS CONTEXT ===\n"
    context += f"Position: {structured_job.job_title}\n"
    context += f"Seniority: {structured_job.seniority_level}\n"
    context += f"Domain: {structured_job.domain}\n"
    context += f"Technology Focus: {technology_focus}\n\n"

    if structured_job.required_skills:
        context += "REQUIRED SKILLS:\n"
        for skill in structured_job.required_skills[:10]:
            context += f"- {skill}\n"
        context += "\n"

    if structured_job.responsibilities:
        context += "KEY RESPONSIBILITIES:\n"
        for resp in structured_job.responsibilities[:5]:
            context += f"- {resp}\n"
        context += "\n"

    if structured_job.technologies:
        context += f"TECHNOLOGIES: {', '.join(structured_job.technologies[:10])}\n\n"

    return context
def build_job_focused_followup_context(previous_question: str, previous_answer: str,
                                       structured_job: StructuredJobDescription,
                                       technology_focus: str) -> str:
    """
    Build follow-up context based on previous answer and job requirements (no CV).

    Args:
        previous_question: The previous question asked
        previous_answer: Candidate's answer to previous question
        structured_job: Job description
        technology_focus: Current technology focus

    Returns:
        Formatted context for follow-up question generation
    """
    context = "=== JOB-FOCUSED FOLLOW-UP CONTEXT ===\n\n"
    context += f"PREVIOUS QUESTION: \"{previous_question}\"\n\n"
    context += f"CANDIDATE'S RESPONSE: \"{previous_answer}\"\n\n"

    # Analyze their answer
    extracted_technologies = extract_technologies_from_answer(previous_answer, [])
    key_topics = extract_key_topics_from_answer(previous_answer)

    if extracted_technologies:
        context += f"TECHNOLOGIES MENTIONED: {', '.join(extracted_technologies[:5])}\n"

    if key_topics:
        context += f"KEY TOPICS DISCUSSED: {', '.join(key_topics[:5])}\n"

    context += "\n=== JOB REQUIREMENTS CONTEXT ===\n"
    context += f"Position: {structured_job.job_title}\n"
    context += f"Technology Focus: {technology_focus}\n"

    if structured_job.industry:
        context += f"Industry: {structured_job.industry}\n"

    if structured_job.business_context:
        context += f"Business Context: {', '.join(structured_job.business_context[:3])}\n"

    context += "\n=== FOLLOW-UP STRATEGY ===\n"
    context += "Generate a deeper technical question that:\n"
    context += "1. References specific details from their answer\n"
    context += "2. Digs into technical implementation for THIS role\n"
    context += "3. Explores challenges specific to this job's requirements\n"
    context += "4. Tests deeper understanding of technologies they mentioned\n"
    context += "5. Maintains focus on the JOB requirements, not their past experience\n"

    return context
def build_enhanced_followup_context(previous_question: str, previous_answer: str, experience: WorkExperience) -> str:
    """Build enhanced context for answer-aware follow-up questions"""
    context = "=== ENHANCED FOLLOW-UP CONTEXT ===\n"

    context += f"EXPERIENCE FOCUS: {experience.position} role at {experience.company}\n\n"
    context += f"PREVIOUS QUESTION: \"{previous_question}\"\n\n"
    context += f"CANDIDATE'S RESPONSE: \"{previous_answer}\"\n\n"

    # Enhanced answer analysis
    mentioned_technologies = extract_technologies_from_answer(previous_answer, experience.technologies)
    key_topics = extract_key_topics_from_answer(previous_answer)

    if mentioned_technologies:
        context += f"TECHNOLOGIES MENTIONED: {', '.join(mentioned_technologies)}\n"

    if key_topics:
        context += f"KEY TOPICS DISCUSSED: {', '.join(key_topics)}\n"

    context += "\n=== FOLLOW-UP STRATEGY ===\n"

    # Provide specific guidance based on what was mentioned
    if 'challenges' in key_topics:
        context += "• Candidate mentioned challenges - ask for deeper technical details about how they were resolved\n"
    if 'solutions' in key_topics:
        context += "• Candidate described solutions - explore the technical implementation or alternative approaches\n"
    if 'improvements' in key_topics:
        context += "• Candidate discussed improvements - ask about specific metrics or how they measured success\n"
    if 'quantifiable_results' in key_topics:
        context += "• Candidate provided metrics - ask about the methodology behind achieving these results\n"
    if mentioned_technologies:
        context += f"• Focus questions on: {mentioned_technologies[0]} (most relevant technology mentioned)\n"

    context += "\nFOLLOW-UP QUESTION SHOULD:\n"
    context += "1. Reference specific parts of their answer (use quotes when appropriate)\n"
    context += "2. Dig deeper into technical implementation details they mentioned\n"
    context += "3. Ask about challenges, trade-offs, or alternative approaches\n"
    context += "4. Explore the 'how' and 'why' behind their technical decisions\n"
    context += "5. Maintain conversational flow and show active listening\n"

    return context
def build_cv_context(structured_cv: StructuredCV) -> str:
    """Build structured CV context for prompts"""
    if not structured_cv:
        return "No CV data available"

    cv_context = "=== STRUCTURED CV DATA ===\n"

    # Experience section
    if structured_cv.experiences:
        cv_context += "\nWORK EXPERIENCE:\n"
        for exp in structured_cv.experiences:
            cv_context += f"- {exp.position} at {exp.company}"
            if exp.start_date or exp.end_date:
                cv_context += f" ({exp.start_date} - {exp.end_date})"
            if exp.duration:
                cv_context += f" [Duration: {exp.duration}]"
            cv_context += "\n"
            if exp.responsibilities:
                cv_context += f"  Responsibilities: {'; '.join(exp.responsibilities)}\n"
            if exp.technologies:
                cv_context += f"  Technologies: {', '.join(exp.technologies)}\n"

    # Education section
    if structured_cv.education:
        cv_context += "\nEDUCATION:\n"
        for edu in structured_cv.education:
            cv_context += f"- {edu.degree} in {edu.field_of_study or 'N/A'} at {edu.institution}"
            if edu.start_date or edu.end_date:
                cv_context += f" ({edu.start_date} - {edu.end_date})"
            cv_context += "\n"

    # Skills section
    if structured_cv.skills:
        cv_context += "\nSKILLS:\n"
        skills_by_category = {}
        for skill in structured_cv.skills:
            if skill.category not in skills_by_category:
                skills_by_category[skill.category] = []
            skills_by_category[skill.category].append(skill.name)

        for category, skills in skills_by_category.items():
            cv_context += f"- {category.title()}: {', '.join(skills)}\n"

    # Projects section
    if structured_cv.projects:
        cv_context += "\nPROJECTS:\n"
        for proj in structured_cv.projects:
            cv_context += f"- {proj.name}: {proj.description}\n"
            if proj.technologies:
                cv_context += f"  Technologies: {', '.join(proj.technologies)}\n"
            if proj.achievements:
                cv_context += f"  Achievements: {'; '.join(proj.achievements)}\n"

    return cv_context
def parse_qcm_response(raw_response: str, technology_focus: str) -> QCMQuestion:
    """Parse QCM response from LLM"""
    try:
        lines = raw_response.strip().split('\n')
        question = ""
        options = []
        correct_answer = ""
        explanation = ""

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("Question:"):
                question = line.replace("Question:", "").strip()
                current_section = "question"
            elif line.startswith(("A)", "B)", "C)", "D)")):
                option_letter = line[0]
                option_text = line[2:].strip()
                options.append(QCMOption(option=option_letter, text=option_text))
            elif line.startswith("Correct Answer:"):
                correct_answer = line.replace("Correct Answer:", "").strip()
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()

        return QCMQuestion(
            question=question,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            technology_focus=technology_focus
        )
    except Exception as e:
        print(f"Error parsing QCM response: {e}")
        # Return a fallback QCM
        return QCMQuestion(
            question="What is a key concept in software development?",
            options=[
                QCMOption(option="A", text="Code reusability"),
                QCMOption(option="B", text="Random coding"),
                QCMOption(option="C", text="Ignoring best practices"),
                QCMOption(option="D", text="No documentation")
            ],
            correct_answer="A",
            explanation="Code reusability is a fundamental principle in software development.",
            technology_focus=technology_focus
        )
