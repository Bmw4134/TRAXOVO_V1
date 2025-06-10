/**
 * TRAXOVO Rate Limiter - Prevents excessive API polling
 * Fixes flashing and server overload issues
 */

class RateLimiter {
    constructor() {
        this.apiCalls = new Map();
        this.intervals = new Map();
    }

    // Clear all existing intervals to prevent multiple polling
    clearAllIntervals() {
        this.intervals.forEach(interval => clearInterval(interval));
        this.intervals.clear();
        console.log('✓ Cleared excessive polling intervals');
    }

    // Rate limit API calls
    canMakeCall(endpoint, minimumInterval = 30000) {
        const now = Date.now();
        const lastCall = this.apiCalls.get(endpoint);
        
        if (!lastCall || (now - lastCall) >= minimumInterval) {
            this.apiCalls.set(endpoint, now);
            return true;
        }
        return false;
    }

    // Controlled API fetch with rate limiting
    async controlledFetch(endpoint, minimumInterval = 30000) {
        if (!this.canMakeCall(endpoint, minimumInterval)) {
            return null; // Skip if too soon
        }

        try {
            const response = await fetch(endpoint);
            return await response.json();
        } catch (error) {
            console.warn(`API call failed for ${endpoint}:`, error);
            return null;
        }
    }

    // Set up controlled polling with proper intervals
    setupControlledPolling(endpoint, callback, interval = 60000) {
        // Clear any existing interval for this endpoint
        if (this.intervals.has(endpoint)) {
            clearInterval(this.intervals.get(endpoint));
        }

        // Set up new controlled interval
        const intervalId = setInterval(async () => {
            const data = await this.controlledFetch(endpoint, interval);
            if (data && callback) {
                callback(data);
            }
        }, interval);

        this.intervals.set(endpoint, intervalId);
        console.log(`✓ Setup controlled polling for ${endpoint} every ${interval/1000}s`);
    }
}

// Global rate limiter instance
window.rateLimiter = new RateLimiter();

// Initialize rate limiting on page load
document.addEventListener('DOMContentLoaded', () => {
    // Clear any existing aggressive polling
    window.rateLimiter.clearAllIntervals();
    
    // Set up controlled polling for essential endpoints only
    window.rateLimiter.setupControlledPolling('/api/quantum-infinity-consciousness', 
        (data) => {
            console.log('🔄 Quantum metrics updated');
        }, 
        30000 // 30 seconds
    );
});