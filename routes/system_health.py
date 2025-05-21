"""
TRAXORA Fleet Management System - System Health Module

This module provides routes and functionality for system health monitoring
and diagnostics, including database connectivity checks.
"""
import os
import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, jsonify, current_app

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import Asset, AssetLocation, Driver, JobSite, User
from utils.database_health import run_health_check

logger = logging.getLogger(__name__)

# Create blueprint
system_health_bp = Blueprint('system_health', __name__, url_prefix='/system-health')

# Define models to check in health check
MODELS_TO_CHECK = [Asset, AssetLocation, Driver, JobSite, User]

@system_health_bp.route('/')
def system_health_dashboard():
    """System Health Dashboard main page"""
    return render_template(
        'system_health/index.html',
        title="TRAXORA System Health"
    )

@system_health_bp.route('/api/database-health')
def api_database_health():
    """API endpoint to check database health"""
    try:
        # Run database health check
        results, report = run_health_check(db, MODELS_TO_CHECK)
        
        # Log the results
        if results.get('overall_health', False):
            logger.info("Database health check passed")
        else:
            logger.warning("Database health check failed")
            logger.warning(report)
        
        # Return the results
        return jsonify({
            'status': 'success',
            'health_check': results,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error in database health check: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@system_health_bp.route('/api/gauge-api-status')
def api_gauge_api_status():
    """API endpoint to check Gauge API status"""
    try:
        from gauge_api import GaugeAPI
        
        # Create Gauge API instance
        gauge_api = GaugeAPI()
        
        # Check API status
        status = gauge_api.check_connection()
        
        # Return status
        return jsonify({
            'status': 'success',
            'gauge_api_status': status,
            'authenticated': gauge_api.authenticated,
            'asset_list_id': gauge_api.asset_list_id,
            'username': gauge_api.username,
            'last_authentication_attempt': gauge_api.last_auth_attempt.isoformat() if gauge_api.last_auth_attempt else None,
            'fallback_endpoints_tried': gauge_api.fallback_endpoints_tried
        })
    
    except Exception as e:
        logger.error(f"Error in Gauge API status check: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@system_health_bp.route('/api/system-status')
def api_system_status():
    """API endpoint to check overall system status"""
    try:
        # Get database health
        db_results, _ = run_health_check(db, MODELS_TO_CHECK)
        
        # Check Gauge API status
        from gauge_api import GaugeAPI
        gauge_api = GaugeAPI()
        gauge_api_status = gauge_api.check_connection()
        
        # Check filesystem status
        try:
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            test_file_path = os.path.join(data_dir, 'test_file.txt')
            with open(test_file_path, 'w') as f:
                f.write(f"Test file created at {datetime.now().isoformat()}")
            filesystem_status = os.path.exists(test_file_path)
            os.remove(test_file_path)
        except Exception as fs_error:
            logger.error(f"Filesystem check error: {str(fs_error)}")
            filesystem_status = False
        
        # Get asset and driver counts
        try:
            asset_count = db.session.query(Asset).count()
            asset_location_count = db.session.query(AssetLocation).count()
            driver_count = db.session.query(Driver).count()
            job_site_count = db.session.query(JobSite).count()
        except Exception as count_error:
            logger.error(f"Error getting counts: {str(count_error)}")
            asset_count = asset_location_count = driver_count = job_site_count = 0
        
        # Return system status
        return jsonify({
            'status': 'success',
            'database_health': db_results.get('overall_health', False),
            'gauge_api_health': gauge_api_status,
            'filesystem_health': filesystem_status,
            'stats': {
                'asset_count': asset_count,
                'asset_location_count': asset_location_count,
                'driver_count': driver_count,
                'job_site_count': job_site_count
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in system status check: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500