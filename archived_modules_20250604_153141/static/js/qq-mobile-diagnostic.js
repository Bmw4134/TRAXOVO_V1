
// QQ Mobile Diagnostic - Real-time iPhone Optimization
(function() {
    'use strict';
    
    // Device Detection
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isIPhone = /iPhone/i.test(navigator.userAgent);
    const isTablet = /iPad/i.test(navigator.userAgent) || 
                    (navigator.userAgent.includes('Mac') && 'ontouchend' in document);
    
    // Viewport Optimization
    function optimizeViewport() {
        if (isMobile) {
            // Prevent zoom on input focus
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('focus', () => {
                    document.querySelector('meta[name=viewport]').setAttribute(
                        'content', 
                        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
                    );
                });
                
                input.addEventListener('blur', () => {
                    document.querySelector('meta[name=viewport]').setAttribute(
                        'content', 
                        'width=device-width, initial-scale=1.0, viewport-fit=cover'
                    );
                });
            });
        }
    }
    
    // Touch Optimization
    function optimizeTouch() {
        if (isMobile) {
            // Add touch-friendly classes
            const buttons = document.querySelectorAll('button, .btn, a[role="button"]');
            buttons.forEach(btn => {
                btn.classList.add('qq-touch-target');
            });
            
            // Improve scroll performance
            document.documentElement.style.webkitOverflowScrolling = 'touch';
        }
    }
    
    // Performance Monitoring
    function monitorPerformance() {
        const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
                if (entry.entryType === 'measure' && entry.duration > 16) {
                    console.log('Performance issue detected:', entry.name, entry.duration + 'ms');
                }
            });
        });
        
        if ('PerformanceObserver' in window) {
            observer.observe({entryTypes: ['measure', 'navigation']});
        }
    }
    
    // Real-time Layout Optimization
    function optimizeLayout() {
        const containers = document.querySelectorAll('.container, .dashboard, .grid');
        containers.forEach(container => {
            if (isMobile) {
                container.classList.add('qq-mobile-stack');
            } else {
                container.classList.add('qq-desktop-grid');
            }
        });
    }
    
    // Initialize Optimizations
    function init() {
        console.log('QQ Mobile Diagnostic: INITIALIZED');
        optimizeViewport();
        optimizeTouch();
        optimizeLayout();
        monitorPerformance();
        
        // Add device-specific classes
        document.documentElement.classList.add(
            isMobile ? 'qq-mobile' : 'qq-desktop',
            isIPhone ? 'qq-iphone' : '',
            isTablet ? 'qq-tablet' : ''
        );
        
        console.log('QQ Mobile Diagnostic: ACTIVE');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Re-optimize on orientation change
    window.addEventListener('orientationchange', () => {
        setTimeout(optimizeLayout, 100);
    });
    
})();
