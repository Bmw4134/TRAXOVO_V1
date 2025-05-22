"""
TRAXORA | Attendance Report Routes

This module provides routes for the weekly attendance reporting system.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app, Response
from utils.enhanced_data_ingestion import load_data_file
from utils.attendance_summary import summarize_week, get_date_range

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
attendance_report_bp = Blueprint('attendance_report', __name__, url_prefix='/attendance')

@attendance_report_bp.route('/', methods=['GET'])
def index():
    """Render the attendance report interface"""
    return render_template('attendance_report/index.html')

@attendance_report_bp.route('/weekly', methods=['POST'])
def process_weekly():
    """Process and generate weekly attendance report"""
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({
            'error': 'Invalid file type. Please upload a CSV or Excel file.'
        }), 400
    
    try:
        # Save the uploaded file temporarily
        temp_dir = os.path.join(current_app.root_path, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Process the file with enhanced data ingestion
        data = load_data_file(temp_path)
        
        if not data:
            return jsonify({
                'error': 'No valid data found in the file. Please check file format.'
            }), 400
        
        # Determine date range for the report
        weeks = int(request.form.get('weeks', 1))
        start_date, end_date = get_date_range(data, weeks)
        
        # Generate attendance summary
        summary = summarize_week(data, start_date)
        
        # Return the report data
        return jsonify({
            'success': True,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_drivers': len(summary),
            'attendance_summary': summary
        })
    
    except Exception as e:
        logger.error(f"Error processing attendance report: {str(e)}")
        return jsonify({'error': f'Error processing report: {str(e)}'}), 500
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Error removing temp file: {str(e)}")

@attendance_report_bp.route('/download', methods=['POST'])
def download_report():
    """Download attendance report as JSON"""
    try:
        # Get report data from request
        report_data = request.json
        
        if not report_data:
            return jsonify({'error': 'No report data provided'}), 400
        
        # Generate filename with date range
        start_date = report_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = report_data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        filename = f"attendance_report_{start_date}_to_{end_date}.json"
        
        # Return as downloadable file
        return Response(
            json.dumps(report_data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    
    except Exception as e:
        logger.error(f"Error generating download: {str(e)}")
        return jsonify({'error': f'Error generating download: {str(e)}'}), 500