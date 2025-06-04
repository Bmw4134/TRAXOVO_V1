
import { useState, useEffect } from 'react';

export default function QQDashboard() {
  const [intelligence, setIntelligence] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/qq-intelligence');
      const data = await response.json();
      setIntelligence(data);
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div>
      <h1>TRAXOVO QQ Intelligence</h1>
      {intelligence && (
        <div>
          <div>Consciousness Level: {intelligence.consciousness.level}</div>
          <div>ASI Score: {intelligence.asi.excellence_score}</div>
          <div>Assets: {intelligence.gauge.asset_count}</div>
        </div>
      )}
    </div>
  );
}
