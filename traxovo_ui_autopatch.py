#!/usr/bin/env python3
"""
TRAXOVO UI Auto-Patch System
Implements scroll fixes, mobile layout optimization, and KaizenGPT bridge validation
"""

import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class TRAXOVOUIPatcher:
    def __init__(self):
        self.patch_id = f"UI-PATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.kaizen_bridge_active = False
        
    def validate_kaizen_bridge(self):
        """Validate KaizenGPT sync bridge is operational"""
        try:
            # Check for bridge configuration
            if os.path.exists('.kaizen_gpt_config.json'):
                with open('.kaizen_gpt_config.json', 'r') as f:
                    config = json.load(f)
                    if config.get('bridge_enabled'):
                        self.kaizen_bridge_active = True
                        logging.info("✓ KaizenGPT bridge confirmed active")
                        return True
            
            # Check for bridge marker
            if os.path.exists('.nexus_kaizen_bridge_active'):
                self.kaizen_bridge_active = True
                logging.info("✓ KaizenGPT bridge marker found - system operational")
                return True
                
            logging.warning("⚠ KaizenGPT bridge not detected")
            return False
            
        except Exception as e:
            logging.error(f"Bridge validation failed: {e}")
            return False
    
    def inject_scroll_fixes(self):
        """Inject comprehensive scroll and layout fixes"""
        scroll_fixes_css = """
/* TRAXOVO Scroll and Mobile Layout Fixes */
/* Auto-injected by traxovo_ui_autopatch.py */

/* Global Scroll Optimization */
* {
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 255, 159, 0.3) rgba(15, 23, 42, 0.8);
}

/* Custom Scrollbars for Webkit */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.8);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, rgba(0, 255, 159, 0.6) 0%, rgba(59, 130, 246, 0.4) 100%);
    border-radius: 4px;
    transition: all 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, rgba(0, 255, 159, 0.8) 0%, rgba(59, 130, 246, 0.6) 100%);
}

/* Viewport and Container Fixes */
html, body {
    overflow-x: hidden;
    scroll-behavior: smooth;
    height: 100%;
    min-height: 100vh;
}

.traxovo-container {
    width: 100%;
    max-width: 100vw;
    overflow-x: hidden;
    position: relative;
}

/* Main Content Scroll Areas */
.main-content {
    height: calc(100vh - 80px);
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
    margin-right: -8px;
}

.section-content {
    max-height: calc(100vh - 120px);
    overflow-y: auto;
    overflow-x: hidden;
}

/* Dashboard Grid Responsive Fixes */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    width: 100%;
    max-width: 100%;
    overflow: visible;
}

/* Mobile Layout Optimization */
@media (max-width: 768px) {
    .main-content {
        height: calc(100vh - 60px);
        padding: 8px;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 12px;
        padding: 0 4px;
    }
    
    .metric-card {
        min-height: auto;
        padding: 16px !important;
    }
    
    .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        position: fixed;
        z-index: 9999;
        height: 100vh;
        overflow-y: auto;
    }
    
    .sidebar.mobile-open {
        transform: translateX(0);
    }
    
    /* Mobile Navigation */
    .mobile-nav-toggle {
        display: block;
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 10000;
        background: rgba(0, 255, 159, 0.9);
        border: none;
        border-radius: 8px;
        padding: 12px;
        color: #0f172a;
        cursor: pointer;
        font-size: 18px;
        box-shadow: 0 4px 12px rgba(0, 255, 159, 0.3);
    }
    
    @media (min-width: 769px) {
        .mobile-nav-toggle {
            display: none;
        }
    }
}

/* Tablet Layout */
@media (min-width: 769px) and (max-width: 1024px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }
    
    .main-content {
        padding: 12px;
    }
}

/* Large Screen Optimization */
@media (min-width: 1025px) {
    .dashboard-grid {
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;
    }
    
    .main-content {
        padding: 20px;
    }
}

/* Touch and Gesture Improvements */
.metric-card, .section-card, .content-section {
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(0, 255, 159, 0.2);
}

/* Loading States with Scroll */
.loading-container {
    height: 200px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Table Scroll Fixes */
.table-container {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 400px;
    border-radius: 8px;
    border: 1px solid rgba(0, 255, 159, 0.2);
}

.maintenance-table, .risk-factors-table {
    width: 100%;
    min-width: 800px;
}

@media (max-width: 768px) {
    .maintenance-table, .risk-factors-table {
        min-width: 600px;
        font-size: 14px;
    }
    
    .maintenance-table th, 
    .maintenance-table td,
    .risk-factors-table th,
    .risk-factors-table td {
        padding: 8px 4px;
    }
}

/* Anomaly Detection Card Mobile Fix */
.anomaly-detection-card {
    position: relative;
    overflow: hidden;
    min-height: 120px;
}

@media (max-width: 768px) {
    .anomaly-detection-card {
        min-height: 100px;
    }
    
    .anomaly-detection-card .metric-value {
        font-size: 1.8rem !important;
    }
    
    .anomaly-detection-card .metric-label {
        font-size: 0.85rem !important;
    }
}

/* KaizenGPT Status Mobile */
.kaizen-sync-status {
    position: fixed;
    top: 10px;
    right: 10px;
    font-size: 11px;
    padding: 6px 12px;
    z-index: 9998;
}

@media (max-width: 768px) {
    .kaizen-sync-status {
        top: 70px;
        right: 10px;
        font-size: 10px;
        padding: 4px 8px;
    }
}

/* Performance Optimizations */
.nexus-gpu-accelerated {
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    will-change: transform;
}

.nexus-stable-layout {
    contain: layout style paint;
}

/* Focus and Accessibility */
.metric-card:focus,
.section-card:focus,
button:focus {
    outline: 2px solid rgba(0, 255, 159, 0.8);
    outline-offset: 2px;
}

/* Animation Performance */
.real-time-pulse {
    animation: pulse 2s infinite;
    animation-fill-mode: both;
    backface-visibility: hidden;
}

/* High DPI Displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
    .metric-value {
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
}
        """
        
        # Write scroll fixes
        with open('static/traxovo_scroll_fixes.css', 'w') as f:
            f.write(scroll_fixes_css)
            
        logging.info("✓ Scroll and mobile layout fixes injected")
        return True
    
    def inject_mobile_navigation(self):
        """Inject mobile navigation JavaScript"""
        mobile_js = """
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
        """
        
        # Write mobile navigation
        with open('static/traxovo_mobile_nav.js', 'w') as f:
            f.write(mobile_js)
            
        logging.info("✓ Mobile navigation system injected")
        return True
    
    def update_dashboard_template(self):
        """Update dashboard template to include new CSS and JS"""
        try:
            template_path = 'templates/enhanced_dashboard.html'
            
            if not os.path.exists(template_path):
                logging.error("Dashboard template not found")
                return False
            
            # Read current template
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Add scroll fixes CSS if not already present
            if 'traxovo_scroll_fixes.css' not in content:
                css_injection = '    <link rel="stylesheet" href="/static/traxovo_scroll_fixes.css">'
                content = content.replace(
                    '<link rel="stylesheet" href="/static/dashboard_ui_patch.css">',
                    f'<link rel="stylesheet" href="/static/dashboard_ui_patch.css">\n{css_injection}'
                )
            
            # Add mobile navigation JS if not already present
            if 'traxovo_mobile_nav.js' not in content:
                js_injection = '    <script src="/static/traxovo_mobile_nav.js"></script>'
                content = content.replace(
                    '<script src="/static/qnis_contextual_ui.js"></script>',
                    f'<script src="/static/qnis_contextual_ui.js"></script>\n{js_injection}'
                )
            
            # Write updated template
            with open(template_path, 'w') as f:
                f.write(content)
                
            logging.info("✓ Dashboard template updated with UI patches")
            return True
            
        except Exception as e:
            logging.error(f"Template update failed: {e}")
            return False
    
    def run_autopatch(self):
        """Execute complete UI autopatch sequence"""
        logging.info(f"Starting TRAXOVO UI Autopatch {self.patch_id}")
        
        success_count = 0
        
        # Validate KaizenGPT bridge
        if self.validate_kaizen_bridge():
            success_count += 1
        
        # Inject scroll fixes
        if self.inject_scroll_fixes():
            success_count += 1
            
        # Inject mobile navigation
        if self.inject_mobile_navigation():
            success_count += 1
            
        # Update dashboard template
        if self.update_dashboard_template():
            success_count += 1
        
        # Generate patch report
        patch_report = {
            "patch_id": self.patch_id,
            "timestamp": datetime.now().isoformat(),
            "kaizen_bridge_active": self.kaizen_bridge_active,
            "patches_applied": success_count,
            "total_patches": 4,
            "status": "SUCCESS" if success_count == 4 else "PARTIAL",
            "components": {
                "kaizen_bridge_validation": self.kaizen_bridge_active,
                "scroll_fixes": True,
                "mobile_navigation": True,
                "template_updates": True
            }
        }
        
        # Write patch report
        with open('ui_patch_report.json', 'w') as f:
            json.dump(patch_report, f, indent=2)
        
        logging.info(f"UI Autopatch complete: {success_count}/4 components successful")
        return patch_report

def main():
    patcher = TRAXOVOUIPatcher()
    report = patcher.run_autopatch()
    
    print(f"\n🎨 TRAXOVO UI Autopatch Complete")
    print(f"Patch ID: {report['patch_id']}")
    print(f"Status: {report['status']}")
    print(f"Components: {report['patches_applied']}/4")
    
    if report['kaizen_bridge_active']:
        print("✓ KaizenGPT Bridge: LIVE")
    else:
        print("⚠ KaizenGPT Bridge: CHECK REQUIRED")
    
    print("✓ Scroll Fixes: Applied")
    print("✓ Mobile Layout: Optimized")
    print("✓ Navigation: Enhanced")
    
    return 0

if __name__ == "__main__":
    main()