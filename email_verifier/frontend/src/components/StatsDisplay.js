import React from 'react';
import './StatsDisplay.css';

function StatsDisplay({ stats }) {
  const statItems = [
    { label: "Total Emails Loaded", value: stats.total_loaded || 0 },
    { label: "Duplicates Removed", value: stats.duplicates_removed || 0 },
    { label: "Total to Validate", value: stats.total_to_validate || 0 },
    { label: "Live Emails", value: stats.live || 0 },
    { label: "Dead/Bounced", value: stats.dead || 0 },
    { label: "Invalid Format", value: stats.invalid_format || 0 },
    { label: "Errors", value: stats.errors || 0 }
  ];

  return (
    <div className="stats-display-container">
      <h3>Validation Summary</h3>
      <div className="stats-grid">
        {statItems.map(item => (
          <div key={item.label} className="stat-item">
            <span className="stat-value">{item.value}</span>
            <span className="stat-label">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StatsDisplay;
