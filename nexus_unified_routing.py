"""
NEXUS Unified Routing System
Standardizes all routes through PTNI for seamless navigation
"""

import logging
from flask import redirect, request, session
from datetime import datetime

class NexusUnifiedRouter:
    """Centralized routing system for all NEXUS interfaces"""
    
    def __init__(self):
        self.route_mapping = {
            # Base routes redirect to PTNI
            '/': '/ptni-dashboard',
            '/home': '/ptni-dashboard',
            '/dashboard': '/ptni-dashboard',
            '/main': '/ptni-dashboard',
            
            # Legacy routes standardized
            '/admin': '/ptni-dashboard',
            '/admin-direct': '/ptni-dashboard',
            '/nexus-home': '/ptni-dashboard',
            '/executive-dashboard': '/ptni-dashboard',
            
            # Browser automation accessible through PTNI
            '/browser': '/ptni-dashboard?view=browser',
            '/automation': '/ptni-dashboard?view=automation',
            '/browser-automation': '/ptni-dashboard?view=browser-suite',
            
            # Specialized interfaces
            '/command-center': '/ptni-dashboard?view=command',
            '/intelligence': '/ptni-dashboard?view=intelligence',
            '/monitoring': '/ptni-dashboard?view=monitoring',
            '/logs': '/ptni-dashboard?view=logs',
            
            # API routes remain unchanged
            '/api/': '/api/',
            '/health': '/health',
            
            # Static assets
            '/static/': '/static/',
            '/favicon.ico': '/favicon.ico'
        }
        
        self.ptni_views = {
            'browser': 'Browser Automation Suite',
            'automation': 'Automation Queue',
            'browser-suite': 'Complete Browser Suite',
            'command': 'Command Center',
            'intelligence': 'Intelligence Feed',
            'monitoring': 'System Monitoring',
            'logs': 'System Logs'
        }
        
        logging.info("NEXUS Unified Router initialized")
    
    def standardize_route(self, path):
        """Convert any route to standardized PTNI route"""
        # Exact matches first
        if path in self.route_mapping:
            return self.route_mapping[path]
        
        # Pattern matches
        if path.startswith('/api/'):
            return path  # API routes unchanged
        
        if path.startswith('/static/'):
            return path  # Static routes unchanged
        
        # All other routes go to PTNI
        return '/ptni-dashboard'
    
    def get_ptni_view_context(self, view_param=None):
        """Get context for PTNI view based on parameters"""
        if not view_param:
            view_param = request.args.get('view', 'default')
        
        return {
            'view': view_param,
            'view_title': self.ptni_views.get(view_param, 'NEXUS Dashboard'),
            'timestamp': datetime.now().isoformat(),
            'user_session': session.get('user_id', 'anonymous'),
            'navigation_source': request.referrer or 'direct'
        }
    
    def log_navigation(self, original_path, standardized_path):
        """Log navigation standardization for analytics"""
        navigation_data = {
            'timestamp': datetime.now().isoformat(),
            'original_path': original_path,
            'standardized_path': standardized_path,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'ip_address': request.remote_addr,
            'referrer': request.referrer
        }
        
        logging.info(f"Route standardized: {original_path} -> {standardized_path}")
        return navigation_data

# Global router instance
nexus_router = NexusUnifiedRouter()

def standardize_navigation(original_route):
    """Standardize any route through PTNI"""
    standardized = nexus_router.standardize_route(original_route)
    nexus_router.log_navigation(original_route, standardized)
    return standardized

def get_unified_navigation_html():
    """Generate unified navigation HTML for injection"""
    return '''
    <div id="nexus-unified-nav" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: linear-gradient(90deg, #1a1a2e, #16213e);
        z-index: 10000;
        display: flex;
        align-items: center;
        padding: 0 20px;
        border-bottom: 2px solid #00d4aa;
        box-shadow: 0 2px 10px rgba(0,212,170,0.3);
    ">
        <div style="color: #00d4aa; font-weight: bold; font-size: 18px; margin-right: 30px;">
            NEXUS PTNI
        </div>
        <nav style="display: flex; gap: 20px; flex: 1;">
            <a href="/ptni-dashboard" style="color: #fff; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: all 0.3s;">
                Dashboard
            </a>
            <a href="/ptni-dashboard?view=browser" style="color: #fff; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: all 0.3s;">
                Browser Suite
            </a>
            <a href="/ptni-dashboard?view=automation" style="color: #fff; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: all 0.3s;">
                Automation
            </a>
            <a href="/ptni-dashboard?view=intelligence" style="color: #fff; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: all 0.3s;">
                Intelligence
            </a>
            <a href="/ptni-dashboard?view=monitoring" style="color: #fff; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: all 0.3s;">
                Monitoring
            </a>
        </nav>
        <div id="nexus-status" style="color: #00d4aa; font-size: 12px;">
            OPERATIONAL
        </div>
    </div>
    <style>
        body { margin-top: 60px !important; }
        #nexus-unified-nav a:hover {
            background: rgba(0,212,170,0.2) !important;
            color: #00d4aa !important;
        }
    </style>
    '''

def inject_unified_navigation(response_html):
    """Inject unified navigation into HTML responses"""
    if '<body' in response_html and 'nexus-unified-nav' not in response_html:
        nav_html = get_unified_navigation_html()
        # Inject after opening body tag
        response_html = response_html.replace('<body', nav_html + '<body', 1)
    return response_html