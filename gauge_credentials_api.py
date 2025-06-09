"""
GAUGE API Credentials Management
"""
import os
import requests
import logging
from flask import request, jsonify

def test_gauge_connection():
    """Test GAUGE API connection with provided credentials"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        auth_token = data.get('auth_token')
        
        if not endpoint or not auth_token:
            return jsonify({'success': False, 'error': 'Endpoint and auth token are required'})
        
        # Test API connection
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Try a simple GET request to test connectivity
        test_url = f"{endpoint.rstrip('/')}/health" if '/health' not in endpoint else endpoint
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Connection successful'})
        else:
            return jsonify({'success': False, 'error': f'API returned status {response.status_code}'})
            
    except Exception as e:
        logging.error(f"GAUGE connection test error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def save_gauge_credentials():
    """Save GAUGE API credentials"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        auth_token = data.get('auth_token')
        client_id = data.get('client_id', '')
        client_secret = data.get('client_secret', '')
        
        if not endpoint or not auth_token:
            return jsonify({'success': False, 'error': 'Endpoint and auth token are required'})
        
        # Store credentials in environment variables
        os.environ['GAUGE_API_ENDPOINT'] = endpoint
        os.environ['GAUGE_AUTH_TOKEN'] = auth_token
        if client_id:
            os.environ['GAUGE_CLIENT_ID'] = client_id
        if client_secret:
            os.environ['GAUGE_CLIENT_SECRET'] = client_secret
        
        return jsonify({'success': True, 'message': 'Credentials saved successfully'})
            
    except Exception as e:
        logging.error(f"GAUGE credentials save error: {e}")
        return jsonify({'success': False, 'error': str(e)})