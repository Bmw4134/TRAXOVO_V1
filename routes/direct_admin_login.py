"""
Direct Admin Login for TRAXOVO System Administrator
"""

from flask import Blueprint, render_template, redirect, url_for, session, request
from datetime import datetime

direct_admin_bp = Blueprint('direct_admin', __name__)

@direct_admin_bp.route('/admin-access')
def admin_access():
    """Direct admin access without complex authentication"""
    # Set session as authenticated admin
    session['authenticated'] = True
    session['user_id'] = 'admin'
    session['user_role'] = 'system_admin'
    session['login_time'] = datetime.now().isoformat()
    session.permanent = True
    
    # Redirect to dashboard
    return redirect(url_for('dashboard'))

@direct_admin_bp.route('/quick-login')
def quick_login():
    """Quick login page for admin access"""
    return render_template('quick_admin_login.html')