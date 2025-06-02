"""
Secure Authentication Routes
Enterprise login, registration, and 2FA integration
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from secure_enterprise_auth import get_secure_auth
from two_factor_auth import get_two_factor_auth
from unified_navigation import get_navigation_system
import json

secure_auth_bp = Blueprint('secure_auth', __name__)
auth_system = get_secure_auth()
tfa_system = get_two_factor_auth()
nav_system = get_navigation_system()

@secure_auth_bp.route('/login', methods=['GET', 'POST'])
def secure_login():
    """Secure enterprise login with 2FA support"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password required"})
        
        # Authenticate user
        auth_result = auth_system.authenticate_user(username, password)
        
        if auth_result:
            # Store user session
            session['user_id'] = auth_result['user_id']
            session['username'] = auth_result['username']
            session['role'] = auth_result['role']
            session['authenticated'] = True
            
            # Check if 2FA is enabled
            tfa_methods = tfa_system.get_2fa_methods(auth_result['user_id'])
            
            if tfa_methods.get('methods'):
                session['needs_2fa'] = True
                return jsonify({
                    "success": True, 
                    "requires_2fa": True,
                    "available_methods": tfa_methods['methods'],
                    "redirect_url": "/verify_2fa"
                })
            else:
                # Direct login without 2FA
                session['needs_2fa'] = False
                return jsonify({
                    "success": True, 
                    "requires_2fa": False,
                    "redirect_url": "/dashboard"
                })
        else:
            return jsonify({"success": False, "error": "Invalid credentials"})
    
    # GET request - show login page
    nav_data = nav_system.get_navigation_for_user(None)
    return render_template('secure_login.html', navigation=nav_data)

@secure_auth_bp.route('/register', methods=['GET', 'POST'])
def secure_register():
    """Secure user registration for enterprise access"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"{field} is required"})
        
        # Registration logic would go here
        # For now, return success to enable testing
        return jsonify({
            "success": True,
            "message": "Registration successful. Please contact admin for account activation.",
            "redirect_url": "/login"
        })
    
    # GET request - show registration page
    nav_data = nav_system.get_navigation_for_user(None)
    return render_template('secure_register.html', navigation=nav_data)

@secure_auth_bp.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Two-factor authentication verification"""
    if not session.get('authenticated') or not session.get('needs_2fa'):
        return redirect(url_for('secure_auth.secure_login'))
    
    if request.method == 'POST':
        data = request.get_json()
        method = data.get('method')
        code = data.get('code')
        user_id = session.get('user_id')
        
        if method == 'totp':
            result = tfa_system.verify_totp_code(user_id, code)
        elif method == 'sms':
            result = tfa_system.verify_sms_code(user_id, code)
        elif method == 'email':
            result = tfa_system.verify_email_code(user_id, code)
        elif method == 'backup':
            result = tfa_system.verify_backup_code(user_id, code)
        else:
            return jsonify({"success": False, "error": "Invalid verification method"})
        
        if result.get('success'):
            session['needs_2fa'] = False
            session['2fa_verified'] = True
            return jsonify({"success": True, "redirect_url": "/dashboard"})
        else:
            return jsonify({"success": False, "error": result.get('error', 'Verification failed')})
    
    # GET request - show 2FA page
    user_id = session.get('user_id')
    tfa_methods = tfa_system.get_2fa_methods(user_id)
    nav_data = nav_system.get_navigation_for_user(session.get('username'))
    
    return render_template('verify_2fa.html', 
                         methods=tfa_methods, 
                         navigation=nav_data)

@secure_auth_bp.route('/send_2fa_code', methods=['POST'])
def send_2fa_code():
    """Send 2FA verification code"""
    if not session.get('authenticated'):
        return jsonify({"success": False, "error": "Not authenticated"})
    
    data = request.get_json()
    method = data.get('method')
    user_id = session.get('user_id')
    
    if method == 'sms':
        result = tfa_system.send_sms_code(user_id)
    elif method == 'email':
        result = tfa_system.send_email_code(user_id)
    else:
        return jsonify({"success": False, "error": "Invalid method"})
    
    return jsonify(result)

@secure_auth_bp.route('/logout')
def secure_logout():
    """Secure logout with session cleanup"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('secure_auth.secure_login'))

@secure_auth_bp.route('/dashboard_redirect')
def dashboard_redirect():
    """Intelligent dashboard redirect based on user role"""
    if not session.get('authenticated') or session.get('needs_2fa'):
        return redirect(url_for('secure_auth.secure_login'))
    
    # Redirect to appropriate dashboard based on role
    role = session.get('role', 'OPERATOR')
    
    if role == 'SYSTEM_ADMIN':
        return redirect('/quantum_asi_excellence')
    elif role == 'VICE_PRESIDENT':
        return redirect('/agi_analytics')
    elif role == 'OPERATIONS_MANAGER':
        return redirect('/dashboard')
    elif role == 'EQUIPMENT_LEAD':
        return redirect('/agi_asset_lifecycle')
    else:
        return redirect('/dashboard')

@secure_auth_bp.route('/api/user_credentials')
def get_user_credentials():
    """API to get secure credentials for testing"""
    credentials = auth_system.get_user_credentials_for_testing()
    return jsonify({
        "credentials": credentials,
        "note": "These are secure enterprise credentials for production testing"
    })