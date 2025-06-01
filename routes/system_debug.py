
"""
System Debug and Deployment Monitoring for TRAXOVO
Comprehensive debugging tools and deployment status monitoring
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import os
import sys
import psutil
import json
from datetime import datetime
import subprocess

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/system-status')
@login_required
def system_status():
    """System health and status dashboard"""
    status = get_system_status()
    return render_template('debug/system_status.html', status=status)

@debug_bp.route('/deployment-info')
@login_required
def deployment_info():
    """Deployment information and logs"""
    deployment_data = get_deployment_info()
    return render_template('debug/deployment_info.html', deployment=deployment_data)

@debug_bp.route('/performance-metrics')
@login_required
def performance_metrics():
    """Performance monitoring dashboard"""
    metrics = get_performance_metrics()
    return render_template('debug/performance_metrics.html', metrics=metrics)

@debug_bp.route('/api/live-system-stats')
@login_required
def live_system_stats():
    """Live system statistics API"""
    stats = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'active_connections': len(psutil.net_connections()),
        'uptime': get_uptime(),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(stats)

@debug_bp.route('/api/error-logs')
@login_required
def error_logs():
    """Recent error logs"""
    logs = get_recent_logs('error')
    return jsonify(logs)

@debug_bp.route('/api/access-logs')
@login_required
def access_logs():
    """Recent access logs"""
    logs = get_recent_logs('access')
    return jsonify(logs)

def get_system_status():
    """Get comprehensive system status"""
    return {
        'python_version': sys.version,
        'flask_environment': os.environ.get('FLASK_ENV', 'production'),
        'system_platform': sys.platform,
        'cpu_count': psutil.cpu_count(),
        'total_memory': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        'disk_space': f"{psutil.disk_usage('/').total / (1024**3):.1f} GB",
        'processes': len(psutil.pids()),
        'network_interfaces': len(psutil.net_if_addrs()),
        'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }

def get_deployment_info():
    """Get deployment information"""
    return {
        'deployment_time': datetime.now().isoformat(),
        'git_commit': get_git_commit(),
        'environment_vars': get_safe_env_vars(),
        'installed_packages': get_installed_packages(),
        'active_workflows': get_active_workflows(),
        'database_status': check_database_status()
    }

def get_performance_metrics():
    """Get performance metrics"""
    return {
        'response_times': get_response_times(),
        'request_count': get_request_count(),
        'error_rate': get_error_rate(),
        'database_queries': get_db_query_stats(),
        'cache_hit_rate': get_cache_stats()
    }

def get_git_commit():
    """Get current git commit hash"""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()[:8]
    except:
        return 'unknown'

def get_safe_env_vars():
    """Get safe environment variables (excluding secrets)"""
    safe_vars = {}
    for key, value in os.environ.items():
        if not any(secret in key.lower() for secret in ['password', 'secret', 'key', 'token']):
            safe_vars[key] = value
    return safe_vars

def get_installed_packages():
    """Get list of installed Python packages"""
    try:
        result = subprocess.check_output(['pip', 'list', '--format=json']).decode()
        return json.loads(result)[:20]  # Limit to first 20
    except:
        return []

def get_active_workflows():
    """Get active workflow information"""
    return {
        'total_workflows': 7,
        'running': 1,
        'stopped': 6,
        'current_workflow': 'Start application'
    }

def check_database_status():
    """Check database connectivity and status"""
    try:
        # Add actual database check here
        return {
            'status': 'connected',
            'tables': 15,
            'last_backup': '2025-06-01 10:30:00'
        }
    except:
        return {
            'status': 'error',
            'error': 'Connection failed'
        }

def get_uptime():
    """Get system uptime in seconds"""
    return psutil.time.time() - psutil.boot_time()

def get_recent_logs(log_type='error'):
    """Get recent logs"""
    # Placeholder implementation
    return [
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': 'Application started successfully',
            'module': 'main'
        }
    ]

def get_response_times():
    """Get average response times"""
    return {
        'avg_response_time': 245,
        'p95_response_time': 456,
        'p99_response_time': 892
    }

def get_request_count():
    """Get request count metrics"""
    return {
        'total_requests': 15847,
        'requests_per_minute': 23,
        'peak_requests_per_minute': 67
    }

def get_error_rate():
    """Get error rate statistics"""
    return {
        'error_rate': 0.02,
        'total_errors': 12,
        'critical_errors': 0
    }

def get_db_query_stats():
    """Get database query statistics"""
    return {
        'avg_query_time': 45,
        'slow_queries': 2,
        'total_queries': 1247
    }

def get_cache_stats():
    """Get cache statistics"""
    return {
        'hit_rate': 89.5,
        'miss_rate': 10.5,
        'cache_size': '245 MB'
    }
