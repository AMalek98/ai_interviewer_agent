"""
Text Interview Module

A modular text-based interview system for assessing candidates.

This module provides:
- Interview state management
- Question generation (open and QCM)
- Response processing
- Flask route handlers

Usage:
    from text_interview import register_text_routes

    app = Flask(__name__)
    register_text_routes(app)
"""

import os

# Import public functions from submodules
from .routes import start_interview, submit_response, record
from .managers import (
    initialize_interview, end_interview,
    load_interview_prompts, get_prompt_template,
    get_current_interview, set_current_interview, clear_current_interview,
    interview_prompts
)
from .generators import generate_question
from .processors import process_response, should_continue
from .utils import *

# Module version
__version__ = '1.0.0'

# Public API
__all__ = [
    'register_text_routes',
    'initialize_text_interview',
    # Route handlers
    'start_interview',
    'submit_response',
    'record',
    # Managers
    'initialize_interview',
    'end_interview',
    'load_interview_prompts',
    'get_prompt_template',
    # Generators
    'generate_question',
    # Processors
    'process_response',
    'should_continue',
]


def initialize_text_interview(flask_app=None):
    """
    Initialize text interview module (lazy loading).
    Load prompts and create necessary directories.

    Args:
        flask_app: Optional Flask app instance for config access
    """
    # Load interview prompts if not already loaded
    if interview_prompts is None:
        load_interview_prompts()

    # Ensure directories exist
    # Use hardcoded paths if no Flask app provided (consistent with current behavior)
    if flask_app and hasattr(flask_app, 'config'):
        upload_folder = flask_app.config.get('UPLOAD_FOLDER', 'C:\\Users\\Mega-PC\\Desktop\\ai_interviewer\\uploads')
        audio_folder = flask_app.config.get('AUDIO_FOLDER', '../static/audio')
    else:
        upload_folder = 'C:\\Users\\Mega-PC\\Desktop\\ai_interviewer\\uploads'
        audio_folder = '../static/audio'

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(audio_folder, exist_ok=True)

    # Ensure interviews directory exists
    interviews_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "interviews")
    os.makedirs(interviews_dir, exist_ok=True)

    print("✅ Text interview module initialized")


def register_text_routes(flask_app):
    """
    Register text interview routes on the provided Flask app instance.
    This allows text interview routes to be used in main.py unified server.

    Args:
        flask_app: The Flask app instance to register routes on
    """
    # Initialize the module
    initialize_text_interview(flask_app)

    # Register the route handlers on the provided app
    # Using unique endpoint names to avoid conflicts

    flask_app.add_url_rule(
        '/start_interview',
        'text_start_interview',
        start_interview,
        methods=['GET']
    )

    flask_app.add_url_rule(
        '/submit_response',
        'text_submit_response',
        submit_response,
        methods=['POST', 'OPTIONS']
    )

    flask_app.add_url_rule(
        '/record',
        'text_record',
        record,
        methods=['POST']
    )

    print("✅ Text interview routes registered on unified server")
