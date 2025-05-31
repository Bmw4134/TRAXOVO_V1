
from flask import Blueprint, redirect, url_for, render_template, request, session
from flask_login import logout_user, login_user

replit_auth_unique = Blueprint('replit_auth_unique', __name__)

@replit_auth_unique.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login for fleet access"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Your credentials: tester/tester or watson/watson
        if (username == 'tester' and password == 'tester') or (username == 'watson' and password == 'watson'):
            session['authenticated'] = True
            session['username'] = username
            return redirect(url_for('seamless_fleet_map'))
    
    return render_template('simple_login.html')

@replit_auth_unique.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))
