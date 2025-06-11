/**
 * Sidebar Touch Navigation Fix for iPhone Desktop Override Mode
 * Rebinds all sidebar event listeners after viewport script loads
 */

(function() {
    'use strict';
    
    let sidebarInitialized = false;
    
    function initializeSidebarTouch() {
        if (sidebarInitialized) return;
        
        console.log('🔧 Force rebinding sidebar events - sidebar_click_fix_patch_01');
        
        // Enhanced selector targeting for all sidebar elements
        const sidebarSelectors = [
            '.sidebar-menu a',
            '.mobile-nav-item', 
            '.sidebar-nav a', 
            '.nav-link', 
            '[data-nav]',
            '.sidebar a',
            '.mobile-nav a',
            '.navigation-item',
            'nav a'
        ];
        
        let sidebarLinks = [];
        sidebarSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (!sidebarLinks.includes(el)) {
                    sidebarLinks.push(el);
                }
            });
        });
        
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const mobileNavMenu = document.querySelector('.mobile-nav-menu');
        
        console.log(`🔍 Found ${sidebarLinks.length} sidebar elements to bind`);
        
        // Enhanced touch event binding for sidebar links
        sidebarLinks.forEach((link, index) => {
            // Remove existing listeners to prevent duplicates
            link.removeEventListener('click', handleSidebarClick);
            link.removeEventListener('touchstart', handleTouchStart);
            link.removeEventListener('touchend', handleTouchEnd);
            
            // Force pointer events and z-index layering
            link.style.pointerEvents = 'auto';
            link.style.position = 'relative';
            link.style.zIndex = '9999';
            
            // Add comprehensive event listeners with capture
            link.addEventListener('click', handleSidebarClick, { passive: false, capture: true });
            link.addEventListener('touchstart', handleTouchStart, { passive: false, capture: true });
            link.addEventListener('touchend', handleTouchEnd, { passive: false, capture: true });
            link.addEventListener('mousedown', handleSidebarClick, { passive: false });
            
            // Ensure proper CSS for touch compatibility
            link.style.touchAction = 'manipulation';
            link.style.userSelect = 'none';
            link.style.webkitTouchCallout = 'none';
            link.style.webkitUserSelect = 'none';
            link.style.cursor = 'pointer';
            link.style.display = 'block';
            
            // Validate bounding box for touch compatibility
            const rect = link.getBoundingClientRect();
            if (rect.height < 44) {
                link.style.minHeight = '44px';
                link.style.paddingTop = '8px';
                link.style.paddingBottom = '8px';
            }
            
            // Add data attribute for verification
            link.setAttribute('data-sidebar-bound', 'true');
            link.setAttribute('data-bind-timestamp', Date.now());
            
            console.log(`✅ Sidebar link ${index + 1} force-bound:`, link.textContent.trim(), link.href || link.getAttribute('data-action'));
        });
        
        // Mobile menu toggle functionality
        if (mobileMenuToggle) {
            mobileMenuToggle.removeEventListener('click', toggleMobileMenu);
            mobileMenuToggle.addEventListener('click', toggleMobileMenu, { passive: false });
            mobileMenuToggle.style.touchAction = 'manipulation';
            console.log('Mobile menu toggle bound');
        }
        
        sidebarInitialized = true;
        const timestamp = new Date().toISOString();
        console.log(`✅ Sidebar listeners rebound [${timestamp}] - sidebar_click_fix_patch_01`);
        
        // Log binding status and create audit entry
        const auditEntry = {
            patch_id: 'sidebar_click_fix_patch_01',
            timestamp: timestamp,
            elements_bound: sidebarLinks.length,
            status: 'complete',
            pointer_events_fixed: true,
            z_index_layering: true,
            capture_mode: true
        };
        
        // Store audit in localStorage
        const existingAudit = JSON.parse(localStorage.getItem('sidebar_patch_audit') || '[]');
        existingAudit.push(auditEntry);
        localStorage.setItem('sidebar_patch_audit', JSON.stringify(existingAudit));
        
        // Also log to console for verification
        console.table(auditEntry);
    }
    
    function handleSidebarClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const link = e.currentTarget;
        const href = link.getAttribute('href') || link.getAttribute('data-href');
        const action = link.getAttribute('data-action');
        
        console.log('Sidebar click detected:', { href, action, text: link.textContent.trim() });
        
        // Add visual feedback
        link.style.transform = 'scale(0.95)';
        setTimeout(() => {
            link.style.transform = 'scale(1)';
        }, 150);
        
        // Handle navigation
        if (action) {
            handleSidebarAction(action);
        } else if (href && href !== '#') {
            if (href.startsWith('/')) {
                window.location.href = href;
            } else if (href.startsWith('#')) {
                scrollToSection(href.substring(1));
            }
        }
    }
    
    function handleTouchStart(e) {
        const link = e.currentTarget;
        link.style.backgroundColor = 'rgba(0, 255, 136, 0.3)';
        link.style.transform = 'scale(0.98)';
    }
    
    function handleTouchEnd(e) {
        const link = e.currentTarget;
        setTimeout(() => {
            link.style.backgroundColor = '';
            link.style.transform = 'scale(1)';
        }, 200);
    }
    
    function handleSidebarAction(action) {
        switch(action) {
            case 'nexus-control':
                window.location.href = '/personal-nexus';
                break;
            case 'api-benchmark':
                openAPIBenchmark();
                break;
            case 'driver-recording':
                startDriverRecording();
                break;
            case 'asset-overview':
                scrollToSection('assets');
                break;
            case 'performance-metrics':
                scrollToSection('performance');
                break;
            default:
                console.log('Unknown sidebar action:', action);
        }
    }
    
    function toggleMobileMenu() {
        const menu = document.getElementById('mobileNavMenu') || document.querySelector('.mobile-nav-menu');
        if (menu) {
            menu.classList.toggle('active');
            console.log('Mobile menu toggled:', menu.classList.contains('active'));
        }
    }
    
    function scrollToSection(sectionId) {
        const targetElement = document.getElementById(sectionId) || 
                            document.querySelector(`[data-section="${sectionId}"]`) ||
                            document.querySelector(`.${sectionId}`);
        
        if (targetElement) {
            targetElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start',
                inline: 'nearest'
            });
            console.log('Scrolled to section:', sectionId);
        }
    }
    
    function openAPIBenchmark() {
        // Open API benchmark modal or navigate to benchmark page
        const benchmarkButton = document.querySelector('[onclick*="benchmark"]') || 
                               document.querySelector('.api-benchmark-btn');
        if (benchmarkButton) {
            benchmarkButton.click();
        } else {
            console.log('Opening API benchmark interface...');
            // Trigger benchmark modal if available
            if (window.openAPIBenchmarkModal) {
                window.openAPIBenchmarkModal();
            }
        }
    }
    
    function startDriverRecording() {
        console.log('Starting driver recording...');
        if (window.startDriverRecording) {
            window.startDriverRecording();
        } else if (window.driverRecorder) {
            window.driverRecorder.start();
        } else {
            alert('Driver recording system initializing...');
        }
    }
    
    // Initialize after DOM is ready and viewport is set
    function initialize() {
        // Wait for viewport override to complete and layout stabilization
        setTimeout(() => {
            initializeSidebarTouch();
        }, 1000);
        
        // Force additional initialization after full page load
        setTimeout(() => {
            sidebarInitialized = false;
            initializeSidebarTouch();
        }, 2000);
        
        // Re-initialize on resize to handle orientation changes
        window.addEventListener('resize', () => {
            setTimeout(() => {
                sidebarInitialized = false;
                initializeSidebarTouch();
            }, 500);
        });
        
        // Add delegation handler as backup
        document.addEventListener('click', function(e) {
            const target = e.target.closest('.mobile-nav-item, .sidebar-nav a, nav a');
            if (target) {
                console.log('🔄 Delegation handler triggered for:', target.textContent.trim());
                handleSidebarClick.call(target, e);
            }
        }, true);
    }
    
    // Multiple initialization triggers to ensure compatibility
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Also initialize on window load for safety
    window.addEventListener('load', initialize);
    
    // Expose functions globally for debugging
    window.sidebarTouchFix = {
        reinitialize: initializeSidebarTouch,
        isInitialized: () => sidebarInitialized
    };
    
})();