# server.py

import subprocess
import psutil
import os
import sys
import secrets
import logging
from pathlib import Path
from functools import wraps
from flask import (
    Flask, request, jsonify, send_from_directory, render_template,
    session, redirect, url_for
)
from flask_cors import CORS

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__) # Use a logger instance

app = Flask(__name__)
# IMPORTANT: Use a strong, unpredictable secret key, ideally from environment variables
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(24))
# Allow credentials (cookies) to be sent with requests from frontend origins
CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000"]) # Adjust origins if needed

# --- Paths and Script Constants ---
# Assumes server.py is at the root of your project directory
OUTPUT_PATH = Path(__file__).parent
SCRIPT_HEADAWAY = "headaway.py"
SCRIPT_EYETRACKING = "eyetracking.py"
# Ensure this matches the actual filename for your Arduino script
SCRIPT_ARDUINO = "arduino_control.py"
ALLOWED_SCRIPTS = [SCRIPT_HEADAWAY, SCRIPT_EYETRACKING, SCRIPT_ARDUINO]

# --- Mock User Database ---
# !!! WARNING: Store hashed passwords in a real application !!!
# Example: from werkzeug.security import generate_password_hash, check_password_hash
USERS = {
    "doctor@example.com": {
        "password": "doctor123", # HASH ME: generate_password_hash("doctor123")
        "name": "Dr. Jane Smith",
        "role": "doctor"
    },
    "patient@example.com": {
        "password": "patient123", # HASH ME: generate_password_hash("patient123")
        "name": "John Doe",
        "role": "patient"
    }
}

# --- Helper Function ---
def is_script_running(script_name):
    """Checks if a script with the given name is likely running."""
    script_full_path = str(OUTPUT_PATH / script_name)
    python_exe = sys.executable # Get the path of the current python interpreter
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Check if process info is accessible
            if proc.info['cmdline']:
                cmdline = proc.info['cmdline']
                # Check if the command line involves the python interpreter and the target script path
                if (python_exe in cmdline or 'python' in cmdline[0].lower()) and script_full_path in cmdline:
                    log.debug(f"Found running process for {script_name}: PID {proc.info['pid']}, Cmdline: {' '.join(cmdline)}")
                    return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        log.warning(f"Error checking process list: {e}")
        # Decide how to handle - conservatively assume it might be running? Or not?
        # For now, assume not running if we can't check properly.
        return False
    except Exception as e:
        log.error(f"Unexpected error in is_script_running: {e}", exc_info=True)
        return False # Fail safe
    return False


# --- Authentication Decorators ---
def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            log.info(f"Login required for route {request.path}, redirecting to landing.")
            return redirect(url_for('landing_page')) # Redirect to landing if not logged in
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    """Decorator to ensure user is logged in AND is a doctor."""
    @wraps(f)
    @login_required # Apply login_required first
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'doctor':
            log.warning(f"Doctor role required for {request.path}. User '{session.get('user')}' has role '{session.get('role')}'. Redirecting.")
            # Decide where to redirect non-doctors: landing page or patient home? Landing is safer.
            return redirect(url_for('landing_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- Page Routes ---

@app.route('/')
def landing_page():
    """Serves the initial landing page or redirects if already logged in."""
    if 'user' in session:
        user_role = session.get('role')
        log.debug(f"User '{session.get('user')}' already logged in with role '{user_role}'. Redirecting from landing.")
        if user_role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif user_role == 'patient':
            return redirect(url_for('patient_home'))
        else:
            # Unknown role? Clear session and redirect to landing
            session.clear()
    return render_template('landing.html')

@app.route('/auth')
def auth_page():
    """Serves the combined login/register page."""
    if 'user' in session:
        # Redirect logged-in users away from the auth page
        user_role = session.get('role')
        log.debug(f"User '{session.get('user')}' already logged in. Redirecting from auth page.")
        if user_role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        else: # Patients or unknown roles go to patient home
            return redirect(url_for('patient_home'))

    role = request.args.get('role', 'patient').lower()
    if role not in ['patient', 'doctor']:
        role = 'patient' # Default to patient for safety
    log.debug(f"Serving auth page for role: {role}")
    return render_template('login_register.html', role=role)


@app.route('/home')
@login_required # Protect this route
def patient_home():
    """Serves the main application page for logged-in patients."""
    if session.get('role') != 'patient':
         # Prevent non-patients (e.g., doctors) from accessing patient home directly
         log.warning(f"Non-patient user '{session.get('user')}' tried to access /home. Redirecting.")
         return redirect(url_for('landing_page'))
    log.debug(f"Serving patient home page for user '{session.get('user')}'")
    return render_template('index.html')

@app.route('/doctor/dashboard')
@doctor_required # Protect this route for doctors only
def doctor_dashboard():
    """Serves the dashboard for logged-in doctors."""
    log.debug(f"Serving doctor dashboard for user '{session.get('user')}'")
    return render_template('doctor_dashboard.html')

# --- API Routes ---

@app.route('/api/login', methods=['POST'])
def login():
    """Handles user login attempts."""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    log.info(f"Login attempt for email: {email}")
    user_data = USERS.get(email)

    # !!! Replace with password hash check: check_password_hash(user_data['password'], password)
    if user_data and user_data['password'] == password:
        session['user'] = email
        session['name'] = user_data['name']
        session['role'] = user_data['role']
        session.permanent = True # Make session last longer (configure lifetime via app.permanent_session_lifetime)
        log.info(f"Login successful for {email}, role: {user_data['role']}")
        return jsonify({
            "success": True,
            "message": "Login successful",
            "name": user_data['name'],
            "role": user_data['role'] # Send role back for client-side redirect logic
        })
    else:
        log.warning(f"Login failed for email: {email}")
        return jsonify({"success": False, "error": "Invalid email or password"}), 401


@app.route('/api/register', methods=['POST'])
def register():
    """Handles new user registration."""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')

    log.info(f"Registration attempt: Email={email}, Name={name}, Role={role}")

    if not all([email, password, name, role]):
        log.warning("Registration failed: Missing required fields.")
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    if role not in ['patient', 'doctor']:
        log.warning(f"Registration failed: Invalid role '{role}'.")
        return jsonify({"success": False, "error": "Invalid role specified"}), 400

    if email in USERS:
        log.warning(f"Registration failed: Email {email} already exists.")
        return jsonify({"success": False, "error": "Email already registered"}), 400

    # Basic validation (add more as needed)
    if len(password) < 6:
         log.warning(f"Registration failed: Password too short for {email}.")
         return jsonify({"success": False, "error": "Password must be at least 6 characters long"}), 400

    # !!! HASH the password securely before storing !!!
    # from werkzeug.security import generate_password_hash
    # hashed_password = generate_password_hash(password)
    USERS[email] = {
        "password": password, # Store the hash: hashed_password
        "name": name,
        "role": role
    }
    log.info(f"Registration successful for {email}, role: {role}")
    # Consider logging the user in immediately or requiring them to log in.
    # For now, require login after registration.
    return jsonify({
        "success": True,
        "message": "Registration successful. Please log in."
    })


@app.route('/api/logout', methods=['POST'])
@login_required # User must be logged in to log out
def logout():
    """Clears the user session."""
    user = session.get('user', 'Unknown user')
    session.clear()
    log.info(f"User {user} logged out.")
    # Return success even if session was already somehow clear
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Checks if the current user is authenticated via session cookie."""
    if 'user' in session and 'role' in session and 'name' in session:
        log.debug(f"Auth check successful for user '{session['user']}'")
        return jsonify({
            "authenticated": True,
            "name": session.get('name'),
            "role": session.get('role')
        })
    else:
        # If session exists but is incomplete, clear it for safety
        if 'user' in session:
             log.warning("Incomplete session found during auth check. Clearing.")
             session.clear()
        log.debug("Auth check failed: User not authenticated.")
        return jsonify({"authenticated": False}), 401 # Use 401 Unauthorized


# --- Script Running API ---
@app.route('/api/run-script', methods=['POST'])
@login_required # Only logged-in users can run scripts
def run_script():
    """Starts a specified python script in the background."""
    data = request.json
    script_name = data.get('script')
    user_email = session.get('user', 'Unknown') # Get logged in user for logging

    log.info(f"User '{user_email}' requested to run script: {script_name}")

    if not script_name:
        log.warning(f"API run-script: No script specified by user '{user_email}'.")
        return jsonify({"success": False, "error": "No script specified"}), 400

    if script_name not in ALLOWED_SCRIPTS:
        log.warning(f"API run-script: Invalid script name '{script_name}' requested by '{user_email}'.")
        return jsonify({"success": False, "error": "Invalid script name"}), 400

    script_path = OUTPUT_PATH / script_name
    if not script_path.exists():
        log.error(f"API run-script: Script file not found at: {script_path}")
        return jsonify({"success": False, "error": f"Script '{script_name}' not found on server."}), 404

    # --- Check if script is already running ---
    if is_script_running(script_name):
         log.info(f"API run-script: {script_name} is already running (requested by '{user_email}').")
         return jsonify({"success": True, "already_running": True, "message": f"{script_name} is already running."})

    try:
        # --- Use the *correct* Python executable (the one running Flask) ---
        python_exe = sys.executable
        log.info(f"API run-script: Using Python interpreter: {python_exe}")

        command = [python_exe, str(script_path)]

        # --- Add --headless for eyetracking (Modify script to accept it!) ---
        if script_name == SCRIPT_EYETRACKING:
            command.append('--headless')
            log.info("API run-script: Adding --headless argument for eyetracking.py")
        # --- Add similar flags if other scripts need non-interactive modes ---
        # Example:
        # if script_name == SCRIPT_HEADAWAY:
        #     command.append('--some-non-interactive-flag')

        log.info(f"API run-script: Attempting to start: {' '.join(command)}")
        log.info(f"API run-script: Working directory: {OUTPUT_PATH}")

        # --- Launch in background ---
        # Use CREATE_NO_WINDOW on Windows to prevent brief console flashes
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        process = subprocess.Popen(
            command,
            cwd=OUTPUT_PATH,
            stdout=subprocess.PIPE, # Capture output for potential later logging/debugging
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )

        # --- Check for Immediate Failure ---
        # Give the process a very short time to potentially fail on startup
        try:
             stdout, stderr = process.communicate(timeout=0.75) # Check for immediate exit/error (adjust timeout slightly if needed)

             # If communicate() finishes, the process terminated very quickly. Check return code.
             if process.returncode is not None and process.returncode != 0:
                 log.error(f"API run-script: {script_name} failed immediately on launch. PID: {process.pid}, Code: {process.returncode}")
                 log.error(f"API run-script: {script_name} STDERR:\n{stderr.strip()}")
                 return jsonify({
                     "success": False,
                     "error": f"{script_name} failed to start properly.",
                     "details": stderr.strip() if stderr else "No specific error output captured on immediate exit."
                 }), 500
             else:
                 # Script finished extremely quickly without error (maybe intended?)
                 log.warning(f"API run-script: {script_name} finished very quickly. PID: {process.pid}, Code: {process.returncode}")
                 return jsonify({"success": True, "message": f"{script_name} started (and finished almost immediately).", "pid": process.pid})

        except subprocess.TimeoutExpired:
             # This is the EXPECTED successful path for scripts running in the background
             log.info(f"API run-script: {script_name} started successfully in background (PID: {process.pid}).")
             return jsonify({"success": True, "message": f"{script_name} started successfully.", "pid": process.pid})

    except FileNotFoundError:
        # This usually means python_exe wasn't found, less likely with sys.executable
        log.exception(f"API run-script: Error running script '{script_name}': Python executable '{python_exe}' not found?")
        return jsonify({"success": False, "error": f"Server configuration error: Failed to find the Python interpreter."}), 500
    except OSError as e:
        # Catch potential OS-level errors during Popen (e.g., permissions)
        log.exception(f"API run-script: OS error occurred while trying to start {script_name}")
        return jsonify({"success": False, "error": f"Server OS error prevented script start: {str(e)}"}), 500
    except Exception as e:
        # Catch other potential errors during Popen setup
        log.exception(f"API run-script: An unexpected error occurred while trying to start {script_name}")
        return jsonify({"success": False, "error": f"An unexpected server error occurred: {str(e)}"}), 500


# --- Static Files Route (Optional - Flask usually handles this) ---
# If you have issues with static files, uncommenting this might help sometimes,
# but usually it's automatic if the 'static' folder is present.
# @app.route('/static/<path:path>')
# def serve_static(path):
#    log.debug(f"Serving static file: {path}")
#    return send_from_directory('static', path)


# --- Main Execution ---
if __name__ == '__main__':
    # Optional: Check/Create directories on startup (useful for deployment)
    static_dir = OUTPUT_PATH / 'static'
    templates_dir = OUTPUT_PATH / 'templates'
    log.info(f"Checking for static directory: {static_dir}")
    static_dir.mkdir(exist_ok=True)
    log.info(f"Checking for templates directory: {templates_dir}")
    templates_dir.mkdir(exist_ok=True)
    # Check subdirs if needed
    (static_dir / 'css').mkdir(exist_ok=True)
    (static_dir / 'js').mkdir(exist_ok=True)
    (static_dir / 'images').mkdir(exist_ok=True)

    log.info("Starting Flask development server...")
    log.warning("DEBUG MODE IS ON. Do not use in production.")
    # Use debug=False and a production WSGI server (like Gunicorn or Waitress) for deployment
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))