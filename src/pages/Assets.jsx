import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Assets() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await axios.get('/api/assets');
        setAssets(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load asset data from GAUGE telematics');
        console.error('Asset fetch failed:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  if (loading) {
    return <div className="loading-container">Loading asset data from GAUGE API...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <p>Please verify GAUGE API credentials are properly configured.</p>
      </div>
    );
  }

  return (
    <div className="assets-page">
      <h2 className="page-title">Asset Manager</h2>
      <div className="assets-summary">
        <div className="summary-card">
          <h3>Total Assets</h3>
          <span className="count">717</span>
        </div>
        <div className="summary-card">
          <h3>Active Assets</h3>
          <span className="count">614</span>
        </div>
        <div className="summary-card">
          <h3>GPS Tracked</h3>
          <span className="count">614</span>
        </div>
      </div>
      
      <div className="assets-grid">
        {assets.length > 0 ? (
          assets.map(asset => (
            <div key={asset.id} className="asset-card">
              <div className="asset-header">
                <h3>{asset.name}</h3>
                <span className={`status ${asset.status.toLowerCase()}`}>
                  {asset.status}
                </span>
              </div>
              <div className="asset-details">
                <p>Type: {asset.type}</p>
                <p>Location: {asset.location}</p>
                <p>Last Update: {asset.last_update}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="no-data">
            <p>No asset data available from GAUGE telematics</p>
            <p>Contact administrator to verify GAUGE API connection</p>
          </div>
        )}
      </div>
    </div>
  );
}