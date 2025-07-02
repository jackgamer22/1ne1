import React, { useState } from 'react';
// Assuming FileUpload.css contains relevant styles or can be adapted.
// If this new component has different class names, FileUpload.css might need minor updates.
import './FileUpload.css';

const FileUpload = ({ onUploadSuccess, processing }) => { // Renamed prop for clarity, was onFileSelect
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  // 'processing' prop will be passed from App.js to disable during backend processing

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
        if (!selectedFile.name.endsWith('.txt')) {
            setError('Please upload a valid .txt file.');
            setFile(null);
            e.target.value = null; // Clear the input
            return;
        }
        setFile(selectedFile);
        setError('');
    } else {
        setFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) { // Check if a file is selected
      setError('Please select a .txt file to upload.');
      return;
    }
    // Redundant check if handleFileChange is robust, but good for safety
    if (!file.name.endsWith('.txt')) {
        setError('Please upload a valid .txt file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // onUploadSuccess in this context will now effectively mean "onUploadAttempt"
    // The actual success/task_id will come from the fetch.
    // Let App.js handle the isProcessing state for the whole app.
    // For this component, we can just use the 'processing' prop to disable the button.

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json(); // Try to parse JSON regardless of response.ok

      if (!response.ok) {
        throw new Error(data.error || `Upload failed with status: ${response.status}`);
      }

      if (data.task_id) {
        onUploadSuccess(data.task_id); // Pass task_id to parent (App.js)
        setFile(null); // Clear the file input
        // Reset the actual file input element so the same file can be re-selected
        if (document.getElementById('file-upload-input-actual')) {
            document.getElementById('file-upload-input-actual').value = "";
        }
      } else {
        throw new Error(data.error || "Upload succeeded but no task_id received.");
      }
    } catch (err) {
      setError(err.message);
      // onUploadSuccess will not be called, so App.js won't transition to polling.
      // App.js might need a separate onError callback from FileUpload if more complex error handling is needed there.
    }
    // The 'processing' state (disabling button etc.) should be managed by App.js based on API calls
  };

  return (
    // Using class names from the previous FileUpload.css for now
    <form onSubmit={handleSubmit} className="file-upload-container">
      <label htmlFor="file-upload-input-actual" className="file-upload-label">
        <h2>Upload Email List (.txt)</h2>
      </label>
      <input
        id="file-upload-input-actual" // Different ID to avoid conflict if old label code is still somewhere
        type="file"
        accept=".txt"
        onChange={handleFileChange}
        disabled={processing} // Controlled by App.js isProcessing state
      />
      <button
        type="submit"
        disabled={processing || !file} // Disable if processing or no file selected
        className="upload-button"
      >
        {processing ? 'Processing...' : 'Start Verification'}
      </button>
      {error && <div className="error-message" style={{marginTop: '10px'}}>{error}</div>}
    </form>
  );
};

export default FileUpload;
