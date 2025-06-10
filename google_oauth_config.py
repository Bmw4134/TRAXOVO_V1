"""
Google OAuth Configuration for TRAXOVO
Using provided Google Cloud Platform credentials
"""

import os
import json

# Google OAuth Configuration from provided credentials
GOOGLE_OAUTH_CONFIG = {
    "client_id": "572770624466-qquq1irt447kubal3ig2cgq735l2u7hh.apps.googleusercontent.com",
    "project_id": "geocoding-api-445715",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "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",
    "redirect_uris": ["https://replit.com/@bmwatson34/NEXUS-TRAXOVO"]
}

def get_google_oauth_config():
    """Get Google OAuth configuration"""
    return GOOGLE_OAUTH_CONFIG

def get_oauth_redirect_uri():
    """Get appropriate OAuth redirect URI based on environment"""
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN')
    if replit_domain:
        return f'https://{replit_domain}/auth/google/callback'
    else:
        return GOOGLE_OAUTH_CONFIG["redirect_uris"][0]

def validate_oauth_setup():
    """Validate OAuth configuration"""
    config = get_google_oauth_config()
    required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
    
    for field in required_fields:
        if not config.get(field):
            return False, f"Missing {field}"
    
    return True, "OAuth configuration valid"

if __name__ == "__main__":
    is_valid, message = validate_oauth_setup()
    print(f"OAuth Setup: {message}")
    if is_valid:
        print(f"Client ID: {GOOGLE_OAUTH_CONFIG['client_id'][:20]}...")
        print(f"Redirect URI: {get_oauth_redirect_uri()}")