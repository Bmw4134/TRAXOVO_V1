"""
QQ Intelligent Fullscreen Override System
Intelligent fullscreen toggle that overrides all other fullscreen controls
Ensures perfect scaling on iPhone and all mobile devices
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class ViewportState:
    """Current viewport state tracking"""
    device_type: str
    width: int
    height: int
    is_fullscreen: bool
    scale_factor: float
    orientation: str
    user_agent: str

class QQIntelligentFullscreenSystem:
    """
    Intelligent fullscreen system that overrides all other fullscreen controls
    Provides perfect scaling across all devices with special iPhone optimization
    """
    
    def __init__(self):
        self.fullscreen_db = "qq_fullscreen_states.db"
        self.initialize_fullscreen_system()
        
    def initialize_fullscreen_system(self):
        """Initialize fullscreen system database"""
        
        conn = sqlite3.connect(self.fullscreen_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fullscreen_states (
                user_id TEXT,
                device_fingerprint TEXT,
                is_fullscreen BOOLEAN DEFAULT FALSE,
                viewport_width INTEGER,
                viewport_height INTEGER,
                scale_factor REAL DEFAULT 1.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, device_fingerprint)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scaling_preferences (
                device_type TEXT PRIMARY KEY,
                preferred_scale REAL,
                css_overrides TEXT,
                viewport_meta TEXT
            )
        ''')
        
        # Insert default scaling preferences
        scaling_defaults = [
            ('iphone', 1.0, self.get_iphone_css_overrides(), self.get_iphone_viewport_meta()),
            ('android', 1.0, self.get_android_css_overrides(), self.get_android_viewport_meta()),
            ('tablet', 1.0, self.get_tablet_css_overrides(), self.get_tablet_viewport_meta()),
            ('desktop', 1.0, self.get_desktop_css_overrides(), self.get_desktop_viewport_meta())
        ]
        
        for device_type, scale, css, viewport in scaling_defaults:
            cursor.execute('''
                INSERT OR REPLACE INTO scaling_preferences 
                (device_type, preferred_scale, css_overrides, viewport_meta)
                VALUES (?, ?, ?, ?)
            ''', (device_type, scale, css, viewport))
            
        conn.commit()
        conn.close()
        
        logging.info("QQ Intelligent Fullscreen System initialized")
        
    def get_iphone_css_overrides(self) -> str:
        """Get iPhone-specific CSS overrides for perfect scaling"""
        return '''
/* QQ iPhone Fullscreen Overrides */
.qq-fullscreen-mode {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    max-width: 100vw !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    z-index: 999999 !important;
    overflow: auto !important;
    -webkit-overflow-scrolling: touch !important;
    transform: none !important;
    background: #000 !important;
}

/* Override all existing fullscreen classes */
.fullscreen, .full-screen, .fs, .maximize, .expanded {
    position: static !important;
    width: auto !important;
    height: auto !important;
    z-index: auto !important;
}

/* iPhone Safe Area Handling */
.qq-fullscreen-mode .dashboard-content {
    padding-top: env(safe-area-inset-top, 0px) !important;
    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
    padding-left: env(safe-area-inset-left, 0px) !important;
    padding-right: env(safe-area-inset-right, 0px) !important;
}

/* iPhone Viewport Scaling */
.qq-fullscreen-mode {
    -webkit-text-size-adjust: 100% !important;
    -ms-text-size-adjust: 100% !important;
    text-size-adjust: 100% !important;
    touch-action: manipulation !important;
}

/* Remove iPhone zoom on input focus */
.qq-fullscreen-mode input,
.qq-fullscreen-mode select,
.qq-fullscreen-mode textarea {
    font-size: 16px !important;
    transform: none !important;
}

/* iPhone scrolling optimization */
.qq-fullscreen-mode {
    -webkit-overflow-scrolling: touch !important;
    scroll-behavior: smooth !important;
}

/* Override Replit preview frame constraints */
.qq-fullscreen-mode {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    min-width: 100vw !important;
    min-height: 100vh !important;
}

/* Force fullscreen on all child elements */
.qq-fullscreen-mode > * {
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* iPhone landscape orientation fixes */
@media screen and (orientation: landscape) and (max-height: 500px) {
    .qq-fullscreen-mode {
        height: 100vh !important;
        min-height: 100vh !important;
    }
    
    .qq-fullscreen-mode .navbar,
    .qq-fullscreen-mode .header {
        height: 44px !important;
        min-height: 44px !important;
    }
}

/* iPhone notch handling */
@supports (padding: max(0px)) {
    .qq-fullscreen-mode {
        padding-top: max(0px, env(safe-area-inset-top)) !important;
        padding-bottom: max(0px, env(safe-area-inset-bottom)) !important;
        padding-left: max(0px, env(safe-area-inset-left)) !important;
        padding-right: max(0px, env(safe-area-inset-right)) !important;
    }
}
        '''
        
    def get_iphone_viewport_meta(self) -> str:
        """Get iPhone-specific viewport meta tag"""
        return '''<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover, shrink-to-fit=no">'''
        
    def get_android_css_overrides(self) -> str:
        """Get Android-specific CSS overrides"""
        return '''
/* QQ Android Fullscreen Overrides */
.qq-fullscreen-mode {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999999 !important;
    background: #000 !important;
}

/* Android navigation bar handling */
.qq-fullscreen-mode {
    padding-bottom: env(keyboard-inset-height, 0px) !important;
}
        '''
        
    def get_android_viewport_meta(self) -> str:
        """Get Android-specific viewport meta tag"""
        return '''<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">'''
        
    def get_tablet_css_overrides(self) -> str:
        """Get tablet-specific CSS overrides"""
        return '''
/* QQ Tablet Fullscreen Overrides */
.qq-fullscreen-mode {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999999 !important;
}
        '''
        
    def get_tablet_viewport_meta(self) -> str:
        """Get tablet-specific viewport meta tag"""
        return '''<meta name="viewport" content="width=device-width, initial-scale=1.0">'''
        
    def get_desktop_css_overrides(self) -> str:
        """Get desktop-specific CSS overrides"""
        return '''
/* QQ Desktop Fullscreen Overrides */
.qq-fullscreen-mode {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999999 !important;
}
        '''
        
    def get_desktop_viewport_meta(self) -> str:
        """Get desktop-specific viewport meta tag"""
        return '''<meta name="viewport" content="width=device-width, initial-scale=1.0">'''
        
    def generate_fullscreen_toggle_js(self) -> str:
        """Generate intelligent fullscreen toggle JavaScript"""
        return '''
// QQ Intelligent Fullscreen Override System
class QQFullscreenSystem {
    constructor() {
        this.isFullscreen = false;
        this.originalStyles = new Map();
        this.deviceType = this.detectDeviceType();
        this.setupEventListeners();
        this.injectStyles();
    }
    
    detectDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        if (/iphone|ipod/.test(userAgent)) {
            return 'iphone';
        } else if (/ipad/.test(userAgent) || (userAgent.includes('mac') && 'ontouchend' in document)) {
            return 'ipad';
        } else if (/android/.test(userAgent)) {
            if (viewport.width < 768) return 'android';
            return 'android_tablet';
        } else if (viewport.width < 768) {
            return 'mobile';
        } else if (viewport.width < 1024) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    injectStyles() {
        const styleId = 'qq-fullscreen-styles';
        let existingStyle = document.getElementById(styleId);
        
        if (existingStyle) {
            existingStyle.remove();
        }
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = this.getDeviceSpecificCSS();
        document.head.appendChild(style);
    }
    
    getDeviceSpecificCSS() {
        const baseCSS = `
            /* QQ Universal Fullscreen Overrides */
            .qq-fullscreen-mode {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                max-width: 100vw !important;
                max-height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                z-index: 2147483647 !important;
                overflow: auto !important;
                background: var(--bg-color, #1a1a1a) !important;
                box-sizing: border-box !important;
            }
            
            /* Override ALL existing fullscreen classes */
            .qq-fullscreen-mode .fullscreen,
            .qq-fullscreen-mode .full-screen,
            .qq-fullscreen-mode .fs,
            .qq-fullscreen-mode .maximize,
            .qq-fullscreen-mode .expanded,
            .qq-fullscreen-mode .modal-fullscreen {
                position: relative !important;
                width: auto !important;
                height: auto !important;
                z-index: auto !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
            }
            
            /* Force responsive behavior */
            .qq-fullscreen-mode * {
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            
            /* Prevent zoom on input focus */
            .qq-fullscreen-mode input,
            .qq-fullscreen-mode select,
            .qq-fullscreen-mode textarea {
                font-size: 16px !important;
                transform: none !important;
            }
            
            /* Hide scrollbars but keep functionality */
            .qq-fullscreen-mode::-webkit-scrollbar {
                width: 0px !important;
                background: transparent !important;
            }
            
            .qq-fullscreen-mode {
                -ms-overflow-style: none !important;
                scrollbar-width: none !important;
            }
        `;
        
        const iphoneCSS = `
            /* iPhone Specific Overrides */
            @supports (-webkit-touch-callout: none) {
                .qq-fullscreen-mode {
                    -webkit-overflow-scrolling: touch !important;
                    -webkit-text-size-adjust: 100% !important;
                    touch-action: manipulation !important;
                    height: 100vh !important;
                    height: -webkit-fill-available !important;
                }
                
                .qq-fullscreen-mode .dashboard-content {
                    padding-top: env(safe-area-inset-top, 0px) !important;
                    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
                    padding-left: env(safe-area-inset-left, 0px) !important;
                    padding-right: env(safe-area-inset-right, 0px) !important;
                    min-height: calc(100vh - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px)) !important;
                }
            }
            
            /* iPhone landscape orientation */
            @media screen and (orientation: landscape) and (max-height: 500px) {
                .qq-fullscreen-mode {
                    height: 100vh !important;
                    height: -webkit-fill-available !important;
                }
            }
        `;
        
        return baseCSS + (this.deviceType.includes('iphone') ? iphoneCSS : '');
    }
    
    setupEventListeners() {
        // Listen for orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                if (this.isFullscreen) {
                    this.refreshFullscreen();
                }
            }, 100);
        });
        
        // Listen for resize events
        window.addEventListener('resize', () => {
            if (this.isFullscreen) {
                this.refreshFullscreen();
            }
        });
        
        // Prevent default fullscreen behavior
        document.addEventListener('fullscreenchange', (e) => {
            if (document.fullscreenElement && !this.isFullscreen) {
                document.exitFullscreen();
            }
        });
    }
    
    toggleFullscreen(targetElement = null) {
        const element = targetElement || document.body;
        
        if (this.isFullscreen) {
            this.exitFullscreen(element);
        } else {
            this.enterFullscreen(element);
        }
        
        return this.isFullscreen;
    }
    
    enterFullscreen(element) {
        // Store original styles
        this.storeOriginalStyles(element);
        
        // Override any existing fullscreen
        this.exitAllFullscreenModes();
        
        // Apply QQ fullscreen class
        element.classList.add('qq-fullscreen-mode');
        
        // Force specific iPhone fixes
        if (this.deviceType.includes('iphone')) {
            this.applyiPhoneFixes(element);
        }
        
        // Update viewport meta tag
        this.updateViewportMeta();
        
        // Hide address bar on mobile
        if (this.deviceType.includes('iphone') || this.deviceType.includes('android')) {
            setTimeout(() => {
                window.scrollTo(0, 1);
                window.scrollTo(0, 0);
            }, 100);
        }
        
        this.isFullscreen = true;
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('qq-fullscreen-enter', {
            detail: { deviceType: this.deviceType }
        }));
        
        // Store state
        this.saveFullscreenState(true);
    }
    
    exitFullscreen(element) {
        // Remove QQ fullscreen class
        element.classList.remove('qq-fullscreen-mode');
        
        // Restore original styles
        this.restoreOriginalStyles(element);
        
        this.isFullscreen = false;
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('qq-fullscreen-exit', {
            detail: { deviceType: this.deviceType }
        }));
        
        // Store state
        this.saveFullscreenState(false);
    }
    
    exitAllFullscreenModes() {
        // Exit browser fullscreen
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(() => {});
        }
        
        // Remove all other fullscreen classes
        const fullscreenClasses = [
            'fullscreen', 'full-screen', 'fs', 'maximize', 'expanded',
            'modal-fullscreen', 'fullscreen-mode', 'full-screen-mode'
        ];
        
        fullscreenClasses.forEach(className => {
            const elements = document.querySelectorAll('.' + className);
            elements.forEach(el => {
                if (!el.classList.contains('qq-fullscreen-mode')) {
                    el.classList.remove(className);
                }
            });
        });
    }
    
    applyiPhoneFixes(element) {
        // Force height recalculation for iPhone
        element.style.setProperty('height', '100vh', 'important');
        element.style.setProperty('height', '-webkit-fill-available', 'important');
        
        // Prevent bounce scrolling
        document.body.style.setProperty('overscroll-behavior', 'none', 'important');
        
        // Force repaint
        element.style.transform = 'translateZ(0)';
        setTimeout(() => {
            element.style.transform = 'none';
        }, 50);
    }
    
    updateViewportMeta() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        if (this.deviceType.includes('iphone')) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover, shrink-to-fit=no';
        } else {
            viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=no';
        }
    }
    
    refreshFullscreen() {
        if (this.isFullscreen) {
            const element = document.querySelector('.qq-fullscreen-mode');
            if (element) {
                // Force style recalculation
                this.injectStyles();
                if (this.deviceType.includes('iphone')) {
                    this.applyiPhoneFixes(element);
                }
            }
        }
    }
    
    storeOriginalStyles(element) {
        const computedStyle = window.getComputedStyle(element);
        this.originalStyles.set(element, {
            position: element.style.position,
            top: element.style.top,
            left: element.style.left,
            width: element.style.width,
            height: element.style.height,
            zIndex: element.style.zIndex,
            margin: element.style.margin,
            padding: element.style.padding,
            overflow: element.style.overflow
        });
    }
    
    restoreOriginalStyles(element) {
        const originalStyles = this.originalStyles.get(element);
        if (originalStyles) {
            Object.keys(originalStyles).forEach(property => {
                element.style[property] = originalStyles[property];
            });
            this.originalStyles.delete(element);
        }
    }
    
    saveFullscreenState(isFullscreen) {
        // Save to localStorage for persistence
        const state = {
            isFullscreen: isFullscreen,
            deviceType: this.deviceType,
            timestamp: Date.now()
        };
        localStorage.setItem('qq-fullscreen-state', JSON.stringify(state));
        
        // Send to server if API is available
        if (typeof fetch !== 'undefined') {
            fetch('/api/save-fullscreen-state', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(state)
            }).catch(() => {}); // Fail silently
        }
    }
    
    restoreFullscreenState() {
        try {
            const saved = localStorage.getItem('qq-fullscreen-state');
            if (saved) {
                const state = JSON.parse(saved);
                if (state.isFullscreen && (Date.now() - state.timestamp) < 86400000) { // 24 hours
                    setTimeout(() => {
                        this.enterFullscreen(document.body);
                    }, 100);
                }
            }
        } catch (e) {
            // Ignore errors
        }
    }
}

// Initialize QQ Fullscreen System
window.qqFullscreen = new QQFullscreenSystem();

// Add global toggle function
window.toggleQQFullscreen = function(element) {
    return window.qqFullscreen.toggleFullscreen(element);
};

// Restore previous state on page load
document.addEventListener('DOMContentLoaded', () => {
    window.qqFullscreen.restoreFullscreenState();
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // F11 key override
    if (e.key === 'F11') {
        e.preventDefault();
        window.qqFullscreen.toggleFullscreen();
    }
    
    // Escape key to exit
    if (e.key === 'Escape' && window.qqFullscreen.isFullscreen) {
        window.qqFullscreen.exitFullscreen(document.querySelector('.qq-fullscreen-mode'));
    }
});
        '''
        
    def generate_fullscreen_button_html(self) -> str:
        """Generate fullscreen toggle button HTML"""
        return '''
<!-- QQ Intelligent Fullscreen Toggle Button -->
<div id="qq-fullscreen-toggle" class="qq-fullscreen-toggle-btn" 
     onclick="toggleQQFullscreen()" 
     title="Toggle Intelligent Fullscreen (Optimized for iPhone)">
    <svg id="qq-fullscreen-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
    </svg>
    <span class="qq-fullscreen-text">Fullscreen</span>
</div>

<style>
.qq-fullscreen-toggle-btn {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999998;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    border: 2px solid #007bff;
    border-radius: 8px;
    padding: 10px 15px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    user-select: none;
    -webkit-user-select: none;
    touch-action: manipulation;
}

.qq-fullscreen-toggle-btn:hover {
    background: rgba(0, 123, 255, 0.9);
    transform: scale(1.05);
    box-shadow: 0 4px 20px rgba(0, 123, 255, 0.4);
}

.qq-fullscreen-toggle-btn:active {
    transform: scale(0.95);
}

/* iPhone specific styles */
@supports (-webkit-touch-callout: none) {
    .qq-fullscreen-toggle-btn {
        top: max(20px, env(safe-area-inset-top, 0px) + 10px);
        right: max(20px, env(safe-area-inset-right, 0px) + 10px);
    }
}

/* Hide text on very small screens */
@media (max-width: 380px) {
    .qq-fullscreen-text {
        display: none;
    }
    .qq-fullscreen-toggle-btn {
        padding: 8px;
    }
}

/* Fullscreen mode adjustments */
.qq-fullscreen-mode .qq-fullscreen-toggle-btn {
    background: rgba(220, 53, 69, 0.8);
    border-color: #dc3545;
}

.qq-fullscreen-mode .qq-fullscreen-toggle-btn:hover {
    background: rgba(220, 53, 69, 0.9);
    box-shadow: 0 4px 20px rgba(220, 53, 69, 0.4);
}

/* Animation for icon change */
#qq-fullscreen-icon {
    transition: transform 0.3s ease;
}

.qq-fullscreen-mode #qq-fullscreen-icon {
    transform: rotate(180deg);
}
</style>

<script>
// Update button text and icon based on fullscreen state
window.addEventListener('qq-fullscreen-enter', () => {
    const btn = document.getElementById('qq-fullscreen-toggle');
    const text = btn.querySelector('.qq-fullscreen-text');
    const icon = btn.querySelector('#qq-fullscreen-icon path');
    
    if (text) text.textContent = 'Exit Fullscreen';
    if (icon) icon.setAttribute('d', 'M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3');
});

window.addEventListener('qq-fullscreen-exit', () => {
    const btn = document.getElementById('qq-fullscreen-toggle');
    const text = btn.querySelector('.qq-fullscreen-text');
    const icon = btn.querySelector('#qq-fullscreen-icon path');
    
    if (text) text.textContent = 'Fullscreen';
    if (icon) icon.setAttribute('d', 'M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3');
});
</script>
        '''

# Global instance
qq_fullscreen_system = None

def initialize_fullscreen_system():
    """Initialize the intelligent fullscreen system"""
    global qq_fullscreen_system
    
    if qq_fullscreen_system is None:
        qq_fullscreen_system = QQIntelligentFullscreenSystem()
        
    return qq_fullscreen_system

def get_fullscreen_system():
    """Get the fullscreen system instance"""
    return qq_fullscreen_system

def generate_fullscreen_assets():
    """Generate all fullscreen assets"""
    system = initialize_fullscreen_system()
    
    return {
        'javascript': system.generate_fullscreen_toggle_js(),
        'button_html': system.generate_fullscreen_button_html(),
        'iphone_css': system.get_iphone_css_overrides(),
        'viewport_meta': system.get_iphone_viewport_meta()
    }

if __name__ == "__main__":
    # Initialize and test fullscreen system
    system = initialize_fullscreen_system()
    assets = generate_fullscreen_assets()
    
    print("QQ Intelligent Fullscreen Override System")
    print("=" * 45)
    print("Status: READY - iPhone scaling optimization active")
    print("Features: Override all existing fullscreen controls")
    print("Optimization: Perfect scaling on iPhone and all devices")
    print("Integration: Ready for dashboard deployment")
    print("\nThe system will override any existing fullscreen controls and ensure perfect scaling.")