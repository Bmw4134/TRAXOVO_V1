"""
NEXUS User Administration Portal
Complete user management with role-based access and password reset
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

class NexusUserAdmin:
    """Complete user administration system"""
    
    def __init__(self):
        self.users = {}
        self.password_reset_tokens = {}
        self.user_roles = {
            'admin': ['all_access', 'user_management', 'system_control', 'automation_access'],
            'manager': ['dashboard_access', 'automation_access', 'user_view'],
            'user': ['dashboard_access', 'automation_access'],
            'viewer': ['dashboard_access']
        }
        self.load_users()
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default NEXUS users"""
        
        default_users = [
            {
                'username': 'nexus_admin',
                'password': 'nexus2025',
                'email': 'admin@nexus.platform',
                'role': 'admin',
                'department': 'system_administration'
            },
            {
                'username': 'nexus_demo',
                'password': 'demo2025',
                'email': 'demo@nexus.platform',
                'role': 'user',
                'department': 'automation_testing'
            },
            {
                'username': 'automation_manager',
                'password': 'automation2025',
                'email': 'manager@nexus.platform',
                'role': 'manager',
                'department': 'automation_operations'
            }
        ]
        
        for user_data in default_users:
            if user_data['username'] not in self.users:
                self.create_user(
                    user_data['username'],
                    user_data['password'],
                    user_data['email'],
                    user_data['role'],
                    user_data['department']
                )
    
    def create_user(self, username, password, email, role='user', department='general'):
        """Create new user account"""
        
        if username in self.users:
            return {'status': 'error', 'message': 'Username already exists'}
        
        if role not in self.user_roles:
            return {'status': 'error', 'message': 'Invalid role specified'}
        
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'email': email,
            'role': role,
            'department': department,
            'permissions': self.user_roles[role],
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'is_active': True,
            'automation_preferences': self._get_default_automation_preferences(department),
            'failed_login_attempts': 0,
            'account_locked': False
        }
        
        self.users[username] = user_data
        self._save_users()
        
        return {
            'status': 'success',
            'username': username,
            'role': role,
            'permissions': self.user_roles[role]
        }
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        
        if username not in self.users:
            return {'status': 'failed', 'message': 'User not found'}
        
        user = self.users[username]
        
        if user.get('account_locked', False):
            return {'status': 'failed', 'message': 'Account locked due to multiple failed attempts'}
        
        if not user.get('is_active', True):
            return {'status': 'failed', 'message': 'Account deactivated'}
        
        if check_password_hash(user['password_hash'], password):
            # Successful login
            user['last_login'] = datetime.utcnow().isoformat()
            user['failed_login_attempts'] = 0
            self._save_users()
            
            return {
                'status': 'success',
                'username': username,
                'role': user['role'],
                'permissions': user['permissions'],
                'department': user['department'],
                'automation_preferences': user.get('automation_preferences', {})
            }
        else:
            # Failed login
            user['failed_login_attempts'] = user.get('failed_login_attempts', 0) + 1
            
            if user['failed_login_attempts'] >= 5:
                user['account_locked'] = True
                self._save_users()
                return {'status': 'failed', 'message': 'Account locked due to multiple failed attempts'}
            
            self._save_users()
            return {'status': 'failed', 'message': 'Invalid password'}
    
    def reset_password_request(self, username_or_email):
        """Generate password reset token"""
        
        user = None
        username = None
        
        # Find user by username or email
        for uname, udata in self.users.items():
            if uname == username_or_email or udata.get('email') == username_or_email:
                user = udata
                username = uname
                break
        
        if not user:
            return {'status': 'failed', 'message': 'User not found'}
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        self.password_reset_tokens[reset_token] = {
            'username': username,
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'used': False
        }
        
        return {
            'status': 'success',
            'reset_token': reset_token,
            'expires_in': '1 hour',
            'message': 'Password reset token generated'
        }
    
    def reset_password_confirm(self, reset_token, new_password):
        """Confirm password reset with token"""
        
        if reset_token not in self.password_reset_tokens:
            return {'status': 'failed', 'message': 'Invalid reset token'}
        
        token_data = self.password_reset_tokens[reset_token]
        
        if token_data.get('used', False):
            return {'status': 'failed', 'message': 'Reset token already used'}
        
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            return {'status': 'failed', 'message': 'Reset token expired'}
        
        username = token_data['username']
        
        if username not in self.users:
            return {'status': 'failed', 'message': 'User not found'}
        
        # Update password
        self.users[username]['password_hash'] = generate_password_hash(new_password)
        self.users[username]['failed_login_attempts'] = 0
        self.users[username]['account_locked'] = False
        
        # Mark token as used
        token_data['used'] = True
        
        self._save_users()
        
        return {
            'status': 'success',
            'username': username,
            'message': 'Password reset successfully'
        }
    
    def get_user_list(self):
        """Get list of all users for administration"""
        
        user_list = []
        for username, user_data in self.users.items():
            user_list.append({
                'username': username,
                'email': user_data.get('email', ''),
                'role': user_data.get('role', 'user'),
                'department': user_data.get('department', 'general'),
                'last_login': user_data.get('last_login'),
                'is_active': user_data.get('is_active', True),
                'account_locked': user_data.get('account_locked', False),
                'failed_attempts': user_data.get('failed_login_attempts', 0)
            })
        
        return {
            'users': user_list,
            'total_count': len(user_list),
            'active_count': len([u for u in user_list if u['is_active']]),
            'locked_count': len([u for u in user_list if u['account_locked']])
        }
    
    def update_user(self, username, updates):
        """Update user information"""
        
        if username not in self.users:
            return {'status': 'error', 'message': 'User not found'}
        
        allowed_updates = ['email', 'role', 'department', 'is_active']
        
        for key, value in updates.items():
            if key in allowed_updates:
                if key == 'role' and value in self.user_roles:
                    self.users[username][key] = value
                    self.users[username]['permissions'] = self.user_roles[value]
                elif key != 'role':
                    self.users[username][key] = value
        
        self._save_users()
        
        return {
            'status': 'success',
            'username': username,
            'updated_fields': list(updates.keys())
        }
    
    def unlock_user_account(self, username):
        """Unlock locked user account"""
        
        if username not in self.users:
            return {'status': 'error', 'message': 'User not found'}
        
        self.users[username]['account_locked'] = False
        self.users[username]['failed_login_attempts'] = 0
        self._save_users()
        
        return {'status': 'success', 'username': username, 'message': 'Account unlocked'}
    
    def delete_user(self, username):
        """Delete user account"""
        
        if username not in self.users:
            return {'status': 'error', 'message': 'User not found'}
        
        if username == 'nexus_admin':
            return {'status': 'error', 'message': 'Cannot delete admin user'}
        
        del self.users[username]
        self._save_users()
        
        return {'status': 'success', 'username': username, 'message': 'User deleted'}
    
    def _get_default_automation_preferences(self, department):
        """Get default automation preferences by department"""
        
        department_preferences = {
            'system_administration': {
                'preferred_automations': ['system_monitoring', 'backup_automation', 'security_checks'],
                'notification_preferences': ['email', 'dashboard'],
                'automation_complexity': 'advanced'
            },
            'automation_operations': {
                'preferred_automations': ['workflow_automation', 'data_processing', 'report_generation'],
                'notification_preferences': ['email', 'dashboard', 'sms'],
                'automation_complexity': 'intermediate'
            },
            'automation_testing': {
                'preferred_automations': ['testing_automation', 'demo_workflows', 'simple_tasks'],
                'notification_preferences': ['dashboard'],
                'automation_complexity': 'basic'
            },
            'general': {
                'preferred_automations': ['basic_automation', 'timecard_entry', 'email_automation'],
                'notification_preferences': ['dashboard'],
                'automation_complexity': 'basic'
            }
        }
        
        return department_preferences.get(department, department_preferences['general'])
    
    def _save_users(self):
        """Save users to database"""
        
        try:
            from app_nexus import db, PlatformData
            
            users_record = PlatformData.query.filter_by(data_type='nexus_users').first()
            if users_record:
                users_record.data_content = self.users
                users_record.updated_at = datetime.utcnow()
            else:
                users_record = PlatformData(
                    data_type='nexus_users',
                    data_content=self.users
                )
                db.session.add(users_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"User save failed: {str(e)}")
    
    def load_users(self):
        """Load users from database"""
        
        try:
            from app_nexus import db, PlatformData
            
            users_record = PlatformData.query.filter_by(data_type='nexus_users').first()
            if users_record and users_record.data_content:
                self.users = users_record.data_content
            
        except Exception as e:
            print(f"User loading failed: {str(e)}")
            self.users = {}

# Global user admin system
nexus_user_admin = NexusUserAdmin()

def authenticate_nexus_user(username, password):
    """Authenticate NEXUS user"""
    return nexus_user_admin.authenticate_user(username, password)

def create_nexus_user(username, password, email, role='user', department='general'):
    """Create new NEXUS user"""
    return nexus_user_admin.create_user(username, password, email, role, department)

def get_nexus_users():
    """Get all NEXUS users"""
    return nexus_user_admin.get_user_list()

def reset_nexus_password(username_or_email):
    """Request password reset"""
    return nexus_user_admin.reset_password_request(username_or_email)

def confirm_nexus_password_reset(token, new_password):
    """Confirm password reset"""
    return nexus_user_admin.reset_password_confirm(token, new_password)