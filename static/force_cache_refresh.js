/**
 * Force Cache Refresh - Eliminates MacBook Browser Cache Issues
 * Version: 1749649200 - Authentic Personnel Only
 */

(function() {
    'use strict';
    
    const AUTHENTIC_VERSION = 1749649200;
    
    // Immediate cache clearing
    try {
        // Clear all storage
        localStorage.clear();
        sessionStorage.clear();
        
        // Remove specific fictional personnel cache keys
        const fictionalKeys = ['MT-07', 'JAMES_WILSON', 'fictional_telemetry'];
        fictionalKeys.forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
        
        console.log('✓ All caches cleared - Authentic personnel only');
        
        // Force reload all scripts with new version
        const scripts = document.querySelectorAll('script[src]');
        scripts.forEach(script => {
            if (script.src && !script.src.includes('v=' + AUTHENTIC_VERSION)) {
                const newSrc = script.src.split('?')[0] + '?v=' + AUTHENTIC_VERSION + '&authentic=true';
                script.src = newSrc;
            }
        });
        
        // Force reload all CSS with new version
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            if (link.href && !link.href.includes('v=' + AUTHENTIC_VERSION)) {
                const newHref = link.href.split('?')[0] + '?v=' + AUTHENTIC_VERSION + '&authentic=true';
                link.href = newHref;
            }
        });
        
    } catch (error) {
        console.warn('Cache refresh error:', error);
    }
    
    // Global force refresh function
    window.forceAuthenticRefresh = function() {
        const url = window.location.href.split('?')[0];
        window.location.href = url + '?v=' + AUTHENTIC_VERSION + '&authentic=true&refresh=' + Date.now();
    };
    
    console.log('✓ Force cache refresh activated - Authentic version:', AUTHENTIC_VERSION);
})();