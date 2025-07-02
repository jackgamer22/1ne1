import React from 'react';
import './ProgressBar.css';

function ProgressBar({ progress, processing }) {
  if (!processing && progress === 0) {
    return null; // Don't show if not processing and progress is 0
  }

  return (
    <div className="progress-bar-container">
      <div className="progress-bar-outer">
        <div
          className="progress-bar-inner"
          style={{ width: `${progress}%` }}
        >
          {progress > 0 && `${progress}%`}
        </div>
      </div>
      {processing && progress < 100 && <p className="progress-text">Processing... please wait.</p>}
      {!processing && progress === 100 && <p className="progress-text">Validation Complete!</p>}
    </div>
  );
}

export default ProgressBar;
