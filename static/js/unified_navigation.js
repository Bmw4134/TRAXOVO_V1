/**
 * TRAXORA Unified Navigation System
 * 
 * This script provides synchronized navigation across all TRAXORA dashboard pages.
 * It maintains state across page loads and ensures a consistent user experience.
 */

// Store navigation state in session storage for persistence
const NAVIGATION_STATE_KEY = 'traxora_navigation_state';

// Initialize navigation system
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    attachNavigationHandlers();
    highlightCurrentSection();
    initializeResponsiveLayout();
});

/**
 * Initialize the navigation system
 */
function initializeNavigation() {
    // Load saved navigation state
    let state = loadNavigationState();
    
    // If no state exists, create default
    if (!state) {
        state = {
            sidebarOpen: true,
            lastVisitedPages: {},
            activeSection: getCurrentSection()
        };
        saveNavigationState(state);
    }
    
    // Apply sidebar state
    applySidebarState(state.sidebarOpen);
    
    // Track page visit
    trackPageVisit();
    
    console.log('TRAXORA Navigation System Initialized');
}

/**
 * Attach event handlers to navigation elements
 */
function attachNavigationHandlers() {
    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            toggleSidebar();
        });
    }
    
    // Track all navigation link clicks
    document.querySelectorAll('.navbar-nav a, .list-group-item').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't interrupt normal navigation
            const destination = this.getAttribute('href');
            if (destination && !destination.startsWith('#') && !destination.startsWith('javascript:')) {
                const state = loadNavigationState();
                state.lastVisitedPage = window.location.pathname;
                state.nextDestination = destination;
                saveNavigationState(state);
            }
        });
    });
    
    // Handle mobile navigation special cases
    handleMobileNavigation();
}

/**
 * Handle mobile-specific navigation behaviors
 */
function handleMobileNavigation() {
    // Close mobile nav menu when item is clicked
    if (window.innerWidth < 992) { // Bootstrap lg breakpoint
        document.querySelectorAll('.navbar-nav a').forEach(link => {
            link.addEventListener('click', function() {
                const navbarToggler = document.querySelector('.navbar-toggler');
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarToggler && !navbarToggler.classList.contains('collapsed') && navbarCollapse) {
                    navbarToggler.click();
                }
            });
        });
    }
    
    // Handle swipe to open/close sidebar on mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const swipeThreshold = 100; // Minimum distance for swipe
        const state = loadNavigationState();
        
        if (touchEndX - touchStartX > swipeThreshold) {
            // Swipe right - open sidebar
            if (!state.sidebarOpen) {
                toggleSidebar();
            }
        }
        
        if (touchStartX - touchEndX > swipeThreshold) {
            // Swipe left - close sidebar
            if (state.sidebarOpen) {
                toggleSidebar();
            }
        }
    }
}

/**
 * Highlight the current section in the navigation
 */
function highlightCurrentSection() {
    const currentPath = window.location.pathname;
    
    // Remove all active classes
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    document.querySelectorAll('.sidebar .list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to current section
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
    
    document.querySelectorAll('.sidebar .list-group-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            item.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            item.classList.add('active');
        }
    });
}

/**
 * Initialize responsive layout adaptations
 */
function initializeResponsiveLayout() {
    // Adjust layout based on screen size
    function adjustLayout() {
        const state = loadNavigationState();
        
        if (window.innerWidth < 768) {
            // Mobile view - auto-close sidebar
            if (state.sidebarOpen) {
                state.sidebarOpen = false;
                saveNavigationState(state);
                applySidebarState(false);
            }
            
            // Add mobile-specific classes
            document.body.classList.add('mobile-view');
        } else {
            document.body.classList.remove('mobile-view');
        }
    }
    
    // Initial adjustment
    adjustLayout();
    
    // Adjust on resize
    window.addEventListener('resize', adjustLayout);
}

/**
 * Toggle sidebar open/closed state
 */
function toggleSidebar() {
    const state = loadNavigationState();
    state.sidebarOpen = !state.sidebarOpen;
    saveNavigationState(state);
    
    applySidebarState(state.sidebarOpen);
}

/**
 * Apply sidebar open/closed state to DOM
 */
function applySidebarState(isOpen) {
    const wrapper = document.getElementById('wrapper');
    if (wrapper) {
        if (isOpen) {
            wrapper.classList.remove('toggled');
        } else {
            wrapper.classList.add('toggled');
        }
    }
}

/**
 * Get the current section based on URL
 */
function getCurrentSection() {
    const path = window.location.pathname;
    
    if (path.startsWith('/auto-attendance')) {
        return 'attendance';
    } else if (path.startsWith('/asset-map')) {
        return 'assets';
    } else if (path.startsWith('/weekly-report')) {
        return 'weekly';
    } else if (path.startsWith('/system-health')) {
        return 'system';
    } else {
        return 'dashboard';
    }
}

/**
 * Track the current page visit in state
 */
function trackPageVisit() {
    const state = loadNavigationState();
    const currentSection = getCurrentSection();
    
    state.lastVisitedPages[currentSection] = window.location.pathname;
    state.activeSection = currentSection;
    
    saveNavigationState(state);
}

/**
 * Load navigation state from session storage
 */
function loadNavigationState() {
    const stateJson = sessionStorage.getItem(NAVIGATION_STATE_KEY);
    if (stateJson) {
        try {
            return JSON.parse(stateJson);
        } catch (e) {
            console.error('Error parsing navigation state:', e);
            return null;
        }
    }
    return null;
}

/**
 * Save navigation state to session storage
 */
function saveNavigationState(state) {
    try {
        sessionStorage.setItem(NAVIGATION_STATE_KEY, JSON.stringify(state));
    } catch (e) {
        console.error('Error saving navigation state:', e);
    }
}