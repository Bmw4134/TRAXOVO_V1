/*
TRAXOVO Enterprise Polish - Samsara/Stripe Level UX
Final interaction and visual refinement layer
*/

(function() {
    'use strict';
    
    // Enterprise-grade smooth scrolling and interactions
    function initializeEnterprisePolish() {
        addMicroInteractions();
        optimizeChartResponsiveness();
        enhanceTouchTargets();
        preventLayoutShift();
        addLoadingStates();
    }
    
    function addMicroInteractions() {
        // Smooth hover states for interactive elements
        var interactiveElements = document.querySelectorAll(
            '.metric-card, .nav-link, .btn, .card, [data-asset-id]'
        );
        
        for (var i = 0; i < interactiveElements.length; i++) {
            var element = interactiveElements[i];
            
            element.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            });
            
            element.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
            
            // Touch feedback for mobile
            element.addEventListener('touchstart', function() {
                this.style.opacity = '0.8';
            });
            
            element.addEventListener('touchend', function() {
                var self = this;
                setTimeout(function() {
                    self.style.opacity = '1';
                }, 150);
            });
        }
    }
    
    function optimizeChartResponsiveness() {
        // Ensure charts resize properly on all screen sizes
        var charts = document.querySelectorAll('canvas, .chart-container');
        
        function resizeCharts() {
            for (var i = 0; i < charts.length; i++) {
                var chart = charts[i];
                if (chart.style) {
                    chart.style.maxWidth = '100%';
                    chart.style.height = 'auto';
                }
            }
        }
        
        window.addEventListener('resize', debounce(resizeCharts, 250));
        resizeCharts();
    }
    
    function enhanceTouchTargets() {
        // Ensure minimum 44px touch targets for mobile
        var touchTargets = document.querySelectorAll(
            'button, .nav-link, .metric-card, [role="button"]'
        );
        
        for (var i = 0; i < touchTargets.length; i++) {
            var target = touchTargets[i];
            var computedStyle = window.getComputedStyle(target);
            var height = parseInt(computedStyle.height);
            var width = parseInt(computedStyle.width);
            
            if (height < 44) {
                target.style.minHeight = '44px';
                target.style.display = 'flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
            
            if (width < 44) {
                target.style.minWidth = '44px';
            }
        }
    }
    
    function preventLayoutShift() {
        // Prevent cumulative layout shift with proper sizing
        var metricElements = document.querySelectorAll('.metric-value, .animated-number');
        
        for (var i = 0; i < metricElements.length; i++) {
            var element = metricElements[i];
            element.style.minHeight = '1.5em';
            element.style.display = 'inline-block';
        }
        
        // Reserve space for loading images
        var images = document.querySelectorAll('img');
        for (var j = 0; j < images.length; j++) {
            var img = images[j];
            if (!img.style.height && !img.getAttribute('height')) {
                img.style.minHeight = '200px';
                img.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            }
        }
    }
    
    function addLoadingStates() {
        // Skeleton loading for metric cards
        var metricCards = document.querySelectorAll('.metric-card');
        
        for (var i = 0; i < metricCards.length; i++) {
            var card = metricCards[i];
            var metricValue = card.querySelector('.metric-value, .animated-number');
            
            if (metricValue && (metricValue.textContent === '--' || metricValue.textContent === '')) {
                metricValue.style.background = 'linear-gradient(90deg, rgba(255,255,255,0.1) 25%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 75%)';
                metricValue.style.backgroundSize = '200% 100%';
                metricValue.style.animation = 'shimmer 1.5s infinite';
                metricValue.textContent = '\u00A0\u00A0\u00A0\u00A0';
            }
        }
    }
    
    function debounce(func, wait) {
        var timeout;
        return function executedFunction() {
            var context = this;
            var args = arguments;
            var later = function() {
                timeout = null;
                func.apply(context, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Mobile sidebar enhancement
    function enhanceMobileSidebar() {
        var sidebar = document.querySelector('.sidebar');
        var overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; opacity: 0; visibility: hidden; transition: all 0.3s ease;';
        
        if (sidebar && window.innerWidth <= 768) {
            document.body.appendChild(overlay);
            
            overlay.addEventListener('click', function() {
                sidebar.classList.remove('show');
                overlay.style.opacity = '0';
                overlay.style.visibility = 'hidden';
            });
        }
    }
    
    // Initialize everything
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeEnterprisePolish();
            enhanceMobileSidebar();
        });
    } else {
        initializeEnterprisePolish();
        enhanceMobileSidebar();
    }
    
    // Add shimmer animation CSS
    var style = document.createElement('style');
    style.textContent = '@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }';
    document.head.appendChild(style);
    
})();