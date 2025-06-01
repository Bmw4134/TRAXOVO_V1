/**
 * TRAXOVO Mobile Optimization Engine
 * Comprehensive mobile performance and UI optimization
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
        // Ensure proper viewport settings
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }

    optimizeTouch() {
        // Optimize all clickable elements for touch
        const clickableElements = document.querySelectorAll('a, button, [role="button"], .btn-module');
        
        clickableElements.forEach(element => {
            // Increase touch target size
            if (this.isMobile) {
                element.style.minHeight = '44px';
                element.style.minWidth = '44px';
                element.style.padding = element.style.padding || '12px 16px';
            }
            
            // Add touch feedback
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
        // Create mobile-optimized sidebar
        const sidebar = document.querySelector('.sidebar, nav');
        if (sidebar && this.isMobile) {
            sidebar.style.transform = 'translateX(-100%)';
            sidebar.style.transition = 'transform 0.3s ease';
            
            // Add mobile menu toggle
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
        
        // Add overlay
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
        // Implement progressive loading for mobile
        if (this.isMobile) {
            // Defer non-critical resources
            this.deferNonCriticalCSS();
            this.optimizeImageLoading();
        }
    }

    deferNonCriticalCSS() {
        const nonCriticalCSS = [
            'asset-tooltips.css',
            'smooth-transitions.css'
        ];
        
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
        
        // Add swipe gestures for navigation
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
            
            // Swipe right to open menu (only if near left edge)
            if (Math.abs(diffY) < 100 && diffX < -100 && startX < 50) {
                const sidebar = document.querySelector('.sidebar, nav');
                if (sidebar && sidebar.style.transform === 'translateX(-100%)') {
                    this.toggleMobileMenu();
                }
            }
        });
    }

    preventZoom() {
        // Prevent accidental zoom on inputs
        if (this.isMobile) {
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            });
        }
    }

    // Performance monitoring
    measurePerformance() {
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            const loadTime = timing.loadEventEnd - timing.navigationStart;
            console.log(`TRAXOVO Mobile Load Time: ${loadTime}ms`);
            
            // Report slow performance
            if (loadTime > 3000) {
                console.warn('TRAXOVO: Slow page load detected for mobile');
            }
        }
    }
}

// Initialize mobile optimizer
document.addEventListener('DOMContentLoaded', function() {
    const mobileOptimizer = new TRAXOVOMobileOptimizer();
    
    // Measure performance after load
    window.addEventListener('load', () => {
        mobileOptimizer.measurePerformance();
    });
    
    // Handle orientation changes
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            mobileOptimizer.isMobile = window.innerWidth <= 768;
            mobileOptimizer.setupResponsiveNavigation();
        }, 500);
    });
});

// Export for global use
window.TRAXOVOMobileOptimizer = TRAXOVOMobileOptimizer;
// Advanced Mobile Optimization for TRAXOVO
class MobileOptimizer {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.orientation = this.getOrientation();
        
        this.init();
        this.setupGestures();
        this.optimizeForDevice();
    }

    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
               window.innerWidth <= 768;
    }

    detectTablet() {
        return /iPad|Android/i.test(navigator.userAgent) && window.innerWidth > 768 && window.innerWidth <= 1024;
    }

    getOrientation() {
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    }

    init() {
        if (this.isMobile) {
            document.body.classList.add('mobile-device');
            this.setupMobileNavigation();
            this.optimizeTouchTargets();
            this.setupSwipeGestures();
        }

        if (this.isTablet) {
            document.body.classList.add('tablet-device');
        }

        // Listen for orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // Listen for resize events
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));
    }

    setupMobileNavigation() {
        const sidebar = document.getElementById('sidebarMenu');
        const toggleBtn = document.querySelector('[data-bs-toggle="collapse"]');
        
        if (sidebar && toggleBtn) {
            // Enhanced mobile sidebar behavior
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSidebar();
            });

            // Close sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (this.isMobile && 
                    !sidebar.contains(e.target) && 
                    !toggleBtn.contains(e.target) &&
                    sidebar.classList.contains('show')) {
                    this.closeSidebar();
                }
            });

            // Close sidebar when navigating
            sidebar.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    if (this.isMobile) {
                        this.closeSidebar();
                    }
                });
            });
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebarMenu');
        const overlay = this.getOrCreateOverlay();
        
        if (sidebar.classList.contains('show')) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        const sidebar = document.getElementById('sidebarMenu');
        const overlay = this.getOrCreateOverlay();
        
        sidebar.classList.add('show');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebarMenu');
        const overlay = document.getElementById('mobile-overlay');
        
        sidebar.classList.remove('show');
        if (overlay) overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    getOrCreateOverlay() {
        let overlay = document.getElementById('mobile-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'mobile-overlay';
            overlay.className = 'mobile-overlay';
            overlay.addEventListener('click', () => this.closeSidebar());
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    optimizeTouchTargets() {
        // Ensure all interactive elements meet minimum touch target size
        const minTouchSize = 44; // iOS HIG recommendation
        
        const targets = document.querySelectorAll('button, .btn, a, input, select, .nav-link');
        targets.forEach(target => {
            const rect = target.getBoundingClientRect();
            if (rect.width < minTouchSize || rect.height < minTouchSize) {
                target.style.minWidth = `${minTouchSize}px`;
                target.style.minHeight = `${minTouchSize}px`;
                target.style.display = 'inline-flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
        });
    }

    setupSwipeGestures() {
        let startX, startY, startTime;
        const sidebar = document.getElementById('sidebarMenu');
        
        // Swipe to open/close sidebar
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            startTime = Date.now();
        });

        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const endTime = Date.now();
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;
            
            // Check for horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && 
                Math.abs(deltaX) > 50 && 
                deltaTime < 300) {
                
                if (deltaX > 0 && startX < 50) {
                    // Swipe right from left edge - open sidebar
                    this.openSidebar();
                } else if (deltaX < 0 && sidebar.classList.contains('show')) {
                    // Swipe left - close sidebar
                    this.closeSidebar();
                }
            }
            
            startX = startY = null;
        });
    }

    setupGestures() {
        // Pull-to-refresh gesture (optional)
        if ('serviceWorker' in navigator) {
            this.setupPullToRefresh();
        }
    }

    setupPullToRefresh() {
        let startY = 0;
        let isRefreshing = false;
        
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        });
        
        document.addEventListener('touchmove', (e) => {
            if (isRefreshing || window.scrollY > 0) return;
            
            const currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;
            
            if (pullDistance > 100) {
                this.showRefreshIndicator();
            }
        });
        
        document.addEventListener('touchend', (e) => {
            if (isRefreshing) return;
            
            const endY = e.changedTouches[0].clientY;
            const pullDistance = endY - startY;
            
            if (pullDistance > 100 && window.scrollY === 0) {
                this.performRefresh();
            } else {
                this.hideRefreshIndicator();
            }
        });
    }

    showRefreshIndicator() {
        // Implementation for refresh indicator
        console.log('Show refresh indicator');
    }

    hideRefreshIndicator() {
        // Implementation for hiding refresh indicator
        console.log('Hide refresh indicator');
    }

    performRefresh() {
        window.location.reload();
    }

    handleOrientationChange() {
        this.orientation = this.getOrientation();
        document.body.classList.toggle('landscape', this.orientation === 'landscape');
        document.body.classList.toggle('portrait', this.orientation === 'portrait');
        
        // Adjust layout for orientation
        if (this.orientation === 'landscape' && this.isMobile) {
            this.closeSidebar();
        }
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = this.detectMobile();
        
        if (wasMobile !== this.isMobile) {
            if (this.isMobile) {
                document.body.classList.add('mobile-device');
            } else {
                document.body.classList.remove('mobile-device');
                this.closeSidebar();
            }
        }
    }

    optimizeForDevice() {
        // Device-specific optimizations
        if (this.isMobile) {
            // Prevent zoom on input focus
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.type !== 'file') {
                    input.style.fontSize = '16px';
                }
            });
            
            // Optimize table scrolling
            const tables = document.querySelectorAll('.table-responsive');
            tables.forEach(table => {
                table.style.webkitOverflowScrolling = 'touch';
            });
        }
    }

    debounce(func, wait) {
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
}

// Initialize mobile optimizer
document.addEventListener('DOMContentLoaded', () => {
    window.mobileOptimizer = new MobileOptimizer();
});

// Add mobile-specific CSS
const mobileCSS = `
.mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1040;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.mobile-overlay.show {
    opacity: 1;
    visibility: visible;
}

.mobile-device .table-responsive {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.mobile-device .card {
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border: none;
}

.mobile-device .btn {
    transition: all 0.2s ease;
}

.mobile-device .btn:active {
    transform: scale(0.98);
}

@media (max-width: 768px) {
    .sidebar {
        box-shadow: 2px 0 20px rgba(0,0,0,0.15);
    }
    
    .landscape .metric-card {
        min-height: 60px;
    }
    
    .portrait .metric-card {
        min-height: 80px;
    }
}
`;

const mobileStyle = document.createElement('style');
mobileStyle.textContent = mobileCSS;
document.head.appendChild(mobileStyle);
