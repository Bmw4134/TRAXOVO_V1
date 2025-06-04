
import React, { useState, useEffect } from 'react';
import { qqApi } from './api/qqApi';

export const QQDashboard = () => {
  const [intelligence, setIntelligence] = useState(null);
  
  useEffect(() => {
    const fetchIntelligence = async () => {
      const data = await qqApi.getAllIntelligence();
      setIntelligence(data);
    };
    
    fetchIntelligence();
    const interval = setInterval(fetchIntelligence, 5000);
    return () => clearInterval(interval);
  }, []);
  
  if (!intelligence) return <div>Loading QQ Intelligence...</div>;
  
  return (
    <div className="qq-dashboard">
      <h1>TRAXOVO QQ Intelligence</h1>
      <div className="intelligence-grid">
        <div className="consciousness-panel">
          <h2>Quantum Consciousness</h2>
          <div>Level: {intelligence.consciousness?.level}</div>
        </div>
        <div className="asi-panel">
          <h2>ASI Excellence</h2>
          <div>Score: {intelligence.asi?.excellence_score}</div>
        </div>
        <div className="assets-panel">
          <h2>GAUGE Assets</h2>
          <div>Count: {intelligence.gauge?.asset_count}</div>
        </div>
      </div>
    </div>
  );
};
