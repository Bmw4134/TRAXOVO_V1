"""
Email Configuration Manager
Secure email settings management for TRAXOVO system
"""
import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailConfigManager:
    def __init__(self):
        self.config_file = 'email_config.json'
        self.smtp_providers = {
            'gmail': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'requires_app_password': True
            },
            'outlook': {
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'requires_app_password': False
            },
            'office365': {
                'smtp_server': 'smtp.office365.com',
                'smtp_port': 587,
                'requires_app_password': False
            },
            'custom': {
                'smtp_server': 'custom',
                'smtp_port': 587,
                'requires_app_password': False
            }
        }
    
    def get_email_config(self):
        """Get current email configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Don't return actual password for security
                    if 'password' in config:
                        config['password_set'] = True
                        del config['password']
                    return config
            else:
                return self._get_default_config()
        except Exception as e:
            return {'error': f'Failed to load config: {str(e)}'}
    
    def save_email_config(self, config_data):
        """Save email configuration securely"""
        try:
            # Validate required fields
            required_fields = ['provider', 'email', 'password']
            for field in required_fields:
                if field not in config_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Get provider settings
            provider = config_data['provider']
            if provider not in self.smtp_providers:
                return {'success': False, 'error': f'Unsupported provider: {provider}'}
            
            provider_config = self.smtp_providers[provider]
            
            # Build configuration
            email_config = {
                'provider': provider,
                'email': config_data['email'],
                'password': config_data['password'],
                'smtp_server': config_data.get('smtp_server', provider_config['smtp_server']),
                'smtp_port': config_data.get('smtp_port', provider_config['smtp_port']),
                'use_tls': config_data.get('use_tls', True),
                'display_name': config_data.get('display_name', 'TRAXOVO System'),
                'last_updated': datetime.now().isoformat()
            }
            
            # Test connection before saving
            test_result = self._test_smtp_connection(email_config)
            if not test_result['success']:
                return test_result
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(email_config, f, indent=2)
            
            return {
                'success': True,
                'message': 'Email configuration saved successfully',
                'provider': provider,
                'email': config_data['email']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to save config: {str(e)}'}
    
    def test_email_connection(self):
        """Test current email configuration"""
        config = self.get_email_config()
        if 'error' in config:
            return config
        
        # Load password from file
        try:
            with open(self.config_file, 'r') as f:
                full_config = json.load(f)
            return self._test_smtp_connection(full_config)
        except Exception as e:
            return {'success': False, 'error': f'Failed to test connection: {str(e)}'}
    
    def _test_smtp_connection(self, config):
        """Test SMTP connection with given configuration"""
        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
            
            return {
                'success': True,
                'message': 'Email connection successful',
                'server': config['smtp_server'],
                'port': config['smtp_port']
            }
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False,
                'error': 'Authentication failed. Check email and password.',
                'help': 'For Gmail, use an App Password instead of your regular password.'
            }
        except smtplib.SMTPConnectError:
            return {
                'success': False,
                'error': 'Could not connect to SMTP server',
                'help': 'Check server address and port settings.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection test failed: {str(e)}'
            }
    
    def send_test_email(self, recipient_email=None):
        """Send a test email"""
        config = self.get_email_config()
        if 'error' in config:
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                full_config = json.load(f)
            
            recipient = recipient_email or full_config['email']
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = full_config['email']
            msg['To'] = recipient
            msg['Subject'] = 'TRAXOVO Email Configuration Test'
            
            body = f"""
This is a test email from your TRAXOVO system.

Configuration Details:
- Provider: {full_config['provider']}
- SMTP Server: {full_config['smtp_server']}:{full_config['smtp_port']}
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, your email configuration is working correctly.

Best regards,
TRAXOVO System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(full_config['smtp_server'], full_config['smtp_port'])
            if full_config.get('use_tls', True):
                server.starttls()
            server.login(full_config['email'], full_config['password'])
            server.send_message(msg)
            server.quit()
            
            return {
                'success': True,
                'message': f'Test email sent successfully to {recipient}',
                'recipient': recipient
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send test email: {str(e)}'
            }
    
    def _get_default_config(self):
        """Get default email configuration"""
        return {
            'provider': None,
            'email': None,
            'password_set': False,
            'smtp_server': None,
            'smtp_port': 587,
            'use_tls': True,
            'display_name': 'TRAXOVO System',
            'setup_required': True
        }
    
    def get_provider_instructions(self, provider):
        """Get setup instructions for specific email provider"""
        instructions = {
            'gmail': {
                'title': 'Gmail Configuration',
                'steps': [
                    '1. Enable 2-factor authentication on your Google account',
                    '2. Go to Google Account settings > Security > 2-Step Verification',
                    '3. Generate an App Password for "Mail"',
                    '4. Use your Gmail address and the App Password (not your regular password)',
                    '5. SMTP Server: smtp.gmail.com, Port: 587'
                ],
                'help_url': 'https://support.google.com/accounts/answer/185833'
            },
            'outlook': {
                'title': 'Outlook Configuration',
                'steps': [
                    '1. Use your Outlook.com email address',
                    '2. Use your regular Outlook password',
                    '3. SMTP Server: smtp-mail.outlook.com, Port: 587',
                    '4. Ensure "Less secure app access" is enabled if needed'
                ],
                'help_url': 'https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040'
            },
            'office365': {
                'title': 'Office 365 Configuration',
                'steps': [
                    '1. Use your Office 365 business email address',
                    '2. Use your Office 365 password',
                    '3. SMTP Server: smtp.office365.com, Port: 587',
                    '4. Contact your IT admin if authentication fails'
                ],
                'help_url': 'https://docs.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-office-365'
            }
        }
        
        return instructions.get(provider, {
            'title': 'Custom SMTP Configuration',
            'steps': [
                '1. Enter your SMTP server address',
                '2. Enter the correct port (usually 587 for TLS)',
                '3. Use your email credentials',
                '4. Contact your email provider for specific settings'
            ]
        })

# Global email manager instance
_email_manager = None

def get_email_manager():
    """Get global email manager instance"""
    global _email_manager
    if _email_manager is None:
        _email_manager = EmailConfigManager()
    return _email_manager

def get_email_configuration():
    """Get current email configuration"""
    manager = get_email_manager()
    return manager.get_email_config()

def save_email_configuration(config_data):
    """Save email configuration"""
    manager = get_email_manager()
    return manager.save_email_config(config_data)

def test_email_setup():
    """Test email configuration"""
    manager = get_email_manager()
    return manager.test_email_connection()

def send_test_email(recipient=None):
    """Send test email"""
    manager = get_email_manager()
    return manager.send_test_email(recipient)