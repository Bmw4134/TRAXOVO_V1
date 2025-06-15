"""
TRAXOVO Watson Intelligence Platform - Lightweight Deployment
Optimized for standard cloud deployment without reserved VM requirements
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "watson_intelligence_2025")

# Lightweight configuration for standard deployment
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# User database
USERS = {
    'watson': {
        'password': 'Btpp@1513',
        'full_name': 'Watson Intelligence',
        'role': 'admin',
        'access_level': 10
    },
    'demo': {
        'password': 'demo123',
        'full_name': 'Demo User',
        'role': 'user',
        'access_level': 5
    }
}

@app.route('/')
def home():
    """Landing page"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['POST'])
def login():
    """Authentication"""
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    
    user_data = USERS.get(username)
    if user_data and user_data['password'] == password:
        session['user'] = {
            'username': username,
            'full_name': user_data['full_name'],
            'role': user_data['role'],
            'access_level': user_data['access_level']
        }
        return redirect(url_for('dashboard'))
    
    flash('Invalid credentials')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if 'user' not in session:
        return redirect(url_for('home'))
    
    return render_template('dashboard.html', 
                         user=session['user'],
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/status')
def api_status():
    """System status API"""
    return jsonify({
        'status': 'operational',
        'users': len(USERS),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)