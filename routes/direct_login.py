"""
Direct Login System for TRAXOVO
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from datetime import datetime

direct_login_bp = Blueprint('direct_login', __name__)

@direct_login_bp.route('/direct-login', methods=['GET', 'POST'])
def direct_login():
    """Direct login that sets session and redirects immediately"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        # Simple credential check
        if username == 'admin' and password == 'admin':
            # Clear any existing session
            session.clear()
            
            # Set minimal session data
            session['logged_in'] = True
            session['user'] = 'admin'
            session['role'] = 'admin'
            session.permanent = True
            
            # Direct redirect to dashboard
            return redirect('/dashboard')
        else:
            flash('Invalid credentials')
    
    return render_template('direct_login.html')

@direct_login_bp.route('/quick-access')
def quick_access():
    """Instant admin access"""
    session.clear()
    session['logged_in'] = True
    session['user'] = 'admin'
    session['role'] = 'admin'
    session.permanent = True
    return redirect('/dashboard')