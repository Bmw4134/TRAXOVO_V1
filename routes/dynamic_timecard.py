"""
TRAXORA Fleet Management System - Dynamic Timecard Routes

This module provides routes for processing and comparing dynamic timecard workbooks
with GPS data for driver attendance verification.
"""
import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort
)
from werkzeug.utils import secure_filename

from utils.dynamic_timecard_processor import process_dynamic_timecard, compare_dynamic_timecards_with_gps

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
dynamic_timecard_bp = Blueprint('dynamic_timecard', __name__, url_prefix='/dynamic-timecard')

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join(current_app.root_path, 'data', 'dynamic_timecard')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_upload_directory():
    """Get upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'timecard')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@dynamic_timecard_bp.route('/')
def dashboard():
    """Dynamic timecard dashboard"""
    return render_template(
        'dynamic_timecard/dashboard.html',
        api_status='connected',
        database_status='connected',
        storage_status='connected'
    )

@dynamic_timecard_bp.route('/upload', methods=['POST'])
def upload_timecard():
    """Upload and process dynamic timecard workbook"""
    try:
        # Check for file
        if 'timecard_file' not in request.files:
            flash("No timecard file selected", "danger")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        timecard_file = request.files['timecard_file']
        if not timecard_file or timecard_file.filename == '':
            flash("No timecard file selected", "danger")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        # Get date range
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not start_date or not end_date:
            flash("Please provide start and end dates", "danger")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        # Save the timecard file
        filename = f"timecard_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(timecard_file.filename)}"
        file_path = os.path.join(get_upload_directory(), filename)
        timecard_file.save(file_path)
        
        # Process the timecard data
        timecard_data = process_dynamic_timecard(
            file_path,
            start_date=start_date,
            end_date=end_date
        )
        
        if timecard_data is None or timecard_data.empty:
            flash("No valid timecard data found in the workbook", "warning")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        # Load existing driver reports for comparison
        reports_dir = get_reports_directory()
        gps_data = {}
        dates_processed = []
        
        # Parse date range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = [start + timedelta(days=x) for x in range((end - start).days + 1)]
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            report_dir = os.path.join(reports_dir, date_str)
            if os.path.exists(report_dir):
                # Find JSON report
                for filename in os.listdir(report_dir):
                    if filename.endswith('.json') and not filename.startswith('summary'):
                        with open(os.path.join(report_dir, filename), 'r') as f:
                            report_data = json.load(f)
                            gps_data[date_str] = report_data
                            dates_processed.append(date_str)
        
        if not dates_processed:
            flash("No driver reports found for the selected date range", "warning")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        # Compare timecard with GPS data
        comparisons = []
        for date_str in dates_processed:
            comparison = compare_dynamic_timecards_with_gps(
                file_path,
                gps_data,
                target_date=date_str
            )
            comparisons.extend(comparison)
        
        if not comparisons:
            flash("No comparison data could be generated", "warning")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        # Save comparison results
        data_dir = get_data_directory()
        comparison_file = os.path.join(data_dir, 'dynamic_timecard_comparisons.json')
        with open(comparison_file, 'w') as f:
            json.dump(comparisons, f, indent=2)
        
        flash(f"Timecard comparison complete: {len(comparisons)} records processed", "success")
        
        # Redirect to view comparison
        return redirect(url_for('dynamic_timecard.view_comparison'))
    
    except Exception as e:
        logger.error(f"Error processing dynamic timecard: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error processing timecard: {str(e)}", "danger")
        return redirect(url_for('dynamic_timecard.dashboard'))

@dynamic_timecard_bp.route('/view')
def view_comparison():
    """View dynamic timecard comparison results"""
    try:
        # Load comparison data
        data_dir = get_data_directory()
        comparison_file = os.path.join(data_dir, 'dynamic_timecard_comparisons.json')
        
        if not os.path.exists(comparison_file):
            flash("No comparison data available", "warning")
            return redirect(url_for('dynamic_timecard.dashboard'))
        
        with open(comparison_file, 'r') as f:
            comparisons = json.load(f)
        
        # Group comparisons by date
        dates = sorted(list(set(comp['date'] for comp in comparisons)))
        
        # Calculate summary statistics
        summary = {
            'total_records': len(comparisons),
            'discrepancy_count': sum(1 for comp in comparisons if comp.get('has_discrepancy', False)),
            'missing_gps': sum(1 for comp in comparisons if comp.get('classification') == 'not_found'),
            'missing_timecard': sum(1 for comp in comparisons if comp.get('timecard_status') == 'missing'),
            'job_mismatches': sum(1 for comp in comparisons if any('Job mismatch' in issue for issue in comp.get('issues', []))),
            'hours_discrepancies': sum(1 for comp in comparisons if any('Hours discrepancy' in issue for issue in comp.get('issues', [])))
        }
        
        return render_template(
            'dynamic_timecard/comparison.html',
            comparisons=comparisons,
            dates=dates,
            summary=summary,
            api_status='connected',
            database_status='connected',
            storage_status='connected'
        )
    
    except Exception as e:
        logger.error(f"Error viewing comparison: {str(e)}")
        flash(f"Error viewing comparison: {str(e)}", "danger")
        return redirect(url_for('dynamic_timecard.dashboard'))

@dynamic_timecard_bp.route('/api/comparison_data')
def api_comparison_data():
    """API endpoint to get comparison data"""
    try:
        # Load comparison data
        data_dir = get_data_directory()
        comparison_file = os.path.join(data_dir, 'dynamic_timecard_comparisons.json')
        
        if not os.path.exists(comparison_file):
            return jsonify({"error": "No comparison data available"}), 404
        
        with open(comparison_file, 'r') as f:
            comparisons = json.load(f)
        
        return jsonify(comparisons), 200
    
    except Exception as e:
        logger.error(f"Error getting comparison data: {str(e)}")
        return jsonify({"error": f"Error getting comparison data: {str(e)}"}), 500