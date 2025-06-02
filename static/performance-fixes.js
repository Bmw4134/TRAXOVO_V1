/**
 * TRAXOVO Performance Optimization Module
 * Ensures smooth dashboard rendering and data loading
 */
(function() {
    'use strict';
    
    // Performance monitoring
    const performanceMonitor = {
        startTime: Date.now(),
        
        logTiming: function(operation) {
            const elapsed = Date.now() - this.startTime;
            console.log(`TRAXOVO ${operation}: ${elapsed}ms`);
        },
        
        optimizeImages: function() {
            // Lazy load images if present
            const images = document.querySelectorAll('img[data-src]');
            images.forEach(img => {
                if (img.getBoundingClientRect().top < window.innerHeight) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
            });
        },
        
        cacheAPIResponses: function() {
            // Simple cache for API responses
            if (!window.traxovoCache) {
                window.traxovoCache = new Map();
            }
        },
        
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };
    
    // Initialize performance optimizations
    document.addEventListener('DOMContentLoaded', function() {
        performanceMonitor.cacheAPIResponses();
        performanceMonitor.optimizeImages();
        performanceMonitor.logTiming('DOM Ready');
        
        // Optimize scroll events
        const optimizedScroll = performanceMonitor.debounce(() => {
            performanceMonitor.optimizeImages();
        }, 100);
        
        window.addEventListener('scroll', optimizedScroll);
    });
    
    // Export for global use
    window.TRAXOVOPerformance = performanceMonitor;
    
})();