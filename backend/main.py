"""
AI Interviewer - Unified Server
Combines text, oral, and coding interviews into a single Flask application
with lazy loading for optimal startup time
"""

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

# Verify API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("=" * 60)
    print("❌ ERROR: GOOGLE_API_KEY not found!")
    print("Please check that backend/config/.env contains:")
    print("GOOGLE_API_KEY=your_api_key_here")
    print("=" * 60)
    exit(1)

# Create Flask app
app = Flask(__name__)

# Configure CORS (matching original servers)
CORS(
    app,
    origins="http://localhost:5173",
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With"],
    methods=["GET", "POST", "OPTIONS"],
    supports_credentials=True
)

# Configure folders using new data/ structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'data', 'uploads')
app.config['INTERVIEWS_FOLDER'] = os.path.join(BASE_DIR, 'data', 'interviews')
app.config['REPORTS_FOLDER'] = os.path.join(BASE_DIR, 'data', 'evaluation_reports')

# Create all necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['INTERVIEWS_FOLDER'], 'text'), exist_ok=True)
os.makedirs(os.path.join(app.config['INTERVIEWS_FOLDER'], 'oral'), exist_ok=True)
os.makedirs(os.path.join(app.config['INTERVIEWS_FOLDER'], 'coding'), exist_ok=True)
os.makedirs(os.path.join(app.config['REPORTS_FOLDER'], 'text'), exist_ok=True)
os.makedirs(os.path.join(app.config['REPORTS_FOLDER'], 'oral'), exist_ok=True)
os.makedirs(os.path.join(app.config['REPORTS_FOLDER'], 'coding'), exist_ok=True)

# ============================================================================
# BLUEPRINT REGISTRATION (Lazy Loading)
# ============================================================================

# Import and register oral interview blueprint
try:
    from oral_interview.routes import oral_bp
    app.register_blueprint(oral_bp)
    oral_available = True
    print("✅ Oral interview module registered")
except ImportError as e:
    oral_available = False
    print(f"⚠️  Oral interview module not available: {e}")

# Import and register coding interview blueprint
try:
    from coding_interview.routes import coding_bp
    app.register_blueprint(coding_bp)
    coding_available = True
    print("✅ Coding interview module registered")
except ImportError as e:
    coding_available = False
    print(f"⚠️  Coding interview module not available: {e}")

# Import and register text interview routes from modular text_interview package
try:
    from text_interview import register_text_routes
    register_text_routes(app)
    text_available = True
    print("✅ Text interview module registered (modular)")
except ImportError as e:
    text_available = False
    print(f"⚠️  Text interview module not available: {e}")
except Exception as e:
    text_available = False
    print(f"⚠️  Error registering text interview routes: {e}")

# ============================================================================
# BACKWARD COMPATIBILITY ROUTES
# ============================================================================

@app.route('/upload_cv', methods=['POST'])
def upload_cv_redirect():
    """Redirect old upload_cv route to oral interview"""
    return redirect('/oral/upload_cv', code=307)


# Text Interview Routes
# NOTE: Text interview uses original route paths (not prefixed with /text/)
# Routes available: /start_interview, /submit_response, /record
# These are registered directly from app.py without modification


# Oral Interview Legacy Routes
@app.route('/oral_interview/start', methods=['GET'])
def oral_start_redirect():
    """Redirect old oral start route"""
    return redirect('/oral/start', code=307)


@app.route('/oral_interview/continue', methods=['POST'])
def oral_continue_redirect():
    """Redirect old oral continue route"""
    return redirect('/oral/continue', code=307)


@app.route('/oral_interview/complete', methods=['POST'])
def oral_complete_redirect():
    """Redirect old oral complete route"""
    return redirect('/oral/complete', code=307)


@app.route('/oral_interview/upload_audio', methods=['POST'])
def oral_upload_audio_redirect():
    """Redirect old oral upload audio route"""
    return redirect('/oral/upload_audio', code=307)


@app.route('/oral_interview/evaluate', methods=['POST'])
def oral_evaluate_redirect():
    """Redirect old oral evaluate route"""
    return redirect('/oral/evaluate', code=307)


# Coding Interview Legacy Routes
@app.route('/start_coding_interview', methods=['GET', 'POST'])
def start_coding_redirect():
    """Redirect old coding start route"""
    return redirect('/coding/start', code=307)


@app.route('/submit_coding_response', methods=['POST'])
def submit_coding_response_redirect():
    """Redirect old coding submit response route (used by frontend)"""
    return redirect('/coding/submit', code=307)


@app.route('/submit_code', methods=['POST'])
def submit_code_redirect():
    """Redirect old coding submit route"""
    return redirect('/coding/submit', code=307)


@app.route('/evaluate_coding', methods=['POST'])
def evaluate_coding_redirect():
    """Redirect old coding evaluate route"""
    return redirect('/coding/evaluate', code=307)


# ============================================================================
# HEALTH CHECK & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'modules': {
            'text': text_available,
            'oral': oral_available,
            'coding': coding_available
        },
        'version': '2.0.0'
    })


@app.route('/api/info', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'AI Interviewer API',
        'version': '2.0.0',
        'description': 'Unified interview system with lazy loading',
        'modules': {
            'text_interview': {
                'available': text_available,
                'note': 'Uses legacy routes (not prefixed)',
                'endpoints': ['/start_interview', '/submit_response', '/record'] if text_available else []
            },
            'oral_interview': {
                'available': oral_available,
                'base_url': '/oral/',
                'endpoints': ['/start', '/continue', '/complete', '/upload_audio', '/evaluate'] if oral_available else []
            },
            'coding_interview': {
                'available': coding_available,
                'base_url': '/coding/',
                'endpoints': ['/start', '/submit', '/evaluate'] if coding_available else []
            }
        },
        'backward_compatible': True
    })


@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'message': 'AI Interviewer Unified Server',
        'version': '2.0.0',
        'health': '/health',
        'info': '/api/info'
    })


# ============================================================================
# SECURITY ENDPOINTS
# ============================================================================

@app.route('/api/security/violation', methods=['POST'])
def log_security_violation():
    """
    Log a security violation to file

    Expected JSON body:
    {
        "type": "fullscreen_exit",
        "timestamp": "2025-10-30T14:30:00.000Z",
        "sessionId": "text-1730300000000",
        "interviewType": "text",
        "violationCount": 1,
        "isWarning": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['type', 'timestamp', 'sessionId', 'interviewType']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Create security logs directory if it doesn't exist
        security_logs_dir = os.path.join(BASE_DIR, 'data', 'security_logs')
        os.makedirs(security_logs_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        violation_type = 'warning' if data.get('isWarning', False) else 'disqualification'
        filename = f"violation-{data['interviewType']}-{violation_type}-{timestamp}.json"
        filepath = os.path.join(security_logs_dir, filename)

        # Add server-side timestamp
        log_entry = {
            **data,
            'server_timestamp': datetime.now().isoformat(),
            'logged': True,
            'violationCount': data.get('violationCount', 1),
            'isWarning': data.get('isWarning', False)
        }

        # Write to file
        with open(filepath, 'w') as f:
            json.dump(log_entry, f, indent=2)

        status_msg = "Warning" if data.get('isWarning', False) else "Disqualification"
        print(f"[SECURITY] {status_msg} logged: {filename}")

        return jsonify({
            'success': True,
            'logged': True,
            'filename': filename,
            'isWarning': data.get('isWarning', False),
            'violationCount': data.get('violationCount', 1)
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to log security violation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/security/stats', methods=['GET'])
def get_security_stats():
    """
    Get security violation statistics
    """
    try:
        security_logs_dir = os.path.join(BASE_DIR, 'data', 'security_logs')

        if not os.path.exists(security_logs_dir):
            return jsonify({
                'success': True,
                'total_violations': 0,
                'by_type': {},
                'by_interview': {}
            })

        # Read all violation files
        violations = []
        for filename in os.listdir(security_logs_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(security_logs_dir, filename)
                with open(filepath, 'r') as f:
                    violations.append(json.load(f))

        # Calculate stats
        by_type = {}
        by_interview = {}

        for v in violations:
            v_type = v.get('type', 'unknown')
            i_type = v.get('interviewType', 'unknown')

            by_type[v_type] = by_type.get(v_type, 0) + 1
            by_interview[i_type] = by_interview.get(i_type, 0) + 1

        return jsonify({
            'success': True,
            'total_violations': len(violations),
            'by_type': by_type,
            'by_interview': by_interview,
            'recent': violations[-10:]  # Last 10
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status': 500
    }), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 AI INTERVIEWER - UNIFIED SERVER")
    print("=" * 70)
    print("\n📦 Available Modules:")
    if text_available:
        print("   ✅ Text Interview      → /start_interview, /submit_response, /record")
    else:
        print("   ❌ Text Interview      → (not available)")
    if oral_available:
        print("   ✅ Oral Interview      → /oral/")
    else:
        print("   ❌ Oral Interview      → (not available)")
    if coding_available:
        print("   ✅ Coding Interview    → /coding/")
    else:
        print("   ❌ Coding Interview    → (not available)")

    print("\n📍 Server Configuration:")
    print(f"   - URL: http://127.0.0.1:5000")
    print(f"   - Frontend Origin: http://localhost:5173")
    print(f"   - Upload Folder: {app.config['UPLOAD_FOLDER']}")
    print(f"   - Interviews Folder: {app.config['INTERVIEWS_FOLDER']}")

    print("\n🔄 Features:")
    print("   - Lazy Loading: Modules initialize on first use")
    print("   - Backward Compatible: Old routes redirect to new ones")
    print("   - Health Check: GET /health")
    print("   - API Info: GET /api/info")

    print("\n" + "=" * 70)
    print("💡 Frontend should connect to: http://127.0.0.1:5000")
    print("=" * 70)
    print("\nPress CTRL+C to stop the server\n")

    app.run(debug=False, port=5000, host='127.0.0.1')
