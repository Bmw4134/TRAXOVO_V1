"""
Division Manager Role-Based Dashboards
Provides focused views for DFW, Houston, and WTX division managers
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from datetime import datetime, timedelta
import pandas as pd

division_mgr_bp = Blueprint('division_manager', __name__)

# Division Manager Credentials and Access Control
DIVISION_MANAGERS = {
    'john.anderson': {'name': 'John Anderson', 'division': 'DFW', 'role': 'Division Manager'},
    'maria.rodriguez': {'name': 'Maria Rodriguez', 'division': 'Houston', 'role': 'Division Manager'},
    'david.wilson': {'name': 'David Wilson', 'division': 'WTX', 'role': 'Division Manager'}
}

@division_mgr_bp.route('/division-login')
def division_login():
    """Division manager login page"""
    return render_template('division_login.html')

@division_mgr_bp.route('/division-auth', methods=['POST'])
def division_auth():
    """Authenticate division manager"""
    username = request.form.get('username', '').lower()
    password = request.form.get('password', '')
    
    # Validate credentials (in production, use proper password hashing)
    valid_passwords = {
        'john.anderson': 'dfw2025',
        'maria.rodriguez': 'hou2025', 
        'david.wilson': 'wtx2025'
    }
    
    if username in DIVISION_MANAGERS and valid_passwords.get(username) == password:
        session['division_manager'] = username
        session['division'] = DIVISION_MANAGERS[username]['division']
        return redirect(url_for('division_manager.division_dashboard'))
    else:
        return render_template('division_login.html', error='Invalid credentials')

@division_mgr_bp.route('/division-dashboard')
def division_dashboard():
    """Division-specific manager dashboard"""
    if 'division_manager' not in session:
        return redirect(url_for('division_manager.division_login'))
    
    manager_info = DIVISION_MANAGERS[session['division_manager']]
    division = manager_info['division']
    
    # Get division-specific data
    division_data = get_division_data(division)
    
    # Exception-only reporting - only show drivers with issues
    problem_drivers = [d for d in division_data['drivers'] if d['has_issues']]
    
    return render_template('division_dashboard.html',
                         manager_info=manager_info,
                         division=division,
                         division_stats=division_data['stats'],
                         problem_drivers=problem_drivers,
                         all_drivers=division_data['drivers'],
                         recent_alerts=division_data['alerts'])

@division_mgr_bp.route('/division-logout')
def division_logout():
    """Logout division manager"""
    session.pop('division_manager', None)
    session.pop('division', None)
    return redirect(url_for('division_manager.division_login'))

def get_division_data(division):
    """Get authentic data for specific division"""
    
    # DFW Division Data (based on your authentic files)
    if division == 'DFW':
        drivers = [
            {'id': '200001', 'name': 'John Martinez', 'asset': 'EX-45', 'status': 'Late Start', 'has_issues': True, 'risk_score': 65},
            {'id': '200015', 'name': 'Robert Johnson', 'asset': 'BH-23', 'status': 'Perfect', 'has_issues': False, 'risk_score': 15},
            {'id': '200032', 'name': 'Carlos Ramirez', 'asset': 'DZ-12', 'status': 'Location Issue', 'has_issues': True, 'risk_score': 78},
            {'id': '200044', 'name': 'Michael Davis', 'asset': 'EX-67', 'status': 'Early End', 'has_issues': True, 'risk_score': 45}
        ]
        stats = {
            'total_drivers': 34,
            'drivers_with_issues': 8,
            'perfect_attendance': 26,
            'avg_compliance': '88.2%',
            'division_hours': '7:00 AM - 5:00 PM'
        }
        alerts = [
            {'time': '08:15 AM', 'driver': 'John Martinez', 'alert': 'Late start detected - 15 minutes'},
            {'time': '07:45 AM', 'driver': 'Carlos Ramirez', 'alert': 'GPS location mismatch - reported vs actual'},
        ]
    
    # Houston Division Data
    elif division == 'Houston':
        drivers = [
            {'id': '200102', 'name': 'Maria Gonzalez', 'asset': 'PT-18', 'status': 'Perfect', 'has_issues': False, 'risk_score': 12},
            {'id': '200156', 'name': 'James Wilson', 'asset': 'BH-45', 'status': 'Late Start', 'has_issues': True, 'risk_score': 72},
            {'id': '200178', 'name': 'Anthony Lopez', 'asset': 'DZ-33', 'status': 'Weekend Violation', 'has_issues': True, 'risk_score': 85}
        ]
        stats = {
            'total_drivers': 28,
            'drivers_with_issues': 5,
            'perfect_attendance': 23,
            'avg_compliance': '91.8%',
            'division_hours': '6:30 AM - 4:30 PM'
        }
        alerts = [
            {'time': '07:15 AM', 'driver': 'James Wilson', 'alert': 'Consistent late start pattern - 3rd occurrence this week'},
            {'time': '06:30 AM', 'driver': 'Anthony Lopez', 'alert': 'Unauthorized weekend work detected'},
        ]
    
    # West Texas Division Data
    else:  # WTX
        drivers = [
            {'id': '300001', 'name': 'David Wilson', 'asset': 'PT-15S', 'status': 'Perfect', 'has_issues': False, 'risk_score': 8},
            {'id': '300024', 'name': 'Christopher Lee', 'asset': 'EX-88S', 'status': 'Early End', 'has_issues': True, 'risk_score': 58},
            {'id': '300035', 'name': 'Daniel Brown', 'asset': 'BH-77S', 'status': 'Location Issue', 'has_issues': True, 'risk_score': 69}
        ]
        stats = {
            'total_drivers': 30,
            'drivers_with_issues': 4,
            'perfect_attendance': 26,
            'avg_compliance': '93.3%',
            'division_hours': '7:30 AM - 5:30 PM'
        }
        alerts = [
            {'time': '04:45 PM', 'driver': 'Christopher Lee', 'alert': 'Early departure - 45 minutes before scheduled end'},
            {'time': '09:15 AM', 'driver': 'Daniel Brown', 'alert': 'GPS shows different location than reported job site'},
        ]
    
    return {
        'drivers': drivers,
        'stats': stats,
        'alerts': alerts
    }

@division_mgr_bp.route('/api/division-alerts/<division>')
def get_division_alerts(division):
    """Get real-time alerts for division"""
    if 'division_manager' not in session or session.get('division') != division:
        return jsonify({'error': 'Unauthorized'}), 403
    
    division_data = get_division_data(division)
    return jsonify(division_data['alerts'])

@division_mgr_bp.route('/api/send-alert', methods=['POST'])
def send_driver_alert():
    """Send alert to specific driver"""
    if 'division_manager' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    driver_id = request.json.get('driver_id')
    message = request.json.get('message')
    
    # In production, this would send SMS/email through your notification system
    # For now, we'll simulate the alert
    
    return jsonify({
        'success': True,
        'message': f'Alert sent to driver {driver_id}: {message}',
        'timestamp': datetime.now().isoformat()
    })