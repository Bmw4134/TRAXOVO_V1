#!/usr/bin/env python3
"""
NEXUS EZ-Integration Suite
Comprehensive Trello, OneDrive OAuth, and Twilio integration with dashboard routing
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='[EZ-INTEGRATION] %(message)s')
logger = logging.getLogger(__name__)

class TrelloConnector:
    """Trello API integration with key/token injection"""
    
    def __init__(self):
        self.api_key = os.environ.get('TRELLO_API_KEY')
        self.api_token = os.environ.get('TRELLO_API_TOKEN')
        self.base_url = "https://api.trello.com/1"
        
    def authenticate(self, api_key: str = None, api_token: str = None):
        """Authenticate with Trello API"""
        if api_key:
            self.api_key = api_key
        if api_token:
            self.api_token = api_token
            
        if not self.api_key or not self.api_token:
            return {
                'success': False,
                'error': 'Trello API key and token required',
                'setup_url': f'https://trello.com/app-key'
            }
        
        try:
            response = requests.get(
                f"{self.base_url}/members/me",
                params={'key': self.api_key, 'token': self.api_token}
            )
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'username': user_data.get('username'),
                    'full_name': user_data.get('fullName'),
                    'email': user_data.get('email')
                }
            else:
                return {'success': False, 'error': 'Invalid credentials'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_boards(self):
        """Get user's Trello boards"""
        if not self.api_key or not self.api_token:
            return {'error': 'Not authenticated'}
            
        try:
            response = requests.get(
                f"{self.base_url}/members/me/boards",
                params={'key': self.api_key, 'token': self.api_token}
            )
            return response.json() if response.status_code == 200 else {'error': 'Failed to fetch boards'}
        except Exception as e:
            return {'error': str(e)}
    
    def create_card(self, list_id: str, name: str, desc: str = None):
        """Create new Trello card with automation trigger"""
        try:
            params = {
                'key': self.api_key,
                'token': self.api_token,
                'name': name,
                'idList': list_id
            }
            if desc:
                params['desc'] = desc
                
            response = requests.post(f"{self.base_url}/cards", params=params)
            if response.status_code == 200:
                card = response.json()
                self._trigger_card_event(card)
                return card
            return {'error': 'Failed to create card'}
        except Exception as e:
            return {'error': str(e)}
    
    def _trigger_card_event(self, card_data):
        """Trigger automation event when card is created"""
        logger.info(f"Card created: {card_data.get('name')} - Triggering automation")
        # Integration point for automation workflows

class OneDriveOAuthConnector:
    """OneDrive OAuth integration with Graph API permissions"""
    
    def __init__(self):
        self.client_id = os.environ.get('MICROSOFT_CLIENT_ID')
        self.client_secret = os.environ.get('MICROSOFT_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/auth/microsoft/callback')
        self.scopes = ['Files.ReadWrite', 'User.Read', 'offline_access']
        
    def get_auth_url(self):
        """Generate OAuth authorization URL"""
        if not self.client_id:
            return {
                'error': 'Microsoft Client ID required',
                'setup_instructions': 'Register app at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps'
            }
        
        scope_string = ' '.join(self.scopes)
        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={scope_string}&"
            f"response_mode=query"
        )
        
        return {
            'auth_url': auth_url,
            'redirect_uri': self.redirect_uri,
            'scopes': self.scopes
        }
    
    def exchange_code_for_token(self, authorization_code: str):
        """Exchange authorization code for access token"""
        try:
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(token_url, data=data)
            return response.json() if response.status_code == 200 else {'error': 'Token exchange failed'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_user_files(self, access_token: str):
        """Get user's OneDrive files"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://graph.microsoft.com/v1.0/me/drive/root/children', headers=headers)
            return response.json() if response.status_code == 200 else {'error': 'Failed to fetch files'}
        except Exception as e:
            return {'error': str(e)}

class TwilioMessagingService:
    """Twilio SMS integration with phone number prompting"""
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
    def setup_credentials(self, account_sid: str = None, auth_token: str = None, phone_number: str = None):
        """Setup Twilio credentials"""
        if account_sid:
            self.account_sid = account_sid
        if auth_token:
            self.auth_token = auth_token
        if phone_number:
            self.phone_number = phone_number
            
        return self.validate_credentials()
    
    def validate_credentials(self):
        """Validate Twilio credentials"""
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            return {
                'success': False,
                'error': 'Twilio Account SID, Auth Token, and Phone Number required',
                'setup_url': 'https://console.twilio.com/'
            }
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            # Test by fetching account info
            account = client.api.account.fetch()
            return {
                'success': True,
                'account_name': account.friendly_name,
                'phone_number': self.phone_number
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_test_sms(self, to_number: str, message: str = None):
        """Send test SMS message"""
        if not message:
            message = f"NEXUS EZ-Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            message_instance = client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message_instance.sid,
                'status': message_instance.status,
                'to': to_number
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

class NEXUSEZIntegration:
    """Main EZ-Integration coordinator"""
    
    def __init__(self):
        self.trello = TrelloConnector()
        self.onedrive = OneDriveOAuthConnector()
        self.twilio = TwilioMessagingService()
        self.integration_status = {}
        
    def execute_full_sweep(self):
        """Execute complete EZ-integration sweep"""
        logger.info("Executing NEXUS EZ-Integration sweep")
        
        # Deploy integrations
        trello_status = self._deploy_trello_integration()
        onedrive_status = self._deploy_onedrive_integration()
        twilio_status = self._deploy_twilio_integration()
        
        # Update integration status
        self.integration_status = {
            'trello': trello_status,
            'onedrive': onedrive_status,
            'twilio': twilio_status,
            'deployment_timestamp': datetime.utcnow().isoformat()
        }
        
        # Push to dashboards
        self._push_to_dashboards()
        
        return self.integration_status
    
    def _deploy_trello_integration(self):
        """Deploy Trello API connector"""
        logger.info("Deploying Trello API connector")
        
        # Check for existing credentials
        auth_result = self.trello.authenticate()
        
        status = {
            'service': 'Trello',
            'status': 'ready' if auth_result.get('success') else 'needs_setup',
            'setup_required': not auth_result.get('success'),
            'capabilities': ['board_access', 'card_creation', 'automation_triggers']
        }
        
        if not auth_result.get('success'):
            status['setup_instructions'] = {
                'step1': 'Get API key from https://trello.com/app-key',
                'step2': 'Generate token with read/write permissions',
                'step3': 'Set TRELLO_API_KEY and TRELLO_API_TOKEN environment variables'
            }
        
        return status
    
    def _deploy_onedrive_integration(self):
        """Deploy OneDrive OAuth connector"""
        logger.info("Deploying OneDrive OAuth connector")
        
        auth_info = self.onedrive.get_auth_url()
        
        status = {
            'service': 'OneDrive',
            'status': 'ready' if not auth_info.get('error') else 'needs_setup',
            'oauth_permissions': self.onedrive.scopes,
            'capabilities': ['file_access', 'automation_triggers', 'workflow_integration']
        }
        
        if auth_info.get('error'):
            status['setup_instructions'] = {
                'step1': 'Register app at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps',
                'step2': 'Add redirect URI: http://localhost:5000/auth/microsoft/callback',
                'step3': 'Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET',
                'permissions': 'Files.ReadWrite, User.Read, offline_access'
            }
        else:
            status['auth_url'] = auth_info['auth_url']
        
        return status
    
    def _deploy_twilio_integration(self):
        """Deploy Twilio messaging service"""
        logger.info("Deploying Twilio messaging service")
        
        validation = self.twilio.validate_credentials()
        
        status = {
            'service': 'Twilio',
            'status': 'ready' if validation.get('success') else 'needs_setup',
            'capabilities': ['sms_messaging', 'automation_alerts', 'event_notifications']
        }
        
        if not validation.get('success'):
            status['setup_instructions'] = {
                'step1': 'Create account at https://console.twilio.com/',
                'step2': 'Get Account SID and Auth Token from console',
                'step3': 'Purchase phone number for messaging',
                'step4': 'Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER'
            }
        
        return status
    
    def _push_to_dashboards(self):
        """Push integration status to active dashboards"""
        logger.info("Pushing integration routes to dashboards")
        
        dashboard_routes = {
            'admin_control': '/admin-direct',
            'intelligence_dashboard': '/nexus-dashboard',
            'file_processing': '/upload'
        }
        
        # Store integration status for dashboard access
        integration_data = {
            'ez_integration_status': self.integration_status,
            'active_routes': dashboard_routes,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        with open('nexus_ez_integration_status.json', 'w') as f:
            json.dump(integration_data, f, indent=2)
    
    def test_all_integrations(self):
        """Test all integrated services"""
        test_results = {}
        
        # Test Trello
        if self.integration_status.get('trello', {}).get('status') == 'ready':
            boards = self.trello.get_boards()
            test_results['trello'] = {
                'test': 'board_access',
                'success': not boards.get('error'),
                'boards_count': len(boards) if isinstance(boards, list) else 0
            }
        
        # Test OneDrive
        if self.integration_status.get('onedrive', {}).get('status') == 'ready':
            test_results['onedrive'] = {
                'test': 'oauth_ready',
                'success': True,
                'auth_url_generated': True
            }
        
        # Test Twilio
        if self.integration_status.get('twilio', {}).get('status') == 'ready':
            validation = self.twilio.validate_credentials()
            test_results['twilio'] = {
                'test': 'credentials_validation',
                'success': validation.get('success', False),
                'account_name': validation.get('account_name')
            }
        
        return test_results

def execute_ez_integration():
    """Main EZ-integration execution"""
    print("\n" + "="*60)
    print("NEXUS EZ-INTEGRATION SUITE")
    print("="*60)
    
    integration = NEXUSEZIntegration()
    
    # Execute full sweep
    status = integration.execute_full_sweep()
    
    # Test integrations
    test_results = integration.test_all_integrations()
    
    print("\nEZ-INTEGRATION DEPLOYMENT COMPLETE")
    print(f"→ Trello API: {status['trello']['status'].upper()}")
    print(f"→ OneDrive OAuth: {status['onedrive']['status'].upper()}")
    print(f"→ Twilio Messaging: {status['twilio']['status'].upper()}")
    print("→ Dashboard routes updated")
    print("→ Automation triggers enabled")
    print("="*60)
    
    return status, test_results

if __name__ == "__main__":
    execute_ez_integration()