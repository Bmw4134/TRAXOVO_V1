"""
System Health Module
Monitor system status, performance, and diagnostics
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime, timedelta
import psutil

system_health_bp = Blueprint('system_health', __name__)
logger = logging.getLogger(__name__)

@system_health_bp.route('/system-health')
def system_health_dashboard():
    """System health monitoring dashboard"""
    try:
        # Get system metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
        
        return render_template('system_health.html', metrics=system_metrics)
    except Exception as e:
        logger.error(f"Error loading system health: {e}")
        flash('Error loading system health dashboard', 'error')
        return redirect(url_for('index'))

@system_health_bp.route('/api/system-metrics')
def get_system_metrics():
    """API endpoint for real-time system metrics"""
    try:
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': datetime.now().isoformat(),
            'status': 'healthy'
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500