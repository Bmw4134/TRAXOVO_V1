"""
GAUGE API Credentials Status Checker
"""
import os
import json
from datetime import datetime

def check_saved_credentials():
    """Check if GAUGE credentials are saved and return status"""
    try:
        # Check environment variables
        env_credentials = {
            'endpoint': os.environ.get('GAUGE_API_ENDPOINT'),
            'auth_token': os.environ.get('GAUGE_AUTH_TOKEN'),
            'client_id': os.environ.get('GAUGE_CLIENT_ID'),
            'client_secret': os.environ.get('GAUGE_CLIENT_SECRET')
        }
        
        # Check if credentials file exists
        file_credentials = None
        try:
            with open('gauge_credentials.json', 'r') as f:
                file_credentials = json.load(f)
        except FileNotFoundError:
            pass
        
        has_env_creds = bool(env_credentials['endpoint'] and env_credentials['auth_token'])
        has_file_creds = bool(file_credentials and file_credentials.get('endpoint') and file_credentials.get('auth_token'))
        
        return {
            'has_environment_credentials': has_env_creds,
            'has_file_credentials': has_file_creds,
            'environment_credentials': {k: '***' if v and 'token' in k or 'secret' in k else v for k, v in env_credentials.items()},
            'file_credentials': {k: '***' if v and ('token' in k or 'secret' in k) else v for k, v in file_credentials.items()} if file_credentials else None,
            'status': 'connected' if (has_env_creds or has_file_creds) else 'not_configured',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }

def load_saved_credentials():
    """Load saved credentials from file or environment"""
    try:
        # Try file first
        try:
            with open('gauge_credentials.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            pass
        
        # Fall back to environment variables
        env_creds = {
            'endpoint': os.environ.get('GAUGE_API_ENDPOINT'),
            'auth_token': os.environ.get('GAUGE_AUTH_TOKEN'),
            'client_id': os.environ.get('GAUGE_CLIENT_ID'),
            'client_secret': os.environ.get('GAUGE_CLIENT_SECRET')
        }
        
        if env_creds['endpoint'] and env_creds['auth_token']:
            return env_creds
            
        return None
        
    except Exception as e:
        return None