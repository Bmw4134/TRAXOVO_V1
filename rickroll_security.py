"""
TRAXOVO Rickroll Security Module
Advanced protection against reverse engineering with instant rickroll redirects
"""

import re
import hashlib
from flask import request, redirect
from functools import wraps

RICKROLL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def detect_hacking_attempt():
    """Detect reverse engineering, hacking, or unauthorized analysis attempts"""
    
    # Check user agent for suspicious patterns (more targeted)
    user_agent = str(request.headers.get('User-Agent', '')).lower()
    suspicious_agents = [
        'burp', 'owasp', 'scanner', 'nikto', 'sqlmap',
        'nessus', 'acunetix', 'w3af', 'skipfish'
    ]
    
    if any(agent in user_agent for agent in suspicious_agents):
        return True
    
    # Check for suspicious headers
    headers_to_check = ['x-forwarded-for', 'x-real-ip', 'referer', 'origin']
    for header in headers_to_check:
        value = str(request.headers.get(header, '')).lower()
        if any(suspicious in value for suspicious in ['github', 'gitlab', 'reverse', 'hack', 'analyze']):
            return True
    
    # Check request parameters for suspicious activity
    all_params = {**request.args, **request.form}
    for param, value in all_params.items():
        param_str = f"{param}={value}".lower()
        if any(keyword in param_str for keyword in ['source', 'code', 'debug', 'admin', 'hack', 'exploit']):
            return True
    
    # Check for code analysis tools in request path
    path = request.path.lower()
    if any(keyword in path for keyword in ['.git', '.env', 'source', 'debug', 'admin', 'config']):
        return True
    
    return False

def rickroll_protection(func):
    """Decorator to protect routes with rickroll redirect"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if detect_hacking_attempt():
            return redirect(RICKROLL_URL)
        return func(*args, **kwargs)
    return wrapper

def setup_rickroll_traps(app):
    """Setup comprehensive rickroll traps for common hacking attempts"""
    
    # Common paths hackers try to access
    trap_paths = [
        '/.git', '/.git/', '/.git/config', '/.git/HEAD',
        '/.env', '/.env.local', '/.env.production',
        '/admin', '/admin/', '/admin/login',
        '/debug', '/debug/', '/debug/console',
        '/source', '/src', '/code',
        '/config', '/config.json', '/config.yml',
        '/api/debug', '/api/admin', '/api/source',
        '/robots.txt', '/sitemap.xml',
        '/wp-admin/', '/phpmyadmin/',
        '/package.json', '/composer.json',
        '/requirements.txt', '/Pipfile',
        '/dockerfile', '/docker-compose.yml',
        '/.htaccess', '/web.config'
    ]
    
    # Create rickroll trap for each path
    for path in trap_paths:
        app.add_url_rule(
            path,
            f'rickroll_trap_{hashlib.md5(path.encode()).hexdigest()[:8]}',
            lambda: redirect(RICKROLL_URL)
        )
    
    # Global before_request handler - disabled for legitimate users
    # @app.before_request
    # def global_rickroll_check():
    #     if detect_hacking_attempt():
    #         return redirect(RICKROLL_URL)
    
    # Custom error handlers that rickroll
    @app.errorhandler(404)
    def not_found_rickroll(error):
        # If path looks suspicious, rickroll them
        if any(keyword in request.path.lower() for keyword in [
            'admin', 'debug', 'source', 'git', 'env', 'config', 'hack'
        ]):
            return redirect(RICKROLL_URL)
        return "Not Found", 404
    
    @app.errorhandler(403)
    def forbidden_rickroll(error):
        return redirect(RICKROLL_URL)
    
    @app.errorhandler(500)
    def error_rickroll(error):
        # If there's an error and request looks suspicious, rickroll
        if detect_hacking_attempt():
            return redirect(RICKROLL_URL)
        return "Internal Server Error", 500
    
    return app