/**
 * TRAXOVO Mobile Optimization Engine
 * Clean, optimized mobile performance and UI optimization
 */

class TRAXOVOMobileOptimizer {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
        this.touchSupported = 'ontouchstart' in window;
        this.init();
    }

    init() {
        this.setupMobileViewport();
        this.optimizeTouch();
        this.setupResponsiveNavigation();
        this.optimizeAsyncLoading();
        this.setupMobileGestures();
        this.preventZoom();
    }

    setupMobileViewport() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }

    optimizeTouch() {
        const clickableElements = document.querySelectorAll('a, button, [role="button"], .btn-module');
        
        clickableElements.forEach(element => {
            if (this.isMobile) {
                element.style.minHeight = '44px';
                element.style.minWidth = '44px';
                element.style.padding = element.style.padding || '12px 16px';
            }
            
            element.addEventListener('touchstart', function() {
                this.style.opacity = '0.7';
            });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.opacity = '1';
                }, 150);
            });
        });
    }

    setupResponsiveNavigation() {
        const sidebar = document.querySelector('.sidebar, nav');
        if (sidebar && this.isMobile) {
            sidebar.style.transform = 'translateX(-100%)';
            sidebar.style.transition = 'transform 0.3s ease';
            this.createMobileMenuToggle();
        }
    }

    createMobileMenuToggle() {
        const existingToggle = document.querySelector('.mobile-menu-toggle');
        if (existingToggle) return;

        const toggle = document.createElement('button');
        toggle.className = 'mobile-menu-toggle';
        toggle.innerHTML = '☰';
        toggle.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 18px;
            min-height: 44px;
            min-width: 44px;
        `;
        
        toggle.addEventListener('click', this.toggleMobileMenu.bind(this));
        document.body.appendChild(toggle);
    }

    toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar, nav');
        if (!sidebar) return;
        
        const isOpen = sidebar.style.transform === 'translateX(0px)' || sidebar.style.transform === '';
        sidebar.style.transform = isOpen ? 'translateX(-100%)' : 'translateX(0px)';
        
        if (!isOpen) {
            this.createOverlay();
        } else {
            this.removeOverlay();
        }
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'mobile-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        `;
        overlay.addEventListener('click', this.toggleMobileMenu.bind(this));
        document.body.appendChild(overlay);
    }

    removeOverlay() {
        const overlay = document.querySelector('.mobile-overlay');
        if (overlay) overlay.remove();
    }

    optimizeAsyncLoading() {
        if (this.isMobile) {
            this.deferNonCriticalCSS();
            this.optimizeImageLoading();
        }
    }

    deferNonCriticalCSS() {
        const nonCriticalCSS = ['asset-tooltips.css', 'smooth-transitions.css'];
        
        nonCriticalCSS.forEach(cssFile => {
            const link = document.querySelector(`link[href*="${cssFile}"]`);
            if (link) {
                link.media = 'print';
                link.onload = function() {
                    this.media = 'all';
                };
            }
        });
    }

    optimizeImageLoading() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.loading !== 'lazy') {
                img.loading = 'lazy';
            }
        });
    }

    setupMobileGestures() {
        if (!this.touchSupported) return;
        
        let startX, startY;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            if (Math.abs(diffY) < 100 && diffX < -100 && startX < 50) {
                const sidebar = document.querySelector('.sidebar, nav');
                if (sidebar && sidebar.style.transform === 'translateX(-100%)') {
                    this.toggleMobileMenu();
                }
            }
        });
    }

    preventZoom() {
        if (this.isMobile) {
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            });
        }
    }

    measurePerformance() {
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            const loadTime = timing.loadEventEnd - timing.navigationStart;
            console.log(`TRAXOVO Mobile Load Time: ${loadTime}ms`);
            
            if (loadTime > 3000) {
                console.warn('TRAXOVO: Slow page load detected for mobile');
            }
        }
    }
}

// Initialize mobile optimizer
document.addEventListener('DOMContentLoaded', function() {
    const mobileOptimizer = new TRAXOVOMobileOptimizer();
    
    window.addEventListener('load', () => {
        mobileOptimizer.measurePerformance();
    });
    
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            mobileOptimizer.isMobile = window.innerWidth <= 768;
            mobileOptimizer.setupResponsiveNavigation();
        }, 500);
    });
});

window.TRAXOVOMobileOptimizer = TRAXOVOMobileOptimizer;