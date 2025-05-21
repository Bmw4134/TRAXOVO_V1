"""
Attendance Trends API Routes

This module provides the Flask routes for accessing attendance trend data.
"""

import logging
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

from utils.attendance_trends_api import get_driver_trends, enrich_attendance_data_with_trends
from utils.attendance_processor import process_attendance_data
from utils.activity_logger import log_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
trend_api_bp = Blueprint('trend_api', __name__, url_prefix='/api')

@trend_api_bp.route('/driver-trends', methods=['GET'])
@login_required
def driver_trends_api():
    """API endpoint for driver attendance trends"""
    # Get date range from query parameters
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    days = request.args.get('days', 5, type=int)
    
    # Log activity
    log_activity(
        activity_type="api_request",
        description="Requested driver attendance trends",
        details={"start_date": start_date, "end_date": end_date, "days": days}
    )
    
    # Get trend data
    trend_data = get_driver_trends(start_date, end_date, days)
    
    return jsonify(trend_data)

@trend_api_bp.route('/attendance-with-trends', methods=['GET'])
@login_required
def attendance_with_trends_api():
    """API endpoint for attendance data enriched with trend information"""
    # Get date from query parameters
    date = request.args.get('date')
    days = request.args.get('days', 5, type=int)
    
    # Get attendance data for specified date
    attendance_data = process_attendance_data(date)
    
    # Enrich with trend data
    enriched_data = enrich_attendance_data_with_trends(attendance_data, days)
    
    # Log activity
    log_activity(
        activity_type="api_request",
        description="Requested attendance data with trends",
        details={"date": date, "days_analyzed": days}
    )
    
    return jsonify(enriched_data)

# Function to register this blueprint with the app
def register_trend_api(app):
    app.register_blueprint(trend_api_bp)
    logger.info("Registered Attendance Trends API blueprint")
@trend_api_bp.route('/driver-trends')
def driver_trends():
    """Handler for /driver-trends"""
    try:
        # Add your route handler logic here
        return render_template('trend_api/driver_trends.html')
    except Exception as e:
        logger.error(f"Error in driver_trends: {e}")
        return render_template('error.html', error=str(e)), 500

@trend_api_bp.route('/attendance-with-trends')
def attendance_with_trends():
    """Handler for /attendance-with-trends"""
    try:
        # Add your route handler logic here
        return render_template('trend_api/attendance_with_trends.html')
    except Exception as e:
        logger.error(f"Error in attendance_with_trends: {e}")
        return render_template('error.html', error=str(e)), 500
