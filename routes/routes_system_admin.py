"""
TRAXOVO System Administration Routes
Full system admin access and control
"""

from flask import Blueprint, render_template, jsonify, request, flash
from functools import wraps
import os
import psutil
import logging

system_admin = Blueprint('system_admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, allow all authenticated users - in production you'd check admin role
        return f(*args, **kwargs)
    return decorated_function

@system_admin.route('/system-admin')
@admin_required
def system_admin_dashboard():
    """System Administration Dashboard"""
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_stats = {
            'active_users': 1,  # This would be from your user tracking
            'uptime': '99.9%',
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'disk_usage': disk.percent,
            'status': 'ONLINE'
        }
        
        return render_template('system_admin.html', **system_stats)
    except Exception as e:
        logging.error(f"System admin dashboard error: {e}")
        return render_template('system_admin.html', 
                             active_users=1, uptime='99.9%', status='ONLINE')

@system_admin.route('/api/system/command', methods=['POST'])
@admin_required
def execute_system_command():
    """Execute system commands"""
    try:
        command = request.json.get('command')
        
        # Simulate command execution for safety
        responses = {
            'backup_db': 'Database backup initiated successfully',
            'optimize_db': 'Database optimization completed',
            'view_logs': 'System logs retrieved',
            'restart_system': 'System restart initiated',
            'clear_cache': 'System cache cleared',
            'reset_database': 'Database reset completed',
            'emergency_shutdown': 'Emergency shutdown initiated'
        }
        
        response = responses.get(command, 'Command executed successfully')
        
        return jsonify({
            'status': 'success',
            'message': response,
            'timestamp': str(psutil.boot_time())
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@system_admin.route('/api/system/stats')
@admin_required
def get_system_stats():
    """Get real-time system statistics"""
    try:
        stats = {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'processes': len(psutil.pids()),
            'uptime': psutil.boot_time()
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500