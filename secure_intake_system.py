"""
Secure Intake Form System for TRAXOVO
Email/SMS distribution with direct feedback collection - no dev links required
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app import db
from models_clean import PlatformData

class SecureIntakeSystem:
    """Secure intake form distribution and collection system"""
    
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.base_url = "https://jddconsulting.replit.app"  # Current deployment
        self.intake_tokens = {}  # Store temporary access tokens
    
    def generate_secure_token(self, email):
        """Generate secure one-time access token"""
        
        # Generate random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Store token with expiration (24 hours)
        token_data = {
            'email': email,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            'used': False,
            'ip_address': None
        }
        
        # Store in database
        try:
            tokens_record = PlatformData.query.filter_by(data_type='intake_tokens').first()
            
            if tokens_record:
                tokens_data = tokens_record.data_content
                tokens_data[token] = token_data
                tokens_record.data_content = tokens_data
                tokens_record.updated_at = datetime.utcnow()
            else:
                tokens_record = PlatformData(
                    data_type='intake_tokens',
                    data_content={token: token_data}
                )
                db.session.add(tokens_record)
            
            db.session.commit()
            return token
            
        except Exception as e:
            print(f"Token generation failed: {e}")
            return None
    
    def validate_token(self, token):
        """Validate access token"""
        
        try:
            tokens_record = PlatformData.query.filter_by(data_type='intake_tokens').first()
            
            if not tokens_record:
                return False
            
            tokens_data = tokens_record.data_content
            
            if token not in tokens_data:
                return False
            
            token_info = tokens_data[token]
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_info['expires_at'])
            if datetime.utcnow() > expires_at:
                return False
            
            # Check if token already used
            if token_info.get('used', False):
                return False
            
            return True
            
        except Exception as e:
            print(f"Token validation failed: {e}")
            return False
    
    def mark_token_used(self, token, ip_address=None):
        """Mark token as used"""
        
        try:
            tokens_record = PlatformData.query.filter_by(data_type='intake_tokens').first()
            
            if tokens_record and token in tokens_record.data_content:
                tokens_data = tokens_record.data_content
                tokens_data[token]['used'] = True
                tokens_data[token]['used_at'] = datetime.utcnow().isoformat()
                if ip_address:
                    tokens_data[token]['ip_address'] = ip_address
                
                tokens_record.data_content = tokens_data
                tokens_record.updated_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            print(f"Failed to mark token as used: {e}")
    
    def send_intake_form_email(self, recipient_email, recipient_name=None):
        """Send intake form via email - bypasses organizational link filters"""
        
        if not self.sendgrid_api_key:
            return {
                'status': 'error',
                'message': 'SendGrid API key not configured. Please add SENDGRID_API_KEY to environment.'
            }
        
        # Generate secure token
        token = self.generate_secure_token(recipient_email)
        
        if not token:
            return {'status': 'error', 'message': 'Failed to generate access token'}
        
        # Create secure intake form URL
        intake_url = f"{self.base_url}/intake/{token}"
        
        # Create email content
        name_display = recipient_name or recipient_email.split('@')[0]
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TRAXOVO Automation Request</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .brand {{ font-size: 24px; font-weight: bold; color: #2563eb; margin-bottom: 10px; }}
        .subtitle {{ color: #6b7280; }}
        .content {{ line-height: 1.6; color: #374151; }}
        .cta-button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .security-note {{ background: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0; 
                         font-size: 14px; color: #6b7280; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; 
                  font-size: 12px; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">⚡ TRAXOVO</div>
            <div class="subtitle">Enterprise Intelligence Platform</div>
        </div>
        
        <div class="content">
            <h2>Hi {name_display},</h2>
            
            <p>You've been invited to help shape the future of automation at our organization.</p>
            
            <p>We're building an intelligent automation platform and need your input on what tasks you'd like to automate in your daily work.</p>
            
            <p><strong>This takes only 2-3 minutes and your feedback directly impacts what gets built.</strong></p>
            
            <div style="text-align: center;">
                <a href="{intake_url}" class="cta-button">Share Your Automation Ideas</a>
            </div>
            
            <div class="security-note">
                <strong>🔒 Secure Access:</strong> This link is unique to you and expires in 24 hours. 
                No login credentials required - just click and share your thoughts.
            </div>
            
            <p>Your responses will help us prioritize which automation features to build first, ensuring we create tools that actually solve your daily challenges.</p>
            
            <p>Questions? Just reply to this email.</p>
            
            <p>Thanks for helping us build something useful!</p>
            
            <p>— The TRAXOVO Development Team</p>
        </div>
        
        <div class="footer">
            This invitation expires in 24 hours. If you have trouble accessing the form, please contact your IT administrator.
        </div>
    </div>
</body>
</html>
        """
        
        try:
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            message = Mail(
                from_email=('noreply@traxovo.com', 'TRAXOVO Platform'),
                to_emails=recipient_email,
                subject='Help Us Build Your Perfect Automation Tool (2 min survey)',
                html_content=html_content
            )
            
            response = sg.send(message)
            
            # Log the distribution
            self._log_distribution(recipient_email, 'email', token)
            
            return {
                'status': 'success',
                'message': f'Intake form sent to {recipient_email}',
                'token': token,
                'expires_in': '24 hours'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Email sending failed: {str(e)}'
            }
    
    def send_bulk_intake_forms(self, recipient_list):
        """Send intake forms to multiple recipients"""
        
        results = {
            'successful': [],
            'failed': [],
            'total_sent': 0
        }
        
        for recipient in recipient_list:
            if isinstance(recipient, str):
                email = recipient
                name = None
            else:
                email = recipient.get('email')
                name = recipient.get('name')
            
            result = self.send_intake_form_email(email, name)
            
            if result['status'] == 'success':
                results['successful'].append(email)
                results['total_sent'] += 1
            else:
                results['failed'].append({
                    'email': email,
                    'error': result['message']
                })
        
        return results
    
    def save_intake_response(self, token, response_data, ip_address=None):
        """Save intake form response"""
        
        # Validate token first
        if not self.validate_token(token):
            return {'status': 'error', 'message': 'Invalid or expired access token'}
        
        # Mark token as used
        self.mark_token_used(token, ip_address)
        
        # Get token info for email
        tokens_record = PlatformData.query.filter_by(data_type='intake_tokens').first()
        token_info = tokens_record.data_content.get(token, {})
        submitter_email = token_info.get('email', 'unknown')
        
        # Prepare response data
        intake_response = {
            'token': token,
            'submitter_email': submitter_email,
            'submission_time': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'responses': response_data,
            'development_insights': self._extract_development_insights(response_data)
        }
        
        try:
            # Store response
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            
            if responses_record:
                existing_responses = responses_record.data_content.get('responses', [])
                existing_responses.append(intake_response)
                responses_record.data_content = {'responses': existing_responses}
                responses_record.updated_at = datetime.utcnow()
            else:
                responses_record = PlatformData(
                    data_type='intake_responses',
                    data_content={'responses': [intake_response]}
                )
                db.session.add(responses_record)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'message': 'Response saved successfully',
                'insights_generated': True
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to save response: {str(e)}'}
    
    def _extract_development_insights(self, response_data):
        """Extract actionable development insights from responses"""
        
        insights = {
            'priority_features': [],
            'technical_requirements': [],
            'integration_needs': [],
            'complexity_indicators': []
        }
        
        # Analyze task descriptions for patterns
        task_description = response_data.get('task_description', '').lower()
        
        # Feature priority detection
        if any(word in task_description for word in ['daily', 'every day', 'routine']):
            insights['priority_features'].append('daily_automation_scheduler')
        
        if any(word in task_description for word in ['data', 'report', 'analysis']):
            insights['priority_features'].append('data_processing_pipeline')
        
        if any(word in task_description for word in ['email', 'notification', 'alert']):
            insights['priority_features'].append('notification_system')
        
        # Technical requirements detection
        if any(word in task_description for word in ['api', 'integration', 'connect']):
            insights['technical_requirements'].append('api_integration_framework')
        
        if any(word in task_description for word in ['database', 'storage', 'save']):
            insights['technical_requirements'].append('data_storage_system')
        
        # Integration needs
        data_sources = response_data.get('data_sources_needed', [])
        if data_sources:
            insights['integration_needs'].extend(data_sources)
        
        # Complexity indicators
        complexity = response_data.get('automation_complexity', 'simple')
        if complexity in ['complex', 'advanced']:
            insights['complexity_indicators'].append('requires_advanced_workflow_engine')
        
        return insights
    
    def get_development_brain_feed(self):
        """Generate development insights from all intake responses"""
        
        try:
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            
            if not responses_record:
                return {'message': 'No intake responses available yet'}
            
            all_responses = responses_record.data_content.get('responses', [])
            
            # Aggregate insights
            brain_feed = {
                'total_responses': len(all_responses),
                'feature_demand': {},
                'technical_priorities': {},
                'integration_requests': {},
                'development_roadmap': [],
                'immediate_actions': []
            }
            
            # Process all insights
            for response in all_responses:
                insights = response.get('development_insights', {})
                
                # Count feature demands
                for feature in insights.get('priority_features', []):
                    brain_feed['feature_demand'][feature] = brain_feed['feature_demand'].get(feature, 0) + 1
                
                # Count technical requirements
                for tech in insights.get('technical_requirements', []):
                    brain_feed['technical_priorities'][tech] = brain_feed['technical_priorities'].get(tech, 0) + 1
                
                # Count integration needs
                for integration in insights.get('integration_needs', []):
                    brain_feed['integration_requests'][integration] = brain_feed['integration_requests'].get(integration, 0) + 1
            
            # Generate development roadmap
            if brain_feed['feature_demand']:
                top_feature = max(brain_feed['feature_demand'], key=brain_feed['feature_demand'].get)
                brain_feed['development_roadmap'].append(f"Priority 1: Build {top_feature}")
            
            if brain_feed['technical_priorities']:
                top_tech = max(brain_feed['technical_priorities'], key=brain_feed['technical_priorities'].get)
                brain_feed['development_roadmap'].append(f"Priority 2: Implement {top_tech}")
            
            # Generate immediate actions
            if len(all_responses) >= 5:
                brain_feed['immediate_actions'].append("Sufficient data collected - begin development sprint")
            else:
                brain_feed['immediate_actions'].append(f"Need {5 - len(all_responses)} more responses for reliable insights")
            
            return brain_feed
            
        except Exception as e:
            return {'error': f'Brain feed generation failed: {str(e)}'}
    
    def _log_distribution(self, recipient, method, token):
        """Log intake form distribution"""
        
        try:
            log_entry = {
                'recipient': recipient,
                'method': method,
                'token': token,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            log_record = PlatformData.query.filter_by(data_type='intake_distribution_log').first()
            
            if log_record:
                existing_logs = log_record.data_content.get('logs', [])
                existing_logs.append(log_entry)
                log_record.data_content = {'logs': existing_logs}
                log_record.updated_at = datetime.utcnow()
            else:
                log_record = PlatformData(
                    data_type='intake_distribution_log',
                    data_content={'logs': [log_entry]}
                )
                db.session.add(log_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to log distribution: {e}")

# Global intake system
secure_intake = SecureIntakeSystem()

def send_intake_email(email, name=None):
    """Send secure intake form via email"""
    return secure_intake.send_intake_form_email(email, name)

def send_bulk_intake_emails(recipient_list):
    """Send intake forms to multiple recipients"""
    return secure_intake.send_bulk_intake_forms(recipient_list)

def validate_intake_token(token):
    """Validate intake access token"""
    return secure_intake.validate_token(token)

def save_intake_response(token, response_data, ip_address=None):
    """Save intake form response"""
    return secure_intake.save_intake_response(token, response_data, ip_address)

def get_development_insights():
    """Get development insights from intake responses"""
    return secure_intake.get_development_brain_feed()