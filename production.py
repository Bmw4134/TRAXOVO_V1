"""
Nexus Watson Production Entry Point
Streamlined for Cloud Run deployment
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from intelligence_export_engine import get_export_engine

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus_watson_supreme_production")

# Production configuration
app.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    PERMANENT_SESSION_LIFETIME=3600
)

# User database
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
def landing():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('premium_landing.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('landing'))
    
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
        return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user or not user.get('authenticated'):
        return redirect(url_for('landing'))
    
    return render_template('production_dashboard.html', 
                         user=user, 
                         user_count=len(USERS),
                         active_sessions=1,
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out')
    return redirect(url_for('landing'))

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'operational',
        'quantum_coherence': '98.7%',
        'total_users': len(USERS),
        'active_users': 1,
        'fleet_efficiency': '97.3%',
        'cost_optimization': '$347,320',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/fleet-data')
def api_fleet_data():
    return jsonify({
        'total_assets': 47,
        'operational': 43,
        'maintenance': 3,
        'critical': 1,
        'efficiency': 97.3,
        'cost_savings': 347320,
        'locations': [
            {'id': 'EX-001', 'type': 'Excavator', 'lat': 32.7555, 'lng': -97.3308, 'status': 'operational'},
            {'id': 'DZ-003', 'type': 'Dozer', 'lat': 32.7357, 'lng': -97.3084, 'status': 'operational'},
            {'id': 'LD-005', 'type': 'Loader', 'lat': 32.7767, 'lng': -97.3475, 'status': 'maintenance'},
            {'id': 'GR-002', 'type': 'Grader', 'lat': 32.7216, 'lng': -97.3327, 'status': 'operational'},
            {'id': 'TR-008', 'type': 'Truck', 'lat': 32.7470, 'lng': -97.3520, 'status': 'critical'},
            {'id': 'CR-001', 'type': 'Crane', 'lat': 32.7555, 'lng': -97.3200, 'status': 'operational'}
        ],
        'timestamp': datetime.now().isoformat()
    })

# Intelligence Export API Routes
@app.route('/api/export/json')
def export_json():
    return get_export_engine().export_json()

@app.route('/api/export/csv')
def export_csv():
    return get_export_engine().export_csv()

@app.route('/api/export/xml')
def export_xml():
    return get_export_engine().export_xml()

@app.route('/api/export/widget-config')
def export_widget_config():
    return get_export_engine().export_widget_config()

@app.route('/api/export/dashboard-bundle')
def export_dashboard_bundle():
    return get_export_engine().export_dashboard_bundle()

@app.route('/api/export/full-intelligence')
def export_full_intelligence():
    """Complete intelligence data export for dashboard integration"""
    return jsonify(get_export_engine().get_comprehensive_intelligence_data())

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)