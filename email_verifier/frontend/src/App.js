import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import StatsDisplay from './components/StatsDisplay';
import ProgressBar from './components/ProgressBar';
import ExportResults from './components/ExportResults';

function App() {
  // No longer need 'file' state here for triggering upload, FileUpload handles its own selection
  const [taskId, setTaskId] = useState(null);
  const [stats, setStats] = useState({});
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false); // True when backend is processing
  const [error, setError] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  const handleUploadSuccess = (newTaskId) => {
    setTaskId(newTaskId);
    setStats({}); // Reset stats for new task
    setProgress(0);
    setIsProcessing(true); // Start polling and show processing UI in App
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

  // Effect for polling status - This remains largely the same
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
        {/* FileUpload now handles its own upload state, but App still controls overall processing UI via 'isProcessing' */}
        {/* The 'processing' prop for FileUpload now indicates if the *backend* is busy, so user can't submit another file. */}
        <FileUpload onUploadSuccess={handleUploadSuccess} processing={isProcessing} />

        {error && <p className="error-message">Error: {error}</p>}

        {/* Show progress and stats if processing OR if completed (to see final stats) */}
        {(isProcessing || isCompleted || taskId) && (Object.keys(stats).length > 0 || isProcessing) && (
          <>
            <ProgressBar progress={progress} processing={isProcessing} />
            <StatsDisplay stats={stats} />
            {/* ExportResults is shown when completed */}
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
