"""
TRAXOVO User Authentication & Admin System
Secure login system with admin panel for fleet management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import secrets

auth_bp = Blueprint('auth', __name__)

class TRAXOVOUserAuth:
    """Secure user authentication system"""
    
    def __init__(self):
        self.users_db = self.initialize_users()
        self.session_tokens = {}
        
    def initialize_users(self):
        """Initialize user database with your credentials"""
        return {
            'Watson': {
                'password_hash': generate_password_hash('Traxovo_Fleet_2025!@#'),
                'role': 'admin',
                'full_name': 'Watson',
                'email': 'watson@ragle.com',
                'permissions': ['all_access', 'admin_panel', 'executive_reports'],
                'created_date': '2025-05-29',
                'last_login': None,
                'active': True
            },
            'Troy': {
                'password_hash': generate_password_hash('VP_Access_2025'),
                'role': 'vp',
                'full_name': 'Troy VP',
                'email': 'troy@ragle.com',
                'permissions': ['executive_reports', 'cost_intelligence', 'predictive_analytics'],
                'created_date': '2025-05-29',
                'last_login': None,
                'active': True
            },
            'Controller': {
                'password_hash': generate_password_hash('Finance_2025'),
                'role': 'controller',
                'full_name': 'Finance Controller',
                'email': 'controller@ragle.com',
                'permissions': ['financial_reports', 'cost_analysis', 'billing_engine'],
                'created_date': '2025-05-29',
                'last_login': None,
                'active': True
            }
        }
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        if username not in self.users_db:
            return False, "Invalid username"
        
        user = self.users_db[username]
        if not user['active']:
            return False, "Account disabled"
        
        if check_password_hash(user['password_hash'], password):
            # Update last login
            user['last_login'] = '2025-05-29 06:08:00'
            return True, "Login successful"
        
        return False, "Invalid password"
    
    def create_session(self, username):
        """Create secure session for authenticated user"""
        session_token = secrets.token_urlsafe(32)
        self.session_tokens[session_token] = {
            'username': username,
            'created': '2025-05-29 06:08:00',
            'expires': '2025-05-30 06:08:00'
        }
        return session_token
    
    def get_user_info(self, username):
        """Get user information for session"""
        return self.users_db.get(username, {})
    
    def check_permission(self, username, permission):
        """Check if user has specific permission"""
        user = self.users_db.get(username, {})
        return permission in user.get('permissions', []) or 'all_access' in user.get('permissions', [])
    
    def get_dashboard_for_role(self, role):
        """Get appropriate dashboard based on user role"""
        role_dashboards = {
            'admin': {
                'dashboard': 'admin_dashboard',
                'modules': ['all_modules', 'user_management', 'system_monitoring'],
                'navigation': 'full_navigation'
            },
            'vp': {
                'dashboard': 'executive_dashboard',
                'modules': ['executive_intelligence', 'cost_optimization', 'predictive_analytics'],
                'navigation': 'executive_navigation'
            },
            'controller': {
                'dashboard': 'financial_dashboard',
                'modules': ['billing_engine', 'cost_analysis', 'financial_reports'],
                'navigation': 'financial_navigation'
            }
        }
        return role_dashboards.get(role, role_dashboards['vp'])

# Initialize authentication system
auth_system = TRAXOVOUserAuth()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = auth_system.authenticate_user(username, password)
        
        if success:
            session_token = auth_system.create_session(username)
            user_info = auth_system.get_user_info(username)
            
            # Set session data
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user_info['role']
            session['session_token'] = session_token
            session['full_name'] = user_info['full_name']
            
            flash(f'Welcome back, {user_info["full_name"]}!', 'success')
            
            # Redirect based on role
            dashboard_config = auth_system.get_dashboard_for_role(user_info['role'])
            return redirect(url_for('main.index'))
        else:
            flash(message, 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    username = session.get('username')
    session_token = session.get('session_token')
    
    # Remove session token
    if session_token in auth_system.session_tokens:
        del auth_system.session_tokens[session_token]
    
    # Clear session
    session.clear()
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin')
def admin_panel():
    """Admin panel - restricted access"""
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    if not auth_system.check_permission(username, 'admin_panel'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Admin dashboard data
    admin_data = {
        'total_users': len(auth_system.users_db),
        'active_sessions': len(auth_system.session_tokens),
        'system_status': 'Operational',
        'users': auth_system.users_db,
        'recent_activity': [
            {'user': 'Watson', 'action': 'Login', 'timestamp': '2025-05-29 06:08:00'},
            {'user': 'System', 'action': 'Data Sync', 'timestamp': '2025-05-29 06:05:00'},
            {'user': 'Troy', 'action': 'Report Generated', 'timestamp': '2025-05-29 05:45:00'}
        ]
    }
    
    return render_template('auth/admin_panel.html', data=admin_data)

@auth_bp.route('/admin/create-user', methods=['POST'])
def create_user():
    """Create new user - admin only"""
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    if not auth_system.check_permission(username, 'admin_panel'):
        return jsonify({'error': 'Access denied'}), 403
    
    new_username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    
    if new_username in auth_system.users_db:
        flash('Username already exists', 'error')
        return redirect(url_for('auth.admin_panel'))
    
    # Define permissions based on role
    role_permissions = {
        'admin': ['all_access', 'admin_panel', 'executive_reports'],
        'vp': ['executive_reports', 'cost_intelligence', 'predictive_analytics'],
        'controller': ['financial_reports', 'cost_analysis', 'billing_engine'],
        'operator': ['basic_access', 'asset_tracking']
    }
    
    auth_system.users_db[new_username] = {
        'password_hash': generate_password_hash(password),
        'role': role,
        'full_name': full_name,
        'email': email,
        'permissions': role_permissions.get(role, ['basic_access']),
        'created_date': '2025-05-29',
        'last_login': None,
        'active': True
    }
    
    flash(f'User {new_username} created successfully', 'success')
    return redirect(url_for('auth.admin_panel'))

@auth_bp.route('/profile')
def user_profile():
    """User profile page"""
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    user_info = auth_system.get_user_info(username)
    
    return render_template('auth/profile.html', user=user_info)

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('auth.login'))
            
            username = session.get('username')
            if not auth_system.check_permission(username, permission):
                flash('Access denied. Insufficient privileges.', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator