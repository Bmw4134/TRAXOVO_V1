/**
 * Responsive Orientation Handler for Quantum ASI Dashboard
 * Handles dynamic scaling and layout optimization for portrait/landscape
 */

class ResponsiveOrientationHandler {
    constructor() {
        this.currentOrientation = this.getOrientation();
        this.resizeTimeout = null;
        this.init();
    }

    init() {
        // Listen for orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleOrientationChange(), 100);
        });

        // Listen for resize events (covers desktop and mobile)
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => this.handleResize(), 250);
        });

        // Initial setup
        this.optimizeLayout();
        this.setupViewportMeta();
    }

    getOrientation() {
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    }

    handleOrientationChange() {
        const newOrientation = this.getOrientation();
        if (newOrientation !== this.currentOrientation) {
            this.currentOrientation = newOrientation;
            this.optimizeLayout();
            this.triggerLayoutUpdate();
        }
    }

    handleResize() {
        this.optimizeLayout();
        this.adjustGridSpacing();
    }

    optimizeLayout() {
        const body = document.body;
        const isPortrait = this.currentOrientation === 'portrait';
        const isMobile = window.innerWidth <= 768;
        const isLandscapeShort = this.currentOrientation === 'landscape' && window.innerHeight <= 600;

        // Apply responsive classes
        body.classList.toggle('orientation-portrait', isPortrait);
        body.classList.toggle('orientation-landscape', !isPortrait);
        body.classList.toggle('mobile-device', isMobile);
        body.classList.toggle('landscape-short', isLandscapeShort);

        // Optimize grid layout
        this.optimizeGridLayout();
        
        // Adjust consciousness display
        this.adjustConsciousnessDisplay();
        
        // Optimize metrics display
        this.optimizeMetricsDisplay();
    }

    optimizeGridLayout() {
        const mainGrid = document.querySelector('.main-grid');
        if (!mainGrid) return;

        const isMobile = window.innerWidth <= 768;
        const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
        const isLandscapeShort = this.currentOrientation === 'landscape' && window.innerHeight <= 600;

        if (isMobile) {
            mainGrid.style.gridTemplateColumns = '1fr';
            mainGrid.style.gap = '1rem';
        } else if (isTablet) {
            mainGrid.style.gridTemplateColumns = '1fr 1fr';
            mainGrid.style.gap = '1.5rem';
        } else if (isLandscapeShort) {
            mainGrid.style.gridTemplateColumns = '1fr 2fr 1fr';
            mainGrid.style.gap = '1rem';
        } else {
            mainGrid.style.gridTemplateColumns = '1fr 2fr 1fr';
            mainGrid.style.gap = '2rem';
        }
    }

    adjustConsciousnessDisplay() {
        const consciousnessDisplay = document.querySelector('.consciousness-display');
        if (!consciousnessDisplay) return;

        const isMobile = window.innerWidth <= 768;
        const isLandscapeShort = this.currentOrientation === 'landscape' && window.innerHeight <= 600;

        if (isMobile) {
            consciousnessDisplay.style.height = '250px';
        } else if (isLandscapeShort) {
            consciousnessDisplay.style.height = '200px';
        } else {
            consciousnessDisplay.style.height = '400px';
        }
    }

    optimizeMetricsDisplay() {
        const excellenceMetrics = document.querySelector('.excellence-metrics');
        if (!excellenceMetrics) return;

        const isMobile = window.innerWidth <= 768;
        const isLandscapeShort = this.currentOrientation === 'landscape' && window.innerHeight <= 600;

        if (isMobile) {
            excellenceMetrics.style.gridTemplateColumns = '1fr';
        } else if (isLandscapeShort) {
            excellenceMetrics.style.gridTemplateColumns = '1fr 1fr 1fr 1fr';
        } else {
            excellenceMetrics.style.gridTemplateColumns = '1fr 1fr';
        }
    }

    adjustGridSpacing() {
        const decisionMatrix = document.querySelector('.decision-matrix');
        if (!decisionMatrix) return;

        const isMobile = window.innerWidth <= 768;
        const isLandscapeShort = this.currentOrientation === 'landscape' && window.innerHeight <= 600;

        if (isMobile) {
            decisionMatrix.style.gridTemplateColumns = 'repeat(3, 1fr)';
            decisionMatrix.style.gap = '0.5rem';
        } else if (isLandscapeShort) {
            decisionMatrix.style.gridTemplateColumns = 'repeat(6, 1fr)';
            decisionMatrix.style.gap = '0.3rem';
        } else {
            decisionMatrix.style.gridTemplateColumns = 'repeat(4, 1fr)';
            decisionMatrix.style.gap = '1rem';
        }
    }

    triggerLayoutUpdate() {
        // Trigger any chart or visualization updates
        const event = new CustomEvent('orientationChanged', {
            detail: {
                orientation: this.currentOrientation,
                width: window.innerWidth,
                height: window.innerHeight
            }
        });
        window.dispatchEvent(event);
    }

    setupViewportMeta() {
        // Ensure proper viewport meta tag
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }

    // Public method to manually trigger layout optimization
    refresh() {
        this.optimizeLayout();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.responsiveHandler = new ResponsiveOrientationHandler();
});

// Export for global access
window.ResponsiveOrientationHandler = ResponsiveOrientationHandler;