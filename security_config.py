"""
TRAXOVO Security Configuration
Fixed security headers and rate limiting for production deployment
"""

import os
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def configure_security(app):
    """Configure enterprise-grade security for TRAXOVO"""
    
    # Fixed Talisman configuration
    csp = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
        'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'img-src': "'self' data: https:",
        'font-src': "'self' https://cdn.jsdelivr.net",
        'connect-src': "'self'",
    }
    
    # Corrected Talisman initialization
    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,  # Set to True in production
        strict_transport_security=True,
        content_security_policy_nonce_in=['script-src']
    )
    
    # Production-ready rate limiting with Redis fallback
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=os.environ.get('REDIS_URL', 'memory://'),
        default_limits=["1000 per hour", "100 per minute"]
    )
    
    return limiter

def get_rate_limits():
    """Return rate limiting configuration"""
    return {
        'api_endpoints': "10 per minute",
        'login_attempts': "5 per minute", 
        'file_uploads': "3 per minute",
        'reports_generation': "2 per minute"
    }