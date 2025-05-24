"""
TRAXORA Fleet Management System - System Health Routes

This module provides routes for system health monitoring and status checks.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
system_health_bp = Blueprint('system_health', __name__, url_prefix='/system-health')

@system_health_bp.route('/')
def system_health():
    """System health dashboard"""
    return render_template('system_health/index.html', 
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@system_health_bp.route('/api/status')
def api_status():
    """API endpoint for system health status"""
    try:
        # Check database connection
        from app import db
        from sqlalchemy import text
        db_status = "connected"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db_status = "disconnected"
            
        # Check Gauge API connection
        gauge_status = "connected"
        try:
            gauge_api_url = os.environ.get('GAUGE_API_URL')
            if not gauge_api_url:
                gauge_status = "not_configured"
        except Exception as e:
            logger.error(f"Gauge API error: {str(e)}")
            gauge_status = "error"
            
        # Check file system
        storage_status = "connected"
        try:
            test_dir = os.path.join('uploads')
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            storage_status = "error"
            
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'gauge_api': gauge_status,
            'storage': storage_status
        })
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500