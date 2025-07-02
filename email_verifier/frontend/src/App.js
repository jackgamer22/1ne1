import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import StatsDisplay from './components/StatsDisplay';
import ProgressBar from './components/ProgressBar';
import ExportResults from './components/ExportResults';

function App() {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [stats, setStats] = useState({});
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setTaskId(null);
    setStats({});
    setProgress(0);
    setIsProcessing(true); // Set processing true when file is selected to trigger upload
    setIsCompleted(false);
    setError('');
  };

  const handleExport = (format) => {
    if (taskId) {
      const filename = format === 'csv' ? 'results.csv' : 'valid_emails.txt';
      // Assuming backend is running on port 5000
      window.location.href = `http://localhost:5000/download/${taskId}/${filename}`;
    }
  };

  // Effect for file upload
  useEffect(() => {
    if (file && isProcessing && !taskId) { // Only upload if file is set, processing is true, and no taskId yet
      const uploadFile = async () => {
        const formData = new FormData();
        formData.append('file', file);

        try {
          // Assuming backend is running on port 5000
          const response = await fetch('http://localhost:5000/upload', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || `HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          setTaskId(data.task_id);
          // setIsProcessing(true); // Already set
          setFile(null); // Clear the file state after successful upload trigger
        } catch (err) {
          setError(`Upload failed: ${err.message}`);
          setIsProcessing(false);
          setFile(null);
        }
      };
      uploadFile();
    }
  }, [file, isProcessing, taskId]);

  // Effect for polling status
  useEffect(() => {
    let intervalId;
    if (taskId && isProcessing) {
      intervalId = setInterval(async () => {
        try {
          // Assuming backend is running on port 5000
          const response = await fetch(`http://localhost:5000/status/${taskId}`);
          if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || `Status fetch failed: ${response.status}`);
          }
          const data = await response.json();
          setStats(data.stats || {});
          setProgress(data.progress || 0);

          if (data.status === 'completed') {
            setIsProcessing(false);
            setIsCompleted(true);
            clearInterval(intervalId);
          } else if (data.status === 'error') {
            setError(data.error_message || 'Processing failed on the server.');
            setIsProcessing(false);
            setIsCompleted(false); // Ensure it's not marked as completed on error
            clearInterval(intervalId);
          }
        } catch (err) {
          setError(`Error fetching status: ${err.message}`);
          setIsProcessing(false); // Stop polling on error
          clearInterval(intervalId);
        }
      }, 2000); // Poll every 2 seconds
    }
    return () => clearInterval(intervalId); // Cleanup on component unmount or when taskId/isProcessing changes
  }, [taskId, isProcessing]);


  return (
    <div className="App">
      <header className="App-header">
        <h1>Email Verifier</h1>
      </header>
      <main className="App-main">
        <FileUpload onFileSelect={handleFileSelect} processing={isProcessing && !isCompleted} />
        {error && <p className="error-message">Error: {error}</p>}
        {(isProcessing || isCompleted || Object.keys(stats).length > 0) && (
          <>
            <ProgressBar progress={progress} processing={isProcessing && !isCompleted} />
            <StatsDisplay stats={stats} />
            <ExportResults taskId={taskId} onExport={handleExport} isCompleted={isCompleted} />
          </>
        )}
      </main>
      <footer className="App-footer">
        <p>&copy; 2024 Email Verifier App</p>
      </footer>
    </div>
  );
}

export default App;
