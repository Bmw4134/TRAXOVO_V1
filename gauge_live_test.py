"""
GAUGE API Live Connection Test
Test authentic GAUGE API connection with user credentials
"""

import requests
import base64
import json
import os
from datetime import datetime

class GAUGELiveConnector:
    def __init__(self):
        self.base_url = "https://api.gaugesmart.com"
        self.asset_endpoint = "/AssetList/28dcba94c01e453fa8e9215a068f30e4"
        
    def test_connection(self, username, password, api_key):
        """Test live GAUGE API connection with user credentials"""
        try:
            # Create Basic Auth header
            auth_string = f"{username}:{password}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'X-API-Key': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'TRAXOVO-NEXUS/1.0'
            }
            
            # Test the exact endpoint provided
            test_url = f"{self.base_url}{self.asset_endpoint}"
            
            print(f"Testing GAUGE API connection to: {test_url}")
            print(f"Using username: {username}")
            print(f"API Key length: {len(api_key) if api_key else 0}")
            
            response = requests.get(test_url, headers=headers, timeout=30, verify=False)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Success! Retrieved {len(data) if isinstance(data, list) else 'data'} from GAUGE API")
                    return {
                        'success': True,
                        'data': data,
                        'asset_count': len(data) if isinstance(data, list) else 1,
                        'timestamp': datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    print("Response is not valid JSON")
                    return {
                        'success': True,
                        'data': response.text,
                        'raw_response': True,
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                print(f"Error: {response.status_code} - {response.text[:500]}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}",
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: {e}")
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
        except requests.exceptions.Timeout as e:
            print(f"Timeout Error: {e}")
            return {'success': False, 'error': f'Request timeout: {str(e)}'}
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def save_credentials(self, username, password, api_key):
        """Save GAUGE credentials to environment and file"""
        try:
            # Save to environment
            os.environ['GAUGE_API_ENDPOINT'] = self.base_url
            os.environ['GAUGE_AUTH_TOKEN'] = api_key
            os.environ['GAUGE_CLIENT_ID'] = username
            os.environ['GAUGE_CLIENT_SECRET'] = password
            
            # Save to credentials file
            credentials = {
                'endpoint': self.base_url,
                'asset_endpoint': self.asset_endpoint,
                'username': username,
                'password': password,
                'api_key': api_key,
                'saved_at': datetime.now().isoformat(),
                'status': 'configured'
            }
            
            with open('gauge_live_credentials.json', 'w') as f:
                json.dump(credentials, f, indent=2)
            
            print("GAUGE credentials saved successfully")
            return True
            
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

if __name__ == "__main__":
    connector = GAUGELiveConnector()
    
    # Test with placeholder - user will provide real credentials
    test_result = connector.test_connection("bwatson", "user_password", "user_api_key")
    print(json.dumps(test_result, indent=2))