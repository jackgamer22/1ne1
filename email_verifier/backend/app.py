import os
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from collections import defaultdict

# Assuming email_processing_logic.py is in the same directory
from email_processing_logic import process_emails

app = Flask(__name__)

# --- Project Structure Setup ---
# app.py is in email_verifier/backend/
# So, BASE_DIR is email_verifier/
BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
STATIC_FOLDER = BASE_DIR / 'static'    # For React JS/CSS
TEMPLATE_FOLDER = BASE_DIR / 'templates' # For React index.html

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.static_folder = str(STATIC_FOLDER)
app.template_folder = str(TEMPLATE_FOLDER)


# Ensure required folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.static_folder, exist_ok=True)
os.makedirs(app.template_folder, exist_ok=True)

# In-memory store for task statuses and stats
tasks_status = {} # Global dictionary to store task progress

def update_status_callback(task_id, processed_count, total_to_validate, current_stats_dict, overall_status_str):
    """Callback function for process_emails to update status."""
    if task_id in tasks_status:
        tasks_status[task_id]['status'] = overall_status_str
        tasks_status[task_id]['processed_count'] = processed_count
        tasks_status[task_id]['total_to_validate'] = total_to_validate
        tasks_status[task_id]['stats'] = current_stats_dict
        if total_to_validate > 0:
            tasks_status[task_id]['progress'] = round((processed_count / total_to_validate) * 100)
        else:
            tasks_status[task_id]['progress'] = 100 if overall_status_str == 'completed' else 0

        print(f"Status update for {task_id}: {tasks_status[task_id]['status']} - {tasks_status[task_id]['progress']}%")

def run_email_validation_thread(task_id, file_path, original_filename):
    """Wrapper to run process_emails in a thread and update final status."""
    try:
        # Update status to processing
        if task_id in tasks_status:
            tasks_status[task_id]['status'] = 'processing'
            # Initialize basic stats if not already done by an initial callback
            if 'total_loaded' not in tasks_status[task_id]['stats']:
                 tasks_status[task_id]['stats']['total_loaded'] = 0 # Will be updated by process_emails
                 tasks_status[task_id]['stats']['duplicates_removed'] = 0
                 tasks_status[task_id]['stats']['total_to_validate'] = 0


        print(f"Starting processing for task {task_id} with file {file_path.name}")

        final_stats = process_emails(
            input_path=str(file_path),
            output_dir=str(app.config['OUTPUT_FOLDER']), # Pass the main output folder
            status_updater=update_status_callback,
            task_id=task_id
        )

        if task_id in tasks_status:
            tasks_status[task_id]['status'] = 'completed'
            tasks_status[task_id]['stats'] = dict(final_stats)
            tasks_status[task_id]['progress'] = 100
            print(f"Task {task_id} completed. Final stats: {tasks_status[task_id]['stats']}")

        # Optional: Clean up uploaded file
        # try:
        #     os.remove(file_path)
        #     print(f"Cleaned up uploaded file: {file_path}")
        # except OSError as e:
        #     print(f"Error deleting uploaded file {file_path}: {e}")

    except Exception as e:
        if task_id in tasks_status:
            tasks_status[task_id]['status'] = 'error'
            tasks_status[task_id]['error_message'] = str(e)
            tasks_status[task_id]['progress'] = 100 # Mark as 'done' for progress bar
        print(f"Error processing task {task_id}: {e}")


@app.route('/upload', methods=['POST'])
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.txt'):
        task_id = str(uuid.uuid4())
        # Save to a generic name first, or use a secure filename
        # original_filename = secure_filename(file.filename) # Consider using werkzeug.utils.secure_filename
        original_filename = file.filename
        # Save uploaded file with task_id to avoid collisions if multiple users upload same filename
        upload_filename = f"{task_id}_{original_filename}"
        file_path = app.config['UPLOAD_FOLDER'] / upload_filename

        try:
            file.save(file_path)
        except Exception as e:
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

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

        return jsonify({"message": "File uploaded successfully. Processing started.", "task_id": task_id}), 202
    else:
        return jsonify({"error": "Invalid file type. Please upload a .txt file."}), 400

@app.route('/status/<task_id>', methods=['GET'])
def get_status_route(task_id):
    status_info = tasks_status.get(task_id)
    if not status_info:
        return jsonify({"error": "Invalid task ID"}), 404

    # Make a copy and ensure stats is a plain dict for JSON
    response_data = status_info.copy()
    response_data['stats'] = dict(status_info.get('stats', {}))
    return jsonify(response_data)

@app.route('/download/<task_id>/<filename>', methods=['GET'])
def download_file_route(task_id, filename):
    task_info = tasks_status.get(task_id)
    if not task_info:
        return jsonify({"error": "Task not found"}), 404

    # Allow download only if completed, or if an error occurred but files might still exist
    if task_info.get('status') not in ['completed', 'error']:
         return jsonify({"error": f"Task status is '{task_info.get('status')}', not ready for download."}), 400

    if filename not in ["valid_emails.txt", "results.csv"]:
        return jsonify({"error": "Invalid filename requested"}), 400

    # Output files are in a subdirectory named after the task_id
    task_specific_output_dir = app.config['OUTPUT_FOLDER'] / task_id

    if not (task_specific_output_dir / filename).exists():
        # Check if the files exist in the main output folder (if task_id wasn't used in process_emails pathing somehow)
        # This is a fallback, ideally process_emails always uses task_id for output subfolder
        if (app.config['OUTPUT_FOLDER'] / filename).exists() and task_id in str(app.config['OUTPUT_FOLDER'] / filename):
             #This case should not happen if process_emails is correct
             return send_from_directory(directory=app.config['OUTPUT_FOLDER'], path=filename, as_attachment=True)
        return jsonify({"error": f"File '{filename}' not found for task {task_id}."}), 404

    return send_from_directory(directory=str(task_specific_output_dir), path=filename, as_attachment=True)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_frontend_route(path):
    if path != "" and (Path(app.static_folder) / path).exists():
        return send_from_directory(app.static_folder, path)
    else:
        index_html_path = Path(app.template_folder) / 'index.html'
        if not index_html_path.exists():
            return "Error: Main application file (index.html) not found in templates folder. Ensure React app is built and files are copied.", 500
        return send_from_directory(app.template_folder, 'index.html')

if __name__ == '__main__':
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"Serving static files from: {app.static_folder}")
    print(f"Serving templates from: {app.template_folder}")
    print(f"Uploads will go to: {app.config['UPLOAD_FOLDER'].resolve()}")
    print(f"Outputs will go to: {app.config['OUTPUT_FOLDER'].resolve()}")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
