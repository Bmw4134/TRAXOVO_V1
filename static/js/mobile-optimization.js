
// Mobile Optimization Module
(function() {
    'use strict';
    
    function initMobileOptimization() {
        // Touch-friendly interactions
        addTouchSupport();
        optimizeForMobile();
        handleOrientationChange();
    }
    
    function addTouchSupport() {
        const touchElements = document.querySelectorAll('.btn, .card, .metric-card');
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });
            
            element.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            });
        });
    }
    
    function optimizeForMobile() {
        if (window.innerWidth <= 768) {
            document.body.classList.add('mobile-optimized');
            
            // Optimize tables for mobile
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                table.classList.add('table-responsive');
            });
        }
    }
    
    function handleOrientationChange() {
        window.addEventListener('orientationchange', function() {
            setTimeout(optimizeForMobile, 100);
        });
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileOptimization);
    } else {
        initMobileOptimization();
    }
    
})();
