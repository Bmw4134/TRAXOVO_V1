/**
 * Test Automation Endpoint for NEXUS Telematics
 */

async function testAutomationEndpoint() {
    console.log('🔧 Testing NEXUS Telematics automation endpoint...');
    
    try {
        const response = await fetch('/api/automation/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                assetId: 'EX-210013',
                task: 'healthCheck'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ Automation endpoint working:', result);
            console.log(`Job ID: ${result.jobId}`);
            return result;
        } else {
            console.error('❌ Automation endpoint error:', result);
            return null;
        }
    } catch (error) {
        console.error('❌ Network error testing automation:', error);
        return null;
    }
}

// Test automation endpoint when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        testAutomationEndpoint();
    }, 2000);
});

// Global function for manual testing
window.testAutomationEndpoint = testAutomationEndpoint;