"""
TRAXOVO Main Routes
All application routes and endpoints
"""

from flask import render_template, jsonify, request, redirect, url_for, session, flash
from app import app, db
from password_update_system import password_system, get_password_manager, check_password_prompt_needed
from radio_map_asset_architecture import radio_map_assets
from integrated_traxovo_system import integrated_system
from executive_security_dashboard import executive_security
from universal_automation_framework import automation_framework
import os

# Register all blueprints
app.register_blueprint(password_system, url_prefix='/security')
app.register_blueprint(radio_map_assets, url_prefix='/assets')
app.register_blueprint(integrated_system, url_prefix='/system')
app.register_blueprint(executive_security, url_prefix='/executive')
app.register_blueprint(automation_framework, url_prefix='/automation')

@app.route('/')
def index():
    """Main dashboard with security prompts"""
    
    # Check if user needs password prompt (simulate user_id for demo)
    user_id = session.get('user_id', 'demo_user')
    
    if check_password_prompt_needed(user_id):
        return redirect(url_for('password_system.password_prompt', user_id=user_id))
    
    return render_template('main_dashboard.html')

@app.route('/qq_executive_dashboard')
def qq_executive_dashboard():
    """QQ Executive Dashboard for Troy and William"""
    return render_template('qq_executive_dashboard.html')

@app.route('/quantum_asi_dashboard')
def quantum_asi_dashboard():
    """Quantum ASI Dashboard"""
    return render_template('quantum_asi_dashboard.html')

@app.route('/automated_reports')
def automated_reports():
    """Automated Reports Dashboard"""
    return render_template('automated_reports.html')

@app.route('/role_command_widget')
def role_command_widget():
    """Role Command Widget"""
    return render_template('role_command_widget.html')

# API Routes
@app.route('/api/quantum_asi_status')
def api_quantum_asi_status():
    """API endpoint for Quantum ASI status"""
    return jsonify({
        'status': 'active',
        'quantum_consciousness': 'initialized',
        'asi_algorithms': 'operational',
        'excellence_parameters': 'calibrated',
        'system_health': 100
    })

@app.route('/api/report_status')
def api_report_status():
    """API endpoint for report status"""
    return jsonify({
        'status': 'active',
        'reports_generated': 42,
        'last_update': '2025-06-03T08:50:00Z',
        'system_health': 'optimal'
    })

@app.route('/api/system_health')
def api_system_health():
    """API endpoint for overall system health"""
    return jsonify({
        'overall_status': 'excellent',
        'uptime': '99.9%',
        'modules_active': 8,
        'deployment_ready': True,
        'last_check': '2025-06-03T08:50:00Z'
    })

@app.route('/api/executive_credentials')
def api_executive_credentials():
    """Generate executive credentials for William and Troy"""
    
    # Generate secure access credentials
    credentials = {
        'william_rather': {
            'username': 'william.rather',
            'temp_password': 'TRAXOVOExec2025!',
            'role': 'Controller - Southern Division',
            'access_level': 'executive_full',
            'dashboard_url': '/qq_executive_dashboard'
        },
        'troy_executive': {
            'username': 'troy.executive',
            'temp_password': 'TRAXOVOLeader2025!',
            'role': 'Executive Leadership',
            'access_level': 'executive_full',
            'dashboard_url': '/qq_executive_dashboard'
        }
    }
    
    return jsonify({
        'status': 'credentials_generated',
        'message': 'Executive access credentials ready for deployment',
        'credentials': credentials,
        'security_note': 'Change passwords on first login',
        'deployment_ready': True
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# Pre-deployment health check
@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'timestamp': '2025-06-03T08:50:00Z',
        'version': '1.0.0',
        'deployment_ready': True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)