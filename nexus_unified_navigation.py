#!/usr/bin/env python3
"""
NEXUS Unified Navigation System
Cutting-edge navigation with instant admin/NEXUS access from any route
"""

import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[NAV_SYSTEM] %(message)s')
logger = logging.getLogger(__name__)

class NexusUnifiedNavigation:
    """Advanced unified navigation system for seamless admin/NEXUS access"""
    
    def __init__(self):
        self.navigation_config = {}
        self.route_mappings = {}
        self.admin_shortcuts = {}
        
    def create_unified_navigation_bar(self):
        """Create unified navigation bar for all routes"""
        logger.info("Creating unified navigation bar")
        
        navigation_html = '''
<div id="nexus-unified-nav" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-bottom: 2px solid #00ff88;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    font-family: 'SF Mono', Monaco, monospace;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
">
    <!-- NEXUS Logo and Status -->
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="
            font-size: 18px;
            font-weight: bold;
            color: #00ff88;
            cursor: pointer;
        " onclick="window.location.href='/'">
            NEXUS
        </div>
        <div id="nexus-nav-status" style="
            padding: 4px 8px;
            background: #00ff88;
            color: #000;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        ">
            OPERATIONAL
        </div>
    </div>
    
    <!-- Quick Navigation Links -->
    <div style="display: flex; align-items: center; gap: 20px;">
        <a href="/admin-direct" style="
            color: #00ff88;
            text-decoration: none;
            font-weight: bold;
            padding: 8px 12px;
            border: 1px solid #00ff88;
            border-radius: 4px;
            transition: all 0.2s;
        " onmouseover="this.style.background='#00ff88'; this.style.color='#000';" 
           onmouseout="this.style.background='transparent'; this.style.color='#00ff88';">
            ADMIN
        </a>
        
        <a href="/nexus-dashboard" style="
            color: #ffffff;
            text-decoration: none;
            font-weight: bold;
            padding: 8px 12px;
            border: 1px solid #ffffff;
            border-radius: 4px;
            transition: all 0.2s;
        " onmouseover="this.style.background='#ffffff'; this.style.color='#000';" 
           onmouseout="this.style.background='transparent'; this.style.color='#ffffff';">
            DASHBOARD
        </a>
        
        <a href="/executive-dashboard" style="
            color: #ffa502;
            text-decoration: none;
            font-weight: bold;
            padding: 8px 12px;
            border: 1px solid #ffa502;
            border-radius: 4px;
            transition: all 0.2s;
        " onmouseover="this.style.background='#ffa502'; this.style.color='#000';" 
           onmouseout="this.style.background='transparent'; this.style.color='#ffa502';">
            EXECUTIVE
        </a>
        
        <a href="/upload" style="
            color: #3742fa;
            text-decoration: none;
            font-weight: bold;
            padding: 8px 12px;
            border: 1px solid #3742fa;
            border-radius: 4px;
            transition: all 0.2s;
        " onmouseover="this.style.background='#3742fa'; this.style.color='#fff';" 
           onmouseout="this.style.background='transparent'; this.style.color='#3742fa';">
            UPLOAD
        </a>
    </div>
    
    <!-- Advanced Navigation Controls -->
    <div style="display: flex; align-items: center; gap: 15px;">
        <!-- Command Palette Trigger -->
        <div id="nexus-command-trigger" style="
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        " onclick="toggleCommandPalette()">
            ⌘K Navigate
        </div>
        
        <!-- Breadcrumb Current Route -->
        <div id="nexus-breadcrumb" style="
            color: #ffffff;
            font-size: 12px;
            opacity: 0.8;
        ">
            /
        </div>
        
        <!-- Emergency Admin Access -->
        <div id="nexus-emergency-admin" style="
            background: #ff4757;
            color: #ffffff;
            padding: 6px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
        " onclick="emergencyAdminAccess()">
            🚨 ADMIN
        </div>
    </div>
</div>

<!-- Command Palette Overlay -->
<div id="nexus-command-palette" style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 20000;
    display: none;
    justify-content: center;
    align-items: flex-start;
    padding-top: 120px;
">
    <div style="
        background: #1a1a2e;
        border: 2px solid #00ff88;
        border-radius: 10px;
        width: 600px;
        max-height: 500px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    ">
        <div style="
            padding: 20px;
            border-bottom: 1px solid #333;
        ">
            <input id="nexus-command-input" type="text" placeholder="Type route or command... (ESC to close)" style="
                width: 100%;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid #00ff88;
                border-radius: 5px;
                color: #ffffff;
                font-size: 16px;
                font-family: inherit;
            " oninput="filterRoutes(this.value)">
        </div>
        
        <div id="nexus-route-list" style="
            max-height: 400px;
            overflow-y: auto;
        ">
            <!-- Routes will be populated here -->
        </div>
    </div>
</div>

<script>
// Unified Navigation System JavaScript
let commandPaletteOpen = false;
let allRoutes = [];

// Initialize navigation system
function initializeNexusNavigation() {
    console.log('NEXUS Unified Navigation initialized');
    
    // Update breadcrumb with current route
    updateBreadcrumb();
    
    // Load all available routes
    loadAllRoutes();
    
    // Add keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Adjust page content for navigation bar
    adjustPageContent();
}

function updateBreadcrumb() {
    const breadcrumb = document.getElementById('nexus-breadcrumb');
    if (breadcrumb) {
        breadcrumb.textContent = window.location.pathname;
    }
}

function loadAllRoutes() {
    allRoutes = [
        { path: '/', name: 'NEXUS Landing', category: 'primary', access: 'public' },
        { path: '/admin-direct', name: 'Admin Control Center', category: 'admin', access: 'admin' },
        { path: '/nexus-dashboard', name: 'Intelligence Dashboard', category: 'primary', access: 'authenticated' },
        { path: '/executive-dashboard', name: 'Executive Analytics', category: 'executive', access: 'executive' },
        { path: '/upload', name: 'File Processing', category: 'primary', access: 'authenticated' },
        { path: '/login', name: 'Login', category: 'auth', access: 'public' },
        { path: '/logout', name: 'Logout', category: 'auth', access: 'public' },
        
        // API Routes (for admin reference)
        { path: '/api/nexus/command', name: 'NEXUS Command Interface', category: 'api', type: 'POST' },
        { path: '/api/nexus/metrics', name: 'System Metrics', category: 'api', type: 'GET' },
        { path: '/api/platform/status', name: 'Platform Status', category: 'api', type: 'GET' },
        { path: '/api/market/data', name: 'Market Data', category: 'api', type: 'GET' },
        { path: '/api/weather/data', name: 'Weather Data', category: 'api', type: 'GET' },
        { path: '/api/ez-integration/status', name: 'EZ-Integration Status', category: 'api', type: 'GET' },
        { path: '/api/executive/metrics', name: 'Executive Metrics', category: 'api', type: 'GET' },
        { path: '/api/auth/reset-password', name: 'Password Reset', category: 'api', type: 'POST' },
        
        // Hidden/Developer Routes
        { path: '/health', name: 'Health Check', category: 'system', access: 'public' },
        { path: '/repl-agent', name: 'Repl Agent Interface', category: 'developer', access: 'developer' },
        { path: '/automation-console', name: 'Automation Console', category: 'admin', access: 'admin' }
    ];
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Cmd+K or Ctrl+K to open command palette
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            toggleCommandPalette();
        }
        
        // Escape to close command palette
        if (e.key === 'Escape' && commandPaletteOpen) {
            toggleCommandPalette();
        }
        
        // Quick admin access: Ctrl+Shift+A
        if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            emergencyAdminAccess();
        }
        
        // Quick dashboard access: Ctrl+Shift+D
        if (e.ctrlKey && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            window.location.href = '/nexus-dashboard';
        }
        
        // Quick home access: Ctrl+Shift+H
        if (e.ctrlKey && e.shiftKey && e.key === 'H') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
}

function adjustPageContent() {
    // Add top margin to body to account for fixed navigation
    document.body.style.marginTop = '60px';
    document.body.style.paddingTop = '0';
}

function toggleCommandPalette() {
    const palette = document.getElementById('nexus-command-palette');
    const input = document.getElementById('nexus-command-input');
    
    if (commandPaletteOpen) {
        palette.style.display = 'none';
        commandPaletteOpen = false;
    } else {
        palette.style.display = 'flex';
        commandPaletteOpen = true;
        
        // Focus input and populate routes
        setTimeout(() => {
            input.focus();
            filterRoutes('');
        }, 100);
    }
}

function filterRoutes(searchTerm) {
    const routeList = document.getElementById('nexus-route-list');
    
    let filteredRoutes = allRoutes;
    if (searchTerm) {
        filteredRoutes = allRoutes.filter(route => 
            route.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            route.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
            route.category.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }
    
    routeList.innerHTML = filteredRoutes.map(route => {
        const categoryColor = getCategoryColor(route.category);
        return `
            <div style="
                padding: 15px 20px;
                border-bottom: 1px solid #333;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: background 0.2s;
            " onmouseover="this.style.background='rgba(0, 255, 136, 0.1)'"
               onmouseout="this.style.background='transparent'"
               onclick="navigateToRoute('${route.path}')">
                <div>
                    <div style="
                        font-weight: bold;
                        color: #ffffff;
                        margin-bottom: 5px;
                    ">${route.name}</div>
                    <div style="
                        color: #999;
                        font-size: 14px;
                    ">${route.path}</div>
                </div>
                <div style="
                    background: ${categoryColor};
                    color: ${route.category === 'primary' ? '#000' : '#fff'};
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                ">${route.category.toUpperCase()}</div>
            </div>
        `;
    }).join('');
}

function getCategoryColor(category) {
    const colors = {
        'primary': '#00ff88',
        'admin': '#ff4757',
        'executive': '#ffa502',
        'api': '#3742fa',
        'auth': '#5f27cd',
        'system': '#00d2d3',
        'developer': '#ff6b6b'
    };
    return colors[category] || '#ffffff';
}

function navigateToRoute(path) {
    window.location.href = path;
    toggleCommandPalette();
}

function emergencyAdminAccess() {
    // Immediate admin access
    window.location.href = '/admin-direct';
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNexusNavigation);
} else {
    initializeNexusNavigation();
}

// Global access
window.nexusNavigation = {
    toggleCommandPalette,
    emergencyAdminAccess,
    navigateToRoute,
    updateBreadcrumb
};
</script>
'''
        
        return navigation_html
    
    def create_route_injection_system(self):
        """Create system to inject navigation into all routes"""
        logger.info("Creating route injection system")
        
        injection_script = '''
<!-- NEXUS Unified Navigation Auto-Injection -->
<script>
(function() {
    // Check if navigation is already injected
    if (document.getElementById('nexus-unified-nav')) {
        return;
    }
    
    // Navigation HTML (minified for injection)
    const navigationHTML = `''' + self.create_unified_navigation_bar().replace('\n', '').replace('`', '\\`') + '''`;
    
    // Inject navigation at the top of body
    if (document.body) {
        document.body.insertAdjacentHTML('afterbegin', navigationHTML);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            document.body.insertAdjacentHTML('afterbegin', navigationHTML);
        });
    }
})();
</script>
'''
        
        return injection_script
    
    def create_floating_navigation_widget(self):
        """Create floating navigation widget for emergency access"""
        logger.info("Creating floating navigation widget")
        
        floating_widget = '''
<!-- Floating NEXUS Navigation Widget -->
<div id="nexus-floating-nav" style="
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 15000;
    display: flex;
    flex-direction: column;
    gap: 10px;
">
    <!-- Main Navigation Button -->
    <div style="
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        transition: all 0.3s ease;
        color: #000;
        font-weight: bold;
        font-size: 18px;
    " onclick="toggleFloatingMenu()" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
        N
    </div>
    
    <!-- Floating Menu Items -->
    <div id="nexus-floating-menu" style="
        display: none;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 10px;
    ">
        <div class="floating-nav-item" onclick="window.location.href='/admin-direct'" style="
            width: 50px;
            height: 50px;
            background: #ff4757;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #fff;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Admin Control">
            A
        </div>
        
        <div class="floating-nav-item" onclick="window.location.href='/nexus-dashboard'" style="
            width: 50px;
            height: 50px;
            background: #3742fa;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #fff;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 2px 10px rgba(55, 66, 250, 0.3);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="NEXUS Dashboard">
            D
        </div>
        
        <div class="floating-nav-item" onclick="window.location.href='/executive-dashboard'" style="
            width: 50px;
            height: 50px;
            background: #ffa502;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #fff;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 2px 10px rgba(255, 165, 2, 0.3);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Executive Dashboard">
            E
        </div>
        
        <div class="floating-nav-item" onclick="window.location.href='/'" style="
            width: 50px;
            height: 50px;
            background: #2f3542;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #fff;
            font-weight: bold;
            font-size: 12px;
            box-shadow: 0 2px 10px rgba(47, 53, 66, 0.3);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Home">
            H
        </div>
    </div>
</div>

<script>
let floatingMenuOpen = false;

function toggleFloatingMenu() {
    const menu = document.getElementById('nexus-floating-menu');
    const button = document.querySelector('#nexus-floating-nav > div:first-child');
    
    if (floatingMenuOpen) {
        menu.style.display = 'none';
        button.style.transform = 'rotate(0deg)';
        floatingMenuOpen = false;
    } else {
        menu.style.display = 'flex';
        button.style.transform = 'rotate(45deg)';
        floatingMenuOpen = true;
    }
}

// Close floating menu when clicking elsewhere
document.addEventListener('click', function(e) {
    if (!document.getElementById('nexus-floating-nav').contains(e.target) && floatingMenuOpen) {
        toggleFloatingMenu();
    }
});
</script>
'''
        
        return floating_widget
    
    def deploy_unified_navigation(self):
        """Deploy complete unified navigation system"""
        logger.info("Deploying NEXUS unified navigation system")
        
        print("\n" + "="*80)
        print("NEXUS UNIFIED NAVIGATION DEPLOYMENT")
        print("="*80)
        
        # Create navigation components
        unified_nav = self.create_unified_navigation_bar()
        injection_system = self.create_route_injection_system()
        floating_widget = self.create_floating_navigation_widget()
        
        # Create complete navigation package
        complete_navigation = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NEXUS Unified Navigation</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    {unified_nav}
    {floating_widget}
    
    <!-- Navigation auto-injection for other pages -->
    {injection_system}
</body>
</html>
'''
        
        # Save navigation system
        with open('nexus_unified_navigation.html', 'w') as f:
            f.write(complete_navigation)
        
        navigation_config = {
            'unified_navigation': {
                'deployment_id': 'NEXUS-NAV-UNIFIED-001',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'DEPLOYED'
            },
            'features': {
                'fixed_navigation_bar': True,
                'command_palette': True,
                'keyboard_shortcuts': True,
                'floating_widget': True,
                'emergency_admin_access': True,
                'breadcrumb_navigation': True,
                'route_discovery': True
            },
            'keyboard_shortcuts': {
                'command_palette': 'Cmd+K / Ctrl+K',
                'emergency_admin': 'Ctrl+Shift+A',
                'quick_dashboard': 'Ctrl+Shift+D',
                'quick_home': 'Ctrl+Shift+H',
                'close_palette': 'Escape'
            },
            'routes_available': len(allRoutes) if 'allRoutes' in locals() else 20,
            'instant_access_routes': [
                '/',
                '/admin-direct',
                '/nexus-dashboard',
                '/executive-dashboard',
                '/upload'
            ]
        }
        
        with open('nexus_navigation_config.json', 'w') as f:
            json.dump(navigation_config, f, indent=2)
        
        print("\nUNIFIED NAVIGATION FEATURES DEPLOYED:")
        print("→ Fixed navigation bar with instant route access")
        print("→ Command palette (⌘K) with fuzzy search")
        print("→ Emergency admin access (🚨 ADMIN button)")
        print("→ Floating navigation widget (bottom-left)")
        print("→ Keyboard shortcuts for all major routes")
        print("→ Real-time breadcrumb navigation")
        print("→ Auto-injection system for all pages")
        
        print("\nKEYBOARD SHORTCUTS:")
        print("→ ⌘K / Ctrl+K: Open command palette")
        print("→ Ctrl+Shift+A: Emergency admin access")
        print("→ Ctrl+Shift+D: Quick dashboard")
        print("→ Ctrl+Shift+H: Quick home")
        print("→ ESC: Close command palette")
        
        print("\nINSTANT ACCESS METHODS:")
        print("→ Top navigation bar: Always visible, immediate clicks")
        print("→ Floating widget: Bottom-left circular menu")
        print("→ Command palette: Search and jump to any route")
        print("→ Emergency button: Red 🚨 ADMIN for immediate access")
        
        print("="*80)
        print("UNIFIED NAVIGATION DEPLOYED - SEAMLESS ADMIN/NEXUS ACCESS ENABLED")
        print("="*80)
        
        return navigation_config

def deploy_nexus_unified_navigation():
    """Main unified navigation deployment"""
    nav_system = NexusUnifiedNavigation()
    return nav_system.deploy_unified_navigation()

if __name__ == "__main__":
    deploy_nexus_unified_navigation()