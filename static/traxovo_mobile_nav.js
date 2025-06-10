// TRAXOVO Mobile Navigation Handler
// Auto-injected by traxovo_ui_autopatch.py

document.addEventListener('DOMContentLoaded', function() {
    // Create mobile navigation toggle
    if (window.innerWidth <= 768) {
        createMobileNavToggle();
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            createMobileNavToggle();
        } else {
            removeMobileNavToggle();
        }
    });
});

function createMobileNavToggle() {
    if (document.getElementById('mobileNavToggle')) return;
    
    const toggle = document.createElement('button');
    toggle.id = 'mobileNavToggle';
    toggle.className = 'mobile-nav-toggle';
    toggle.innerHTML = '<i class="fas fa-bars"></i>';
    toggle.onclick = toggleMobileSidebar;
    
    document.body.appendChild(toggle);
}

function removeMobileNavToggle() {
    const toggle = document.getElementById('mobileNavToggle');
    if (toggle) {
        toggle.remove();
    }
}

function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('mobile-open');
        
        // Close when clicking outside
        if (sidebar.classList.contains('mobile-open')) {
            document.addEventListener('click', closeSidebarOnOutsideClick);
        }
    }
}

function closeSidebarOnOutsideClick(event) {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.getElementById('mobileNavToggle');
    
    if (sidebar && !sidebar.contains(event.target) && event.target !== toggle) {
        sidebar.classList.remove('mobile-open');
        document.removeEventListener('click', closeSidebarOnOutsideClick);
    }
}

// Scroll optimization
function optimizeScrollPerformance() {
    const scrollElements = document.querySelectorAll('.main-content, .section-content');
    
    scrollElements.forEach(element => {
        let isScrolling = false;
        
        element.addEventListener('scroll', function() {
            if (!isScrolling) {
                window.requestAnimationFrame(function() {
                    // Scroll-based optimizations can go here
                    isScrolling = false;
                });
                isScrolling = true;
            }
        }, { passive: true });
    });
}

// Initialize scroll optimizations
document.addEventListener('DOMContentLoaded', optimizeScrollPerformance);