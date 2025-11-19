"""
Oral Interview Routes Blueprint
Flask routes for conversational technical interviews
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import os
import json
import re

# Import from shared modules
from shared.models import StructuredCV, StructuredJobDescription
from shared.information_extraction import (
    parse_pdf_cv,
    parse_txt_job_description,
    extract_technologies_from_cv
)
from shared.cv_analysis import calculate_difficulty_score
from shared.llm_setup import get_llm

# Import from oral interview module
from .question_generator import (
    DialogueState,
    load_oral_prompts,
    generate_dialogue_question,
    process_dialogue_turn,
    save_oral_interview
)

# Import evaluator
from .evaluator import evaluate_oral_interview


# Create Blueprint
oral_bp = Blueprint('oral', __name__, url_prefix='/oral')


# ============================================================================
# MODULE-LEVEL STATE (Lazy Initialization)
# ============================================================================

_llm = None
_prompts_loaded = False

# Global state management (per-session)
current_dialogue_state: dict = None
current_cv_session: dict = None


def initialize_oral_module():
    """
    Lazy initialization of oral interview module
    Called on first route access
    """
    global _llm, _prompts_loaded

    if not _llm:
        print("🔄 Initializing oral interview LLM...")
        _llm = get_llm()
        print("✅ LLM initialized")

    if not _prompts_loaded:
        print("🔄 Loading oral interview prompts...")
        load_oral_prompts()
        _prompts_loaded = True
        print("✅ Prompts loaded")


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
    """Get oral interviews folder path (use data/interviews/oral/)"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'interviews',
        'oral'
    )


def get_audio_folder():
    """Get audio folder path (use data/interviews/oral/audio/)"""
    return os.path.join(get_interviews_folder(), 'audio')


# Ensure directories exist
os.makedirs(get_upload_folder(), exist_ok=True)
os.makedirs(get_interviews_folder(), exist_ok=True)
os.makedirs(get_audio_folder(), exist_ok=True)


# ============================================================================
# ROUTES
# ============================================================================

@oral_bp.route('/upload_cv', methods=['POST', 'OPTIONS'])
def upload_cv():
    """Handle CV upload for oral interview system"""
    global current_cv_session

    # Initialize module on first request
    initialize_oral_module()

    print("=== ORAL INTERVIEW: UPLOAD_CV ROUTE HIT ===")

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 204

    try:
        # Check for CV file
        if 'cv' not in request.files:
            print("ERROR: No 'cv' in request.files")
            return jsonify({'success': False, 'error': 'No CV file provided'}), 400

        cv_file = request.files['cv']
        print(f"CV file received: {cv_file.filename}")

        if cv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not cv_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

        # Save the uploaded file
        upload_folder = get_upload_folder()
        cv_filename = 'uploaded_cv_oral.pdf'
        cv_path = os.path.join(upload_folder, cv_filename)
        print(f"Saving CV file to: {cv_path}")
        cv_file.save(cv_path)

        # Parse the PDF CV
        print("Starting PDF parsing...")
        llm = get_llm()
        structured_cv = parse_pdf_cv(cv_path, llm)
        print("PDF parsing completed")

        # Load and parse job description to structured format
        job_description_path = os.path.join(upload_folder, 'job_description.txt')
        if os.path.exists(job_description_path):
            print("Parsing job description...")
            # Parse to structured format for proper difficulty calculation
            structured_job = parse_txt_job_description(job_description_path, llm)
            # Also keep text version for dialogue state
            with open(job_description_path, 'r', encoding='utf-8') as f:
                job_description = f.read()
            print("Job description parsed successfully")
        else:
            print("No job description file found, using defaults")
            # Create minimal structured job with defaults
            structured_job = StructuredJobDescription(
                job_title="Unknown Position",
                seniority_level="mid",
                domain="general"
            )
            job_description = "No job description provided"

        # Calculate difficulty with structured job object (correct type)
        difficulty_score = calculate_difficulty_score(structured_cv, structured_job)

        # Store in session
        current_cv_session = {
            'structured_cv': structured_cv,
            'job_description': job_description,
            'difficulty_score': difficulty_score
        }

        # Save structured CV data
        cv_data_path = os.path.join(upload_folder, 'structured_cv_oral.json')
        with open(cv_data_path, 'w', encoding='utf-8') as f:
            json.dump(structured_cv.model_dump(), f, indent=2)

        print("CV session stored successfully")

        return jsonify({
            'success': True,
            'experiences_count': len(structured_cv.experiences),
            'education_count': len(structured_cv.education),
            'skills_count': len(structured_cv.skills),
            'projects_count': len(structured_cv.projects)
        })

    except Exception as e:
        print(f"ERROR in upload_cv: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@oral_bp.route('/start', methods=['GET'])
def start_oral_interview():
    """Initialize conversational interview"""
    global current_dialogue_state, current_cv_session

    # Initialize module on first request
    initialize_oral_module()

    print("=" * 70)
    print("🎤 START ORAL INTERVIEW ROUTE HIT")
    print("=" * 70)

    try:
        # Check if CV has been uploaded
        if not current_cv_session:
            print("❌ ERROR: No CV session found")
            return jsonify({"error": "Please upload CV first"}), 400

        if not current_cv_session.get('structured_cv'):
            print("❌ ERROR: No structured CV in session")
            return jsonify({"error": "Please upload CV first"}), 400

        print("✅ CV session found")

        # Initialize dialogue state
        structured_cv = current_cv_session['structured_cv']
        job_description = current_cv_session['job_description']
        difficulty_score = current_cv_session.get('difficulty_score', 5)

        print(f"📄 CV: {structured_cv.personal_info.name}")
        print(f"📝 Job description: {len(job_description)} chars")
        print(f"⚡ Difficulty: {difficulty_score}")

        # Generate filename
        candidate_name = structured_cv.personal_info.name or "candidate"
        safe_name = re.sub(r'[^\w\s-]', '', candidate_name).strip().replace(' ', '-')
        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        filename = f"oral-{safe_name}-{timestamp}.json"

        print(f"📁 Interview filename: {filename}")

        current_dialogue_state = DialogueState(
            complete=False,
            job_description=job_description,
            structured_cv=structured_cv,
            difficulty_score=difficulty_score,
            conversation_history=[],
            current_turn=0,  # Start at 0 for opening question
            interview_start_time=datetime.now().isoformat(),
            matched_technologies=extract_technologies_from_cv(structured_cv),
            topics_covered=[],
            depth_scores={},
            asked_question_categories=[],  # Track question categories
            current_section="opening",  # Track current section
            audio_files=[],
            interview_filename=filename
        )

        print("✅ Dialogue state initialized")

        # Generate first question
        print("🤖 Generating first question...")
        first_question = generate_dialogue_question(current_dialogue_state)
        print(f"✅ First question generated: {first_question[:100]}...")

        # Save question to history
        current_dialogue_state["conversation_history"].append({
            "speaker": "interviewer",
            "text": first_question,
            "timestamp": datetime.now().isoformat(),
            "turn": 0
        })

        # Increment turn after opening question
        current_dialogue_state["current_turn"] = 1

        print("✅ Returning response to frontend")
        print("=" * 70)

        return jsonify({
            "success": True,
            "question": first_question,
            "turn": 1
        })

    except Exception as e:
        print(f"❌ ERROR starting oral interview: {e}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return jsonify({"error": str(e)}), 500


@oral_bp.route('/continue', methods=['POST', 'OPTIONS'])
def continue_oral_interview():
    """
    Receive candidate response, return next question
    """
    global current_dialogue_state

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 204

    # Initialize module if needed
    initialize_oral_module()

    if not current_dialogue_state:
        return jsonify({"error": "Interview not started"}), 400

    try:
        data = request.json
        candidate_response = data.get('response', '').strip()

        if not candidate_response:
            return jsonify({"error": "Empty response"}), 400

        # Process turn
        result = process_dialogue_turn(current_dialogue_state, candidate_response)

        return jsonify(result)

    except Exception as e:
        print(f"Error continuing interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@oral_bp.route('/complete', methods=['POST', 'OPTIONS'])
def complete_oral_interview():
    """Save final dialogue to JSON file"""
    global current_dialogue_state

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 204

    # Initialize module if needed
    initialize_oral_module()

    # Check if this is a violation save (partial interview data)
    data = request.get_json() or {}
    if data.get('disqualified') or data.get('violation_details'):
        print("Saving partial oral interview due to security violation")
        try:
            interviews_folder = get_interviews_folder()
            os.makedirs(interviews_folder, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = f"oral-interview-violation-{timestamp}.json"
            filepath = os.path.join(interviews_folder, filename)

            # Build partial interview data
            partial_data = {
                "metadata": {
                    "status": "disqualified",
                    "reason": "security_violation",
                    "timestamp": data.get('timestamp', datetime.now().isoformat()),
                    "current_turn": data.get('current_turn', 0),
                    "incomplete": True
                },
                "violation_details": data.get('violation_details', {}),
                "conversation": current_dialogue_state.get('conversation_history', []) if current_dialogue_state else []
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(partial_data, f, indent=2, ensure_ascii=False)

            print(f"Partial oral interview saved: {filepath}")
            return jsonify({
                'success': True,
                'message': 'Partial interview data saved',
                'filename': filename,
                'filepath': filepath
            }), 200

        except Exception as e:
            print(f"Error saving partial oral interview: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # Regular interview completion
    if not current_dialogue_state:
        return jsonify({"error": "No interview to complete"}), 400

    try:
        # Save conversation
        interviews_folder = get_interviews_folder()
        filepath = save_oral_interview(current_dialogue_state, interviews_folder)

        # Return file path
        return jsonify({
            "success": True,
            "filepath": filepath,
            "message": "Interview saved successfully"
        })

    except Exception as e:
        print(f"Error completing interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@oral_bp.route('/upload_audio', methods=['POST', 'OPTIONS'])
def upload_oral_audio():
    """Receive and save audio file for a specific turn"""
    global current_dialogue_state

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 204

    # Initialize module if needed
    initialize_oral_module()

    if not current_dialogue_state:
        return jsonify({"error": "No active interview"}), 400

    try:
        audio_file = request.files.get('audio')
        turn_number = request.form.get('turn')
        timestamp = request.form.get('timestamp')

        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400

        # Create audio directory if it doesn't exist
        audio_dir = get_audio_folder()
        os.makedirs(audio_dir, exist_ok=True)

        # Save audio file
        filename = f"oral-interview-q{turn_number}-{timestamp}.webm"
        filepath = os.path.join(audio_dir, filename)
        audio_file.save(filepath)

        # Track audio file
        current_dialogue_state["audio_files"].append(filename)

        return jsonify({
            "success": True,
            "filename": filename
        })

    except Exception as e:
        print(f"Error uploading audio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@oral_bp.route('/evaluate', methods=['POST', 'OPTIONS'])
def evaluate_oral_route():
    """Evaluate completed oral interview"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 204

    # Initialize module if needed
    initialize_oral_module()

    try:
        data = request.json
        interview_filename = data.get('interview_filename')

        if not interview_filename:
            return jsonify({'error': 'interview_filename required'}), 400

        # Build full path
        interviews_folder = get_interviews_folder()
        interview_path = os.path.join(interviews_folder, interview_filename)

        # Check if file exists
        if not os.path.exists(interview_path):
            return jsonify({'error': f'Interview file not found: {interview_filename}'}), 404

        # Run evaluation
        report = evaluate_oral_interview(interview_path)

        return jsonify({
            'success': True,
            'overall_score': report.overall_score,
            'report': report.model_dump()
        })

    except Exception as e:
        print(f"Error evaluating interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BLUEPRINT CONFIGURATION
# ============================================================================

print("✅ Oral interview routes blueprint created")
print(f"   Routes registered under '/oral' prefix")
print(f"   - POST /oral/upload_cv")
print(f"   - GET  /oral/start")
print(f"   - POST /oral/continue")
print(f"   - POST /oral/complete")
print(f"   - POST /oral/upload_audio")
print(f"   - POST /oral/evaluate")
