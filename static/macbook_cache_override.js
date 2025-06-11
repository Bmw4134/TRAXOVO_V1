/**
 * MacBook Cache Override - Direct Browser Reset
 */

// Immediate execution to bypass MacBook browser cache
(function() {
    'use strict';
    
    // Nuclear cache clearing
    try {
        localStorage.clear();
        sessionStorage.clear();
        
        // Clear any cached fictional personnel data
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.includes('MT-07') || key.includes('JAMES') || key.includes('fictional')) {
                localStorage.removeItem(key);
            }
        });
        
        // Force page reload with timestamp
        const now = Date.now();
        const url = window.location.href.split('?')[0];
        
        // Immediate redirect with cache busting
        if (!window.location.search.includes('macbook_override')) {
            window.location.href = url + '?macbook_override=true&authentic=EX210013&t=' + now;
        }
        
    } catch (e) {
        // Fallback: force reload
        window.location.reload(true);
    }
})();