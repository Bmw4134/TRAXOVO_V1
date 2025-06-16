
/**
 * TRAXOVO Adaptive Display Engine
 * Universal display adaptation for all screen types and orientations
 */

(function() {
    'use strict';
    
    class TRAXOVOAdaptiveEngine {
        constructor() {
            this.breakpoints = {
                xs: 320,
                sm: 576,
                md: 768,
                lg: 992,
                xl: 1200,
                xxl: 1400,
                ultrawide: 1920,
                '4k': 2560
            };
            
            this.currentBreakpoint = this.getCurrentBreakpoint();
            this.orientationState = this.getOrientation();
            this.deviceType = this.detectDeviceType();
            this.displayMetrics = this.calculateDisplayMetrics();
            
            this.init();
        }
        
        init() {
            this.setupViewportMeta();
            this.setupResponsiveImages();
            this.setupAdaptiveLayouts();
            this.setupDynamicFontScaling();
            this.setupTouchOptimization();
            this.setupKeyboardNavigation();
            this.bindEvents();
            
            console.log('TRAXOVO Adaptive Display Engine: Initialized', {
                breakpoint: this.currentBreakpoint,
                orientation: this.orientationState,
                device: this.deviceType,
                metrics: this.displayMetrics
            });
        }
        
        setupViewportMeta() {
            let viewport = document.querySelector('meta[name="viewport"]');
            if (!viewport) {
                viewport = document.createElement('meta');
                viewport.name = 'viewport';
                document.head.appendChild(viewport);
            }
            
            // Adaptive viewport based on device
            const viewportContent = this.deviceType === 'mobile' 
                ? 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes'
                : 'width=device-width, initial-scale=1.0';
                
            viewport.content = viewportContent;
        }
        
        setupResponsiveImages() {
            const images = document.querySelectorAll('img:not([data-adaptive])');
            images.forEach(img => {
                img.setAttribute('data-adaptive', 'true');
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
                
                // Add loading optimization
                if (!img.hasAttribute('loading')) {
                    img.setAttribute('loading', 'lazy');
                }
            });
        }
        
        setupAdaptiveLayouts() {
            document.body.classList.add(
                `traxovo-${this.currentBreakpoint}`,
                `traxovo-${this.orientationState}`,
                `traxovo-${this.deviceType}`
            );
            
            // Apply adaptive grid systems
            this.adaptGridLayouts();
            this.adaptNavigationStructure();
            this.adaptModalSizes();
        }
        
        adaptGridLayouts() {
            const grids = document.querySelectorAll('.row, .grid, .traxovo-grid');
            grids.forEach(grid => {
                const columns = this.calculateOptimalColumns(grid);
                grid.style.setProperty('--adaptive-columns', columns);
                grid.classList.add('traxovo-adaptive-grid');
            });
        }
        
        adaptNavigationStructure() {
            const navbar = document.querySelector('.navbar, .navigation');
            if (navbar) {
                if (this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm') {
                    navbar.classList.add('traxovo-mobile-nav');
                    this.createMobileMenu();
                } else {
                    navbar.classList.add('traxovo-desktop-nav');
                }
            }
        }
        
        createMobileMenu() {
            let mobileMenu = document.querySelector('.traxovo-mobile-menu');
            if (!mobileMenu) {
                mobileMenu = document.createElement('div');
                mobileMenu.className = 'traxovo-mobile-menu';
                mobileMenu.innerHTML = `
                    <button class="traxovo-menu-toggle" aria-label="Toggle Menu">
                        <span></span><span></span><span></span>
                    </button>
                    <div class="traxovo-menu-content"></div>
                `;
                
                const navbar = document.querySelector('.navbar');
                if (navbar) {
                    navbar.appendChild(mobileMenu);
                }
            }
        }
        
        adaptModalSizes() {
            const modals = document.querySelectorAll('.modal, .dialog');
            modals.forEach(modal => {
                const size = this.calculateModalSize();
                modal.style.setProperty('--modal-width', size.width);
                modal.style.setProperty('--modal-height', size.height);
            });
        }
        
        setupDynamicFontScaling() {
            const baseFontSize = this.calculateBaseFontSize();
            document.documentElement.style.setProperty('--adaptive-font-base', `${baseFontSize}px`);
            
            // Apply font scaling to text elements
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, button');
            textElements.forEach(element => {
                if (!element.classList.contains('traxovo-font-scaled')) {
                    this.applyFontScaling(element);
                    element.classList.add('traxovo-font-scaled');
                }
            });
        }
        
        setupTouchOptimization() {
            if (this.deviceType === 'mobile' || this.deviceType === 'tablet') {
                const touchTargets = document.querySelectorAll('button, a, input, select, textarea, .clickable');
                touchTargets.forEach(target => {
                    const currentPadding = window.getComputedStyle(target).padding;
                    if (parseInt(currentPadding) < 12) {
                        target.style.padding = '12px';
                        target.style.minHeight = '48px';
                        target.style.minWidth = '48px';
                    }
                });
            }
        }
        
        setupKeyboardNavigation() {
            // Enhanced keyboard navigation for accessibility
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });
            
            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
        }
        
        calculateOptimalColumns(grid) {
            const containerWidth = grid.offsetWidth;
            if (containerWidth < this.breakpoints.sm) return 1;
            if (containerWidth < this.breakpoints.md) return 2;
            if (containerWidth < this.breakpoints.lg) return 3;
            if (containerWidth < this.breakpoints.xl) return 4;
            if (containerWidth < this.breakpoints.ultrawide) return 5;
            return 6;
        }
        
        calculateModalSize() {
            const viewport = {
                width: window.innerWidth,
                height: window.innerHeight
            };
            
            if (this.deviceType === 'mobile') {
                return { width: '95vw', height: '90vh' };
            } else if (this.deviceType === 'tablet') {
                return { width: '80vw', height: '85vh' };
            } else {
                return { width: '60vw', height: '80vh' };
            }
        }
        
        calculateBaseFontSize() {
            const screenWidth = window.innerWidth;
            const baseSize = 16; // Base 16px
            
            if (screenWidth < this.breakpoints.sm) return Math.max(14, baseSize * 0.875);
            if (screenWidth < this.breakpoints.md) return baseSize;
            if (screenWidth < this.breakpoints.lg) return baseSize * 1.05;
            if (screenWidth < this.breakpoints.xl) return baseSize * 1.1;
            if (screenWidth < this.breakpoints.ultrawide) return baseSize * 1.15;
            return baseSize * 1.2;
        }
        
        applyFontScaling(element) {
            const currentSize = window.getComputedStyle(element).fontSize;
            const scaleFactor = this.calculateScaleFactor();
            const newSize = parseFloat(currentSize) * scaleFactor;
            element.style.fontSize = `${newSize}px`;
        }
        
        calculateScaleFactor() {
            switch (this.currentBreakpoint) {
                case 'xs': return 0.85;
                case 'sm': return 0.9;
                case 'md': return 1.0;
                case 'lg': return 1.05;
                case 'xl': return 1.1;
                case 'xxl': return 1.15;
                case 'ultrawide': return 1.2;
                case '4k': return 1.3;
                default: return 1.0;
            }
        }
        
        getCurrentBreakpoint() {
            const width = window.innerWidth;
            if (width >= this.breakpoints['4k']) return '4k';
            if (width >= this.breakpoints.ultrawide) return 'ultrawide';
            if (width >= this.breakpoints.xxl) return 'xxl';
            if (width >= this.breakpoints.xl) return 'xl';
            if (width >= this.breakpoints.lg) return 'lg';
            if (width >= this.breakpoints.md) return 'md';
            if (width >= this.breakpoints.sm) return 'sm';
            return 'xs';
        }
        
        getOrientation() {
            return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
        }
        
        detectDeviceType() {
            const userAgent = navigator.userAgent.toLowerCase();
            const width = window.innerWidth;
            
            if (/mobile|android|iphone|ipod|blackberry|iemobile/.test(userAgent)) {
                return 'mobile';
            } else if (/tablet|ipad/.test(userAgent) || (width >= 768 && width <= 1024)) {
                return 'tablet';
            } else {
                return 'desktop';
            }
        }
        
        calculateDisplayMetrics() {
            return {
                dpr: window.devicePixelRatio || 1,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                screenWidth: screen.width,
                screenHeight: screen.height,
                availableWidth: screen.availWidth,
                availableHeight: screen.availHeight
            };
        }
        
        bindEvents() {
            window.addEventListener('resize', this.handleResize.bind(this));
            window.addEventListener('orientationchange', this.handleOrientationChange.bind(this));
            document.addEventListener('fullscreenchange', this.handleFullscreenChange.bind(this));
        }
        
        handleResize() {
            clearTimeout(this.resizeTimer);
            this.resizeTimer = setTimeout(() => {
                const newBreakpoint = this.getCurrentBreakpoint();
                if (newBreakpoint !== this.currentBreakpoint) {
                    this.currentBreakpoint = newBreakpoint;
                    this.reapplyAdaptations();
                }
            }, 250);
        }
        
        handleOrientationChange() {
            setTimeout(() => {
                this.orientationState = this.getOrientation();
                this.displayMetrics = this.calculateDisplayMetrics();
                this.reapplyAdaptations();
            }, 300);
        }
        
        handleFullscreenChange() {
            setTimeout(() => {
                this.reapplyAdaptations();
            }, 100);
        }
        
        reapplyAdaptations() {
            // Remove old classes
            document.body.className = document.body.className
                .replace(/traxovo-(xs|sm|md|lg|xl|xxl|ultrawide|4k)/g, '')
                .replace(/traxovo-(portrait|landscape)/g, '')
                .replace(/traxovo-(mobile|tablet|desktop)/g, '');
            
            // Reapply adaptations
            this.setupAdaptiveLayouts();
            this.setupDynamicFontScaling();
            this.setupTouchOptimization();
        }
        
        // Public API methods
        getCurrentState() {
            return {
                breakpoint: this.currentBreakpoint,
                orientation: this.orientationState,
                deviceType: this.deviceType,
                displayMetrics: this.displayMetrics
            };
        }
        
        forceReadaptation() {
            this.reapplyAdaptations();
        }
    }
    
    // Initialize and expose globally
    window.TRAXOVOAdaptiveEngine = new TRAXOVOAdaptiveEngine();
    
    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = TRAXOVOAdaptiveEngine;
    }
    
})();
