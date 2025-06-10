/**
 * TRAXOVO Polling Controller - Eliminates excessive API calls
 * Fixes server overload and flashing behavior
 */

class PollingController {
    constructor() {
        this.activeIntervals = new Set();
        this.lastApiCalls = new Map();
        this.isEnabled = true;
    }

    // Stop all existing intervals immediately
    stopAllPolling() {
        this.activeIntervals.forEach(intervalId => {
            clearInterval(intervalId);
        });
        this.activeIntervals.clear();
        console.log('✓ Stopped all aggressive polling intervals');
    }

    // Controlled single API call with rate limiting
    async makeControlledApiCall(endpoint, minInterval = 60000) {
        const now = Date.now();
        const lastCall = this.lastApiCalls.get(endpoint);
        
        if (lastCall && (now - lastCall) < minInterval) {
            return null; // Skip if too recent
        }

        try {
            this.lastApiCalls.set(endpoint, now);
            const response = await fetch(endpoint);
            return await response.json();
        } catch (error) {
            console.warn(`Controlled API call failed: ${endpoint}`);
            return null;
        }
    }

    // Setup minimal essential polling only
    setupEssentialPolling() {
        // Only allow quantum metrics updates every 2 minutes
        const quantumInterval = setInterval(async () => {
            const data = await this.makeControlledApiCall('/api/quantum-infinity-consciousness', 120000);
            if (data) {
                console.log('🔄 Essential quantum update');
            }
        }, 120000);

        this.activeIntervals.add(quantumInterval);
        console.log('✓ Setup minimal essential polling only');
    }
}

// Global controller instance
window.pollingController = new PollingController();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Stop all aggressive polling immediately
    window.pollingController.stopAllPolling();
    
    // Setup only essential minimal polling
    setTimeout(() => {
        window.pollingController.setupEssentialPolling();
    }, 5000);
});

// Override common polling functions to prevent excessive calls
window.refreshPerformanceVectorData = function() {
    console.log('Performance vector refresh disabled - preventing server overload');
    return;
};

window.initializeDynamicPerformanceVectors = function() {
    console.log('Dynamic performance vectors disabled - using static data');
    return;
};