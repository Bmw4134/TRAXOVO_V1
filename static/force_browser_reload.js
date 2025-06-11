/**
 * Force Browser Reload - MacBook Cache Override
 * Immediate hard refresh to show authentic personnel data
 */

(function() {
    'use strict';
    
    // Immediate aggressive cache clearing
    if (typeof Storage !== "undefined") {
        localStorage.clear();
        sessionStorage.clear();
    }
    
    // Force hard reload
    if (window.location) {
        const url = window.location.href.split('?')[0];
        window.location.replace(url + '?force_refresh=' + Date.now() + '&authentic=true&no_cache=true');
    }
    
})();