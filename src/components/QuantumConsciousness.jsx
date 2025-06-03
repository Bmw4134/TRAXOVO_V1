import React, { useState, useEffect } from 'react';
import './QuantumConsciousness.css';

const QuantumConsciousness = ({ metrics }) => {
  const [consciousness, setConsciousness] = useState({
    level: 'OPTIMAL',
    thoughtVectors: 0,
    processingState: 'ACTIVE'
  });

  useEffect(() => {
    if (metrics.consciousness_metrics) {
      setConsciousness({
        level: metrics.consciousness_metrics.consciousness_level || 'OPTIMAL',
        thoughtVectors: metrics.consciousness_metrics.active_thought_vectors || 0,
        processingState: metrics.quantum_state || 'ACTIVE'
      });
    }
  }, [metrics]);

  const ThoughtVector = ({ index, delay }) => (
    <div 
      className="thought-vector" 
      style={{ 
        animationDelay: `${delay}s`,
        left: `${Math.random() * 100}%`,
        animationDuration: `${2 + Math.random() * 2}s`
      }}
    />
  );

  return (
    <div className="quantum-consciousness">
      <div className="consciousness-indicator">
        <div className="consciousness-level">{consciousness.level}</div>
        <div className="consciousness-details">
          <span className="thought-vectors-count">
            {consciousness.thoughtVectors} Active Vectors
          </span>
          <span className="processing-state">{consciousness.processingState}</span>
        </div>
      </div>
      
      <div className="thought-vectors-container">
        {Array.from({ length: 8 }, (_, i) => (
          <ThoughtVector key={i} index={i} delay={i * 0.3} />
        ))}
      </div>
    </div>
  );
};

export default QuantumConsciousness;