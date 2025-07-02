import React from 'react';
import './ExportResults.css';

function ExportResults({ taskId, onExport, isCompleted }) {
  if (!isCompleted) {
    return null;
  }

  return (
    <div className="export-results-container">
      <h4>Export Results</h4>
      <button
        onClick={() => onExport('csv')}
        className="export-button export-csv"
        disabled={!isCompleted}
      >
        Export Results (CSV)
      </button>
      <button
        onClick={() => onExport('txt')}
        className="export-button export-txt"
        disabled={!isCompleted}
      >
        Export Valid Emails (TXT)
      </button>
    </div>
  );
}

export default ExportResults;
