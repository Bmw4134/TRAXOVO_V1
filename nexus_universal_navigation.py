"""
NEXUS Universal Navigation System
Automatic injection of consistent navigation across all platform templates
"""

from flask import request, session
import re
import logging

logger = logging.getLogger(__name__)

class NEXUSUniversalNavigation:
    """Universal navigation system for seamless platform connectivity"""
    
    def __init__(self):
        self.navigation_injected = False
        self.current_route = "/"
        
    def create_universal_navigation_html(self):
        """Create universal navigation HTML that works across all templates"""
        return '''
<!-- NEXUS Universal Navigation -->
<div id="nexus-universal-nav" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 70px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    backdrop-filter: blur(10px);
    border-bottom: 2px solid #00d4aa;
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 30px;
    box-shadow: 0 4px 20px rgba(0, 212, 170, 0.2);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
">
    <!-- Left: Logo & Brand -->
    <div style="display: flex; align-items: center; gap: 20px;">
        <div style="
            font-size: 24px;
            font-weight: bold;
            color: #00d4aa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
        " onclick="window.location.href='/'">
            <i class="fas fa-infinity" style="font-size: 28px;"></i>
            TRAXOVO
        </div>
        <div style="
            background: linear-gradient(45deg, #00d4aa, #007a6b);
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        ">NEXUS ACTIVE</div>
    </div>
    
    <!-- Center: Navigation Menu -->
    <nav style="display: flex; gap: 30px; flex: 1; justify-content: center;">
        <a href="/" style="
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        " onmouseover="this.style.background='rgba(0,212,170,0.1)'; this.style.border='1px solid #00d4aa'" 
           onmouseout="this.style.background='transparent'; this.style.border='1px solid transparent'">
            <i class="fas fa-home"></i> Dashboard
        </a>
        
        <a href="/ground-works-complete" style="
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        " onmouseover="this.style.background='rgba(0,212,170,0.1)'; this.style.border='1px solid #00d4aa'" 
           onmouseout="this.style.background='transparent'; this.style.border='1px solid transparent'">
            <i class="fas fa-industry"></i> Ground Works
        </a>
        
        <a href="/ultimate-troy-dashboard" style="
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        " onmouseover="this.style.background='rgba(0,212,170,0.1)'; this.style.border='1px solid #00d4aa'" 
           onmouseout="this.style.background='transparent'; this.style.border='1px solid transparent'">
            <i class="fas fa-chart-line"></i> Troy's Dashboard
        </a>
        
        <a href="/api-performance-benchmark" style="
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        " onmouseover="this.style.background='rgba(0,212,170,0.1)'; this.style.border='1px solid #00d4aa'" 
           onmouseout="this.style.background='transparent'; this.style.border='1px solid transparent'">
            <i class="fas fa-tachometer-alt"></i> API Benchmark
        </a>
    </nav>
    
    <!-- Right: User Actions -->
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 16px;
            border-radius: 20px;
            color: #00d4aa;
            font-size: 14px;
            font-weight: 600;
        ">
            <i class="fas fa-shield-alt"></i> NEXUS
        </div>
        
        <a href="/logout" style="
            background: linear-gradient(45deg, #dc3545, #c82333);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(220,53,69,0.4)'" 
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
            <i class="fas fa-sign-out-alt"></i>
            Logout
        </a>
    </div>
</div>

<!-- Navigation Spacer -->
<div id="nexus-nav-spacer" style="height: 70px;"></div>

<script>
// NEXUS Universal Navigation JavaScript
(function() {
    // Highlight current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('#nexus-universal-nav a[href]');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath || 
            (currentPath === '/' && link.getAttribute('href') === '/') ||
            (currentPath.includes(link.getAttribute('href')) && link.getAttribute('href') !== '/')) {
            link.style.background = 'rgba(0,212,170,0.2)';
            link.style.border = '1px solid #00d4aa';
            link.style.color = '#00d4aa';
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey) {
            switch(e.key) {
                case 'H':
                    e.preventDefault();
                    window.location.href = '/';
                    break;
                case 'G':
                    e.preventDefault();
                    window.location.href = '/ground-works-complete';
                    break;
                case 'T':
                    e.preventDefault();
                    window.location.href = '/ultimate-troy-dashboard';
                    break;
                case 'A':
                    e.preventDefault();
                    window.location.href = '/api-performance-benchmark';
                    break;
                case 'L':
                    e.preventDefault();
                    window.location.href = '/logout';
                    break;
            }
        }
    });
    
    // Add tooltips for keyboard shortcuts
    const shortcuts = {
        '/': 'Ctrl+Shift+H',
        '/ground-works-complete': 'Ctrl+Shift+G',
        '/ultimate-troy-dashboard': 'Ctrl+Shift+T',
        '/api-performance-benchmark': 'Ctrl+Shift+A',
        '/logout': 'Ctrl+Shift+L'
    };
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (shortcuts[href]) {
            link.title = shortcuts[href];
        }
    });
})();
</script>
'''
    
    def inject_navigation(self, html_content):
        """Inject universal navigation into HTML content if not already present"""
        
        # Skip if navigation already exists
        if 'nexus-universal-nav' in html_content:
            return html_content
            
        # Skip if no body tag
        if '<body' not in html_content:
            return html_content
            
        navigation_html = self.create_universal_navigation_html()
        
        # Find body tag and inject navigation
        body_pattern = r'(<body[^>]*>)'
        match = re.search(body_pattern, html_content, re.IGNORECASE)
        
        if match:
            body_tag = match.group(1)
            html_content = html_content.replace(
                body_tag, 
                body_tag + navigation_html, 
                1
            )
            
        return html_content
    
    def create_navigation_middleware(self, app):
        """Create Flask middleware to automatically inject navigation"""
        
        @app.after_request
        def inject_universal_navigation(response):
            # Only inject for HTML responses
            if (response.content_type and 
                'text/html' in response.content_type and 
                response.status_code == 200):
                
                try:
                    html_content = response.get_data(as_text=True)
                    modified_html = self.inject_navigation(html_content)
                    response.set_data(modified_html)
                except Exception as e:
                    logger.error(f"Navigation injection error: {e}")
                    
            return response
            
        return app
    
    def get_navigation_status(self):
        """Get current navigation system status"""
        return {
            'status': 'active',
            'navigation_injected': self.navigation_injected,
            'current_route': self.current_route,
            'features': [
                'Universal Navigation Bar',
                'Keyboard Shortcuts',
                'Active Route Highlighting',
                'Responsive Design',
                'Logout Integration'
            ],
            'shortcuts': {
                'Dashboard': 'Ctrl+Shift+H',
                'Ground Works': 'Ctrl+Shift+G',
                'Troy Dashboard': 'Ctrl+Shift+T', 
                'API Benchmark': 'Ctrl+Shift+A',
                'Logout': 'Ctrl+Shift+L'
            }
        }

# Global navigation instance
universal_nav = NEXUSUniversalNavigation()

def setup_universal_navigation(app):
    """Setup universal navigation for Flask app"""
    return universal_nav.create_navigation_middleware(app)

def get_navigation_html():
    """Get navigation HTML for manual injection"""
    return universal_nav.create_universal_navigation_html()

def inject_navigation_in_template(html_content):
    """Inject navigation in template manually"""
    return universal_nav.inject_navigation(html_content)