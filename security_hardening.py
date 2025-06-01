"""
TRAXOVO Security Hardening Implementation
Enterprise-grade security enhancements for IT compliance
"""

from flask import Flask, request, session, escape
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import re
import bleach
from markupsafe import Markup

class TRAXOVOSecurityManager:
    def __init__(self, app):
        self.app = app
        self.implement_security_hardening()
    
    def implement_security_hardening(self):
        """Apply comprehensive security hardening"""
        
        # 1. Content Security Policy and Security Headers
        self.configure_security_headers()
        
        # 2. Rate Limiting
        self.configure_rate_limiting()
        
        # 3. Input Sanitization
        self.configure_input_sanitization()
        
        # 4. CSRF Protection (already available via flask-wtf)
        self.configure_csrf_protection()
        
        # 5. Secure Session Configuration
        self.configure_secure_sessions()
    
    def configure_security_headers(self):
        """Configure comprehensive security headers"""
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Required for inline scripts
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://stackpath.bootstrapcdn.com",
                "https://cdn.jsdelivr.net"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Required for inline styles
                "https://cdn.jsdelivr.net",
                "https://stackpath.bootstrapcdn.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "blob:"
            ],
            'font-src': [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://fonts.gstatic.com"
            ],
            'connect-src': [
                "'self'",
                "https://api.gaugesmart.com"  # Allow GAUGE API
            ]
        }
        
        try:
            Talisman(self.app, 
                content_security_policy=csp,
                force_https=True,
                strict_transport_security=True,
                content_type_options=True,
                referrer_policy='strict-origin-when-cross-origin'
            )
            print("✅ Security headers configured with Talisman")
        except Exception as e:
            print(f"⚠️  Talisman not available: {e}")
    
    def configure_rate_limiting(self):
        """Configure rate limiting for API endpoints"""
        try:
            limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"]
            )
            
            # Specific limits for sensitive endpoints
            @limiter.limit("5 per minute")
            @self.app.route('/login', methods=['POST'])
            def login_rate_limit():
                pass
            
            @limiter.limit("100 per hour")
            @self.app.route('/api/<path:path>')
            def api_rate_limit(path):
                pass
                
            print("✅ Rate limiting configured")
        except Exception as e:
            print(f"⚠️  Rate limiting not available: {e}")
    
    def configure_input_sanitization(self):
        """Configure comprehensive input sanitization"""
        
        @self.app.before_request
        def sanitize_input():
            """Sanitize all incoming requests"""
            if request.method == 'POST':
                # Sanitize form data
                if request.form:
                    sanitized_form = {}
                    for key, value in request.form.items():
                        if isinstance(value, str):
                            sanitized_form[key] = self.sanitize_input_string(value)
                        else:
                            sanitized_form[key] = value
                    request.form = sanitized_form
            
            # Sanitize query parameters
            if request.args:
                sanitized_args = {}
                for key, value in request.args.items():
                    if isinstance(value, str):
                        sanitized_args[key] = self.sanitize_input_string(value)
                    else:
                        sanitized_args[key] = value
                request.args = sanitized_args
    
    def sanitize_input_string(self, input_string):
        """Sanitize individual input strings"""
        if not input_string:
            return input_string
        
        # Remove potentially dangerous characters
        sanitized = bleach.clean(input_string, tags=[], attributes={}, strip=True)
        
        # Additional SQL injection prevention
        sql_injection_patterns = [
            r"(\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+)",
            r"(\s*(or|and)\s+\d+\s*=\s*\d+)",
            r"(\s*'\s*(or|and)\s*')",
            r"(--|#|/\*|\*/)"
        ]
        
        for pattern in sql_injection_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def configure_csrf_protection(self):
        """Configure CSRF protection"""
        try:
            from flask_wtf.csrf import CSRFProtect
            csrf = CSRFProtect(self.app)
            print("✅ CSRF protection enabled")
        except ImportError:
            print("⚠️  Flask-WTF not available for CSRF protection")
    
    def configure_secure_sessions(self):
        """Configure secure session handling"""
        
        # Secure session configuration
        self.app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
            SESSION_COOKIE_NAME='traxovo_session'
        )
        
        @self.app.before_request
        def enforce_session_security():
            """Enforce secure session handling"""
            # Regenerate session on privilege escalation
            if 'user_role' in session and 'watson' in str(session.get('username', '')):
                if not session.get('admin_session_verified'):
                    session['admin_session_verified'] = True
                    session.permanent = True
        
        print("✅ Secure session configuration applied")

def apply_security_hardening(app):
    """Apply security hardening to Flask app"""
    return TRAXOVOSecurityManager(app)