import React from 'react';

export default function SafeMode() {
  return (
    <div className="safe-mode-page">
      <div className="safe-mode-header">
        <h2 className="safe-mode-title">🛡️ SAFE MODE</h2>
        <p className="safe-mode-subtitle">Minimal diagnostic interface</p>
      </div>
      
      <div className="safe-mode-content">
        <div className="diagnostic-card">
          <h3>System Status</h3>
          <div className="status-list">
            <div className="status-item">
              <span>React Frontend</span>
              <span className="status-ok">Operational</span>
            </div>
            <div className="status-item">
              <span>Flask Backend</span>
              <span className="status-ok">Running</span>
            </div>
            <div className="status-item">
              <span>Database</span>
              <span className="status-ok">Connected</span>
            </div>
          </div>
        </div>
        
        <div className="diagnostic-card">
          <h3>Recovery Options</h3>
          <p>This is a minimal diagnostic UI in case the dashboard breaks.</p>
          <p>No external API calls, just layout test mode.</p>
          <div className="recovery-actions">
            <button className="recovery-btn">Clear Cache</button>
            <button className="recovery-btn">Reset Preferences</button>
            <button className="recovery-btn">Return to Dashboard</button>
          </div>
        </div>
        
        <div className="diagnostic-card">
          <h3>System Information</h3>
          <div className="info-list">
            <p>Platform: TRAXOVO Fleet Management</p>
            <p>Mode: Safe Diagnostic</p>
            <p>Last Update: {new Date().toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}