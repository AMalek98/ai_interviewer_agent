"""
Coding Question Generator for AI Interviewer
Generates progressive difficulty coding questions based on job requirements
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import yaml
import os
from pydantic import BaseModel, Field

# Import from shared modules
from shared.llm_setup import get_llm

# Import job skill analyzer
from .job_skill_analyzer import JobSkillAnalysis, SkillImportance, DatabaseRequirement

# Pydantic Models for Coding Questions
class WorkExperience(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job position/title")
    start_date: Optional[str] = Field(description="Start date of employment")
    end_date: Optional[str] = Field(description="End date of employment")
    duration: Optional[str] = Field(description="Duration of employment")
    responsibilities: List[str] = Field(description="List of responsibilities and achievements")
    technologies: List[str] = Field(default=[], description="Technologies used in this role")

class DebugCodingQuestion(BaseModel):
    title: str = Field(description="Debug problem title")

    # NEW: Structured 3-part format
    context_paragraph: str = Field(description="1-2 sentences explaining the situation: What system? Why does this code exist?")
    task_instruction: str = Field(description="Clear, explicit instruction on what the candidate should do")
    expected_outcome: str = Field(description="Specific expected result, e.g., 'When fixed, the function should return 100 for input [1,2,3]'")

    # NEW: Expected output for automated output comparison
    expected_output: str = Field(default="", description="Expected output when the corrected code runs with embedded test data")

    # Existing fields (kept for backward compatibility)
    buggy_code: str = Field(description="The buggy code to debug")
    error_count: int = Field(description="Number of bugs in the code")
    error_types: List[str] = Field(default=[], description="Types of errors (syntax, logic, edge case, etc.)")
    hints: List[str] = Field(default=[], description="Optional hints for the candidate")
    target_language: str = Field(description="Programming language")
    cv_technology: str = Field(description="Technology from CV being tested")

    # Backward compatibility - these will be derived from new fields if not provided
    description: str = Field(default="", description="[DEPRECATED] Use context_paragraph instead")
    expected_behavior: str = Field(default="", description="[DEPRECATED] Use expected_outcome instead")
    context: str = Field(default="", description="[DEPRECATED] Use context_paragraph instead")

class ExplanationCodingQuestion(BaseModel):
    title: str = Field(description="Code explanation problem title")

    # NEW: Structured 3-part format
    context_paragraph: str = Field(description="1-2 sentences: Where would this code be used? What problem does it solve?")
    task_instruction: str = Field(description="Clear instruction on what analysis to perform")
    expected_outcome: str = Field(description="What form the answer should take, e.g., 'Provide detailed explanation covering complexity and improvements'")

    # NEW: Expected output for automated output comparison (if code produces output)
    expected_output: str = Field(default="", description="Expected output when code runs with embedded test data (if applicable)")

    # Existing fields (kept for backward compatibility)
    working_code: str = Field(description="Working code to analyze")
    analysis_questions: List[str] = Field(default=[], description="[DEPRECATED] Specific questions - now included in task_instruction")
    key_concepts: List[str] = Field(default=[], description="Key concepts demonstrated")
    target_language: str = Field(description="Programming language used")
    cv_technology: str = Field(description="Technology from CV being demonstrated")
    skills_tested: List[str] = Field(default=[], description="Skills being tested")

    # Backward compatibility
    context: str = Field(default="", description="[DEPRECATED] Use context_paragraph instead")


class DatabaseSchemaQuestion(BaseModel):
    title: str = Field(description="Database problem title")

    # NEW: Structured 3-part format
    context_paragraph: str = Field(description="Business context paragraph: What company/system? What problem needs solving?")
    task_instruction: str = Field(description="Explicit database task instruction")
    expected_outcome: str = Field(description="What the deliverable should include, e.g., 'Provide SQL CREATE TABLE statements with constraints'")

    # Existing fields (kept for backward compatibility and detail)
    requirements: List[str] = Field(default=[], description="Detailed list of specific requirements")
    db_technology: str = Field(description="Database technology (SQL, MongoDB, etc.)")
    complexity_level: str = Field(description="Complexity level: basic, intermediate, advanced, expert")
    skills_tested: List[str] = Field(default=[], description="Skills being tested")

    # Backward compatibility - map to new fields
    scenario: str = Field(default="", description="[DEPRECATED] Use context_paragraph instead")
    task_description: str = Field(default="", description="[DEPRECATED] Use task_instruction instead")
    expected_deliverable: str = Field(default="", description="[DEPRECATED] Use expected_outcome instead")
    context: str = Field(default="", description="[DEPRECATED] Use context_paragraph instead")

class InterviewQuestion(BaseModel):
    question_id: int = Field(description="Question identifier")
    question_type: str = Field(description="Type of question")
    question_text: str = Field(description="Main question text")
    difficulty_level: int = Field(description="Difficulty score 1-10")
    technology_focus: str = Field(description="Technology being tested")
    debug_data: Optional[DebugCodingQuestion] = Field(default=None, description="Debug question data")
    explanation_data: Optional[ExplanationCodingQuestion] = Field(default=None, description="Explanation question data")
    db_schema_data: Optional[DatabaseSchemaQuestion] = Field(default=None, description="Database schema question data")
    timestamp: str = Field(description="ISO timestamp of question generation")

# Coding Interview State for standalone agent
class CodingInterviewState(BaseModel):
    job_description: str = Field(description="Job description text")
    difficulty_score: int = Field(description="Overall difficulty score 1-10")
    selected_experiences: List[WorkExperience] = Field(default=[], description="Relevant work experiences")
    matched_technologies: List[str] = Field(default=[], description="Technologies matching job and CV")
    preferred_languages: List[str] = Field(default=[], description="Preferred programming languages")
    current_question_count: int = Field(default=0, description="Current question count")
    total_questions: int = Field(default=5, description="Total questions to ask")
    current_question: Optional[InterviewQuestion] = Field(default=None, description="Current question")
    all_questions: List[InterviewQuestion] = Field(default=[], description="All pre-generated questions")
    coding_test_filename: str = Field(default="code-test-unknown.json", description="Unique filename for this coding test session")

    # NEW: Job-centric skill analysis fields
    job_skill_analysis: Optional[JobSkillAnalysis] = Field(default=None, description="Structured analysis of job skills")
    question_distribution: Dict[int, Dict[str, Any]] = Field(default={}, description="Maps question number to {skill, difficulty, type}")
    skill_difficulty_map: Dict[str, int] = Field(default={}, description="Maps skill name to job-required difficulty (1-10)")

def load_coding_prompts():
    """Load coding-specific prompts from YAML file"""
    try:
        prompts_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'coding_prompts.yaml')
        with open(prompts_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading coding prompts: {e}")
        return None

def get_prompt_template(category: str, prompt_type: str) -> Optional[str]:
    """Get a specific prompt template from the prompts file"""
    prompts = load_coding_prompts()
    if prompts and category in prompts and prompt_type in prompts[category]:
        return prompts[category][prompt_type]
    return None

def get_difficulty_description(difficulty_score: int) -> str:
    """Get difficulty description from score"""
    if difficulty_score <= 2:
        return "entry-level/junior"
    elif difficulty_score <= 4:
        return "junior to mid-level"
    elif difficulty_score <= 6:
        return "mid-level"
    elif difficulty_score <= 8:
        return "senior-level"
    else:
        return "expert/principal-level"


def extract_skill_difficulty_from_job(skill: SkillImportance, job_description: str) -> int:
    """
    Extract job-required difficulty for a specific skill based on job description language.
    Returns difficulty score 1-10 based on what the JOB needs, not candidate's level.

    Args:
        skill: SkillImportance object with proficiency level and context
        job_description: Full job description text

    Returns:
        int: Difficulty score 1-10
    """
    proficiency_level = skill.required_proficiency_level.lower()
    importance_rank = skill.importance_rank

    # Base difficulty from proficiency level
    proficiency_map = {
        "expert": 9,
        "advanced": 7,
        "intermediate": 5,
        "basic": 3,
        "familiarity": 2
    }

    base_difficulty = proficiency_map.get(proficiency_level, 5)

    # Adjust based on importance rank (more important = higher difficulty to test thoroughly)
    if importance_rank == 1:  # Critical skill
        base_difficulty = min(10, base_difficulty + 1)
    elif importance_rank == 2:  # Very important
        base_difficulty = base_difficulty  # No adjustment
    elif importance_rank >= 4:  # Nice to have
        base_difficulty = max(1, base_difficulty - 1)

    # Check context clues for additional indicators
    context_text = " ".join(skill.context_clues).lower()
    if any(keyword in context_text for keyword in ["deep", "extensive", "mastery", "complex"]):
        base_difficulty = min(10, base_difficulty + 1)

    return max(1, min(10, base_difficulty))


def calculate_progressive_difficulty(
    question_number: int,
    target_difficulty: int,
    total_questions: int = 5
) -> int:
    """
    Calculate progressive difficulty that starts at 50% and reaches 100% by final question.
    This creates an ascending difficulty curve for a better interview experience.

    Args:
        question_number: Current question number (1-indexed)
        target_difficulty: Final target difficulty from job analysis (1-10)
        total_questions: Total number of questions in interview (default 5)

    Returns:
        int: Difficulty score for this specific question (1-10)

    Examples:
        With target_difficulty=8, total_questions=5:
        - Q1: 4 (50% of target - warm up)
        - Q2: 5 (62.5% of target)
        - Q3: 6 (75% of target)
        - Q4: 7 (87.5% of target)
        - Q5: 8 (100% of target - full challenge)

        With target_difficulty=6, total_questions=5:
        - Q1: 3, Q2: 4, Q3: 4, Q4: 5, Q5: 6

        With target_difficulty=10, total_questions=5:
        - Q1: 5, Q2: 6, Q3: 7, Q4: 9, Q5: 10
    """
    # Start at 50% of target difficulty (warm up)
    start_difficulty = target_difficulty / 2.0

    # Calculate step size to reach full target by final question
    # step_size = (target - start) / (total - 1)
    step_size = (target_difficulty - start_difficulty) / (total_questions - 1)

    # Calculate progressive difficulty for this question
    difficulty = start_difficulty + ((question_number - 1) * step_size)

    # Ensure difficulty stays within valid bounds [1, 10]
    return max(1, min(10, round(difficulty)))


def build_skill_difficulty_map(job_skill_analysis: JobSkillAnalysis) -> Dict[str, int]:
    """
    Build a map of skill names to their required difficulty levels.

    Args:
        job_skill_analysis: Structured job skill analysis

    Returns:
        Dict mapping skill name to difficulty (1-10)
    """
    skill_difficulty_map = {}

    for skill in job_skill_analysis.all_ranked_skills:
        difficulty = extract_skill_difficulty_from_job(skill, "")  # Context already in skill object
        skill_difficulty_map[skill.skill_name.lower()] = difficulty

    return skill_difficulty_map


def create_question_distribution_plan(
    job_skill_analysis: JobSkillAnalysis,
    cv_technologies: List[str],
    total_questions: int = 5
) -> Dict[int, Dict[str, Any]]:
    """
    Create a strategic plan for question distribution with PROGRESSIVE DIFFICULTY.

    NEW: Implements ascending difficulty curve where questions start at 50% of target
    difficulty and progressively increase to 100% by the final question.

    Distribution strategy:
    - Q1-Q2: Top-ranked skill (most critical) - with progressive difficulty
    - Q3: Second-ranked skill - with progressive difficulty
    - Q4: Another important skill (3rd or 4th ranked) - with progressive difficulty
    - Q5: Important skill that appears in both job + CV - with progressive difficulty

    Difficulty progression (example with target=8):
    - Q1: Difficulty 4 (50% - warm up)
    - Q2: Difficulty 5 (62.5%)
    - Q3: Difficulty 6 (75%)
    - Q4: Difficulty 7 (87.5%)
    - Q5: Difficulty 8 (100% - full challenge)

    Args:
        job_skill_analysis: Structured analysis of job skills
        cv_technologies: List of technologies from candidate's CV
        total_questions: Total number of questions to generate (default 5)

    Returns:
        Dict mapping question number to {skill_name, difficulty, question_type}
    """
    question_plan = {}
    all_skills = job_skill_analysis.all_ranked_skills

    if not all_skills:
        # Fallback if no skills found - use progressive difficulty with default target 5
        for i in range(1, total_questions + 1):
            question_plan[i] = {
                "skill_name": "Python",
                "difficulty": calculate_progressive_difficulty(i, 5, total_questions),
                "question_type": "debug"
            }
        return question_plan

    # NEW: Use overall job difficulty as the target for progressive difficulty
    target_difficulty = job_skill_analysis.overall_difficulty
    print(f"\n🎯 Progressive Difficulty Target: {target_difficulty}/10")

    # Normalize CV technologies for comparison
    cv_tech_lower = [tech.lower() for tech in cv_technologies]

    # Q1-Q2: Top-ranked skill (most critical) with progressive difficulty
    top_skill = all_skills[0] if len(all_skills) > 0 else None
    if top_skill:
        # Determine question type based on skill category
        q1_type = determine_question_type_for_skill(top_skill, 1)
        q2_type = determine_question_type_for_skill(top_skill, 2)

        # NEW: Calculate progressive difficulty for Q1
        q1_difficulty = calculate_progressive_difficulty(1, target_difficulty, total_questions)
        question_plan[1] = {
            "skill_name": top_skill.skill_name,
            "difficulty": q1_difficulty,  # Progressive difficulty
            "question_type": q1_type,
            "importance_rank": top_skill.importance_rank,
            "proficiency_level": top_skill.required_proficiency_level
        }

        # NEW: Calculate progressive difficulty for Q2
        q2_difficulty = calculate_progressive_difficulty(2, target_difficulty, total_questions)
        question_plan[2] = {
            "skill_name": top_skill.skill_name,
            "difficulty": q2_difficulty,  # Progressive difficulty
            "question_type": q2_type,
            "importance_rank": top_skill.importance_rank,
            "proficiency_level": top_skill.required_proficiency_level
        }

    # Q3: Second-ranked skill with progressive difficulty
    second_skill = all_skills[1] if len(all_skills) > 1 else all_skills[0]
    if second_skill:
        q3_type = determine_question_type_for_skill(second_skill, 3)

        # NEW: Calculate progressive difficulty for Q3
        q3_difficulty = calculate_progressive_difficulty(3, target_difficulty, total_questions)
        question_plan[3] = {
            "skill_name": second_skill.skill_name,
            "difficulty": q3_difficulty,  # Progressive difficulty
            "question_type": q3_type,
            "importance_rank": second_skill.importance_rank,
            "proficiency_level": second_skill.required_proficiency_level
        }

    # Q4: Another important skill (3rd or 4th ranked) with progressive difficulty
    third_skill = all_skills[2] if len(all_skills) > 2 else all_skills[0]
    if third_skill:
        q4_type = determine_question_type_for_skill(third_skill, 4)

        # NEW: Calculate progressive difficulty for Q4
        q4_difficulty = calculate_progressive_difficulty(4, target_difficulty, total_questions)
        question_plan[4] = {
            "skill_name": third_skill.skill_name,
            "difficulty": q4_difficulty,  # Progressive difficulty
            "question_type": q4_type,
            "importance_rank": third_skill.importance_rank,
            "proficiency_level": third_skill.required_proficiency_level
        }

    # Q5: Important skill from job+CV intersection (to test CV claims) with progressive difficulty
    intersection_skill = None
    for skill in all_skills:
        if skill.skill_name.lower() in cv_tech_lower:
            intersection_skill = skill
            break

    # If no intersection, use 4th ranked skill or fallback
    if not intersection_skill:
        intersection_skill = all_skills[3] if len(all_skills) > 3 else all_skills[0]

    if intersection_skill:
        q5_type = determine_question_type_for_skill(intersection_skill, 5)

        # NEW: Calculate progressive difficulty for Q5 (reaches target difficulty)
        q5_difficulty = calculate_progressive_difficulty(5, target_difficulty, total_questions)
        question_plan[5] = {
            "skill_name": intersection_skill.skill_name,
            "difficulty": q5_difficulty,  # Progressive difficulty (full target)
            "question_type": q5_type,
            "importance_rank": intersection_skill.importance_rank,
            "proficiency_level": intersection_skill.required_proficiency_level,
            "cv_verification": True  # Flag to indicate this tests CV claims
        }

    return question_plan


def determine_question_type_for_skill(skill: SkillImportance, question_number: int) -> str:
    """
    Determine appropriate question type based on skill category and question number.

    Args:
        skill: SkillImportance object
        question_number: Question number in sequence

    Returns:
        str: Question type - 'debug', 'explain', or 'db_schema'
    """
    category = skill.category.lower()

    # Database skills get special treatment
    if category == "database" or skill.skill_name.lower() in ['sql', 'postgresql', 'mysql', 'mongodb', 'nosql', 'redis']:
        # Alternate between schema design and debugging for database questions
        if question_number % 2 == 1:
            return "db_schema"
        else:
            return "debug"

    # For other skills, alternate between debug and explain
    if question_number % 2 == 1:
        return "debug"
    else:
        return "explain"

def determine_error_count_by_difficulty(difficulty_level: int) -> int:
    """Determine number of errors to inject based on difficulty level"""
    if difficulty_level <= 3:
        return 1  # Easy: 1 error
    elif difficulty_level <= 7:
        return 2  # Medium: 2 errors
    else:
        return 3  # Hard: 3 errors


def parse_debug_response(raw_response: str, target_language: str, cv_technology: str, error_count: int) -> DebugCodingQuestion:
    """Parse debug coding response from LLM with new structured format"""
    try:
        lines = raw_response.split('\n')
        title = ""
        context_paragraph = ""
        task_instruction = ""
        expected_outcome = ""
        expected_output = ""
        buggy_code = ""

        current_section = None
        code_block = False

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith("**Problem Title:**"):
                title = line_stripped.replace("**Problem Title:**", "").strip()
            elif line_stripped.startswith("**Context:**"):
                context_paragraph = line_stripped.replace("**Context:**", "").strip()
                current_section = "context"
            elif line_stripped.startswith("**Buggy Code:**"):
                current_section = "code"
            elif line_stripped.startswith("**Your Task:**"):
                task_instruction = line_stripped.replace("**Your Task:**", "").strip()
                current_section = "task"
            elif line_stripped.startswith("**Expected Outcome:**"):
                expected_outcome = line_stripped.replace("**Expected Outcome:**", "").strip()
                current_section = "outcome"
            elif line_stripped.startswith("**Expected Output:**"):
                expected_output = line_stripped.replace("**Expected Output:**", "").strip()
                current_section = "expected_output"
            elif line_stripped.startswith("```"):
                code_block = not code_block
                if not code_block:
                    current_section = None
            elif code_block and current_section == "code":
                if buggy_code:
                    buggy_code += "\n" + line
                else:
                    buggy_code = line
            elif current_section == "context" and line_stripped and not line_stripped.startswith("**"):
                if context_paragraph:
                    context_paragraph += " " + line_stripped
                else:
                    context_paragraph = line_stripped
            elif current_section == "task" and line_stripped and not line_stripped.startswith("**"):
                if task_instruction:
                    task_instruction += " " + line_stripped
                else:
                    task_instruction = line_stripped
            elif current_section == "outcome" and line_stripped and not line_stripped.startswith("**"):
                if expected_outcome:
                    expected_outcome += " " + line_stripped
                else:
                    expected_outcome = line_stripped
            elif current_section == "expected_output" and line_stripped and not line_stripped.startswith("**"):
                if expected_output:
                    expected_output += " " + line_stripped
                else:
                    expected_output = line_stripped

        return DebugCodingQuestion(
            title=title or f"Debug {target_language} Code",
            # NEW: Structured fields
            context_paragraph=context_paragraph or f"This code is part of a {cv_technology} application.",
            task_instruction=task_instruction or f"Find and fix the {error_count} bug(s) in this code.",
            expected_outcome=expected_outcome or "Code should run without errors.",
            expected_output=expected_output or "",  # NEW: Include parsed expected output
            # Required fields
            buggy_code=buggy_code or f"# {target_language} code with {error_count} bugs",
            error_count=error_count,
            error_types=["logic", "syntax"],
            hints=[],
            target_language=target_language,
            cv_technology=cv_technology,
            # Backward compatibility - populate old fields from new ones
            description=context_paragraph or f"Fix the bugs in this {target_language} code",
            expected_behavior=expected_outcome or "Code should run without errors",
            context=context_paragraph or f"This code might be used in a {cv_technology} application"
        )
    except Exception as e:
        print(f"Error parsing debug response: {e}")
        fallback_context = f"This code is part of a {cv_technology} application."
        fallback_task = f"Find and fix the {error_count} bug(s) in this code."
        fallback_outcome = "Code should run without errors."

        return DebugCodingQuestion(
            title=f"Debug {target_language} Code",
            context_paragraph=fallback_context,
            task_instruction=fallback_task,
            expected_outcome=fallback_outcome,
            expected_output="",
            buggy_code=f"# {target_language} code with {error_count} bugs\nprint('Hello World')",
            error_count=error_count,
            error_types=["logic"],
            hints=[],
            target_language=target_language,
            cv_technology=cv_technology,
            description=fallback_context,
            expected_behavior=fallback_outcome,
            context=fallback_context
        )

def parse_explanation_response(raw_response: str, target_language: str, cv_technology: str) -> ExplanationCodingQuestion:
    """Parse explanation coding response from LLM with new structured format"""
    try:
        lines = raw_response.split('\n')
        title = ""
        context_paragraph = ""
        task_instruction = ""
        expected_outcome = ""
        expected_output = ""
        working_code = ""
        analysis_questions = []

        current_section = None
        code_block = False

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith("**Problem Title:**"):
                title = line_stripped.replace("**Problem Title:**", "").strip()
            elif line_stripped.startswith("**Context:**"):
                context_paragraph = line_stripped.replace("**Context:**", "").strip()
                current_section = "context"
            elif line_stripped.startswith("**Code to Analyze:**"):
                current_section = "code"
            elif line_stripped.startswith("**Your Task:**"):
                task_instruction = line_stripped.replace("**Your Task:**", "").strip()
                current_section = "task"
            elif line_stripped.startswith("**Expected Outcome:**"):
                expected_outcome = line_stripped.replace("**Expected Outcome:**", "").strip()
                current_section = "outcome"
            elif line_stripped.startswith("**Expected Output:**"):
                expected_output = line_stripped.replace("**Expected Output:**", "").strip()
                current_section = "expected_output"
            elif line_stripped.startswith("```"):
                code_block = not code_block
                if not code_block:
                    current_section = None
            elif code_block and current_section == "code":
                if working_code:
                    working_code += "\n" + line
                else:
                    working_code = line
            elif current_section == "context" and line_stripped and not line_stripped.startswith("**"):
                if context_paragraph:
                    context_paragraph += " " + line_stripped
                else:
                    context_paragraph = line_stripped
            elif current_section == "task" and line_stripped and not line_stripped.startswith("**"):
                if task_instruction:
                    task_instruction += " " + line_stripped
                else:
                    task_instruction = line_stripped
            elif current_section == "outcome" and line_stripped and not line_stripped.startswith("**"):
                if expected_outcome:
                    expected_outcome += " " + line_stripped
                else:
                    expected_outcome = line_stripped
            elif current_section == "expected_output" and line_stripped and not line_stripped.startswith("**"):
                if expected_output:
                    expected_output += " " + line_stripped
                else:
                    expected_output = line_stripped

        # Extract analysis questions from task if present (for backward compatibility)
        if task_instruction:
            # Try to extract numbered points as individual questions
            question_pattern = r'\(?\d+\)[:\s]+(.*?)(?=\(?\d+\)|$)'
            matches = re.findall(question_pattern, task_instruction, re.DOTALL)
            if matches:
                analysis_questions = [q.strip().rstrip(',') for q in matches if q.strip()]

        return ExplanationCodingQuestion(
            title=title or f"Analyze {target_language} Code",
            # NEW: Structured fields
            context_paragraph=context_paragraph or f"This code is used in a {cv_technology} system.",
            task_instruction=task_instruction or "Analyze this code and explain what it does.",
            expected_outcome=expected_outcome or "Provide a detailed technical explanation.",
            expected_output=expected_output or "",  # NEW: Include parsed expected output
            # Required fields
            working_code=working_code or f"# {target_language} code to analyze\nprint('Hello World')",
            analysis_questions=analysis_questions or ["Explain what this code does"],
            key_concepts=[target_language, cv_technology],
            target_language=target_language,
            cv_technology=cv_technology,
            skills_tested=[target_language, "Code Analysis"],
            # Backward compatibility
            context=context_paragraph or f"This code might be used in a {cv_technology} application"
        )
    except Exception as e:
        print(f"Error parsing explanation response: {e}")
        fallback_context = f"This code is used in a {cv_technology} system."
        fallback_task = "Analyze this code and explain what it does."
        fallback_outcome = "Provide a detailed technical explanation."

        return ExplanationCodingQuestion(
            title=f"Analyze {target_language} Code",
            context_paragraph=fallback_context,
            task_instruction=fallback_task,
            expected_outcome=fallback_outcome,
            expected_output="",
            working_code=f"# {target_language} code to analyze\nprint('Hello World')",
            analysis_questions=["Explain what this code does"],
            key_concepts=[target_language],
            target_language=target_language,
            cv_technology=cv_technology,
            skills_tested=[target_language, "Code Analysis"],
            context=fallback_context
        )

def generate_debug_question(state: CodingInterviewState, question_number: int) -> InterviewQuestion:
    """Generate a debugging coding question using skill-weighted approach"""
    # Get question plan for this question number
    question_plan = state.question_distribution.get(question_number, {})
    skill_name = question_plan.get("skill_name", "Python")
    difficulty = question_plan.get("difficulty", 5)
    proficiency_level = question_plan.get("proficiency_level", "intermediate")
    importance_rank = question_plan.get("importance_rank", 3)

    difficulty_desc = get_difficulty_description(difficulty)

    # Determine question parameters based on job-centric difficulty
    error_count = determine_error_count_by_difficulty(difficulty)
    target_language = skill_name if skill_name in ['Python', 'JavaScript', 'Java', 'C#', 'Go', 'Rust', 'TypeScript'] else "Python"
    cv_technology = skill_name

    # Get debug prompt template
    prompt_template = get_prompt_template("coding_questions", "debug_prompt") or """
Generate a debugging exercise using {target_language} and {cv_technology}.

DIFFICULTY: {difficulty_level}/10
Create a {target_language} code snippet with {error_count} logical error(s).
"""

    formatted_prompt = prompt_template.format(
        target_language=target_language,
        cv_technology=cv_technology,
        job_description=state.job_description,
        importance_rank=importance_rank,
        proficiency_level=proficiency_level,
        difficulty_level=difficulty,
        difficulty_description=difficulty_desc,
        error_count=error_count
    )

    # Generate using LLM
    llm = get_llm()
    response = llm.invoke(formatted_prompt)
    debug_data = parse_debug_response(response.content, target_language, cv_technology, error_count)

    return InterviewQuestion(
        question_id=question_number,  # FIXED: Use question_number instead of state.current_question_count + 1
        question_type="coding_debug",
        question_text=f"Debug Challenge: {debug_data.title}",
        difficulty_level=difficulty,
        technology_focus=cv_technology,
        debug_data=debug_data,
        timestamp=datetime.now().isoformat()
    )

def parse_db_schema_response(raw_response: str, db_technology: str, complexity_level: str) -> DatabaseSchemaQuestion:
    """Parse database schema response from LLM with new structured format"""
    try:
        lines = raw_response.split('\n')
        title = ""
        context_paragraph = ""
        task_instruction = ""
        expected_outcome = ""
        requirements = []

        current_section = None

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith("**Problem Title:**"):
                title = line_stripped.replace("**Problem Title:**", "").strip()
            elif line_stripped.startswith("**Context:**"):
                context_paragraph = line_stripped.replace("**Context:**", "").strip()
                current_section = "context"
            elif line_stripped.startswith("**Your Task:**"):
                task_instruction = line_stripped.replace("**Your Task:**", "").strip()
                current_section = "task"
            elif line_stripped.startswith("**Requirements:**"):
                current_section = "requirements"
            elif line_stripped.startswith("**Expected Outcome:**"):
                expected_outcome = line_stripped.replace("**Expected Outcome:**", "").strip()
                current_section = "outcome"
            elif current_section == "context" and line_stripped and not line_stripped.startswith("**"):
                if context_paragraph:
                    context_paragraph += " " + line_stripped
                else:
                    context_paragraph = line_stripped
            elif current_section == "task" and line_stripped and not line_stripped.startswith("**"):
                if task_instruction:
                    task_instruction += " " + line_stripped
                else:
                    task_instruction = line_stripped
            elif current_section == "requirements" and line_stripped and not line_stripped.startswith("**"):
                # Handle list items
                if line_stripped.startswith("-") or line_stripped.startswith("•"):
                    requirements.append(line_stripped.lstrip("- •").strip())
                elif requirements:
                    requirements[-1] += " " + line_stripped
            elif current_section == "outcome" and line_stripped and not line_stripped.startswith("**"):
                if expected_outcome:
                    expected_outcome += " " + line_stripped
                else:
                    expected_outcome = line_stripped

        return DatabaseSchemaQuestion(
            title=title or f"Database Design Challenge - {db_technology}",
            # NEW: Structured fields
            context_paragraph=context_paragraph or f"Design a database solution for a business using {db_technology}.",
            task_instruction=task_instruction or f"Create a database design for this scenario.",
            expected_outcome=expected_outcome or "Schema design with tables, relationships, and constraints.",
            # Required fields
            requirements=requirements or ["Design an appropriate database schema"],
            db_technology=db_technology,
            complexity_level=complexity_level,
            skills_tested=[db_technology, "Database Design", "Data Modeling"],
            # Backward compatibility - populate old fields from new ones
            scenario=context_paragraph or f"Design a database solution using {db_technology}",
            task_description=task_instruction or f"Create a database design for this scenario",
            expected_deliverable=expected_outcome or "Schema design with tables, relationships, and constraints",
            context=context_paragraph or f"This tests your {db_technology} database design skills"
        )
    except Exception as e:
        print(f"Error parsing database schema response: {e}")
        fallback_context = f"Design a database solution for a business using {db_technology}."
        fallback_task = f"Create a database design for this scenario."
        fallback_outcome = "Schema design with tables, relationships, and constraints."

        return DatabaseSchemaQuestion(
            title=f"Database Design Challenge - {db_technology}",
            context_paragraph=fallback_context,
            task_instruction=fallback_task,
            expected_outcome=fallback_outcome,
            requirements=["Design an appropriate database schema"],
            db_technology=db_technology,
            complexity_level=complexity_level,
            skills_tested=[db_technology, "Database Design"],
            scenario=fallback_context,
            task_description=fallback_task,
            expected_deliverable=fallback_outcome,
            context=fallback_context
        )


def generate_db_schema_question(state: CodingInterviewState, question_number: int) -> InterviewQuestion:
    """Generate a database schema design or query optimization question"""
    # Get question plan for this question number
    question_plan = state.question_distribution.get(question_number, {})
    skill_name = question_plan.get("skill_name", "SQL")
    difficulty = question_plan.get("difficulty", 5)
    proficiency_level = question_plan.get("proficiency_level", "intermediate")
    importance_rank = question_plan.get("importance_rank", 3)

    difficulty_desc = get_difficulty_description(difficulty)

    # Determine database technology
    db_technology = skill_name if skill_name.upper() in ['SQL', 'MONGODB', 'POSTGRESQL', 'MYSQL', 'NOSQL'] else "SQL"

    # Get complexity level from job skill analysis
    complexity_level = "intermediate"
    if state.job_skill_analysis and state.job_skill_analysis.database_requirement:
        complexity_level = state.job_skill_analysis.database_requirement.complexity_level

    # Get db schema prompt template
    prompt_template = get_prompt_template("coding_questions", "db_schema_prompt") or """
Generate a database schema design or query challenge using {db_technology}.

DIFFICULTY: {difficulty_level}/10
Create an appropriate database challenge.
"""

    formatted_prompt = prompt_template.format(
        job_description=state.job_description,
        importance_rank=importance_rank,
        proficiency_level=proficiency_level,
        difficulty_level=difficulty,
        difficulty_description=difficulty_desc,
        db_technology=db_technology,
        complexity_level=complexity_level
    )

    # Generate using LLM
    llm = get_llm()
    response = llm.invoke(formatted_prompt)
    db_schema_data = parse_db_schema_response(response.content, db_technology, complexity_level)

    return InterviewQuestion(
        question_id=question_number,  # FIXED: Use question_number instead of state.current_question_count + 1
        question_type="db_schema",
        question_text=f"Database Challenge: {db_schema_data.title}",
        difficulty_level=difficulty,
        technology_focus=db_technology,
        db_schema_data=db_schema_data,
        timestamp=datetime.now().isoformat()
    )


def generate_explanation_question(state: CodingInterviewState, question_number: int) -> InterviewQuestion:
    """Generate a code explanation question using skill-weighted approach"""
    # Get question plan for this question number
    question_plan = state.question_distribution.get(question_number, {})
    skill_name = question_plan.get("skill_name", "Python")
    difficulty = question_plan.get("difficulty", 5)
    proficiency_level = question_plan.get("proficiency_level", "intermediate")
    importance_rank = question_plan.get("importance_rank", 3)

    difficulty_desc = get_difficulty_description(difficulty)

    # Determine question parameters
    target_language = skill_name if skill_name in ['Python', 'JavaScript', 'Java', 'C#', 'Go', 'Rust', 'TypeScript'] else "Python"
    cv_technology = skill_name

    # Get explanation prompt template
    prompt_template = get_prompt_template("coding_questions", "explanation_prompt") or """
Generate working {target_language} code using {cv_technology}.

DIFFICULTY: {difficulty_level}/10
Create realistic working code they might encounter in their role.
"""

    formatted_prompt = prompt_template.format(
        target_language=target_language,
        cv_technology=cv_technology,
        job_description=state.job_description,
        importance_rank=importance_rank,
        proficiency_level=proficiency_level,
        difficulty_level=difficulty,
        difficulty_description=difficulty_desc
    )

    # Generate using LLM
    llm = get_llm()
    response = llm.invoke(formatted_prompt)
    explanation_data = parse_explanation_response(response.content, target_language, cv_technology)

    return InterviewQuestion(
        question_id=question_number,  # FIXED: Use question_number instead of state.current_question_count + 1
        question_type="coding_explain",
        question_text=f"Code Analysis: {explanation_data.title}",
        difficulty_level=difficulty,
        technology_focus=cv_technology,
        explanation_data=explanation_data,
        timestamp=datetime.now().isoformat()
    )

def generate_coding_question(state: CodingInterviewState, question_number: int) -> InterviewQuestion:
    """Generate a coding interview question using skill-weighted distribution plan"""
    print(f"=== Generating Coding Question {question_number}/{state.total_questions} ===")

    # Get question plan for this question number
    question_plan = state.question_distribution.get(question_number, {})
    question_type = question_plan.get("question_type", "debug")
    skill_name = question_plan.get("skill_name", "Python")
    difficulty = question_plan.get("difficulty", 5)

    print(f"Q{question_number}: {skill_name} (Difficulty {difficulty}/10, Type: {question_type})")

    # Route to appropriate question generator based on plan
    if question_type == "db_schema":
        print(f"  → Database schema/query challenge")
        return generate_db_schema_question(state, question_number)
    elif question_type == "debug":
        print(f"  → Debug coding challenge")
        return generate_debug_question(state, question_number)
    elif question_type == "explain":
        print(f"  → Code explanation challenge")
        return generate_explanation_question(state, question_number)
    else:
        # Fallback to debug
        print(f"  → Fallback to debug challenge")
        return generate_debug_question(state, question_number)


def generate_all_coding_questions(state: CodingInterviewState) -> List[InterviewQuestion]:
    """
    Generate all coding questions upfront based on distribution plan

    This function generates all questions at once at the start of the interview,
    eliminating the need for sequential generation during the interview flow.

    Args:
        state: CodingInterviewState with job analysis and question distribution plan

    Returns:
        List of InterviewQuestion objects (5 questions)
    """
    import time  # For rate limiting

    print("\n" + "="*70)
    print("🚀 GENERATING ALL CODING QUESTIONS UPFRONT")
    print("="*70)

    all_questions = []

    for question_number in range(1, state.total_questions + 1):
        # Add rate limiting delay between LLM calls (except for first question)
        if question_number > 1:
            print(f"\n⏳ Rate limiting delay (300ms)...")
            time.sleep(0.3)

        try:
            # Generate question using existing function
            question = generate_coding_question(state, question_number)
            all_questions.append(question)

            print(f"✅ Q{question_number} generated successfully")

        except Exception as e:
            print(f"❌ Error generating Q{question_number}: {e}")
            # Create fallback question
            fallback_question = InterviewQuestion(
                question_id=question_number,
                question_type="coding_debug",
                question_text=f"Fallback Question {question_number}",
                difficulty_level=5,
                technology_focus="Python",
                debug_data=DebugCodingQuestion(
                    title=f"Fallback Debug Question {question_number}",
                    context_paragraph="This is a fallback question due to generation error.",
                    task_instruction="Debug the code below.",
                    expected_outcome="Code should run without errors.",
                    expected_output="",
                    buggy_code="# Fallback code\nprint('Hello World')",
                    error_count=1,
                    error_types=["logic"],
                    hints=[],
                    target_language="Python",
                    cv_technology="Python",
                    description="Fallback question",
                    expected_behavior="Should work",
                    context="Fallback context"
                ),
                timestamp=datetime.now().isoformat()
            )
            all_questions.append(fallback_question)

    print("\n" + "="*70)
    print(f"✅ ALL {len(all_questions)} QUESTIONS GENERATED SUCCESSFULLY")
    print("="*70 + "\n")

    return all_questions