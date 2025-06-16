
// Performance Engine Module
(function() {
    'use strict';
    
    const cache = new Map();
    const observers = new Map();
    
    function initPerformanceEngine() {
        setupLazyLoading();
        setupImageOptimization();
        setupCaching();
        monitorPerformance();
    }
    
    function setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('img[data-src]');
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
    
    function setupImageOptimization() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            img.addEventListener('load', function() {
                this.classList.add('loaded');
            });
        });
    }
    
    function setupCaching() {
        // Cache API responses
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            
            if (cache.has(url)) {
                return Promise.resolve(new Response(cache.get(url)));
            }
            
            return originalFetch.apply(this, args)
                .then(response => {
                    if (response.ok && url.includes('/api/')) {
                        response.clone().text().then(text => {
                            cache.set(url, text);
                            // Clear cache after 5 minutes
                            setTimeout(() => cache.delete(url), 300000);
                        });
                    }
                    return response;
                });
        };
    }
    
    function monitorPerformance() {
        // Monitor page load performance
        if ('performance' in window) {
            window.addEventListener('load', function() {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    if (perfData.loadEventEnd - perfData.loadEventStart > 3000) {
                        console.log('Slow page load detected, optimizing...');
                        optimizeCurrentPage();
                    }
                }, 1000);
            });
        }
    }
    
    function optimizeCurrentPage() {
        // Remove non-critical animations on slow devices
        if (navigator.hardwareConcurrency <= 2) {
            document.body.classList.add('low-performance');
        }
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPerformanceEngine);
    } else {
        initPerformanceEngine();
    }
    
})();
