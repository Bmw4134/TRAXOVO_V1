/**
 * Real-time Responsive Orientation Handler
 * Handles portrait/landscape transitions with immediate scaling and layout corrections
 */

class ResponsiveOrientationManager {
    constructor() {
        this.currentOrientation = this.getOrientation();
        this.isTransitioning = false;
        this.init();
    }

    init() {
        // Listen for orientation changes
        window.addEventListener('orientationchange', this.handleOrientationChange.bind(this));
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Initial setup
        this.applyOrientationStyles();
        
        // Force layout recalculation after initial load
        setTimeout(() => {
            this.forceLayoutRecalculation();
        }, 100);
    }

    getOrientation() {
        if (screen.orientation) {
            return screen.orientation.angle === 0 || screen.orientation.angle === 180 ? 'portrait' : 'landscape';
        }
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    }

    handleOrientationChange() {
        if (this.isTransitioning) return;
        
        this.isTransitioning = true;
        
        // Small delay to let browser handle the orientation change
        setTimeout(() => {
            const newOrientation = this.getOrientation();
            
            if (newOrientation !== this.currentOrientation) {
                this.currentOrientation = newOrientation;
                this.applyOrientationStyles();
                this.adjustModuleLayouts();
                this.recalculateDashboardElements();
            }
            
            this.isTransitioning = false;
        }, 150);
    }

    handleResize() {
        if (!this.isTransitioning) {
            this.adjustModuleLayouts();
        }
    }

    applyOrientationStyles() {
        const body = document.body;
        
        // Remove existing orientation classes
        body.classList.remove('orientation-portrait', 'orientation-landscape');
        
        // Add current orientation class
        body.classList.add(`orientation-${this.currentOrientation}`);
        
        // Apply orientation-specific CSS
        this.injectOrientationCSS();
    }

    injectOrientationCSS() {
        let existingStyle = document.getElementById('orientation-styles');
        if (existingStyle) {
            existingStyle.remove();
        }

        const style = document.createElement('style');
        style.id = 'orientation-styles';
        
        if (this.currentOrientation === 'landscape') {
            style.textContent = `
                /* Landscape Mode Optimizations */
                .enterprise-sidebar {
                    width: 240px !important;
                    font-size: 0.9rem;
                }
                
                .main-content {
                    margin-left: 240px !important;
                    padding: 15px !important;
                }
                
                .dashboard-header {
                    padding: 20px !important;
                    margin-bottom: 20px !important;
                }
                
                .dashboard-header h1 {
                    font-size: 1.8rem !important;
                }
                
                .metric-value {
                    font-size: 2rem !important;
                }
                
                .row {
                    margin: 0 -8px !important;
                }
                
                .col-md-3, .col-md-4, .col-md-6, .col-md-8, .col-md-12 {
                    padding: 0 8px !important;
                }
                
                .devops-card, .goal-card, .security-card, .inspection-card, .stat-card {
                    padding: 15px !important;
                    margin-bottom: 15px !important;
                }
                
                .audit-panel, .system-panel, .progress-panel, .insight-panel {
                    padding: 18px !important;
                    margin-bottom: 15px !important;
                }
                
                /* Master Command Overlay Landscape */
                #masterCommandOverlay {
                    width: 320px !important;
                    max-height: 70vh !important;
                }
                
                /* Navigation adjustments */
                .nav-link {
                    padding: 8px 15px !important;
                    font-size: 0.85rem !important;
                }
                
                .nav-section-title {
                    font-size: 0.7rem !important;
                    padding: 8px 15px 3px !important;
                }
            `;
        } else {
            style.textContent = `
                /* Portrait Mode Optimizations */
                .enterprise-sidebar {
                    width: 280px !important;
                    font-size: 1rem;
                }
                
                .main-content {
                    margin-left: 280px !important;
                    padding: 20px !important;
                }
                
                .dashboard-header {
                    padding: 30px !important;
                    margin-bottom: 30px !important;
                }
                
                .dashboard-header h1 {
                    font-size: 2.2rem !important;
                }
                
                .metric-value {
                    font-size: 2.5rem !important;
                }
                
                .row {
                    margin: 0 -12px !important;
                }
                
                .col-md-3, .col-md-4, .col-md-6, .col-md-8, .col-md-12 {
                    padding: 0 12px !important;
                }
                
                .devops-card, .goal-card, .security-card, .inspection-card, .stat-card {
                    padding: 25px !important;
                    margin-bottom: 20px !important;
                }
                
                .audit-panel, .system-panel, .progress-panel, .insight-panel {
                    padding: 25px !important;
                    margin-bottom: 20px !important;
                }
                
                /* Master Command Overlay Portrait */
                #masterCommandOverlay {
                    width: 380px !important;
                    max-height: 80vh !important;
                }
                
                /* Navigation normal */
                .nav-link {
                    padding: 12px 20px !important;
                    font-size: 1rem !important;
                }
                
                .nav-section-title {
                    font-size: 0.75rem !important;
                    padding: 10px 20px 5px !important;
                }
            `;
        }
        
        document.head.appendChild(style);
    }

    adjustModuleLayouts() {
        // Adjust card layouts based on orientation
        this.adjustCardLayouts();
        
        // Adjust quantum dashboard elements
        this.adjustQuantumDashboard();
        
        // Adjust master command overlay
        this.adjustMasterCommand();
        
        // Adjust charts and visualizations
        this.adjustVisualizations();
    }

    adjustCardLayouts() {
        const cards = document.querySelectorAll('.devops-card, .goal-card, .security-card, .inspection-card, .stat-card');
        
        cards.forEach(card => {
            if (this.currentOrientation === 'landscape') {
                card.style.minHeight = '120px';
                const metricValue = card.querySelector('.metric-value');
                if (metricValue) {
                    metricValue.style.fontSize = '1.8rem';
                }
            } else {
                card.style.minHeight = '150px';
                const metricValue = card.querySelector('.metric-value');
                if (metricValue) {
                    metricValue.style.fontSize = '2.5rem';
                }
            }
        });
    }

    adjustQuantumDashboard() {
        const quantumElements = document.querySelectorAll('.quantum-metric, .consciousness-display');
        
        quantumElements.forEach(element => {
            if (this.currentOrientation === 'landscape') {
                element.style.transform = 'scale(0.9)';
                element.style.transformOrigin = 'center';
            } else {
                element.style.transform = 'scale(1)';
            }
        });
    }

    adjustMasterCommand() {
        const masterCommand = document.getElementById('masterCommandOverlay');
        if (masterCommand) {
            if (this.currentOrientation === 'landscape') {
                masterCommand.style.fontSize = '0.9rem';
                masterCommand.classList.add('landscape-mode');
            } else {
                masterCommand.style.fontSize = '1rem';
                masterCommand.classList.remove('landscape-mode');
            }
        }
    }

    adjustVisualizations() {
        // Force redraw of any charts or visualizations
        const visualElements = document.querySelectorAll('canvas, svg, .chart-container');
        
        visualElements.forEach(element => {
            // Trigger resize event for chart libraries
            const resizeEvent = new Event('resize');
            window.dispatchEvent(resizeEvent);
        });
    }

    recalculateDashboardElements() {
        // Force browser to recalculate layout
        this.forceLayoutRecalculation();
        
        // Update any dynamic positioning
        this.updateDynamicPositioning();
    }

    forceLayoutRecalculation() {
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            const display = mainContent.style.display;
            mainContent.style.display = 'none';
            mainContent.offsetHeight; // Force reflow
            mainContent.style.display = display;
        }
    }

    updateDynamicPositioning() {
        // Update any absolutely positioned elements
        const floatingElements = document.querySelectorAll('.floating-element, .overlay');
        
        floatingElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            if (rect.right > window.innerWidth || rect.bottom > window.innerHeight) {
                element.style.position = 'fixed';
                element.style.right = '20px';
                element.style.top = '20px';
            }
        });
    }

    // Public method to manually trigger orientation adjustment
    refreshLayout() {
        this.applyOrientationStyles();
        this.adjustModuleLayouts();
        this.recalculateDashboardElements();
    }
}

// Initialize responsive orientation manager
document.addEventListener('DOMContentLoaded', function() {
    window.responsiveManager = new ResponsiveOrientationManager();
    
    // Add CSS for smooth transitions
    const transitionStyle = document.createElement('style');
    transitionStyle.textContent = `
        .enterprise-sidebar,
        .main-content,
        .dashboard-header,
        .devops-card,
        .goal-card,
        .security-card,
        .inspection-card,
        .stat-card,
        .audit-panel,
        .system-panel,
        .progress-panel,
        .insight-panel {
            transition: all 0.3s ease-in-out !important;
        }
        
        .orientation-landscape .enterprise-sidebar {
            transform: translateX(0);
        }
        
        .orientation-portrait .enterprise-sidebar {
            transform: translateX(0);
        }
        
        /* Prevent flash during orientation change */
        body.orientation-transitioning * {
            transition: none !important;
        }
    `;
    
    document.head.appendChild(transitionStyle);
});

// Export for global access
window.ResponsiveOrientationManager = ResponsiveOrientationManager;