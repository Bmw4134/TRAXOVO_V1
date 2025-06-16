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

# Initialize database
try:
    from models import init_db
    init_db(app)
except ImportError:
    pass  # Database models are optional

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
    session.clear()  # Force logout on home page access
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
    
    # Check if user is watson for full console access
    is_watson = user.get('username') == 'watson'
    
    return render_template('dashboard.html', 
                         user=user,
                         is_watson=is_watson,
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
    return jsonify({'status': 'healthy', 'message': 'TRAXOVO Watson Intelligence is operational'})

@app.route('/test')
def test():
    """Simple test page"""
    return '<h1>TRAXOVO Watson Test Page</h1><p>Server is running correctly on port 5000</p>'

@app.route('/ragle')
def ragle_dashboard():
    """Ragle System Dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('ragle_dashboard.html', user=user)

@app.route('/ragle/api/data')
def ragle_api_data():
    """Ragle system API data"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'status': 'operational',
        'systems': {
            'processing_units': 847,
            'active_connections': 12,
            'data_throughput': '1.2TB/hr',
            'efficiency_rating': '94.3%'
        },
        'alerts': [
            {'level': 'info', 'message': 'System optimization completed'},
            {'level': 'warning', 'message': 'Memory usage at 78%'}
        ],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/attendance')
def attendance_matrix():
    """Attendance Matrix Dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('attendance_matrix.html', user=user)

@app.route('/equipment-billing')
def equipment_billing():
    """Equipment Billing Dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('equipment_billing.html', user=user)

@app.route('/job-zones')
def job_zones():
    """Job Zones Management Dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('job_zones.html', user=user)

@app.route('/geofences')
def geofences():
    """Geofence Management Dashboard"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('home'))
    
    return render_template('geofences.html', user=user)

@app.route('/api/attendance')
def api_attendance():
    """Attendance API"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'status': 'present',
        'clock_in': '08:00',
        'hours_today': 8.5,
        'weekly_hours': 42.5,
        'overtime': 2.5
    })

@app.route('/api/equipment')
def api_equipment():
    """Equipment API"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'total_equipment': 247,
        'active_rentals': 89,
        'monthly_revenue': 847000,
        'utilization_rate': 78
    })

@app.route('/api/job-zones')
def api_job_zones():
    """Job Zones API"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'total_zones': 34,
        'active_jobs': 12,
        'workers_on_site': 147,
        'equipment_deployed': 89
    })

@app.route('/api/geofences')
def api_geofences():
    """Geofences API"""
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'active_geofences': 47,
        'assets_tracked': 312,
        'alerts_today': 7,
        'compliance_rate': 94
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# For deployment compatibility
def create_app():
    return app