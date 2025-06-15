"""
TRAXOVO Watson Intelligence Platform - Clean Deployment
Minimal Flask application optimized for Replit deployment
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "watson_intelligence_2025")

# Deployment configuration
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Simple user database
USERS = {
    'watson': {
        'password': 'Btpp@1513',
        'full_name': 'Watson Supreme Intelligence',
        'role': 'watson',
        'department': 'Command Center',
        'access_level': 11
    },
    'demo': {
        'password': 'demo123',
        'full_name': 'Demo User',
        'role': 'operator',
        'department': 'Operations',
        'access_level': 5
    }
}

@app.route('/')
def home():
    """Landing page"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authentication system"""
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('home'))
    
    # Check credentials
    user_data = USERS.get(username.lower())
    if user_data and user_data['password'] == password:
        session['user'] = {
            'username': username,
            'user_id': username,
            'full_name': user_data['full_name'],
            'role': user_data['role'],
            'department': user_data['department'],
            'access_level': user_data['access_level'],
            'authenticated': True
        }
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('dashboard.html', 
                         user=user,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Successfully logged out')
    return redirect(url_for('home'))

@app.route('/api/status')
def api_status():
    """System status API"""
    return jsonify({
        'status': 'operational',
        'users': len(USERS),
        'modules_active': True,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# For deployment compatibility
def create_app():
    return app