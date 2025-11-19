"""
Coding Interview Routes Blueprint
Flask routes for coding challenge interviews
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os
import re

# Import from shared modules
from shared.llm_setup import get_llm

# Import from coding interview module
from .question_generator import (
    CodingInterviewState,
    InterviewQuestion,
    generate_coding_question,
    build_skill_difficulty_map,
    create_question_distribution_plan
)
from .job_skill_analyzer import analyze_job_description_skills, save_skill_analysis
from .evaluator.engine import evaluate_coding_interview


# Create Blueprint
coding_bp = Blueprint('coding', __name__, url_prefix='/coding')


# ============================================================================
# MODULE-LEVEL STATE (Lazy Initialization)
# ============================================================================

_llm = None
_prompts_loaded = False

# Global session storage (per-session)
session_data = {}


def initialize_coding_module():
    """
    Lazy initialization of coding interview module
    Called on first route access
    """
    global _llm, _prompts_loaded

    if not _llm:
        print("🔄 Initializing coding interview LLM...")
        _llm = get_llm()
        print("✅ LLM initialized")

    # Note: Coding questions don't use YAML prompts (prompts are inline in question_generator.py)
    _prompts_loaded = True


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

def get_upload_folder():
    """Get upload folder path (use data/uploads/)"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'uploads'
    )


def get_interviews_folder():
    """Get coding interviews folder path (use data/interviews/coding/)"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'interviews',
        'coding'
    )


# Ensure directories exist
os.makedirs(get_upload_folder(), exist_ok=True)
os.makedirs(get_interviews_folder(), exist_ok=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def initialize_coding_interview(job_description: str) -> CodingInterviewState:
    """Initialize coding interview based on job description only (no CV required)"""

    # Get LLM instance
    llm = get_llm()

    # Default job description if none provided
    if not job_description.strip():
        job_description = "Software Developer role requiring strong programming skills"

    print("\n" + "="*60)
    print("🔍 ANALYZING JOB DESCRIPTION FOR SKILL REQUIREMENTS")
    print("="*60)

    # Analyze job description to extract and rank skills
    job_skill_analysis = analyze_job_description_skills(job_description, llm)

    # Save structured skill analysis to JSON
    upload_folder = get_upload_folder()
    skills_output_path = os.path.join(upload_folder, 'structured_skills.json')
    save_skill_analysis(job_skill_analysis, skills_output_path)

    print(f"\n✅ Job Skill Analysis Complete:")
    print(f"   - Primary Skills: {len(job_skill_analysis.primary_skills)}")
    print(f"   - Job Level: {job_skill_analysis.job_level}")
    print(f"   - Overall Difficulty: {job_skill_analysis.overall_difficulty}/10")
    print(f"   - Database Required: {job_skill_analysis.database_requirement.has_db_requirement}")

    if job_skill_analysis.primary_skills:
        print(f"\n   Top 3 Skills:")
        for i, skill in enumerate(job_skill_analysis.primary_skills[:3], 1):
            print(f"      {i}. {skill.skill_name} (Rank {skill.importance_rank}, {skill.required_proficiency_level})")

    # Use job analysis difficulty directly (no CV needed)
    difficulty_score = job_skill_analysis.overall_difficulty

    # Extract all technologies from job skills
    all_job_technologies = [skill.skill_name for skill in job_skill_analysis.all_ranked_skills]
    matched_technologies = all_job_technologies[:10]  # Top 10 technologies

    # Extract programming languages from job skills
    preferred_languages = [
        skill.skill_name for skill in job_skill_analysis.primary_skills + job_skill_analysis.secondary_skills
        if skill.category == 'programming_language'
    ][:3]  # Top 3 programming languages

    # Build skill-to-difficulty mapping
    skill_difficulty_map = build_skill_difficulty_map(job_skill_analysis)

    # Create question distribution plan (job skills only, no CV)
    question_distribution = create_question_distribution_plan(
        job_skill_analysis,
        all_job_technologies,  # Use job technologies instead of CV
        total_questions=5
    )

    print(f"\n📋 Question Distribution Plan (Progressive Difficulty):")
    print(f"   🎯 Target Difficulty: {job_skill_analysis.overall_difficulty}/10")
    print(f"   📈 Strategy: Start at 50% → Reach 100% by Q5")
    print(f"")
    for q_num, q_plan in question_distribution.items():
        # Calculate percentage of target difficulty
        target = job_skill_analysis.overall_difficulty
        percentage = (q_plan['difficulty'] / target * 100) if target > 0 else 0

        # Visual indicator for difficulty progression
        if q_num == 1:
            indicator = "🔵"  # Starting point
        elif q_num == 5:
            indicator = "🔴"  # Final challenge
        else:
            indicator = "🟡"  # Progressive step

        print(f"   {indicator} Q{q_num}: {q_plan['skill_name']} "
              f"(Difficulty {q_plan['difficulty']}/10 → {percentage:.0f}% of target, "
              f"Type: {q_plan['question_type']})")

    # Generate unique coding test filename (timestamp-based, no CV name)
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    coding_test_filename = f"code-test-{timestamp}.json"
    print(f"\n💾 Coding test filename: {coding_test_filename}")
    print("="*60 + "\n")

    return CodingInterviewState(
        job_description=job_description,
        difficulty_score=difficulty_score,
        selected_experiences=[],  # No CV, empty list
        matched_technologies=matched_technologies,
        preferred_languages=preferred_languages,
        current_question_count=0,
        total_questions=5,
        current_question=None,
        coding_test_filename=coding_test_filename,
        # Job-centric fields
        job_skill_analysis=job_skill_analysis,
        question_distribution=question_distribution,
        skill_difficulty_map=skill_difficulty_map
    )


def save_coding_response(filename: str, current_question: InterviewQuestion, response_text: str, candidate_name: str = "Candidate"):
    """
    Save coding question and response to structured JSON file.
    """
    try:
        interviews_folder = get_interviews_folder()
        filepath = os.path.join(interviews_folder, filename)

        # Load existing data for this coding test session (if any)
        coding_data = {}
        try:
            with open(filepath, 'r') as f:
                coding_data = json.load(f)
        except FileNotFoundError:
            # First question - create new file structure
            coding_data = {
                "candidate_name": candidate_name,
                "interview_date": datetime.now().strftime('%d-%m-%Y'),
                "questions": []
            }

        # Ensure questions array exists
        if "questions" not in coding_data:
            coding_data["questions"] = []

        # Extract question details based on question type
        question_title = ""
        technology = ""
        expected_output = ""

        if current_question.question_type == 'coding_debug' and current_question.debug_data:
            question_title = current_question.debug_data.title
            technology = current_question.debug_data.target_language
            expected_output = current_question.debug_data.expected_output
        elif current_question.question_type == 'coding_explain' and current_question.explanation_data:
            question_title = current_question.explanation_data.title
            technology = current_question.explanation_data.target_language
            expected_output = current_question.explanation_data.expected_output
        elif current_question.question_type == 'db_schema' and current_question.db_schema_data:
            question_title = current_question.db_schema_data.title
            technology = current_question.db_schema_data.db_technology
            expected_output = ""  # Database questions don't have expected output

        # Parse candidate response to extract code and explanation
        candidate_code = ""
        candidate_explanation = ""

        # Try to split by common delimiters
        if "FIXED CODE:" in response_text.upper():
            parts = re.split(r'(?i)FIXED CODE:\s*', response_text, maxsplit=1)
            if len(parts) > 1:
                remaining = parts[1]
                # Look for EXPLANATION section
                expl_parts = re.split(r'(?i)EXPLANATION:\s*', remaining, maxsplit=1)
                if len(expl_parts) > 1:
                    candidate_code = expl_parts[0].strip()
                    candidate_explanation = expl_parts[1].strip()
                else:
                    candidate_code = remaining.strip()
        elif "CODE:" in response_text.upper():
            parts = re.split(r'(?i)CODE:\s*', response_text, maxsplit=1)
            if len(parts) > 1:
                remaining = parts[1]
                expl_parts = re.split(r'(?i)EXPLANATION:\s*', remaining, maxsplit=1)
                if len(expl_parts) > 1:
                    candidate_code = expl_parts[0].strip()
                    candidate_explanation = expl_parts[1].strip()
                else:
                    candidate_code = remaining.strip()
        else:
            # No clear code/explanation split, use heuristics
            # If response contains code blocks, extract them
            code_blocks = re.findall(r'```[\w]*\n(.*?)```', response_text, re.DOTALL)
            if code_blocks:
                candidate_code = code_blocks[0].strip()
                # Everything else is explanation
                candidate_explanation = re.sub(r'```[\w]*\n.*?```', '', response_text, flags=re.DOTALL).strip()
            else:
                # For explanation questions, entire response is the explanation
                if current_question.question_type == 'coding_explain':
                    candidate_explanation = response_text.strip()
                else:
                    # For other types, assume entire response is code
                    candidate_code = response_text.strip()

        # Create question entry
        question_entry = {
            "question_id": current_question.question_id,
            "question_title": question_title,
            "question_type": current_question.question_type,
            "technology": technology,
            "expected_output": expected_output,
            "candidate_code": candidate_code,
            "candidate_explanation": candidate_explanation,
            "candidate_full_response": response_text
        }

        # Update existing question or append new one (prevents duplicates when re-submitting)
        existing_index = next(
            (i for i, q in enumerate(coding_data["questions"])
             if q.get("question_id") == current_question.question_id),
            None
        )

        if existing_index is not None:
            # Update existing entry (user re-submitted same question)
            coding_data["questions"][existing_index] = question_entry
            print(f"✏️  Updated existing Q{current_question.question_id}")
        else:
            # New question - append
            coding_data["questions"].append(question_entry)
            print(f"➕ Added new Q{current_question.question_id}")

        # Write back to file
        with open(filepath, 'w') as f:
            json.dump(coding_data, f, indent=2)

        print(f"✅ Coding response saved to: {filepath}")
        print(f"   Question {current_question.question_id}: {question_title}")
        print(f"   Technology: {technology}")
        print(f"   Expected Output: {expected_output or '(none)'}")
    except Exception as e:
        print(f"❌ Error saving coding response: {e}")


# ============================================================================
# ROUTES
# ============================================================================

@coding_bp.route('/', methods=['GET'])
def home():
    """API information endpoint"""
    initialize_coding_module()

    return jsonify({
        'message': 'Coding Interview API',
        'version': '2.0',
        'endpoints': [
            '/coding/start',
            '/coding/submit',
            '/coding/evaluate',
            '/coding/status'
        ]
    })


@coding_bp.route('/start', methods=['GET'])
def start_coding_interview():
    """Start the coding interview session (job description only, no CV needed)"""
    # Initialize module on first request
    initialize_coding_module()

    print("=== CODING INTERVIEW: START ROUTE HIT ===")

    try:
        # Load job description from file
        upload_folder = get_upload_folder()
        job_description_path = os.path.join(upload_folder, 'job_description.txt')

        if os.path.exists(job_description_path):
            with open(job_description_path, 'r', encoding='utf-8') as f:
                job_description = f.read()
        else:
            return jsonify({'error': 'No job description found. Please add job_description.txt to uploads folder.'}), 400

        # Initialize coding interview (no CV needed)
        state = initialize_coding_interview(job_description)

        # Generate first question only
        first_question = generate_coding_question(state, 1)
        state.current_question = first_question
        state.current_question_count = 1

        # Initialize all_questions cache with first question
        if not hasattr(state, 'all_questions'):
            state.all_questions = []
        state.all_questions.append(first_question)
        print(f"➕ Cached question 1 in state (start)")

        # Test case generation removed - not needed for current evaluation approach
        test_cases_data = []

        # Store state in session
        session_data['coding_state'] = state.model_dump()

        # Prepare response data
        response_data = {
            'question_id': first_question.question_id,
            'question_type': first_question.question_type,
            'question': first_question.question_text,
            'question_count': state.current_question_count,
            'total_questions': state.total_questions,
            'complete': False,
            'test_cases': test_cases_data,
            'coding_test_filename': state.coding_test_filename  # Include for evaluation
        }

        # Add specific data based on question type
        if first_question.question_type == 'coding_debug' and first_question.debug_data:
            response_data.update({
                'title': first_question.debug_data.title,
                'context_paragraph': first_question.debug_data.context_paragraph,
                'task_instruction': first_question.debug_data.task_instruction,
                'expected_outcome': first_question.debug_data.expected_outcome,
                'expected_output': first_question.debug_data.expected_output,
                'buggy_code': first_question.debug_data.buggy_code,
                # Backward compatibility
                'description': first_question.debug_data.description,
                'expected_behavior': first_question.debug_data.expected_behavior,
                'context': first_question.debug_data.context
            })
        elif first_question.question_type == 'coding_explain' and first_question.explanation_data:
            response_data.update({
                'title': first_question.explanation_data.title,
                'context_paragraph': first_question.explanation_data.context_paragraph,
                'task_instruction': first_question.explanation_data.task_instruction,
                'expected_outcome': first_question.explanation_data.expected_outcome,
                'expected_output': first_question.explanation_data.expected_output,
                'working_code': first_question.explanation_data.working_code,
                # Backward compatibility
                'analysis_questions': first_question.explanation_data.analysis_questions,
                'context': first_question.explanation_data.context
            })
        elif first_question.question_type == 'db_schema' and first_question.db_schema_data:
            response_data.update({
                'title': first_question.db_schema_data.title,
                'context_paragraph': first_question.db_schema_data.context_paragraph,
                'task_instruction': first_question.db_schema_data.task_instruction,
                'expected_outcome': first_question.db_schema_data.expected_outcome,
                'requirements': first_question.db_schema_data.requirements,
                'db_technology': first_question.db_schema_data.db_technology,
                # Backward compatibility
                'scenario': first_question.db_schema_data.scenario,
                'task_description': first_question.db_schema_data.task_description,
                'expected_deliverable': first_question.db_schema_data.expected_deliverable,
                'context': first_question.db_schema_data.context
            })

        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR in start_coding_interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error starting coding interview: {str(e)}'}), 500


@coding_bp.route('/generate_question', methods=['GET'])
def generate_question_endpoint():
    """
    Generate a specific question on-demand (for navigation without submission)

    Query params:
        question_number: int (1-5) - Which question to generate

    Returns:
        Question data in standard format
    """
    initialize_coding_module()

    print("=== CODING INTERVIEW: GENERATE_QUESTION ROUTE HIT ===")

    try:
        question_number = request.args.get('question_number', type=int)

        if not question_number or question_number < 1 or question_number > 5:
            return jsonify({'error': 'Invalid question_number. Must be 1-5'}), 400

        # Get current state
        if 'coding_state' not in session_data:
            return jsonify({'error': 'No active coding session'}), 400

        state = CodingInterviewState(**session_data['coding_state'])

        # Generate the requested question
        print(f"Generating question {question_number} on-demand (navigation)")
        question = generate_coding_question(state, question_number)

        # Add to all_questions cache (for later retrieval during submission)
        if not hasattr(state, 'all_questions'):
            state.all_questions = []

        # Check if this question already exists in cache
        existing = next((q for q in state.all_questions if q.question_id == question.question_id), None)
        if not existing:
            state.all_questions.append(question)
            print(f"➕ Cached question {question_number} in state")
        else:
            print(f"✓ Question {question_number} already in cache")

        # Update state (but don't increment current_question_count - user is just navigating)
        session_data['coding_state'] = state.model_dump()

        # Prepare response data (same format as /start)
        response_data = {
            'question_id': question.question_id,
            'question_type': question.question_type,
            'question': question.question_text,
            'question_count': question_number,
            'total_questions': state.total_questions,
            'complete': False,
            'test_cases': []
        }

        # Add specific data based on question type
        if question.question_type == 'coding_debug' and question.debug_data:
            response_data.update({
                'title': question.debug_data.title,
                'context_paragraph': question.debug_data.context_paragraph,
                'task_instruction': question.debug_data.task_instruction,
                'expected_outcome': question.debug_data.expected_outcome,
                'expected_output': question.debug_data.expected_output,
                'buggy_code': question.debug_data.buggy_code,
                'description': question.debug_data.description,
                'expected_behavior': question.debug_data.expected_behavior,
                'context': question.debug_data.context
            })
        elif question.question_type == 'coding_explain' and question.explanation_data:
            response_data.update({
                'title': question.explanation_data.title,
                'context_paragraph': question.explanation_data.context_paragraph,
                'task_instruction': question.explanation_data.task_instruction,
                'expected_outcome': question.explanation_data.expected_outcome,
                'expected_output': question.explanation_data.expected_output,
                'working_code': question.explanation_data.working_code,
                'analysis_questions': question.explanation_data.analysis_questions,
                'context': question.explanation_data.context
            })
        elif question.question_type == 'db_schema' and question.db_schema_data:
            response_data.update({
                'title': question.db_schema_data.title,
                'context_paragraph': question.db_schema_data.context_paragraph,
                'task_instruction': question.db_schema_data.task_instruction,
                'expected_outcome': question.db_schema_data.expected_outcome,
                'requirements': question.db_schema_data.requirements,
                'db_technology': question.db_schema_data.db_technology,
                'scenario': question.db_schema_data.scenario,
                'task_description': question.db_schema_data.task_description,
                'expected_deliverable': question.db_schema_data.expected_deliverable,
                'context': question.db_schema_data.context
            })

        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR in generate_question_endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating question: {str(e)}'}), 500


@coding_bp.route('/submit', methods=['POST'])
def submit_coding_response():
    """Submit coding response and get next question"""
    # Initialize module if needed
    initialize_coding_module()

    print("=== CODING INTERVIEW: SUBMIT RESPONSE ROUTE HIT ===")

    try:
        data = request.get_json()
        response_text = data.get('response', '')

        if not response_text.strip():
            return jsonify({'error': 'No response provided'}), 400

        # Get current state
        if 'coding_state' not in session_data:
            return jsonify({'error': 'No active coding session'}), 400

        state = CodingInterviewState(**session_data['coding_state'])

        # DEBUG: Check if state reconstruction preserved all_questions
        print(f"🔍 State reconstructed from session:")
        print(f"   - all_questions in session: {'all_questions' in session_data['coding_state']}")
        if 'all_questions' in session_data['coding_state']:
            print(f"   - all_questions count in session: {len(session_data['coding_state']['all_questions'])}")

        # Get question number from frontend (which question is being submitted)
        question_number = data.get('question_number', state.current_question_count)

        # DEBUG: Log cache state
        print(f"🔍 DEBUG: Searching for question {question_number}")
        print(f"   - has all_questions attr: {hasattr(state, 'all_questions')}")
        if hasattr(state, 'all_questions') and state.all_questions:
            print(f"   - all_questions length: {len(state.all_questions)}")
            print(f"   - all_questions IDs: {[q.question_id for q in state.all_questions]}")
            print(f"   - question_number type: {type(question_number)}")
        else:
            print(f"   - all_questions is empty or missing!")

        # Find the correct question object
        question_to_save = None

        # Try to find from all_questions list (if available)
        if hasattr(state, 'all_questions') and state.all_questions:
            for q in state.all_questions:
                # FIXED: Type-safe comparison (ensure both are integers)
                if int(q.question_id) == int(question_number):
                    question_to_save = q
                    print(f"✅ Found question {question_number} from all_questions cache")
                    break

        # Fallback to current_question if not found
        if not question_to_save:
            question_to_save = state.current_question
            print(f"⚠️  Using fallback current_question (ID: {state.current_question.question_id if state.current_question else 'None'})")
            print(f"⚠️  This means question {question_number} was NOT found in all_questions cache!")

        # Save the question and response to JSON file
        if question_to_save:
            save_coding_response(
                state.coding_test_filename,
                question_to_save,
                response_text,
                candidate_name="Candidate"
            )
        else:
            print("❌ ERROR: No question object available to save!")

        print(f"Question {question_number} response saved: {response_text[:100]}...")

        # Return simple success response - NO question generation
        # Frontend handles all question generation via /generate_question endpoint
        response_data = {
            'success': True,
            'message': 'Answer submitted successfully',
            'question_count': state.current_question_count,
            'total_questions': state.total_questions,
            'complete': False  # Frontend "Complete Interview" button triggers evaluation
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR in submit_coding_response: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing response: {str(e)}'}), 500


@coding_bp.route('/evaluate', methods=['POST'])
def evaluate_coding_interview_route():
    """
    Manually trigger coding interview evaluation or save violation data
    """
    # Initialize module if needed
    initialize_coding_module()

    print("=== CODING INTERVIEW: EVALUATE ROUTE HIT ===")

    try:
        data = request.get_json()

        # Check if this is a violation save (partial interview data)
        if data.get('disqualified') or data.get('violation_details'):
            print("Saving partial coding interview due to security violation")
            try:
                interviews_folder = get_interviews_folder()
                os.makedirs(interviews_folder, exist_ok=True)

                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                filename = f"coding-interview-violation-{timestamp}.json"
                filepath = os.path.join(interviews_folder, filename)

                # Build partial interview data
                partial_data = {
                    "metadata": {
                        "status": "disqualified",
                        "reason": "security_violation",
                        "timestamp": data.get('timestamp', datetime.now().isoformat()),
                        "question_count": data.get('question_count', 0),
                        "incomplete": True
                    },
                    "violation_details": data.get('violation_details', {}),
                    "interview_log": data.get('interview_log', [])
                }

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(partial_data, f, indent=2, ensure_ascii=False)

                print(f"Partial coding interview saved: {filepath}")
                return jsonify({
                    'success': True,
                    'message': 'Partial interview data saved',
                    'filename': filename
                }), 200

            except Exception as e:
                print(f"Error saving partial coding interview: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500

        # Regular evaluation flow
        coding_test_filename = data.get('coding_test_filename')

        if not coding_test_filename:
            return jsonify({'error': 'No coding_test_filename provided'}), 400

        # Run evaluation
        upload_folder = get_upload_folder()
        interviews_folder = get_interviews_folder()

        evaluation_result = evaluate_coding_interview(
            coding_test_filename,
            upload_folder,
            interviews_folder
        )

        return jsonify(evaluation_result)

    except Exception as e:
        print(f"ERROR in evaluate_coding_interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error evaluating interview: {str(e)}'
        }), 500


@coding_bp.route('/status', methods=['GET'])
def get_coding_status():
    """Get current coding interview status"""
    # Initialize module if needed
    initialize_coding_module()

    try:
        if 'coding_state' not in session_data:
            return jsonify({
                'active': False,
                'message': 'No active coding interview session'
            })

        state = CodingInterviewState(**session_data['coding_state'])

        response_data = {
            'active': True,
            'current_question': state.current_question_count,
            'total_questions': state.total_questions,
            'difficulty_level': state.difficulty_score,
            'progress_percentage': (state.current_question_count / state.total_questions) * 100
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR in get_coding_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error getting status: {str(e)}'}), 500


# ============================================================================
# BLUEPRINT CONFIGURATION
# ============================================================================

print("✅ Coding interview routes blueprint created")
print(f"   Routes registered under '/coding' prefix")
print(f"   - GET  /coding/")
print(f"   - GET  /coding/start")
print(f"   - GET  /coding/generate_question")
print(f"   - POST /coding/submit")
print(f"   - POST /coding/evaluate")
print(f"   - GET  /coding/status")
