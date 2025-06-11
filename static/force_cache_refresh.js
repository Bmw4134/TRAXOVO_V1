/**
 * Force Cache Refresh for MacBook - TRAXOVO NEXUS
 * Implements aggressive cache clearing for updated telemetry data
 */

// Immediate cache clearing on load
(function() {
    'use strict';
    
    // Force reload all cached scripts with version parameter
    const cacheVersion = Date.now();
    
    // Clear all browser caches
    if ('caches' in window) {
        caches.keys().then(function(names) {
            names.forEach(function(name) {
                caches.delete(name);
            });
        });
    }
    
    // Clear localStorage and sessionStorage
    try {
        localStorage.clear();
        sessionStorage.clear();
    } catch(e) {
        console.log('Storage clearing failed:', e);
    }
    
    // Force refresh telemetry data
    window.FORCE_TELEMETRY_REFRESH = true;
    window.CACHE_VERSION = cacheVersion;
    
    console.log('🔄 Force cache refresh initiated - Version:', cacheVersion);
    
    // Override fetch to prevent caching
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        if (args[0] && args[0].includes('/api/')) {
            const url = new URL(args[0], window.location.origin);
            url.searchParams.set('_cache_bust', cacheVersion);
            args[0] = url.toString();
        }
        return originalFetch.apply(this, args);
    };
    
    // Force refresh after DOM loads
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            if (window.location.pathname.includes('dashboard')) {
                window.location.reload(true);
            }
        }, 100);
    });
    
})();