"""
Quick Authentication Route - CSRF Exempt for Immediate Access
Enhanced with Remember Me and 2FA preparation
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from flask_wtf.csrf import exempt
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)

quick_auth_bp = Blueprint('quick_auth', __name__)

@quick_auth_bp.route('/quick-login', methods=['GET', 'POST'])
@exempt  # CSRF exempt for immediate access
def quick_login():
    """CSRF-exempt login for immediate access"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        try:
            from models.user import User
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password):
                # Update last login
                user.last_login = datetime.utcnow()
                
                # Enhanced remember me - 30 days for field crews
                if remember_me:
                    session.permanent = True
                
                # Log successful login
                logger.info(f"Successful login for user: {user.username}")
                
                # Login user with enhanced remember me
                login_user(user, remember=remember_me, duration=timedelta(days=30) if remember_me else None)
                
                flash(f"Welcome to TRAXOVO, {user.username}!", "success")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt for: {username}")
                flash("Invalid credentials", "danger")
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("Login error occurred", "danger")
    
    return render_template('auth/quick_login.html')

@quick_auth_bp.route('/setup-2fa')
def setup_2fa():
    """2FA setup page - ready for implementation"""
    return render_template('auth/setup_2fa.html')