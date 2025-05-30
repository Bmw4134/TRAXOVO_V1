"""
Simple Authentication System for TRAXOVO
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

simple_auth_bp = Blueprint('simple_auth', __name__)

# Default user credentials
DEFAULT_USERS = {
    'admin': {
        'password': 'admin',
        'email': 'admin@traxovo.com',
        'role': 'system_admin',
        'name': 'System Administrator'
    },
    'executive': {
        'password': 'executive', 
        'email': 'executive@traxovo.com',
        'role': 'executive',
        'name': 'Executive User'
    },
    'controller': {
        'password': 'controller',
        'email': 'controller@traxovo.com', 
        'role': 'controller',
        'name': 'Controller User'
    },
    'estimating': {
        'password': 'estimating',
        'email': 'estimating@traxovo.com',
        'role': 'estimating', 
        'name': 'Estimating User'
    },
    'payroll': {
        'password': 'payroll',
        'email': 'payroll@traxovo.com',
        'role': 'payroll',
        'name': 'Payroll User'
    },
    'equipment': {
        'password': 'equipment',
        'email': 'equipment@traxovo.com',
        'role': 'equipment',
        'name': 'Equipment User'
    },
    'viewer': {
        'password': 'viewer',
        'email': 'viewer@traxovo.com',
        'role': 'viewer', 
        'name': 'Viewer User'
    }
}

@simple_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login requests"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        # Check credentials
        if username in DEFAULT_USERS:
            user_data = DEFAULT_USERS[username]
            if password == user_data['password']:
                # Set session
                session['authenticated'] = True
                session['user_id'] = username
                session['user_role'] = user_data['role']
                session['user_name'] = user_data['name']
                session['user_email'] = user_data['email']
                session['login_time'] = datetime.now().isoformat()
                session.permanent = True
                
                # Redirect to dashboard
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('Invalid username', 'error')
    
    return render_template('login.html')

@simple_auth_bp.route('/logout')
def logout():
    """Handle logout requests"""
    session.clear()
    return redirect(url_for('simple_auth.login'))

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('simple_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user info from session"""
    if session.get('authenticated'):
        return {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('user_role'),
            'login_time': session.get('login_time')
        }
    return None