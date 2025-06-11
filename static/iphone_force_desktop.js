/* iPhone Desktop Force JavaScript */
(function() {
    'use strict';
    
    // Force desktop mode on iPhone
    function forceDesktopMode() {
        // Set viewport to desktop size
        let viewport = document.querySelector("meta[name=viewport]");
        if (viewport) {
            viewport.setAttribute('content', 'width=1024, initial-scale=0.3, minimum-scale=0.1, maximum-scale=2.0, user-scalable=yes');
        }
        
        // Add desktop force class to body
        document.body.classList.add('force-desktop');
        
        // Hide mobile navigation
        const mobileNav = document.querySelector('.mobile-nav-header');
        if (mobileNav) {
            mobileNav.style.display = 'none';
        }
        
        // Force desktop grid layout
        const mainGrid = document.querySelector('.main-grid');
        if (mainGrid) {
            mainGrid.style.display = 'grid';
            mainGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
            mainGrid.style.gap = '25px';
            mainGrid.style.padding = '30px';
            mainGrid.style.width = '100%';
            mainGrid.style.overflowX = 'auto';
        }
        
        // Force large header
        const header = document.querySelector('.header h1');
        if (header) {
            header.style.fontSize = '3rem';
            header.style.textAlign = 'center';
        }
        
        // Ensure cards maintain desktop size
        const cards = document.querySelectorAll('.dashboard-card, .nexus-control-card, .api-showcase');
        cards.forEach(card => {
            card.style.minWidth = '300px';
            card.style.width = 'auto';
            card.style.flex = '1 1 300px';
        });
        
        // Force desktop button sizes
        const buttons = document.querySelectorAll('.nexus-access-btn, .desktop-toggle');
        buttons.forEach(btn => {
            btn.style.padding = '15px 30px';
            btn.style.fontSize = '1.1rem';
            btn.style.minWidth = '200px';
        });
        
        console.log('iPhone Desktop Mode Forced');
    }
    
    // Create persistent desktop toggle
    function createDesktopToggle() {
        let toggle = document.querySelector('.desktop-toggle');
        if (!toggle) {
            toggle = document.createElement('button');
            toggle.className = 'desktop-toggle';
            toggle.innerHTML = '📱 Mobile View';
            toggle.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                z-index: 10000 !important;
                background: linear-gradient(45deg, #3a5998, #74c0fc) !important;
                color: white !important;
                font-weight: bold !important;
                border: none !important;
                padding: 12px 20px !important;
                border-radius: 8px !important;
                box-shadow: 0 5px 15px rgba(116, 192, 252, 0.5) !important;
                cursor: pointer !important;
                font-size: 14px !important;
                display: block !important;
            `;
            document.body.appendChild(toggle);
        }
        
        toggle.onclick = function() {
            const isDesktop = document.body.classList.contains('force-desktop');
            if (isDesktop) {
                // Switch to mobile
                document.body.classList.remove('force-desktop');
                toggle.innerHTML = '🖥️ Full Site';
                localStorage.setItem('traxovo_view_mode', 'mobile');
                location.reload();
            } else {
                // Switch to desktop
                document.body.classList.add('force-desktop');
                toggle.innerHTML = '📱 Mobile View';
                localStorage.setItem('traxovo_view_mode', 'desktop');
                forceDesktopMode();
            }
        };
    }
    
    // Initialize on page load
    function initialize() {
        // Check if on iPhone/mobile
        const isIPhone = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        const isSmallScreen = window.innerWidth <= 768;
        
        if (isIPhone || isSmallScreen) {
            // Check stored preference
            const viewMode = localStorage.getItem('traxovo_view_mode');
            
            // Default to desktop mode for better experience
            if (!viewMode || viewMode === 'desktop') {
                forceDesktopMode();
                localStorage.setItem('traxovo_view_mode', 'desktop');
            }
            
            // Always show toggle
            createDesktopToggle();
            
            // Update toggle text based on current mode
            const toggle = document.querySelector('.desktop-toggle');
            if (toggle) {
                if (document.body.classList.contains('force-desktop')) {
                    toggle.innerHTML = '📱 Mobile View';
                } else {
                    toggle.innerHTML = '🖥️ Full Site';
                }
            }
        }
        
        // Ensure NEXUS Control Center is clickable
        const nexusCard = document.querySelector('.nexus-control-card');
        if (nexusCard) {
            nexusCard.style.cursor = 'pointer';
            nexusCard.onclick = function() {
                window.location.href = '/personal-nexus';
            };
        }
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Run on window load for safety
    window.addEventListener('load', initialize);
    
})();