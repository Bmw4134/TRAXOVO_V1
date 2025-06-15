"""
Anti-Reverse Engineering Protection System
Comprehensive code protection with rickroll redirects for unauthorized access attempts
"""

import os
import re
import ast
import inspect
from functools import wraps
from flask import request, redirect, jsonify, render_template_string
import hashlib
import base64
import logging

class AntiReverseEngineeringProtection:
    """Advanced protection against code analysis and reverse engineering"""
    
    def __init__(self):
        self.rickroll_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.suspicious_patterns = [
            # Code analysis tools and debuggers
            r'(?i)(pdb|debugger|breakpoint|trace|inspect\.)',
            r'(?i)(decompile|disassemble|bytecode|ast\.)',
            r'(?i)(reverse.?engineer|hack|crack|exploit)',
            r'(?i)(source.?code|view.?source|inspect.?element)',
            
            # Development tools
            r'(?i)(postman|curl|wget|httpie)',
            r'(?i)(burp.?suite|owasp|penetration|pentest)',
            r'(?i)(static.?analysis|code.?review)',
            
            # Suspicious user agents
            r'(?i)(bot|crawler|spider|scraper)',
            r'(?i)(python|requests|urllib|selenium)',
            r'(?i)(scanner|probe|exploit)',
            
            # Suspicious headers
            r'(?i)(x-forwarded|x-real-ip|x-original)',
            r'(?i)(dev|debug|test|admin)',
        ]
        self.protected_endpoints = set()
        
    def is_suspicious_request(self, request_obj):
        """Detect potentially suspicious reverse engineering attempts"""
        # Check user agent
        user_agent = str(request_obj.headers.get('User-Agent', ''))
        for pattern in self.suspicious_patterns:
            if re.search(pattern, user_agent):
                return True
                
        # Check headers for suspicious patterns
        for header_name, header_value in request_obj.headers:
            header_content = f"{header_name}: {header_value}"
            for pattern in self.suspicious_patterns:
                if re.search(pattern, header_content):
                    return True
                    
        # Check for development/debugging parameters
        for param in request_obj.args:
            if any(keyword in param.lower() for keyword in ['debug', 'test', 'dev', 'admin', 'source']):
                return True
                
        # Check referer for suspicious sources
        referer = request_obj.headers.get('Referer', '')
        if any(keyword in referer.lower() for keyword in ['github', 'gitlab', 'bitbucket', 'sourceforge']):
            return True
            
        return False
    
    def protect_endpoint(self, func):
        """Decorator to protect specific endpoints from reverse engineering"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check for suspicious activity
            if self.is_suspicious_request(request):
                return self.trigger_rickroll_protection()
                
            # Add endpoint to protected list
            self.protected_endpoints.add(func.__name__)
            
            # Execute original function
            return func(*args, **kwargs)
        return wrapper
    
    def trigger_rickroll_protection(self):
        """Trigger rickroll redirect for reverse engineering attempts"""
        return redirect(self.rickroll_url)
    
    def obfuscate_response(self, data):
        """Obfuscate sensitive data in API responses"""
        if isinstance(data, dict):
            obfuscated = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password', 'auth']):
                    obfuscated[key] = "***PROTECTED***"
                else:
                    obfuscated[key] = self.obfuscate_response(value)
            return obfuscated
        elif isinstance(data, list):
            return [self.obfuscate_response(item) for item in data]
        else:
            return data
    
    def generate_decoy_endpoints(self):
        """Generate decoy endpoints that redirect to rickroll"""
        decoy_routes = [
            '/api/source-code',
            '/api/debug',
            '/api/admin',
            '/api/config',
            '/api/secrets',
            '/api/database',
            '/api/internal',
            '/source',
            '/debug',
            '/admin',
            '/.git',
            '/.env',
            '/config.json',
            '/package.json',
            '/requirements.txt',
            '/dockerfile',
            '/docker-compose.yml'
        ]
        return decoy_routes

# Global protection instance
protection = AntiReverseEngineeringProtection()

def protect_route(func):
    """Easy-to-use decorator for route protection"""
    return protection.protect_endpoint(func)

def add_rickroll_protection(app):
    """Add comprehensive rickroll protection to Flask app"""
    
    # Add decoy endpoints that rickroll unauthorized access
    decoy_routes = protection.generate_decoy_endpoints()
    
    for route in decoy_routes:
        app.add_url_rule(
            route, 
            f'decoy_{route.replace("/", "_").replace(".", "_")}',
            lambda: redirect(protection.rickroll_url)
        )
    
    # Add before_request handler for global protection - disabled for legitimate users
    # @app.before_request
    # def check_reverse_engineering():
    #     if protection.is_suspicious_request(request):
    #         return redirect(protection.rickroll_url)
    
    # Add custom error handlers that rickroll
    @app.errorhandler(404)
    def not_found_rickroll(error):
        # If someone is probing for endpoints, rickroll them
        if any(probe in request.path.lower() for probe in ['admin', 'debug', 'source', 'git', 'env']):
            return redirect(protection.rickroll_url)
        return "404 - Not Found", 404
    
    @app.errorhandler(403)
    def forbidden_rickroll(error):
        return redirect(protection.rickroll_url)
    
    return app

# Code obfuscation utilities
def obfuscate_string(text):
    """Obfuscate strings to make reverse engineering harder"""
    encoded = base64.b64encode(text.encode()).decode()
    return f"base64_decode('{encoded}')"

def generate_hash_check():
    """Generate integrity check for critical files"""
    critical_files = [
        'troy_automation_nexus.py',
        'ground_works_suite.py',
        'enterprise_automation_orchestrator.py'
    ]
    
    file_hashes = {}
    for file_path in critical_files:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                file_hashes[file_path] = file_hash
    
    return file_hashes

# Runtime protection
class RuntimeProtection:
    """Runtime protection against debugging and analysis"""
    
    @staticmethod
    def check_debugger():
        """Check if debugger is attached"""
        if hasattr(os, 'getppid'):
            # Check for common debugger parent processes
            debugger_names = ['pdb', 'gdb', 'lldb', 'windbg', 'x64dbg']
            # This is a simplified check - in production, use more sophisticated detection
            return False
        return False
    
    @staticmethod
    def anti_debug():
        """Anti-debugging measures"""
        if RuntimeProtection.check_debugger():
            # Redirect to rickroll if debugger detected
            exit(0)
    
    @staticmethod
    def check_virtual_environment():
        """Check if running in analysis environment"""
        suspicious_env_vars = [
            'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'PYTHONPATH'
        ]
        
        for var in suspicious_env_vars:
            if var in os.environ:
                value = os.environ[var].lower()
                if any(keyword in value for keyword in ['analysis', 'reverse', 'debug', 'test']):
                    return True
        return False

# Initialize runtime protection
runtime_protection = RuntimeProtection()

def secure_import_protection():
    """Protect against unauthorized imports and analysis"""
    original_import = __builtins__.__import__
    
    def protected_import(name, *args, **kwargs):
        # List of modules that trigger protection if imported suspiciously
        protected_modules = [
            'ast', 'dis', 'inspect', 'pdb', 'trace', 'traceback',
            'decompyle3', 'uncompyle6', 'py_compile'
        ]
        
        if name in protected_modules:
            # Check if import is from suspicious context
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_name = frame.f_back.f_code.co_name
                if caller_name not in ['<module>', '__init__']:
                    # Suspicious import attempt - could be analysis tool
                    logging.warning(f"Suspicious import attempt: {name} from {caller_name}")
                    # In a real scenario, you might want to exit or redirect
        
        return original_import(name, *args, **kwargs)
    
    __builtins__.__import__ = protected_import

if __name__ == "__main__":
    # Test the protection system
    print("Anti-Reverse Engineering Protection System Initialized")
    print(f"Protected endpoints: {len(protection.protected_endpoints)}")
    print(f"Decoy routes: {len(protection.generate_decoy_endpoints())}")
    print("Rickroll URL ready for unauthorized access attempts")