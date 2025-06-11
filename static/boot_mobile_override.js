/**
 * Boot Mobile Override - Initialize viewport override, sidebar fix, and recorder load
 * Deployment: mobile_final_push_v1
 */

(function() {
    'use strict';
    
    console.log('🧭 Boot Mobile Override initializing...');
    
    // Phase 1: Viewport Override
    function initializeViewportOverride() {
        console.log('Phase 1: Viewport override starting');
        
        // Force desktop viewport on mobile
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=1024, initial-scale=0.3, maximum-scale=1, user-scalable=yes');
        } else {
            const newViewport = document.createElement('meta');
            newViewport.name = 'viewport';
            newViewport.content = 'width=1024, initial-scale=0.3, maximum-scale=1, user-scalable=yes';
            document.head.appendChild(newViewport);
        }
        
        // Apply desktop force styles with zoom fallback
        document.body.style.zoom = "0.3";
        document.body.classList.add("force-desktop-mode");
        document.body.style.minWidth = '1024px';
        document.body.style.transform = 'scale(0.3)';
        document.body.style.transformOrigin = 'top left';
        document.body.style.width = '333.33vw';
        document.body.style.height = '333.33vh';
        
        console.log('✅ Viewport override applied');
    }
    
    // Phase 2: Sidebar Fix Initialization
    function initializeSidebarFix() {
        console.log('Phase 2: Sidebar fix initialization');
        
        // Wait for DOM elements to be available
        setTimeout(() => {
            // Force load sidebar fix if not already loaded
            if (!window.sidebarTouchFix) {
                const script = document.createElement('script');
                script.src = '/static/sidebar_touch_fix_v2.js';
                script.onload = () => {
                    console.log('✅ Sidebar fix v2 loaded');
                };
                document.head.appendChild(script);
            } else {
                // Reinitialize existing sidebar fix
                if (window.sidebarTouchFix.reinitialize) {
                    window.sidebarTouchFix.reinitialize();
                }
            }
        }, 500);
    }
    
    // Phase 3: Driver Recorder Initialization
    function initializeDriverRecorder() {
        console.log('Phase 3: Driver recorder initialization');
        
        setTimeout(() => {
            // Force load driver recorder if not already loaded
            if (!window.driverRecorder) {
                const script = document.createElement('script');
                script.src = '/static/driver_recorder_restore.js';
                script.onload = () => {
                    console.log('✅ Driver recorder restored');
                };
                document.head.appendChild(script);
            }
        }, 1000);
    }
    
    // Phase 4: Layout CSS Application
    function applyLayoutCSS() {
        console.log('Phase 4: Applying layout CSS');
        
        // Load desktop force grid CSS
        const desktopCSS = document.createElement('link');
        desktopCSS.rel = 'stylesheet';
        desktopCSS.href = '/static/desktop_force_grid.css';
        document.head.appendChild(desktopCSS);
        
        // Load sidebar z-index fixes
        const sidebarCSS = document.createElement('link');
        sidebarCSS.rel = 'stylesheet';
        sidebarCSS.href = '/static/sidebar_zindex_fixes.css';
        document.head.appendChild(sidebarCSS);
        
        console.log('✅ Layout CSS applied');
    }
    
    // Phase 5: Patch Logging
    function logPatchDeployment() {
        const patchEntry = {
            patch_id: 'mobile_final_push_v1',
            timestamp: new Date().toISOString(),
            components: [
                'boot_mobile_override.js',
                'sidebar_touch_fix_v2.js',
                'driver_recorder_restore.js',
                'desktop_force_grid.css',
                'sidebar_zindex_fixes.css'
            ],
            status: 'deployed'
        };
        
        // Store in localStorage
        const existingPatches = JSON.parse(localStorage.getItem('patch_manifest') || '[]');
        existingPatches.push(patchEntry);
        localStorage.setItem('patch_manifest', JSON.stringify(existingPatches));
        
        console.log('✅ Patch deployment logged');
        console.table(patchEntry);
    }
    
    // Execute boot sequence
    function executeBoot() {
        console.log('🚀 Starting mobile final push v1 boot sequence');
        
        initializeViewportOverride();
        
        setTimeout(() => {
            initializeSidebarFix();
        }, 200);
        
        setTimeout(() => {
            initializeDriverRecorder();
        }, 400);
        
        setTimeout(() => {
            applyLayoutCSS();
        }, 600);
        
        setTimeout(() => {
            logPatchDeployment();
            console.log('🎯 Boot sequence complete - mobile_final_push_v1');
        }, 800);
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', executeBoot);
    } else {
        executeBoot();
    }
    
    // Expose for debugging
    window.bootMobileOverride = {
        reinitialize: executeBoot,
        status: 'active'
    };
    
})();