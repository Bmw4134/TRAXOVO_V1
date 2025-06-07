
import React, { useState, useEffect } from 'react';

const NexusValidationDisplay = () => {
    const [validationData, setValidationData] = useState({});
    const [qaMode, setQaMode] = useState(true);

    useEffect(() => {
        // Initialize validation data
        setValidationData({
            qa_state: 'ACTIVE',
            modules_synced: 4,
            total_modules: 4,
            last_validation: new Date().toISOString()
        });
    }, []);

    return (
        <div className="nexus-validation-display" 
             style={{
                 position: 'fixed',
                 bottom: '20px',
                 right: '20px',
                 background: qaMode ? 'rgba(46, 204, 113, 0.9)' : 'rgba(231, 76, 60, 0.9)',
                 color: 'white',
                 padding: '15px',
                 borderRadius: '8px',
                 minWidth: '250px',
                 fontSize: '12px',
                 zIndex: 1000
             }}>
            <div style={{fontWeight: 'bold', marginBottom: '10px'}}>
                {qaMode ? '✓ QA MODE ACTIVE' : '⚠️ VALIDATION FAILED'}
            </div>
            <div style={{marginBottom: '5px'}}>
                Modules Synced: {validationData.modules_synced}/{validationData.total_modules}
            </div>
            <div style={{marginBottom: '5px'}}>
                State: {validationData.qa_state}
            </div>
            <div style={{fontSize: '10px', opacity: 0.8}}>
                Last Validation: {new Date(validationData.last_validation).toLocaleTimeString()}
            </div>
        </div>
    );
};

export default NexusValidationDisplay;
