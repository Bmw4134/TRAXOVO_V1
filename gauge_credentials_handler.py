"""
GAUGE API Credentials Handler
Handles testing and saving GAUGE API credentials for live fleet data
"""

import os
import requests
import logging
from flask import jsonify

def test_gauge_connection(endpoint, auth_token, client_id=None, client_secret=None):
    """Test GAUGE API connection with provided credentials"""
    try:
        if not endpoint or not auth_token:
            return {'success': False, 'error': 'Endpoint and auth token are required'}
        
        # Test API connection
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Try a simple GET request to test connectivity
        test_url = f"{endpoint.rstrip('/')}/health" if '/health' not in endpoint else endpoint
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {'success': True, 'message': 'Connection successful'}
        elif response.status_code == 401:
            return {'success': False, 'error': 'Authentication failed - check your token'}
        elif response.status_code == 404:
            return {'success': False, 'error': 'Endpoint not found - check your URL'}
        else:
            return {'success': False, 'error': f'API returned status {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Connection timeout - check endpoint URL'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Could not connect to API endpoint'}
    except Exception as e:
        logging.error(f"GAUGE connection test error: {e}")
        return {'success': False, 'error': str(e)}

def save_gauge_credentials(endpoint, auth_token, client_id=None, client_secret=None):
    """Save GAUGE API credentials to environment"""
    try:
        if not endpoint or not auth_token:
            return {'success': False, 'error': 'Endpoint and auth token are required'}
        
        # Store credentials in environment variables
        os.environ['GAUGE_API_ENDPOINT'] = endpoint
        os.environ['GAUGE_AUTH_TOKEN'] = auth_token
        if client_id:
            os.environ['GAUGE_CLIENT_ID'] = client_id
        if client_secret:
            os.environ['GAUGE_CLIENT_SECRET'] = client_secret
        
        return {'success': True, 'message': 'Credentials saved successfully'}
            
    except Exception as e:
        logging.error(f"GAUGE credentials save error: {e}")
        return {'success': False, 'error': str(e)}

def get_gauge_status():
    """Get current GAUGE API connection status"""
    try:
        # Check if credentials are configured
        gauge_endpoint = os.environ.get('GAUGE_API_ENDPOINT')
        gauge_token = os.environ.get('GAUGE_AUTH_TOKEN')
        
        if not gauge_endpoint or not gauge_token:
            return {
                'connected': False,
                'status': 'Not configured',
                'message': 'GAUGE API credentials not found'
            }
        
        # Test the connection
        headers = {
            'Authorization': f'Bearer {gauge_token}',
            'Content-Type': 'application/json'
        }
        
        test_url = f"{gauge_endpoint.rstrip('/')}/health" if '/health' not in gauge_endpoint else gauge_endpoint
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'connected': True,
                'status': 'Connected',
                'message': 'GAUGE API connection active'
            }
        else:
            return {
                'connected': False,
                'status': 'Connection failed',
                'message': f'API returned status {response.status_code}'
            }
            
    except Exception as e:
        logging.error(f"GAUGE status check error: {e}")
        return {
            'connected': False,
            'status': 'Error',
            'message': str(e)
        }