"""
TRAXORA | Attendance Report Routes

This module provides routes for displaying the weekly attendance report
with support for grouping by driver, job site, division, and zone.
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from flask import Blueprint, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from agents.weekly_driver_summary_agent import handle as process_weekly_summary
from utils.attendance_summary import get_attendance_stats
from utils.enhanced_data_ingestion import process_file
from utils.jobsite_catalog_loader import get_all_divisions, get_all_categories

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
attendance_report_bp = Blueprint('attendance_report', __name__, url_prefix='/attendance')

# Temp directory for file uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@attendance_report_bp.route('/')
def index():
    """Display the attendance report interface"""
    # Get available divisions and categories for filtering
    divisions = get_all_divisions()
    categories = get_all_categories()
    
    return render_template(
        'attendance_report/index.html',
        divisions=divisions,
        categories=categories
    )

@attendance_report_bp.route('/process', methods=['POST'])
def process_attendance_data():
    """Process multiple uploaded attendance data files"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
        
    uploaded_files = request.files.getlist('files[]')
    file_types = request.form.getlist('fileTypes[]')
    
    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({'error': 'No selected files'}), 400
    
    # Get group by option
    group_by = request.form.get('group_by', 'driver')
    weeks = int(request.form.get('weeks', 1))
    
    # Collected data from each file type
    time_on_site_data = []
    activity_detail_data = []
    driving_history_data = []
    
    # Temporary file paths to clean up later
    temp_paths = []
    
    try:
        # Process each file based on its type
        for i, file in enumerate(uploaded_files):
            if file and file.filename != '':
                # Determine file type (if provided in form data)
                file_type = file_types[i] if i < len(file_types) else 'Unknown'
                
                # Save file temporarily
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1].lower()
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                temp_path = os.path.join(UPLOAD_FOLDER, f"{file_type}_{timestamp}_{i}{file_ext}")
                file.save(temp_path)
                temp_paths.append(temp_path)
                
                # Process the file data
                processed_data = process_file(temp_path)
                
                if processed_data and isinstance(processed_data, list) and len(processed_data) > 0:
                    # Add the data to the appropriate collection based on file type
                    if file_type == 'TimeOnSite':
                        time_on_site_data.extend(processed_data)
                    elif file_type == 'ActivityDetail':
                        activity_detail_data.extend(processed_data)
                    elif file_type == 'DrivingHistory':
                        driving_history_data.extend(processed_data)
                    else:
                        # If type is unknown, try to detect based on content
                        # This is a fallback mechanism
                        logger.info(f"File type unknown, attempting to infer type for {filename}")
                        if any('duration' in str(record).lower() for record in processed_data[:5]):
                            time_on_site_data.extend(processed_data)
                        elif any('activity' in str(record).lower() for record in processed_data[:5]):
                            activity_detail_data.extend(processed_data)
                        elif any('trip' in str(record).lower() for record in processed_data[:5]):
                            driving_history_data.extend(processed_data)
                        else:
                            # Default to TimeOnSite if we can't determine
                            time_on_site_data.extend(processed_data)
        
        # Combine all data sources for a complete view
        from utils.multi_source_processor import combine_attendance_sources
        
        # Log data collection counts
        logger.info(f"Collected data: TimeOnSite: {len(time_on_site_data)}, "
                   f"ActivityDetail: {len(activity_detail_data)}, "
                   f"DrivingHistory: {len(driving_history_data)}")
        
        # Combine data from all sources
        combined_data = combine_attendance_sources(
            time_on_site_data, 
            activity_detail_data, 
            driving_history_data
        )
        
        # No data found across all files
        if not combined_data or len(combined_data) == 0:
            return jsonify({'error': 'No valid data found in uploaded files'}), 400
        
        # Get attendance stats from combined data
        stats = get_attendance_stats(combined_data)
        
        # Process weekly summary with the specified grouping
        summary_options = {
            'group_by': group_by,
            'weeks': weeks
        }
        
        summary = process_weekly_summary(combined_data, summary_options)
        
        # Clean up temp files
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        
        # Return combined response
        return jsonify({
            'stats': stats,
            'summary': summary,
            'success': True,
            'file_counts': {
                'time_on_site': len(time_on_site_data),
                'activity_detail': len(activity_detail_data),
                'driving_history': len(driving_history_data),
                'combined': len(combined_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}", exc_info=True)
        
        # Clean up temp files
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
                
        return jsonify({'error': f'Error processing files: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid files'}), 400

@attendance_report_bp.route('/download/<report_type>')
def download_report(report_type):
    """Download attendance report data"""
    if 'report_data' not in request.args:
        return jsonify({'error': 'No report data provided'}), 400
        
    try:
        # Parse the report data from the URL parameter
        report_data = json.loads(request.args.get('report_data'))
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"attendance_report_{report_type}_{timestamp}.json"
        
        # Create temp file
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Write data to file
        with open(temp_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Send file as attachment
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error generating download: {str(e)}")
        return jsonify({'error': f'Error generating download: {str(e)}'}), 500

def register_blueprint(app):
    """Register the attendance report blueprint with the app"""
    app.register_blueprint(attendance_report_bp)
    logger.info("Attendance Report blueprint registered")