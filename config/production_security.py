"""
Production Security Configuration for TRAXOVO Fleet Management System

This module provides security hardening settings for production deployment.
"""

import os

class ProductionSecurityConfig:
    """Security configuration for production deployment"""
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 8 * 60 * 60  # 8 hours for field crews
    
    # HTTPS Configuration
    FORCE_HTTPS = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Rate Limiting (requests per minute)
    RATELIMIT_DEFAULTS = [
        "200 per day",
        "50 per hour",
        "10 per minute"
    ]
    
    # Sensitive Endpoints - Lower Limits
    API_RATE_LIMITS = {
        '/auth/login': '5 per minute',
        '/auth/password-reset': '3 per hour',
        '/api/gauge': '30 per minute',
        '/api/gps-data': '60 per minute'
    }
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.replit.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.replit.com; img-src 'self' data: https:;"
    }
    
    # Database Security
    DB_POOL_SIZE = 10
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
    
    # Logging Security Events
    SECURITY_LOG_EVENTS = [
        'login_attempt',
        'login_failure', 
        'password_reset_request',
        'api_rate_limit_exceeded',
        'suspicious_gps_data_access'
    ]

def apply_security_config(app):
    """Apply production security configuration to Flask app"""
    
    # Apply session security
    app.config.update({
        'SESSION_COOKIE_SECURE': ProductionSecurityConfig.SESSION_COOKIE_SECURE,
        'SESSION_COOKIE_HTTPONLY': ProductionSecurityConfig.SESSION_COOKIE_HTTPONLY,
        'SESSION_COOKIE_SAMESITE': ProductionSecurityConfig.SESSION_COOKIE_SAMESITE,
        'PERMANENT_SESSION_LIFETIME': ProductionSecurityConfig.PERMANENT_SESSION_LIFETIME,
        'PREFERRED_URL_SCHEME': ProductionSecurityConfig.PREFERRED_URL_SCHEME
    })
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        for header, value in ProductionSecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    # Force HTTPS in production
    if ProductionSecurityConfig.FORCE_HTTPS and not app.debug:
        @app.before_request
        def force_https():
            from flask import request, redirect, url_for
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                return redirect(request.url.replace('http://', 'https://'))
    
    return app