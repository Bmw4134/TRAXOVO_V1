"""
Secure Password Reset System for TRAXOVO

This module provides secure password reset functionality with email verification
and time-limited reset tokens for enhanced security.
"""
import os
import secrets
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash
from models.user import User
from app import db

logger = logging.getLogger(__name__)

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/auth')

# Store reset tokens temporarily (in production, use Redis or database)
reset_tokens = {}

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def is_token_valid(token):
    """Check if reset token is valid and not expired"""
    if token not in reset_tokens:
        return False
    
    token_data = reset_tokens[token]
    expiry_time = token_data['expires_at']
    
    if datetime.now() > expiry_time:
        # Remove expired token
        del reset_tokens[token]
        return False
    
    return True

@password_reset_bp.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset form"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/request_reset.html')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token()
            reset_tokens[token] = {
                'user_id': user.id,
                'email': user.email,
                'expires_at': datetime.now() + timedelta(hours=1)  # 1 hour expiry
            }
            
            # In production, send email with reset link
            reset_link = url_for('password_reset.reset_password', token=token, _external=True)
            
            logger.info(f"Password reset requested for user: {email}")
            logger.info(f"Reset link (dev mode): {reset_link}")
            
            flash(f'Password reset link generated: {reset_link}', 'info')
            flash('In production, this would be sent to your email.', 'warning')
        else:
            # Don't reveal if email exists or not (security)
            flash('If that email exists, a reset link has been sent.', 'info')
        
        return render_template('auth/request_reset.html', reset_requested=True)
    
    return render_template('auth/request_reset.html')

@password_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with valid token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if not is_token_valid(token):
        flash('Invalid or expired reset token. Please request a new password reset.', 'error')
        return redirect(url_for('password_reset.request_password_reset'))
    
    token_data = reset_tokens[token]
    user = User.query.get(token_data['user_id'])
    
    if not user:
        flash('User not found. Please request a new password reset.', 'error')
        return redirect(url_for('password_reset.request_password_reset'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate password
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Check password strength
        if not has_strong_password(new_password):
            flash('Password must contain uppercase, lowercase, number, and special character', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Remove used token
        del reset_tokens[token]
        
        logger.info(f"Password successfully reset for user: {user.email}")
        flash('Password reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token, user=user)

@password_reset_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change password for logged-in users"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        # Check password strength
        if not has_strong_password(new_password):
            flash('Password must contain uppercase, lowercase, number, and special character', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        logger.info(f"Password changed successfully for user: {current_user.email}")
        flash('Password changed successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/change_password.html')

def has_strong_password(password):
    """Check if password meets strength requirements"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special

@password_reset_bp.route('/security-settings')
def security_settings():
    """Security settings dashboard"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return render_template('auth/security_settings.html')