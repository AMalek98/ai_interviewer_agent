"""Text Interview - Flask Route Handlers

HTTP endpoints for text-based interview system:
- /start_interview - Initialize interview and get first question
- /submit_response - Process response and get next question
- /record - Handle transcriptions and security violations
"""

from flask import request, jsonify
import os
import json
from datetime import datetime
from typing import Dict, Any

# Import from shared module
from shared.models import InterviewState, InterviewQuestion, StructuredJobDescription
from shared.information_extraction import parse_txt_job_description

# Import from sibling modules
from .managers import (
    get_current_interview, set_current_interview, interview_lock,
    initialize_interview, end_interview, load_interview_prompts, interview_prompts)
from .generators import generate_question
from .processors import process_response, should_continue
from .utils import prepare_question_response

# Get LLM instance from shared module
from shared.llm_setup import get_llm
llm = get_llm()


# ============================================================================
# PATH CONFIGURATION (Like coding_interview pattern)
# ============================================================================

def get_text_interviews_folder():
    """Get text interviews folder path - all files in one place"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'interviews',
        'text'
    )

# Ensure directory exists
os.makedirs(get_text_interviews_folder(), exist_ok=True)


def start_interview():
    print("=== START_INTERVIEW ROUTE HIT ===")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")

    try:
        print("Processing start interview request...")

        # Parse and load structured job description
        print("Parsing job description...")
        # Use hardcoded paths (consistent with current app.py behavior)
        uploads_folder = 'C:\\Users\\Mega-PC\\Desktop\\ai_interviewer\\backend\\data\\uploads'
        job_desc_txt_path = os.path.join(uploads_folder, 'job_description.txt')
        job_data_path = os.path.join(uploads_folder, 'structured_job_description.json')

        # Check if we need to re-parse or can load from JSON
        structured_job = None
        if os.path.exists(job_data_path):
            print("Structured job description JSON found, loading...")
            try:
                with open(job_data_path, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    structured_job = StructuredJobDescription(**job_data)
                    print("Loaded structured job description from JSON")
            except Exception as e:
                print(f"Error loading structured job description JSON: {e}")
                structured_job = None

        # If no JSON or loading failed, parse the TXT file
        if structured_job is None:
            print("Parsing job description from TXT file...")
            structured_job = parse_txt_job_description(job_desc_txt_path, llm)

            # Save structured job data for future use
            print("Saving structured job description to JSON...")
            with open(job_data_path, 'w', encoding='utf-8') as f:
                json.dump(structured_job.model_dump(), f, indent=2)
            print("Structured job description saved successfully")

        # CV is now OPTIONAL - job-only interview mode
        print("CV is optional in job-only mode - skipping CV loading")
        structured_cv = None  # Will create dummy CV in initialize_interview()

        # Initialize the enhanced interview state with structured data (CV is optional)
        print("Creating enhanced interview state (job-only mode)...")
        state = initialize_interview(structured_job, structured_cv)
        print(f"Interview state created - Difficulty: {state['difficulty_score']} (job-based)")

        # Load interview prompts if not already loaded
        if not interview_prompts:
            load_interview_prompts()

        print("Generating first question...")
        # Generate the first question
        result = generate_question(state)
        print("First question generated successfully")

        if result.get("complete", False):
            print("Interview marked as complete immediately - this shouldn't happen")
            return jsonify({"error": "Interview initialization failed"}), 500

        # Extract question data
        current_question = result["current_question"]
        phase = result.get("phase", "open")
        question_count = result.get("question_count", 1)

        print(f"Generated {phase} question #{question_count}")

        # Set the global interview state
        print("Setting global interview state...")
        set_current_interview({"state": state})
        print("Global interview state set successfully")

        # Prepare response based on question type
        response_data = prepare_question_response(current_question, phase, question_count)
        print(f"Returning response for {current_question.question_type} question")
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in start_interview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def add_enhanced_response_data(response_data: dict, state: InterviewState) -> dict:
    """Add Phase 5 enhanced data to API responses for frontend integration"""

    # Add experience focus information
    current_experience_focus = state.get("current_experience_focus")
    selected_experiences = state.get("selected_experiences", [])

    if current_experience_focus is not None and current_experience_focus < len(selected_experiences):
        experience = selected_experiences[current_experience_focus]
        response_data["experience_focus"] = {
            "experience_index": current_experience_focus,
            "company": experience.company,
            "position": experience.position,
            "duration": experience.duration,
            "technologies": experience.technologies
        }
    else:
        response_data["experience_focus"] = None

    # Add interview progress information (15-question structure)
    phase_question_count = state.get("phase_question_count", {})
    response_data["progress"] = {
        "total_questions": state.get("total_question_count", 0),
        "max_total_questions": 10,  # 5 open + 5 qcm (coding moved to separate agent)
        "current_phase": state.get("current_phase", "open"),
        "phase_progress": {
            "open": {"current": phase_question_count.get("open", 0), "max": 5},
            "qcm": {"current": phase_question_count.get("qcm", 0), "max": 5}
            # "coding": {"current": phase_question_count.get("coding", 0), "max": 5} - moved to separate agent
        }
    }

    # Add follow-up context information if available
    responses_history = state.get("responses_history", [])
    if responses_history:
        last_response = responses_history[-1]
        if hasattr(last_response, 'extracted_technologies') and hasattr(last_response, 'key_topics'):
            response_data["last_response_analysis"] = {
                "extracted_technologies": last_response.extracted_technologies,
                "key_topics": last_response.key_topics,
                "experience_index": last_response.experience_index
            }

    # Add context for follow-up questions (Q2, Q4)
    current_question_count = response_data.get("question_count", 0)
    current_phase = response_data.get("phase", "open")

    if current_phase == "open" and current_question_count in [2, 4]:
        # This is a follow-up question
        response_data["is_followup_question"] = True

        # Get previous question and answer for context
        questions_history = state.get("questions_history", [])
        if len(questions_history) >= 2:
            previous_question = questions_history[-2]
            if responses_history:
                previous_response = responses_history[-1]
                response_data["followup_context"] = {
                    "previous_question": previous_question.question_text,
                    "previous_answer_summary": previous_response.response_text[:100] + "..." if len(previous_response.response_text) > 100 else previous_response.response_text,
                    "mentioned_technologies": getattr(previous_response, 'extracted_technologies', [])
                }
    else:
        response_data["is_followup_question"] = False

    # Add difficulty and technology information
    response_data["interview_context"] = {
        "difficulty_score": state.get("difficulty_score", 5),
        "matched_technologies": state.get("matched_technologies", []),
        "preferred_languages": state.get("preferred_languages", [])
    }

    return response_data


def submit_response():
    print("=== SUBMIT_RESPONSE ROUTE HIT ===")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        print("Handling OPTIONS preflight request")
        response = jsonify({'status': 'preflight accepted'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, X-Requested-With')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 204

    # Handle POST request
    print("Processing POST request for submit_response")
    data = request.json
    print(f"Request data: {data}")

    user_response = data.get('response', '')
    qcm_selected = data.get('qcm_selected', None)  # For single-choice QCM questions
    qcm_selected_multiple = data.get('qcm_selected_multiple', None)  # For multiple-choice MCQ questions
    print(f"User response: {user_response}")
    if qcm_selected:
        print(f"QCM selected (single): {qcm_selected}")
    if qcm_selected_multiple:
        print(f"QCM selected (multiple): {qcm_selected_multiple}")

    with interview_lock:
        print("Checking for active interview...")
        current_interview = get_current_interview()
        if not current_interview:
            print("ERROR: No active interview found")
            response = jsonify({'error': 'No active interview'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            return response, 400

        print("Active interview found, processing response...")
        current_state = current_interview["state"]
        current_question = current_state.get("current_question")

        if not current_question:
            print("ERROR: No current question found")
            response = jsonify({'error': 'No active question to respond to'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            return response, 400

        print(f"Processing response for {current_question.question_type} question")

        # Process the response
        process_result = process_response(current_state, user_response, qcm_selected, qcm_selected_multiple)
        if process_result.get("error"):
            print(f"Error processing response: {process_result['error']}")
            response = jsonify(process_result)
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            return response, 400

        print("Response processed successfully")

        # Check if we should continue or end
        print("Checking if we should continue...")
        next_action = should_continue(current_state)
        print(f"Next action: {next_action}")

        if next_action == "generate_question":
            print("Generating next question...")
            # Generate next question
            result = generate_question(current_state)

            if result.get("complete", False):
                print("Interview completed")
                summary = end_interview(current_state)

                # Load evaluation report to send to frontend
                # Use filenames stored in state (created during end_interview)
                evaluation_filename = current_state.get("evaluation_filename")
                interview_filename = current_state.get("interview_filename")

                evaluation_data = None
                try:
                    if evaluation_filename:
                        evaluation_path = os.path.join(get_text_interviews_folder(), evaluation_filename)
                        if os.path.exists(evaluation_path):
                            with open(evaluation_path, 'r', encoding='utf-8') as f:
                                evaluation_data = json.load(f)
                            print(f"Loaded evaluation report: {evaluation_filename}")

                        # Also load interview JSON to get detailed QCM question data
                        if interview_filename:
                            interview_path = os.path.join(get_text_interviews_folder(), interview_filename)

                            if os.path.exists(interview_path):
                                with open(interview_path, 'r', encoding='utf-8') as f:
                                    interview_data = json.load(f)

                                # Extract QCM question details
                                qcm_question_details = []
                                for question in interview_data.get("questions", []):
                                    if question.get("type") == "qcm":
                                        qcm_detail = {
                                            "question_id": question.get("question_id"),
                                            "question_text": question.get("question_text"),
                                            "user_answer": question.get("selected_answer", ""),
                                            "correct_answer": question.get("correct_answer", ""),
                                            "correct_answers": question.get("correct_answers", []),
                                            "is_correct": question.get("is_correct", False),
                                            "is_multiple_choice": question.get("is_multiple_choice", False),
                                            "options": question.get("options", [])
                                        }
                                        qcm_question_details.append(qcm_detail)

                                # Add to evaluation data
                                evaluation_data["qcm_question_details"] = qcm_question_details
                                print(f"Added {len(qcm_question_details)} QCM question details to evaluation")
                            else:
                                print(f"Warning: Interview JSON not found at {interview_path}")
                    else:
                        print(f"Warning: Evaluation report not found at {evaluation_path}")
                except Exception as e:
                    print(f"Error loading evaluation report: {e}")

                response_data = {
                    'complete': True,
                    'message': 'Interview completed successfully',
                    'summary': summary,
                    'evaluation': evaluation_data
                }
            else:
                print("Next question generated successfully")
                current_question = result["current_question"]
                phase = result.get("phase", "unknown")
                question_count = result.get("question_count", 0)

                print(f"Generated {phase} question #{question_count}: {current_question.question_type}")

                # Update interview state
                set_current_interview({"state": current_state})

                # Prepare response
                response_data = prepare_question_response(current_question, phase, question_count)

                # Phase 6: Add enhanced response data and experience focus information
                response_data = add_enhanced_response_data(response_data, current_state)

            print(f"Returning response: {response_data.get('question_type', 'completion')} response")
            response = jsonify(response_data)

        else:
            print("Ending interview...")
            summary = end_interview(current_state)

            # Load evaluation report to send to frontend
            # Use filenames stored in state (created during end_interview)
            evaluation_filename = current_state.get("evaluation_filename")
            interview_filename = current_state.get("interview_filename")

            evaluation_data = None
            try:
                if evaluation_filename:
                    evaluation_path = os.path.join(get_text_interviews_folder(), evaluation_filename)
                    if os.path.exists(evaluation_path):
                        with open(evaluation_path, 'r', encoding='utf-8') as f:
                            evaluation_data = json.load(f)
                        print(f"Loaded evaluation report: {evaluation_filename}")

                    # Also load interview JSON to get detailed QCM question data
                    if interview_filename:
                        interview_path = os.path.join(os.path.dirname(__file__), "interviews", interview_filename)

                    if os.path.exists(interview_path):
                        with open(interview_path, 'r', encoding='utf-8') as f:
                            interview_data = json.load(f)

                        # Extract QCM question details
                        qcm_question_details = []
                        for question in interview_data.get("questions", []):
                            if question.get("type") == "qcm":
                                qcm_detail = {
                                    "question_id": question.get("question_id"),
                                    "question_text": question.get("question_text"),
                                    "user_answer": question.get("selected_answer", ""),
                                    "correct_answer": question.get("correct_answer", ""),
                                    "correct_answers": question.get("correct_answers", []),
                                    "is_correct": question.get("is_correct", False),
                                    "is_multiple_choice": question.get("is_multiple_choice", False),
                                    "options": question.get("options", [])
                                }
                                qcm_question_details.append(qcm_detail)

                        # Add to evaluation data
                        evaluation_data["qcm_question_details"] = qcm_question_details
                        print(f"Added {len(qcm_question_details)} QCM question details to evaluation")
                    else:
                        print(f"Warning: Interview JSON not found at {interview_path}")
                else:
                    print(f"Warning: Evaluation report not found at {evaluation_path}")
            except Exception as e:
                print(f"Error loading evaluation report: {e}")

            response_data = {
                'complete': True,
                'message': 'Interview completed successfully',
                'summary': summary,
                'evaluation': evaluation_data
            }
            print("Returning interview complete response with evaluation data")
            response = jsonify(response_data)

        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        print("Added CORS headers, returning response")
        return response


def record():
    print("=== RECORD ROUTE HIT ===")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")

    data = request.get_json()
    print(f"Request data: {data}")

    # Check if this is a violation save (partial interview data)
    if data.get('disqualified') or data.get('violation_details'):
        print("Saving partial interview due to security violation")
        try:
            interviews_dir = os.path.join(os.path.dirname(__file__), "data", "interviews", "text")
            os.makedirs(interviews_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = f"interview-violation-{timestamp}.json"
            filepath = os.path.join(interviews_dir, filename)

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

            print(f"Partial interview saved: {filepath}")
            return jsonify({
                'success': True,
                'message': 'Partial interview data saved',
                'filename': filename
            }), 200

        except Exception as e:
            print(f"Error saving partial interview: {e}")
            return jsonify({'error': str(e)}), 500

    # Handle regular transcription (legacy behavior)
    transcription = data.get('transcription')
    print(f"Extracted transcription: {transcription}")

    if not transcription:
        print("ERROR: No transcription provided")
        return jsonify({'error': 'No transcription provided'}), 400

    print(f"Received transcription: {transcription}")
    print("Returning transcription response")

    return jsonify({'transcription': transcription})
