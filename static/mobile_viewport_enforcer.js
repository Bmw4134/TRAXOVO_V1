/**
 * Mobile Viewport Enforcer - Aggressive viewport and zoom control for iOS/Android
 * Deployment: mobile_final_push_v1.1
 */

(function() {
    'use strict';
    
    console.log('📱 Mobile Viewport Enforcer initializing...');
    
    let enforcementAttempts = 0;
    const maxAttempts = 10;
    
    function detectMobileDevice() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        return /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());
    }
    
    function enforceDesktopViewport() {
        enforcementAttempts++;
        
        if (enforcementAttempts > maxAttempts) {
            console.log('Max viewport enforcement attempts reached');
            return;
        }
        
        console.log(`Viewport enforcement attempt ${enforcementAttempts}...`);
        
        // Multiple viewport manipulation strategies
        const viewportMeta = document.querySelector('meta[name="viewport"]') || 
                           document.createElement('meta');
        
        viewportMeta.name = 'viewport';
        viewportMeta.content = 'width=1024, initial-scale=0.3, maximum-scale=1, user-scalable=yes, viewport-fit=cover';
        
        if (!viewportMeta.parentNode) {
            document.head.appendChild(viewportMeta);
        }
        
        // Force body transformations
        const body = document.body;
        if (body) {
            // Multiple zoom/scale approaches for maximum compatibility
            body.style.zoom = "0.3";
            body.style.transform = "scale(0.3)";
            body.style.transformOrigin = "top left";
            body.style.minWidth = "1024px";
            body.style.width = "333.33vw";
            body.style.overflow = "auto";
            
            // iOS specific fixes
            body.style.webkitTransform = "scale(0.3)";
            body.style.webkitTransformOrigin = "top left";
            body.style.webkitTextSizeAdjust = "none";
            
            // Add force desktop class
            body.classList.add("force-desktop-mode", "mobile-viewport-enforced");
            
            console.log('✅ Desktop viewport enforced');
        }
        
        // Force document width
        const html = document.documentElement;
        if (html) {
            html.style.minWidth = "1024px";
            html.style.width = "100%";
        }
        
        // Disable mobile-specific behaviors
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault(); // Prevent pinch zoom
            }
        }, { passive: false });
        
        document.addEventListener('gesturestart', function(e) {
            e.preventDefault(); // Prevent iOS gesture zoom
        }, { passive: false });
        
        // Check if enforcement was successful
        setTimeout(function() {
            const currentZoom = window.devicePixelRatio || 1;
            const bodyZoom = window.getComputedStyle(body).zoom || 
                           window.getComputedStyle(body).transform;
            
            if (!bodyZoom.includes('0.3') && !bodyZoom.includes('scale')) {
                console.log('Viewport enforcement may have failed, retrying...');
                enforceDesktopViewport();
            } else {
                console.log('✅ Viewport enforcement verified successful');
            }
        }, 500);
    }
    
    function injectDesktopCSS() {
        const style = document.createElement('style');
        style.id = 'mobile-viewport-enforcer-css';
        style.textContent = `
            /* Mobile Viewport Enforcer CSS */
            @media screen and (max-width: 768px) {
                html, body {
                    min-width: 1024px !important;
                    width: auto !important;
                    overflow-x: auto !important;
                    -webkit-text-size-adjust: none !important;
                    text-size-adjust: none !important;
                }
                
                body.force-desktop-mode {
                    zoom: 0.3 !important;
                    -webkit-transform: scale(0.3) !important;
                    transform: scale(0.3) !important;
                    -webkit-transform-origin: top left !important;
                    transform-origin: top left !important;
                    width: 333.33vw !important;
                    min-width: 1024px !important;
                }
                
                /* Prevent mobile zoom behaviors */
                * {
                    -webkit-touch-callout: none !important;
                    -webkit-user-select: none !important;
                    -webkit-tap-highlight-color: transparent !important;
                }
                
                /* Force sidebar and navigation to be touchable */
                .sidebar, .nav, .navigation, .menu {
                    pointer-events: all !important;
                    touch-action: manipulation !important;
                    -webkit-touch-callout: default !important;
                    -webkit-user-select: auto !important;
                }
                
                /* Ensure buttons and links work on mobile */
                a, button, [onclick], [data-action] {
                    touch-action: manipulation !important;
                    -webkit-touch-callout: default !important;
                    -webkit-user-select: auto !important;
                    cursor: pointer !important;
                }
            }
            
            /* iOS Safari specific fixes */
            @supports (-webkit-touch-callout: none) {
                body.force-desktop-mode {
                    -webkit-transform: scale(0.3) !important;
                    -webkit-transform-origin: top left !important;
                }
            }
        `;
        
        if (!document.getElementById('mobile-viewport-enforcer-css')) {
            document.head.appendChild(style);
            console.log('✅ Mobile viewport CSS injected');
        }
    }
    
    function initializeViewportEnforcement() {
        if (!detectMobileDevice()) {
            console.log('Desktop device detected, skipping mobile enforcement');
            return;
        }
        
        console.log('Mobile device detected, enforcing desktop viewport...');
        
        // Inject CSS first
        injectDesktopCSS();
        
        // Enforce viewport immediately
        enforceDesktopViewport();
        
        // Re-enforce on orientation change
        window.addEventListener('orientationchange', function() {
            setTimeout(enforceDesktopViewport, 100);
        });
        
        // Re-enforce on resize
        window.addEventListener('resize', function() {
            setTimeout(enforceDesktopViewport, 100);
        });
        
        // Periodic enforcement check
        setInterval(function() {
            const body = document.body;
            if (body && !body.classList.contains('mobile-viewport-enforced')) {
                console.log('Viewport enforcement lost, re-applying...');
                enforceDesktopViewport();
            }
        }, 5000);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeViewportEnforcement);
    } else {
        initializeViewportEnforcement();
    }
    
    // Also initialize immediately if body exists
    if (document.body) {
        initializeViewportEnforcement();
    }
    
    // Global function for manual enforcement
    window.forceMobileViewportEnforcement = enforceDesktopViewport;
    
    console.log('📱 Mobile Viewport Enforcer ready');
    
})();