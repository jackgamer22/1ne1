import os
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from collections import defaultdict

# Assuming email_validator.py is in the same directory or accessible in PYTHONPATH
from email_validator import process_emails

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path('../uploads') # Relative to backend/app.py
OUTPUT_FOLDER = Path('../output') # Relative to backend/app.py
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# In-memory store for task statuses and stats
# For production, consider Redis or a database
tasks_status = {}

def update_status_callback(task_id, processed_count, total_to_validate, current_stats):
    """Callback function for process_emails to update status."""
    if task_id in tasks_status:
        tasks_status[task_id]['processed_count'] = processed_count
        tasks_status[task_id]['total_to_validate'] = total_to_validate
        tasks_status[task_id]['stats'] = current_stats
        if total_to_validate > 0:
            tasks_status[task_id]['progress'] = round((processed_count / total_to_validate) * 100)
        else:
            tasks_status[task_id]['progress'] = 0 # Avoid division by zero if no unique emails

        # Update overall status
        if processed_count == total_to_validate and total_to_validate > 0:
             tasks_status[task_id]['status'] = 'completed'
        print(f"Status update for {task_id}: {tasks_status[task_id]}")


def run_email_validation(task_id, file_path):
    """Wrapper to run process_emails and update final status."""
    try:
        final_stats = process_emails(
            input_path=file_path,
            output_dir=app.config['OUTPUT_FOLDER'],
            status_updater=update_status_callback,
            task_id=task_id
        )
        # Ensure final status reflects completion and includes all stats
        if task_id in tasks_status:
            tasks_status[task_id]['status'] = 'completed'
            tasks_status[task_id]['stats'] = dict(final_stats) # Ensure it's a plain dict
            tasks_status[task_id]['progress'] = 100
            # Clean up the uploaded file after processing
            # os.remove(file_path) # Commented out for now for easier debugging
            print(f"Task {task_id} completed. Final status: {tasks_status[task_id]}")

    except Exception as e:
        if task_id in tasks_status:
            tasks_status[task_id]['status'] = 'error'
            tasks_status[task_id]['error_message'] = str(e)
        print(f"Error processing task {task_id}: {e}")


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.txt'):
        task_id = str(uuid.uuid4())
        filename = f"{task_id}_{file.filename}" # Ensure unique filename for uploaded file
        file_path = app.config['UPLOAD_FOLDER'] / filename
        file.save(file_path)

        tasks_status[task_id] = {
            "status": "queued",
            "progress": 0,
            "processed_count": 0,
            "total_to_validate": 0,
            "stats": defaultdict(int), # Initialize with defaultdict
            "original_filename": file.filename
        }

        # Start processing in a background thread
        thread = threading.Thread(target=run_email_validation, args=(task_id, file_path))
        thread.start()

        return jsonify({"message": "File uploaded successfully. Processing started.", "task_id": task_id}), 202
    else:
        return jsonify({"error": "Invalid file type. Please upload a .txt file."}), 400

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status_info = tasks_status.get(task_id)
    if not status_info:
        return jsonify({"error": "Invalid task ID"}), 404

    # Ensure stats is a plain dictionary for JSON serialization
    response_status_info = status_info.copy()
    response_status_info['stats'] = dict(status_info.get('stats', {}))

    return jsonify(response_status_info)

@app.route('/download/<task_id>/<filename>', methods=['GET'])
def download_file(task_id, filename):
    if task_id not in tasks_status or tasks_status[task_id].get('status') != 'completed':
        return jsonify({"error": "Task not found or not completed"}), 404

    if filename not in ["valid_emails.txt", "results.csv"]:
        return jsonify({"error": "Invalid filename requested"}), 400

    task_output_dir = app.config['OUTPUT_FOLDER'] / task_id

    if not (task_output_dir / filename).exists():
        return jsonify({"error": "File not found for this task after completion."}), 404

    return send_from_directory(directory=task_output_dir, path=filename, as_attachment=True)


# Serve React App
# The static_folder points to the 'static' directory created by create-react-app's build,
# which should be copied to ../static (relative to this app.py file).
# The template_folder points to where index.html from the React build is copied.
app.static_folder = str(Path(__file__).parent.parent / 'static')
app.template_folder = str(Path(__file__).parent.parent / 'templates')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and Path(app.static_folder, path).exists():
        return send_from_directory(app.static_folder, path)
    else:
        # Check if templates/index.html exists
        index_html_path = Path(app.template_folder) / 'index.html'
        if not index_html_path.exists():
            return "Error: Main application file (index.html) not found in templates folder.", 500
        return send_from_directory(app.template_folder, 'index.html')

if __name__ == '__main__':
    # email_validator.py is imported directly, so it should be in the same directory (backend)
    # or installed as a package, or its path added to PYTHONPATH.
    # For this structure, it's assumed to be in the same 'backend' directory.

    # The UPLOAD_FOLDER and OUTPUT_FOLDER are already set relative to this script's parent.
    # UPLOAD_FOLDER = ../uploads
    # OUTPUT_FOLDER = ../output
    # STATIC_FOLDER = ../static
    # TEMPLATE_FOLDER = ../templates

    print(f"Serving static files from: {app.static_folder}")
    print(f"Serving templates from: {app.template_folder}")
    print(f"Uploads will go to: {app.config['UPLOAD_FOLDER'].resolve()}")
    print(f"Outputs will go to: {app.config['OUTPUT_FOLDER'].resolve()}")

    app.run(debug=True, host='0.0.0.0', port=5000)
