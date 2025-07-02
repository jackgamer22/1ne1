import os
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from collections import defaultdict

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Allow frontend to access backend APIs

# --- Project Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
STATIC_FOLDER = BASE_DIR / 'static'
TEMPLATE_FOLDER = BASE_DIR / 'templates'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.static_folder = str(STATIC_FOLDER)
app.template_folder = str(TEMPLATE_FOLDER)

# Create folders if missing
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

# --- Import Logic ---
try:
    from email_processing_logic import process_emails
except ImportError as e:
    print(f"ERROR: Could not import 'email_processing_logic.py'. Make sure it's in the same folder. Details: {e}")
    process_emails = None

# --- Task Store (in-memory) ---
tasks_status = {}

def update_status_callback(task_id, processed_count, total_to_validate, current_stats_dict, overall_status_str):
    if task_id in tasks_status:
        tasks_status[task_id].update({
            'status': overall_status_str,
            'processed_count': processed_count,
            'total_to_validate': total_to_validate,
            'stats': current_stats_dict,
            'progress': round((processed_count / total_to_validate) * 100) if total_to_validate else 0
        })
        print(f"Status update for {task_id}: {overall_status_str} ({tasks_status[task_id]['progress']}%)")

def run_email_validation_thread(task_id, file_path, original_filename):
    try:
        if not process_emails:
            raise Exception("Email processing logic not loaded.")

        tasks_status[task_id]['status'] = 'processing'
        tasks_status[task_id]['stats'] = defaultdict(int) # Ensure stats is initialized for the task

        final_stats = process_emails(
            input_path=str(file_path),
            output_dir=str(app.config['OUTPUT_FOLDER']),
            status_updater=update_status_callback,
            task_id=task_id
        )

        tasks_status[task_id].update({
            'status': 'completed',
            'stats': dict(final_stats), # Convert defaultdict to dict for consistency
            'progress': 100
        })
        print(f"Task {task_id} completed.")
    except Exception as e:
        tasks_status[task_id].update({
            'status': 'error',
            'error_message': str(e),
            'progress': 100 # Or a specific error progress, but 100 indicates processing attempted to finish
        })
        print(f"Error in task {task_id}: {e}")
    finally:
        # Optional: Clean up uploaded file
        try:
            if file_path.exists(): # Check if file exists before trying to remove
                os.remove(file_path)
                print(f"Cleaned up uploaded file: {file_path}")
        except OSError as e_remove:
            print(f"Error deleting uploaded file {file_path}: {e_remove}")


# --- Routes ---

@app.route('/upload', methods=['POST'])
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename: # Check if filename is empty
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.endswith('.txt'):
        return jsonify({"error": "Only .txt files allowed"}), 400

    task_id = str(uuid.uuid4())
    original_filename = file.filename # No need for secure_filename if only using task_id for uniqueness
    file_path = app.config['UPLOAD_FOLDER'] / f"{task_id}_{original_filename}"

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    tasks_status[task_id] = {
        "status": "queued",
        "progress": 0,
        "processed_count": 0,
        "total_to_validate": 0,
        "stats": defaultdict(int),
        "original_filename": original_filename,
        "error_message": None
    }

    thread = threading.Thread(target=run_email_validation_thread, args=(task_id, file_path, original_filename))
    thread.start()

    return jsonify({"message": "File uploaded. Processing started.", "task_id": task_id}), 202

@app.route('/status/<task_id>', methods=['GET'])
def get_status_route(task_id):
    status_info = tasks_status.get(task_id)
    if not status_info:
        return jsonify({"error": "Invalid task ID"}), 404

    # Ensure stats is a plain dict for JSON serialization
    response_data = {**status_info, 'stats': dict(status_info.get('stats', {}))}
    return jsonify(response_data)

@app.route('/download/<task_id>/<filename>', methods=['GET'])
def download_file_route(task_id, filename):
    task_info = tasks_status.get(task_id)
    if not task_info:
        return jsonify({"error": "Task not found"}), 404

    # Allow download if completed, or if an error occurred but files might still exist
    if task_info.get('status') not in ['completed', 'error']: # Added 'error' to allow download of partial results/logs if any
         return jsonify({"error": f"Task status is '{task_info.get('status')}', not ready for download."}), 400

    allowed_files = ["valid_emails.txt", "results.csv"]
    if filename not in allowed_files:
        return jsonify({"error": "Invalid filename requested"}), 400

    # Output files are in a subdirectory named after the task_id
    output_dir = app.config['OUTPUT_FOLDER'] / task_id
    file_path = output_dir / filename

    if not file_path.exists():
        return jsonify({"error": f"File '{filename}' not found for task {task_id}."}), 404

    return send_from_directory(directory=str(output_dir), path=filename, as_attachment=True)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    target_static_file = Path(app.static_folder) / path
    index_html_file = Path(app.template_folder) / 'index.html'

    if path != "" and target_static_file.is_file(): # Check if it's an actual file
        return send_from_directory(app.static_folder, path)
    elif index_html_file.is_file(): # Check if index.html is an actual file
        return send_from_directory(app.template_folder, 'index.html')
    else:
        # Log details if index.html is not found, to help debug setup
        print(f"CRITICAL: index.html not found at expected location: {index_html_file.resolve()}")
        return "Error: React frontend main file (index.html) not found. Please ensure the frontend is built and copied correctly to the 'templates' directory.", 500

# --- Run App ---
if __name__ == '__main__':
    print(f"\n🚀 Backend running at http://localhost:5000")
    print(f"📂 Uploads: {UPLOAD_FOLDER.resolve()}")
    print(f"📁 Outputs: {OUTPUT_FOLDER.resolve()}")
    print(f"🎨 Static (React build): {STATIC_FOLDER.resolve()}")
    print(f"📄 Templates (React index.html): {TEMPLATE_FOLDER.resolve()}")

    if not process_emails:
        print("\nWARNING: 'process_emails' function could not be loaded. Backend processing will fail.")
        print("Ensure 'email_processing_logic.py' is in the 'backend' directory and has no import errors itself.")

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
