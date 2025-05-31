"""
Secrets Manager - Secure API credential management for TRAXORA
Safely store and manage your Gauge API and other service credentials
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import logging
from datetime import datetime

secrets_manager_bp = Blueprint('secrets_manager', __name__)
logger = logging.getLogger(__name__)

@secrets_manager_bp.route('/')
def secrets_dashboard():
    """Main secrets management dashboard"""
    # Get current environment variables (masked for security)
    secrets_status = {
        'GAUGE_API_USERNAME': bool(os.environ.get('GAUGE_API_USERNAME')),
        'GAUGE_API_PASSWORD': bool(os.environ.get('GAUGE_API_PASSWORD')),
        'GAUGE_API_URL': bool(os.environ.get('GAUGE_API_URL')),
        'DATABASE_URL': bool(os.environ.get('DATABASE_URL')),
        'OPENAI_API_KEY': bool(os.environ.get('OPENAI_API_KEY')),
        'SENDGRID_API_KEY': bool(os.environ.get('SENDGRID_API_KEY'))
    }
    
    # Check which secrets are properly configured
    configured_count = sum(secrets_status.values())
    total_secrets = len(secrets_status)
    
    return render_template('secrets_manager/dashboard.html',
                         secrets_status=secrets_status,
                         configured_count=configured_count,
                         total_secrets=total_secrets)

@secrets_manager_bp.route('/test-connections')
def test_connections():
    """Test all API connections"""
    results = {}
    
    # Test Gauge API
    try:
        from gauge_api_legacy import GaugeAPI
        gauge = GaugeAPI()
        if gauge.test_connection():
            results['gauge_api'] = {'status': 'success', 'message': 'Connected successfully'}
        else:
            results['gauge_api'] = {'status': 'error', 'message': 'Connection failed'}
    except Exception as e:
        results['gauge_api'] = {'status': 'error', 'message': str(e)}
    
    # Test Database
    try:
        from app import db
        db.session.execute('SELECT 1')
        results['database'] = {'status': 'success', 'message': 'Database connected'}
    except Exception as e:
        results['database'] = {'status': 'error', 'message': str(e)}
    
    return jsonify(results)

@secrets_manager_bp.route('/status')
def api_status():
    """Get real-time status of all services"""
    status = {
        'gauge_api': check_gauge_status(),
        'database': check_database_status(),
        'file_system': check_file_system_status(),
        'last_updated': datetime.now().isoformat()
    }
    
    return jsonify(status)

def check_gauge_status():
    """Check Gauge API status"""
    try:
        username = os.environ.get('GAUGE_API_USERNAME')
        password = os.environ.get('GAUGE_API_PASSWORD')
        url = os.environ.get('GAUGE_API_URL')
        
        if not all([username, password, url]):
            return {'status': 'warning', 'message': 'Credentials not configured'}
        
        from gauge_api_legacy import GaugeAPI
        gauge = GaugeAPI()
        if gauge.test_connection():
            return {'status': 'success', 'message': 'API responding normally'}
        else:
            return {'status': 'error', 'message': 'API connection failed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def check_database_status():
    """Check database connectivity"""
    try:
        from app import db
        db.session.execute('SELECT 1')
        return {'status': 'success', 'message': 'Database connected'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def check_file_system_status():
    """Check file system access"""
    try:
        import os
        test_dirs = ['uploads', 'reports', 'temp_reports']
        for dir_name in test_dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
        return {'status': 'success', 'message': 'File system accessible'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}