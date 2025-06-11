/**
 * Sidebar Touch Fix v2 - Hard-rebind all sidebar interactions, remove z-index blocks
 * Deployment: mobile_final_push_v1
 */

(function() {
    'use strict';
    
    console.log('🧠 Sidebar Touch Fix v2 initializing...');
    
    let initialized = false;
    
    function hardRebindSidebarEvents() {
        if (initialized) {
            console.log('Sidebar already initialized, forcing reinit...');
            initialized = false;
        }
        
        console.log('🔧 Hard-rebinding all sidebar interactions...');
        
        // Comprehensive selector array for all possible sidebar elements
        const selectors = [
            'nav a',
            '.nav a',
            '.navigation a',
            '.sidebar a',
            '.sidebar-nav a',
            '.sidebar-menu a',
            '.mobile-nav a',
            '.mobile-nav-item',
            '.nav-link',
            '.menu-item',
            '[data-nav]',
            '[data-action]',
            '.menu a',
            '.navbar a',
            '[role="menuitem"]',
            '.dropdown-item'
        ];
        
        let allElements = [];
        
        // Collect all unique elements
        selectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (!allElements.includes(el)) {
                        allElements.push(el);
                    }
                });
            } catch (e) {
                console.warn(`Selector failed: ${selector}`, e);
            }
        });
        
        console.log(`Found ${allElements.length} sidebar elements to rebind`);
        
        // Hard rebind each element
        allElements.forEach((element, index) => {
            // Remove all existing event listeners by cloning
            const newElement = element.cloneNode(true);
            element.parentNode.replaceChild(newElement, element);
            
            // Force CSS properties for interaction
            newElement.style.pointerEvents = 'auto';
            newElement.style.position = 'relative';
            newElement.style.zIndex = '99999';
            newElement.style.touchAction = 'manipulation';
            newElement.style.userSelect = 'none';
            newElement.style.webkitUserSelect = 'none';
            newElement.style.webkitTouchCallout = 'none';
            newElement.style.cursor = 'pointer';
            newElement.style.display = 'block';
            newElement.style.minHeight = '44px';
            newElement.style.padding = '8px 12px';
            
            // Remove any z-index blocking overlays
            const rect = newElement.getBoundingClientRect();
            const elementsAtPoint = document.elementsFromPoint(rect.x + rect.width/2, rect.y + rect.height/2);
            elementsAtPoint.forEach(overlay => {
                if (overlay !== newElement && overlay.style.zIndex && parseInt(overlay.style.zIndex) > 1000) {
                    overlay.style.zIndex = '1';
                }
            });
            
            // Add comprehensive event listeners
            const clickHandler = function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('🎯 Sidebar click detected:', this.textContent.trim());
                
                // Visual feedback
                this.style.transform = 'scale(0.95)';
                this.style.backgroundColor = 'rgba(0, 255, 136, 0.3)';
                
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                    this.style.backgroundColor = '';
                }, 200);
                
                // Handle navigation
                const href = this.getAttribute('href');
                const action = this.getAttribute('data-action');
                
                if (action) {
                    handleAction(action);
                } else if (href && href !== '#') {
                    if (href.startsWith('/')) {
                        window.location.href = href;
                    } else if (href.startsWith('#')) {
                        scrollToSection(href.substring(1));
                    }
                }
            };
            
            // Bind multiple event types
            newElement.addEventListener('click', clickHandler, { passive: false, capture: true });
            newElement.addEventListener('touchend', clickHandler, { passive: false, capture: true });
            newElement.addEventListener('mousedown', clickHandler, { passive: false });
            
            // Add verification attributes
            newElement.setAttribute('data-sidebar-v2-bound', 'true');
            newElement.setAttribute('data-bind-index', index);
            
            console.log(`✅ Rebound element ${index + 1}: ${newElement.textContent.trim()}`);
        });
        
        // Add global delegation handler as ultimate fallback
        document.removeEventListener('click', globalClickHandler, true);
        document.addEventListener('click', globalClickHandler, true);
        
        initialized = true;
        console.log('✅ Sidebar touch fix v2 complete');
    }
    
    function globalClickHandler(e) {
        const target = e.target.closest('nav a, .nav a, .sidebar a, .mobile-nav-item');
        if (target && !target.hasAttribute('data-sidebar-v2-bound')) {
            console.log('🔄 Global handler triggered for unbound element');
            e.preventDefault();
            e.stopPropagation();
            
            const href = target.getAttribute('href');
            const action = target.getAttribute('data-action');
            
            if (action) {
                handleAction(action);
            } else if (href && href !== '#') {
                if (href.startsWith('/')) {
                    window.location.href = href;
                } else if (href.startsWith('#')) {
                    scrollToSection(href.substring(1));
                }
            }
        }
    }
    
    function handleAction(action) {
        console.log(`Handling action: ${action}`);
        
        switch(action) {
            case 'nexus-control':
                window.location.href = '/personal-nexus';
                break;
            case 'api-benchmark':
                if (window.openAPIBenchmarkModal) {
                    window.openAPIBenchmarkModal();
                } else {
                    console.log('Opening API benchmark...');
                }
                break;
            case 'driver-recording':
                if (window.startDriverRecording) {
                    window.startDriverRecording();
                } else {
                    console.log('Starting driver recording...');
                }
                break;
            case 'asset-overview':
                scrollToSection('assets');
                break;
            case 'performance-metrics':
                scrollToSection('performance');
                break;
            default:
                console.log(`Unknown action: ${action}`);
        }
    }
    
    function scrollToSection(sectionId) {
        const target = document.getElementById(sectionId) || 
                      document.querySelector(`[data-section="${sectionId}"]`) ||
                      document.querySelector(`.${sectionId}`);
        
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            console.log(`Scrolled to: ${sectionId}`);
        }
    }
    
    // Initialize with multiple triggers
    function initialize() {
        setTimeout(hardRebindSidebarEvents, 100);
        setTimeout(hardRebindSidebarEvents, 500);
        setTimeout(hardRebindSidebarEvents, 1000);
        setTimeout(hardRebindSidebarEvents, 2000);
    }
    
    // Multiple initialization points
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    window.addEventListener('load', initialize);
    
    // Expose for external access
    window.sidebarTouchFixV2 = {
        reinitialize: hardRebindSidebarEvents,
        isInitialized: () => initialized
    };
    
})();