import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function WatsonAdmin() {
  const [adminData, setAdminData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const response = await axios.get('/api/watson-admin');
        setAdminData(response.data);
        setError(null);
      } catch (err) {
        setError('Watson administrative access restricted or unavailable');
        console.error('Watson admin fetch failed:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
  }, []);

  if (loading) {
    return <div className="loading-container">Loading Watson administrative panel...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Access Restricted</h2>
        <p>{error}</p>
        <p>This panel is reserved for Watson administrative access only.</p>
      </div>
    );
  }

  return (
    <div className="watson-admin-page">
      <h2 className="page-title">Watson Administrative Panel</h2>
      <div className="admin-sections">
        <div className="admin-card">
          <h3>System Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span>GAUGE API</span>
              <span className="status connected">Connected</span>
            </div>
            <div className="status-item">
              <span>RAGLE Billing</span>
              <span className="status connected">Active</span>
            </div>
            <div className="status-item">
              <span>Database</span>
              <span className="status connected">Operational</span>
            </div>
          </div>
        </div>
        
        <div className="admin-card">
          <h3>User Management</h3>
          <p>Total Users: {adminData?.user_count || 'Loading...'}</p>
          <p>Active Sessions: {adminData?.active_sessions || 'Loading...'}</p>
        </div>
        
        <div className="admin-card">
          <h3>System Logs</h3>
          <div className="log-viewer">
            {adminData?.recent_logs ? (
              adminData.recent_logs.map((log, index) => (
                <div key={index} className="log-entry">
                  <span className="timestamp">{log.timestamp}</span>
                  <span className="message">{log.message}</span>
                </div>
              ))
            ) : (
              <p>No recent logs available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}