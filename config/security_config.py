"""
TRAXOVO Security Configuration
Enterprise-grade authentication with demo mode toggle
"""

import os
from datetime import timedelta

class SecurityConfig:
    # Demo mode toggle - set to False for production security
    DEMO_MODE = os.environ.get('TRAXOVO_DEMO_MODE', 'True').lower() == 'true'
    
    # Session security
    SESSION_TIMEOUT = timedelta(hours=8)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Password requirements for production
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_SPECIAL_CHARS = True
    REQUIRE_NUMBERS = True
    
    # User roles and permissions
    USER_ROLES = {
        'admin': {
            'permissions': ['all'],
            'access_level': 'full',
            'can_modify_users': True,
            'can_export_data': True
        },
        'executive': {
            'permissions': ['dashboard', 'reports', 'billing'],
            'access_level': 'executive',
            'can_modify_users': False,
            'can_export_data': True
        },
        'controller': {
            'permissions': ['billing', 'reports', 'attendance'],
            'access_level': 'controller',
            'can_modify_users': False,
            'can_export_data': True
        },
        'estimating': {
            'permissions': ['dashboard', 'assets', 'reports'],
            'access_level': 'estimating',
            'can_modify_users': False,
            'can_export_data': False
        },
        'payroll': {
            'permissions': ['attendance', 'reports'],
            'access_level': 'payroll',
            'can_modify_users': False,
            'can_export_data': False
        },
        'equipment': {
            'permissions': ['assets', 'dashboard'],
            'access_level': 'equipment',
            'can_modify_users': False,
            'can_export_data': False
        },
        'viewer': {
            'permissions': ['dashboard'],
            'access_level': 'viewer',
            'can_modify_users': False,
            'can_export_data': False
        }
    }
    
    # Production user credentials (hashed in real deployment)
    PRODUCTION_USERS = {
        'admin': {
            'password_hash': 'pbkdf2:sha256:260000$...',  # Would be properly hashed
            'email': 'admin@traxovo.com',
            'role': 'admin'
        }
        # Add other production users here
    }
    
    # Demo credentials (only used when DEMO_MODE = True)
    DEMO_CREDENTIALS = {
        'admin': 'admin',
        'executive': 'executive', 
        'controller': 'controller',
        'estimating': 'estimating',
        'payroll': 'payroll',
        'equipment': 'equipment',
        'viewer': 'viewer'
    }
    
    @classmethod
    def is_demo_mode(cls):
        return cls.DEMO_MODE
    
    @classmethod
    def get_user_permissions(cls, role):
        return cls.USER_ROLES.get(role, cls.USER_ROLES['viewer'])
    
    @classmethod
    def validate_access(cls, user_role, required_permission):
        """Check if user role has required permission"""
        user_perms = cls.get_user_permissions(user_role)
        return (required_permission in user_perms['permissions'] or 
                'all' in user_perms['permissions'])