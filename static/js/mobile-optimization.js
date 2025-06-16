
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
        const touchElements = document.querySelectorAll('.btn, .card, .metric-card, .modern-card');
        
        touchElements.forEach(element => {
            // Enhanced touch feedback
            element.addEventListener('touchstart', function(e) {
                this.classList.add('touch-active');
                
                // Add ripple effect
                const ripple = document.createElement('div');
                ripple.className = 'touch-ripple';
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = (e.touches[0].clientX - rect.left - size/2) + 'px';
                ripple.style.top = (e.touches[0].clientY - rect.top - size/2) + 'px';
                this.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
            
            element.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            });
            
            // Prevent double-tap zoom on buttons
            if (element.matches('.btn, button')) {
                element.addEventListener('touchend', function(e) {
                    e.preventDefault();
                    this.click();
                });
            }
        });
        
        // Add swipe gestures for navigation
        addSwipeGestures();
    }
    
    function addSwipeGestures() {
        let startX, startY;
        
        document.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', function(e) {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Right swipe to open sidebar
            if (deltaX > 100 && Math.abs(deltaY) < 50) {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar && window.innerWidth <= 768) {
                    sidebar.classList.add('show');
                }
            }
            
            startX = startY = null;
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
