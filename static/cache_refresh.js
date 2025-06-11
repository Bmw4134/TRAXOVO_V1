/**
 * NEXUS Cache Refresh Module
 * Forces browser cache refresh for updated telemetry data
 */

// Force cache refresh for telemetry updates
const cacheVersion = Date.now();

// Update all script sources with cache busting
document.addEventListener('DOMContentLoaded', function() {
    // Reload telemetry simulator with fresh data
    if (window.TelemetrySimulator) {
        console.log('🔄 Refreshing telemetry data...');
        
        // Force reload of telemetry data
        const event = new CustomEvent('telemetryRefresh', {
            detail: { timestamp: cacheVersion }
        });
        document.dispatchEvent(event);
    }
    
    // Clear any cached asset data
    if (window.nexusTelematics) {
        window.nexusTelematics.assets.clear();
        console.log('🗺️ Asset cache cleared');
    }
});

// Auto-refresh every 30 seconds to ensure latest data
setInterval(() => {
    if (window.location.pathname.includes('dashboard')) {
        console.log('🔄 Auto-refreshing telemetry data...');
        const refreshEvent = new CustomEvent('telemetryRefresh', {
            detail: { timestamp: Date.now() }
        });
        document.dispatchEvent(refreshEvent);
    }
}, 30000);