
import React, { useState, useEffect } from 'react';

const NexusTelemetryDisplay = () => {
    const [telemetryData, setTelemetryData] = useState({});
    const [lastUpdate, setLastUpdate] = useState(new Date());

    useEffect(() => {
        const fetchTelemetry = async () => {
            try {
                const response = await fetch('/api/nexus/telemetry');
                const data = await response.json();
                setTelemetryData(data);
                setLastUpdate(new Date());
            } catch (error) {
                console.error('Telemetry fetch failed:', error);
            }
        };

        // Initial fetch
        fetchTelemetry();

        // Auto-refresh every 3 seconds
        const interval = setInterval(fetchTelemetry, 3000);
        return () => clearInterval(interval);
    }, []);

    const getHealthColor = (indicator) => {
        return indicator === '✓' ? '#2ecc71' : '#e74c3c';
    };

    return (
        <div className="nexus-telemetry-display" 
             style={{
                 position: 'fixed',
                 top: '20px',
                 right: '20px',
                 background: 'rgba(0,0,0,0.9)',
                 color: 'white',
                 padding: '15px',
                 borderRadius: '8px',
                 minWidth: '300px',
                 fontSize: '12px',
                 zIndex: 1000
             }}>
            <div style={{marginBottom: '10px', fontWeight: 'bold'}}>
                NEXUS Widget Telemetry
            </div>
            <div style={{marginBottom: '10px', fontSize: '10px', opacity: 0.7}}>
                Last Update: {lastUpdate.toLocaleTimeString()}
            </div>
            
            {Object.entries(telemetryData).map(([widgetId, data]) => (
                <div key={widgetId} style={{
                    marginBottom: '10px',
                    padding: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px'
                }}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                        <span style={{fontWeight: 'bold'}}>{widgetId}</span>
                        <span style={{
                            color: getHealthColor(data.health_indicator),
                            fontSize: '16px'
                        }}>
                            {data.health_indicator}
                        </span>
                    </div>
                    <div style={{marginTop: '5px', fontSize: '10px'}}>
                        Status: {data.connection_status} | 
                        Core: {data.brain_core_linkage}
                    </div>
                    <div style={{marginTop: '3px', fontSize: '10px'}}>
                        Events: {Object.values(data.event_activity || {}).reduce((a, b) => a + b, 0)}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default NexusTelemetryDisplay;
