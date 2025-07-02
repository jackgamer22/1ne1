import React, { useCallback, useState } from 'react';
import './FileUpload.css';

function FileUpload({ onFileSelect, processing }) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.txt')) {
        onFileSelect(file);
      } else {
        alert("Please upload a .txt file.");
      }
    }
  }, [onFileSelect]);

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.txt')) {
        onFileSelect(file);
      } else {
        alert("Please upload a .txt file.");
      }
      e.target.value = null; // Reset file input
    }
  };

  return (
    <div
      className={`file-upload-container ${dragActive ? "drag-active" : ""}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload-input"
        accept=".txt"
        onChange={handleChange}
        disabled={processing}
      />
      <label htmlFor="file-upload-input" className="file-upload-label">
        {processing ? (
          <p>Processing...</p>
        ) : (
          <>
            <p>Drag and drop your .txt file here, or</p>
            <button type="button" className="upload-button" onClick={() => document.getElementById('file-upload-input').click()} disabled={processing}>
              Click to select file
            </button>
          </>
        )}
      </label>
      {dragActive && <div className="drag-file-element"></div>}
    </div>
  );
}

export default FileUpload;
