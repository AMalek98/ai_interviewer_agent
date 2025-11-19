"""
Centralized Configuration for Backend Paths
Provides consistent path resolution across all interview modules
"""

import os


# ============================================================================
# ROOT DIRECTORIES
# ============================================================================

# Backend root directory (parent of shared/)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Config directory
CONFIG_DIR = os.path.join(BACKEND_ROOT, 'config')
ENV_FILE = os.path.join(CONFIG_DIR, '.env')

# Data root directory
DATA_ROOT = os.path.join(BACKEND_ROOT, 'data')


# ============================================================================
# UPLOAD DIRECTORY
# ============================================================================

UPLOADS_DIR = os.path.join(DATA_ROOT, 'uploads')


# ============================================================================
# INTERVIEW STORAGE DIRECTORIES
# ============================================================================

INTERVIEWS_ROOT = os.path.join(DATA_ROOT, 'interviews')

# Text interview
TEXT_INTERVIEWS_DIR = os.path.join(INTERVIEWS_ROOT, 'text')

# Oral interview
ORAL_INTERVIEWS_DIR = os.path.join(INTERVIEWS_ROOT, 'oral')
ORAL_AUDIO_DIR = os.path.join(ORAL_INTERVIEWS_DIR, 'audio')

# Coding interview
CODING_INTERVIEWS_DIR = os.path.join(INTERVIEWS_ROOT, 'coding')


# ============================================================================
# EVALUATION REPORT DIRECTORIES
# ============================================================================

REPORTS_ROOT = os.path.join(DATA_ROOT, 'evaluation_reports')

# Text interview reports
TEXT_REPORTS_DIR = os.path.join(REPORTS_ROOT, 'text')

# Oral interview reports
ORAL_REPORTS_DIR = os.path.join(REPORTS_ROOT, 'oral')

# Coding interview reports
CODING_REPORTS_DIR = os.path.join(REPORTS_ROOT, 'coding')


# ============================================================================
# YAML CONFIGURATION FILES
# ============================================================================

# Text interview prompts
INTERVIEW_PROMPTS_YAML = os.path.join(CONFIG_DIR, 'interview_prompts.yaml')

# Text interview evaluation prompts
EVALUATION_PROMPTS_YAML = os.path.join(CONFIG_DIR, 'evaluation_prompts.yaml')

# Oral interview system prompts
ORAL_SYSTEM_PROMPTS_YAML = os.path.join(CONFIG_DIR, 'oral_system_prompts.yaml')

# Oral interview evaluation prompts
ORAL_EVALUATION_PROMPTS_YAML = os.path.join(CONFIG_DIR, 'oral_evaluation_prompts.yaml')


# ============================================================================
# DIRECTORY INITIALIZATION
# ============================================================================

def initialize_directories():
    """
    Create all required directories if they don't exist
    Should be called on application startup
    """
    directories = [
        # Uploads
        UPLOADS_DIR,

        # Interviews
        TEXT_INTERVIEWS_DIR,
        ORAL_INTERVIEWS_DIR,
        ORAL_AUDIO_DIR,
        CODING_INTERVIEWS_DIR,

        # Reports
        TEXT_REPORTS_DIR,
        ORAL_REPORTS_DIR,
        CODING_REPORTS_DIR
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    print("✅ All data directories initialized")


# ============================================================================
# PATH HELPERS
# ============================================================================

def get_upload_path(filename: str) -> str:
    """Get full path for an uploaded file"""
    return os.path.join(UPLOADS_DIR, filename)


def get_text_interview_path(filename: str) -> str:
    """Get full path for a text interview file"""
    return os.path.join(TEXT_INTERVIEWS_DIR, filename)


def get_oral_interview_path(filename: str) -> str:
    """Get full path for an oral interview file"""
    return os.path.join(ORAL_INTERVIEWS_DIR, filename)


def get_oral_audio_path(filename: str) -> str:
    """Get full path for an oral interview audio file"""
    return os.path.join(ORAL_AUDIO_DIR, filename)


def get_coding_interview_path(filename: str) -> str:
    """Get full path for a coding interview file"""
    return os.path.join(CODING_INTERVIEWS_DIR, filename)


def get_text_report_path(filename: str) -> str:
    """Get full path for a text interview evaluation report"""
    return os.path.join(TEXT_REPORTS_DIR, filename)


def get_oral_report_path(filename: str) -> str:
    """Get full path for an oral interview evaluation report"""
    return os.path.join(ORAL_REPORTS_DIR, filename)


def get_coding_report_path(filename: str) -> str:
    """Get full path for a coding interview evaluation report"""
    return os.path.join(CODING_REPORTS_DIR, filename)


def get_config_path(filename: str) -> str:
    """Get full path for a config file"""
    return os.path.join(CONFIG_DIR, filename)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_paths():
    """
    Validate that all critical paths exist
    Returns list of missing paths
    """
    missing = []

    # Check config directory
    if not os.path.exists(CONFIG_DIR):
        missing.append(CONFIG_DIR)

    # Check critical config files
    if not os.path.exists(ENV_FILE):
        missing.append(ENV_FILE)

    if not os.path.exists(EVALUATION_PROMPTS_YAML):
        missing.append(EVALUATION_PROMPTS_YAML)

    if not os.path.exists(ORAL_EVALUATION_PROMPTS_YAML):
        missing.append(ORAL_EVALUATION_PROMPTS_YAML)

    # Check data root
    if not os.path.exists(DATA_ROOT):
        missing.append(DATA_ROOT)

    return missing


# ============================================================================
# AUTO-INITIALIZATION
# ============================================================================

# Automatically initialize directories when module is imported
# This ensures all required directories exist
initialize_directories()
