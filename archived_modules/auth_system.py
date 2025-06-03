"""
TRAXOVO Authentication System
Enterprise user authentication with role-based access control
"""
import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize login manager
login_manager = LoginManager()

# User data (in production, this would be in a database)
USERS = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'email': 'admin@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOAdmin2025!'),
        'first_name': 'System',
        'last_name': 'Administrator',
        'role': 'admin',
        'department': 'IT',
        'is_active': True
    },
    'executive': {
        'id': 2,
        'username': 'executive',
        'email': 'executive@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOExec2025!'),
        'first_name': 'Executive',
        'last_name': 'Manager',
        'role': 'executive',
        'department': 'Management',
        'is_active': True
    },
    'controller': {
        'id': 3,
        'username': 'controller',
        'email': 'controller@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOCtrl2025!'),
        'first_name': 'Financial',
        'last_name': 'Controller',
        'role': 'controller',
        'department': 'Finance',
        'is_active': True
    },
    'estimating': {
        'id': 4,
        'username': 'estimating',
        'email': 'estimating@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOEst2025!'),
        'first_name': 'Project',
        'last_name': 'Estimator',
        'role': 'estimating',
        'department': 'Estimating',
        'is_active': True
    },
    'payroll': {
        'id': 5,
        'username': 'payroll',
        'email': 'payroll@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOPay2025!'),
        'first_name': 'Payroll',
        'last_name': 'Manager',
        'role': 'payroll',
        'department': 'HR',
        'is_active': True
    },
    'equipment': {
        'id': 6,
        'username': 'equipment',
        'email': 'equipment@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOEq2025!'),
        'first_name': 'Equipment',
        'last_name': 'Manager',
        'role': 'equipment',
        'department': 'Operations',
        'is_active': True
    },
    'viewer': {
        'id': 7,
        'username': 'viewer',
        'email': 'viewer@traxovo.com',
        'password_hash': generate_password_hash('TRAXOVOView2025!'),
        'first_name': 'View Only',
        'last_name': 'User',
        'role': 'viewer',
        'department': 'External',
        'is_active': True
    }
}

class User:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.role = user_data['role']
        self.department = user_data['department']
        self.is_active = user_data['is_active']
        self.last_login = datetime.utcnow()
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        if self.role == 'admin':
            return True
        return self.role == role
    
    def has_admin_access(self):
        return self.role in ['admin', 'executive']
    
    def get_display_name(self):
        return f"{self.first_name} {self.last_name}"

@login_manager.user_loader
def load_user(user_id):
    for username, user_data in USERS.items():
        if str(user_data['id']) == user_id:
            return User(user_data)
    return None

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role):
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.has_admin_access():
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS:
            user = User(USERS[username])
            if user.check_password(password) and user.is_active:
                login_user(user, remember=True)
                user.last_login = datetime.utcnow()
                flash(f'Welcome back, {user.get_display_name()}!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('auth.dashboard'))
            else:
                flash('Invalid credentials', 'error')
        else:
            flash('User not found', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard based on role"""
    return render_template('auth/dashboard.html', user=current_user)

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile management"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/admin')
@admin_required
def admin():
    """Admin panel"""
    return render_template('auth/admin.html', users=USERS, user=current_user, 
                         permissions=MODULE_PERMISSIONS, view_only=VIEW_ONLY_MODULES)

@auth_bp.route('/admin/update_user/<username>', methods=['POST'])
@admin_required
def update_user_permissions(username):
    """Update user permissions"""
    if username in USERS:
        new_role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        if new_role in MODULE_PERMISSIONS:
            USERS[username]['role'] = new_role
            USERS[username]['is_active'] = is_active
            flash(f'Updated permissions for {username}', 'success')
        else:
            flash('Invalid role selected', 'error')
    else:
        flash('User not found', 'error')
    
    return redirect(url_for('auth.admin'))

@auth_bp.route('/job-zones')
@login_required
def job_zones():
    """Job Zones Management Module"""
    if not (can_access_module(current_user.role, 'job_zones') or 
            can_access_module(current_user.role, 'job_zones_view')):
        flash('Access denied to Job Zones module', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Check if view-only
    is_view_only = current_user.role == 'viewer'
    
    return render_template('modules/job_zones.html', 
                         user=current_user, 
                         is_view_only=is_view_only)

# Module access control
MODULE_PERMISSIONS = {
    'admin': ['all'],
    'executive': ['executive_dashboard', 'executive_reports', 'analytics', 'billing', 'fleet_map', 'job_zones', 'user_management'],
    'controller': ['billing', 'analytics', 'revenue_reports', 'asset_profitability', 'job_zones'],
    'estimating': ['cost_analysis', 'project_estimation', 'asset_utilization', 'job_zones'],
    'payroll': ['attendance', 'driver_management', 'time_tracking'],
    'equipment': ['fleet_map', 'asset_manager', 'equipment_lifecycle', 'maintenance', 'job_zones'],
    'viewer': ['dashboard', 'fleet_map_view', 'analytics_view', 'billing_view', 'job_zones_view'],
    'user': ['dashboard', 'basic_reports']
}

# View-only permissions (no edit/delete capabilities)
VIEW_ONLY_MODULES = ['fleet_map_view', 'analytics_view', 'billing_view', 'job_zones_view']

def can_access_module(user_role, module):
    """Check if user role can access specific module"""
    if user_role == 'admin':
        return True
    return module in MODULE_PERMISSIONS.get(user_role, [])

def init_auth(app):
    """Initialize authentication system"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprint with app
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Add template globals
    @app.template_global()
    def can_user_access_module(module):
        if current_user.is_authenticated:
            return can_access_module(current_user.role, module)
        return False
    
    print("TRAXOVO Authentication System initialized")
    print("Default users created:")
    for username, user_data in USERS.items():
        print(f"  {username}: {user_data['role']} ({user_data['email']})")
    
    return login_manager