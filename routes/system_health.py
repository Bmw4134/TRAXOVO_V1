"""
TRAXORA Fleet Management System - System Health Module

This module provides routes and functionality for monitoring system health
and diagnosing issues with the Gauge API, database, and other components.
"""
import os
import json
import logging
import time
from datetime import datetime
from sqlalchemy import text
from flask import Blueprint, render_template, jsonify, current_app

from app import db
from models import Asset, Driver, JobSite, AssetLocation
from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

# Create blueprint
system_health_bp = Blueprint('system_health', __name__, url_prefix='/system-health')

@system_health_bp.route('/')
def system_health():
    """System Health Dashboard page"""
    return render_template('system_health/index.html')

@system_health_bp.route('/api/database-health')
def api_database_health():
    """API endpoint to get database health status"""
    try:
        start_time = time.time()
        
        # Check basic database connectivity
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            connection_health = True
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            connection_health = False
        
        connection_time = time.time() - start_time
        
        # Check schema integrity
        schema_integrity = True
        model_column_mapping = {}
        
        try:
            # Get information about important tables
            for model_class in [Asset, Driver, JobSite, AssetLocation]:
                table_name = model_class.__tablename__
                try:
                    columns = [column.name for column in model_class.__table__.columns]
                    model_column_mapping[table_name] = columns
                except Exception as e:
                    logger.error(f"Error getting columns for {table_name}: {str(e)}")
                    schema_integrity = False
        except Exception as e:
            logger.error(f"Error checking schema integrity: {str(e)}")
            schema_integrity = False
        
        # Build a detailed health report
        report = f"""
TRAXORA System Health Check Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATABASE CONNECTIVITY:
- Connection Status: {'OK' if connection_health else 'FAILED'}
- Connection Time: {connection_time * 1000:.2f}ms

SCHEMA INTEGRITY:
- Overall Integrity: {'OK' if schema_integrity else 'ISSUES DETECTED'}
- Tables Checked: {len(model_column_mapping)}

TABLE DETAILS:
"""
        for table, columns in model_column_mapping.items():
            report += f"- {table}: {len(columns)} columns\n"
            report += f"  Columns: {', '.join(columns)}\n\n"
        
        # Count records in main tables
        report += "RECORD COUNTS:\n"
        try:
            asset_count = db.session.query(Asset).count()
            driver_count = db.session.query(Driver).count()
            job_site_count = db.session.query(JobSite).count()
            location_count = db.session.query(AssetLocation).count()
            
            report += f"- Assets: {asset_count}\n"
            report += f"- Drivers: {driver_count}\n"
            report += f"- Job Sites: {job_site_count}\n"
            report += f"- Location Records: {location_count}\n\n"
        except Exception as e:
            logger.error(f"Error counting records: {str(e)}")
            report += f"- Error counting records: {str(e)}\n\n"
        
        # Check Gauge API health
        try:
            gauge_api = GaugeAPI()
            api_status = gauge_api.check_connection()
            report += "GAUGE API CONNECTION:\n"
            report += f"- Status: {'Connected' if api_status else 'Not Connected'}\n"
            report += f"- URL: {gauge_api.api_url}\n"
            report += f"- Asset List ID: {gauge_api.asset_list_id}\n"
            report += f"- Authenticated: {gauge_api.authenticated}\n"
            report += f"- Last Auth Attempt: {gauge_api.last_auth_attempt}\n"
            report += f"- Auth Endpoints Tried: {', '.join(gauge_api.fallback_endpoints_tried)}\n\n"
        except Exception as e:
            logger.error(f"Error checking Gauge API health: {str(e)}")
            report += f"- Error checking Gauge API: {str(e)}\n\n"
        
        report += "RECOMMENDATION:\n"
        health_issues = []
        if not connection_health:
            health_issues.append("Database connection issues detected")
        if not schema_integrity:
            health_issues.append("Database schema integrity issues detected")
        if not api_status:
            health_issues.append("Gauge API connection issues detected")
        
        if health_issues:
            report += "- Issues detected that require attention:\n"
            for issue in health_issues:
                report += f"  * {issue}\n"
            if not api_status:
                report += "  * The system will fall back to local data until API connection is restored\n"
        else:
            report += "- All systems are operating normally\n"
        
        return jsonify({
            'health_check': {
                'overall_health': connection_health and schema_integrity,
                'connection_health': connection_health,
                'connection_time': connection_time,
                'schema_integrity': schema_integrity,
                'model_column_mapping': model_column_mapping
            },
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error in database health check: {str(e)}")
        return jsonify({
            'error': f"Error performing health check: {str(e)}"
        }), 500

@system_health_bp.route('/api/gauge-api-status')
def api_gauge_api_status():
    """API endpoint to get Gauge API status"""
    try:
        gauge_api = GaugeAPI()
        api_status = gauge_api.check_connection()
        
        return jsonify({
            'gauge_api_status': api_status,
            'api_url': gauge_api.api_url,
            'asset_list_id': gauge_api.asset_list_id,
            'authenticated': gauge_api.authenticated,
            'last_authentication_attempt': gauge_api.last_auth_attempt.isoformat() if gauge_api.last_auth_attempt else None,
            'fallback_endpoints_tried': gauge_api.fallback_endpoints_tried
        })
    except Exception as e:
        logger.error(f"Error checking Gauge API status: {str(e)}")
        return jsonify({
            'error': f"Error checking Gauge API status: {str(e)}"
        }), 500

@system_health_bp.route('/api/system-status')
def api_system_status():
    """API endpoint to get overall system status"""
    try:
        # Collect system status information
        status_data = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'filesystem_health': True,
            'gauge_api_health': False,
            'database_health': True
        }
        
        # Check database health
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            status_data['database_health'] = True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            status_data['database_health'] = False
            status_data['status'] = 'warning'
        
        # Check Gauge API health
        try:
            gauge_api = GaugeAPI()
            status_data['gauge_api_health'] = gauge_api.check_connection()
            if not status_data['gauge_api_health']:
                status_data['status'] = 'warning'
        except Exception as e:
            logger.error(f"Gauge API health check failed: {str(e)}")
            status_data['gauge_api_health'] = False
            status_data['status'] = 'warning'
        
        # Check filesystem health
        data_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except Exception as e:
                logger.error(f"Error creating data directory: {str(e)}")
                status_data['filesystem_health'] = False
                status_data['status'] = 'warning'
        
        # Get data statistics
        stats = {}
        try:
            stats['asset_count'] = db.session.query(Asset).count()
            stats['driver_count'] = db.session.query(Driver).count()
            stats['job_site_count'] = db.session.query(JobSite).count()
            stats['asset_location_count'] = db.session.query(AssetLocation).count()
            status_data['stats'] = stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
        
        return jsonify(status_data)
    
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Error getting system status: {str(e)}"
        }), 500