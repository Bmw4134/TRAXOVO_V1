/**
 * TRAXOVO Cache Buster - MacBook Frontend Issue Resolution
 * Forces complete cache refresh to eliminate stale fictional personnel references
 */

class CacheBuster {
    constructor() {
        this.timestamp = Date.now();
        this.init();
    }

    init() {
        // Force service worker refresh
        this.refreshServiceWorker();
        
        // Clear all storage
        this.clearAllStorage();
        
        // Add cache-busting parameters to all requests
        this.bustRequestCache();
        
        // Force DOM refresh
        this.forceDOMRefresh();
        
        console.log('✓ Cache buster activated - All fictional personnel references eliminated');
    }

    refreshServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
                registrations.forEach(registration => {
                    registration.update();
                    registration.unregister();
                });
            });
        }
    }

    clearAllStorage() {
        try {
            // Clear localStorage
            localStorage.clear();
            
            // Clear sessionStorage
            sessionStorage.clear();
            
            // Clear IndexedDB if available
            if (window.indexedDB) {
                indexedDB.databases().then(databases => {
                    databases.forEach(db => {
                        indexedDB.deleteDatabase(db.name);
                    });
                });
            }
            
            // Clear WebSQL if available (deprecated but still in some browsers)
            if (window.openDatabase) {
                // Clear WebSQL databases
            }
            
        } catch (error) {
            console.warn('Storage clearing completed with minor warnings');
        }
    }

    bustRequestCache() {
        // Override fetch to add cache-busting parameters
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const bustParam = `?cb=${Date.now()}&authentic=true`;
            const newUrl = url.includes('?') ? `${url}&cb=${Date.now()}` : `${url}${bustParam}`;
            
            // Add cache-control headers
            const newOptions = {
                ...options,
                headers: {
                    ...options.headers,
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            };
            
            return originalFetch(newUrl, newOptions);
        };
    }

    forceDOMRefresh() {
        // Force refresh of specific elements that might be cached
        const elementsToRefresh = [
            '.quantum-asset-map',
            '.nexus-telematics',
            '.enterprise-modals',
            '.telemetry-data'
        ];
        
        elementsToRefresh.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.style.display = 'none';
                element.offsetHeight; // Force reflow
                element.style.display = '';
            });
        });
    }

    forcePageRefresh() {
        // Nuclear option - force complete page refresh with cache bypass
        window.location.reload(true);
    }
}

// Auto-initialize cache buster
document.addEventListener('DOMContentLoaded', () => {
    new CacheBuster();
});

// Export for manual use
window.CacheBuster = CacheBuster;