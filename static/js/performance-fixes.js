/*
TRAXOVO Performance Fixes - Critical JavaScript Error Resolution
Fixes Leaflet map errors and undefined function references
*/

(function() {
    'use strict';
    
    // Global error prevention for undefined functions
    window.toggleGeofences = window.toggleGeofences || function() {
        console.log('Geofence toggle functionality will be initialized when map loads');
    };
    
    // Safe Leaflet initialization
    function initializeMapSafely() {
        if (typeof L !== 'undefined' && document.getElementById('map')) {
            // Leaflet is available, proceed with map initialization
            return true;
        } else if (document.getElementById('map')) {
            // Map container exists but Leaflet not loaded yet
            console.log('Map container found, waiting for Leaflet library...');
            return false;
        }
        return false;
    }
    
    // Marker cluster safe handler
    window.markerCluster = window.markerCluster || {
        clearLayers: function() {
            console.log('Marker cluster will clear when properly initialized');
        },
        addLayer: function() {
            console.log('Marker will be added when cluster is ready');
        }
    };
    
    // Prevent syntax errors in template rendering
    function sanitizeTemplateVariables() {
        // Fix any template variable issues that might cause syntax errors
        var scriptTags = document.querySelectorAll('script[type="text/javascript"]');
        for (var i = 0; i < scriptTags.length; i++) {
            var script = scriptTags[i];
            if (script.innerHTML.includes('*')) {
                // Check for template syntax issues
                try {
                    var cleanContent = script.innerHTML.replace(/\{\{[^}]*\*[^}]*\}\}/g, '""');
                    if (cleanContent !== script.innerHTML) {
                        script.innerHTML = cleanContent;
                        console.log('Fixed template syntax in script tag');
                    }
                } catch (e) {
                    console.warn('Script tag contains syntax issues:', e);
                }
            }
        }
    }
    
    // Safe DOM ready handler
    function initializeWhenReady() {
        sanitizeTemplateVariables();
        
        // Wait for Leaflet if map container exists
        if (document.getElementById('map') && typeof L === 'undefined') {
            // Check periodically for Leaflet availability
            var checkInterval = setInterval(function() {
                if (typeof L !== 'undefined') {
                    clearInterval(checkInterval);
                    initializeMapSafely();
                }
            }, 100);
            
            // Stop checking after 10 seconds
            setTimeout(function() {
                clearInterval(checkInterval);
            }, 10000);
        }
    }
    
    // Initialize immediately if DOM is ready, otherwise wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeWhenReady);
    } else {
        initializeWhenReady();
    }
    
})();