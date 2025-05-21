"""
Report Generator Blueprint

This module defines routes for generating PDF and CSV reports with preview thumbnails.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                  render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from utils.report_generator import generate_csv_report, generate_pdf_report

# Create blueprint
report_generator_bp = Blueprint('report_generator', __name__, url_prefix='/reports')

# Configure logging
logger = logging.getLogger(__name__)

# Ensure export directories exist
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)
PDF_DIR = EXPORTS_DIR / "pdf"
PDF_DIR.mkdir(exist_ok=True)
CSV_DIR = EXPORTS_DIR / "csv"
CSV_DIR.mkdir(exist_ok=True)
PREVIEW_DIR = EXPORTS_DIR / "previews"
PREVIEW_DIR.mkdir(exist_ok=True)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


@report_generator_bp.route('/generator')
@login_required
def report_generator():
    """
    Report generator page
    
    Returns:
        Rendered template for the report generator
    """
    return render_template('reports/export.html')


@report_generator_bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """
    Generate a report based on request parameters
    
    Returns:
        JSON response with report details
    """
    # Get report parameters from request
    data = request.json or {}
    report_type = data.get('reportType')
    format_type = data.get('format', 'pdf').lower()
    
    if not report_type:
        return jsonify({
            'success': False,
            'error': 'Report type is required'
        }), 400
    
    # Get sample data for the report
    sample_data = _get_sample_report_data(report_type)
    
    try:
        # Generate report based on format
        if format_type == 'pdf':
            report_path, preview_path = generate_pdf_report(
                report_type=report_type,
                data=sample_data,
                title=f"{report_type.replace('_', ' ').title()} Report"
            )
        elif format_type == 'csv':
            report_path, preview_path = generate_csv_report(
                report_type=report_type,
                data=sample_data
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400
        
        # Log report generation
        _log_report_generation(report_type, format_type, True)
        
        # Return the file paths
        return jsonify({
            'success': True,
            'report_path': report_path,
            'preview_path': preview_path,
            'download_url': url_for('report_generator.download_report', filename=os.path.basename(report_path)),
            'preview_url': url_for('report_generator.view_preview', filename=os.path.basename(preview_path))
        })
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        _log_report_generation(report_type, format_type, False, str(e))
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@report_generator_bp.route('/preview/<filename>')
@login_required
def view_preview(filename):
    """
    View a report preview image
    
    Args:
        filename (str): Name of the preview file
        
    Returns:
        The preview image file
    """
    return send_from_directory(PREVIEW_DIR, filename)


@report_generator_bp.route('/download/<filename>')
@login_required
def download_report(filename):
    """
    Download a generated report
    
    Args:
        filename (str): Name of the report file
        
    Returns:
        The report file for download
    """
    # Determine format from extension
    if filename.endswith('.pdf'):
        return send_from_directory(PDF_DIR, filename, mimetype='application/pdf')
    elif filename.endswith('.csv'):
        return send_from_directory(CSV_DIR, filename, mimetype='text/csv')
    else:
        flash('Unsupported file format', 'danger')
        return redirect(url_for('report_generator.report_generator'))


@report_generator_bp.route('/recent')
@login_required
def recent_reports():
    """
    Get list of recent reports
    
    Returns:
        JSON list of recent reports
    """
    # Get PDF reports
    pdf_reports = list(PDF_DIR.glob('*.pdf'))
    # Get CSV reports
    csv_reports = list(CSV_DIR.glob('*.csv'))
    
    # Combine and sort by creation time (newest first)
    all_reports = []
    
    for report in pdf_reports:
        preview_filename = f"{report.stem}_preview.png"
        preview_path = PREVIEW_DIR / preview_filename
        
        # Only include reports with previews
        if preview_path.exists():
            report_type = report.stem.split('_')[0] if '_' in report.stem else 'unknown'
            
            all_reports.append({
                'id': report.stem,
                'type': report_type,
                'format': 'pdf',
                'title': _get_report_title(report_type),
                'timestamp': datetime.fromtimestamp(report.stat().st_mtime).isoformat(),
                'previewUrl': url_for('report_generator.view_preview', filename=preview_filename),
                'downloadUrl': url_for('report_generator.download_report', filename=report.name)
            })
    
    for report in csv_reports:
        preview_filename = f"{report.stem}_preview.png"
        preview_path = PREVIEW_DIR / preview_filename
        
        # Only include reports with previews
        if preview_path.exists():
            report_type = report.stem.split('_')[0] if '_' in report.stem else 'unknown'
            
            all_reports.append({
                'id': report.stem,
                'type': report_type,
                'format': 'csv',
                'title': _get_report_title(report_type),
                'timestamp': datetime.fromtimestamp(report.stat().st_mtime).isoformat(),
                'previewUrl': url_for('report_generator.view_preview', filename=preview_filename),
                'downloadUrl': url_for('report_generator.download_report', filename=report.name)
            })
    
    # Sort by timestamp (newest first)
    all_reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to 20 most recent
    all_reports = all_reports[:20]
    
    return jsonify(all_reports)


# Helper functions
def _get_report_title(report_type):
    """
    Get a human-readable title for a report type
    
    Args:
        report_type (str): Report type identifier
        
    Returns:
        str: Human-readable title
    """
    titles = {
        'daily_driver': 'Daily Driver Report',
        'pm_allocation': 'PM Allocation Report',
        'asset_status': 'Asset Status Report',
        'maintenance': 'Maintenance Report',
        'job_zone_efficiency': 'Job Zone Efficiency Report',
        'attendance_metrics': 'Attendance Metrics Report'
    }
    
    return titles.get(report_type, report_type.replace('_', ' ').title())


def _log_report_generation(report_type, format_type, success, error=None):
    """
    Log report generation activity
    
    Args:
        report_type (str): Type of report
        format_type (str): Format of report (pdf, csv)
        success (bool): Whether the generation was successful
        error (str): Error message if unsuccessful
    """
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    
    log_data = {
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'action': 'report_generation',
        'report_type': report_type,
        'format': format_type,
        'success': success
    }
    
    if error:
        log_data['error'] = error
    
    # Log to file
    try:
        with open(LOGS_DIR / 'activity_log.jsonl', 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    except Exception as e:
        logger.error(f"Error writing to activity log: {e}")


def _get_sample_report_data(report_type):
    """
    Get sample data for report generation
    
    Args:
        report_type (str): Type of report
        
    Returns:
        list or dict: Sample data for the report
    """
    if report_type == 'daily_driver':
        return [
            {'Driver': 'John Smith', 'Asset': 'Truck 101', 'Late Starts': 2, 'Early Ends': 1, 'Not On Job': 0, 'Notes': 'Traffic delays reported'},
            {'Driver': 'Sarah Johnson', 'Asset': 'Excavator 203', 'Late Starts': 0, 'Early Ends': 0, 'Not On Job': 1, 'Notes': 'Equipment malfunction'},
            {'Driver': 'Mike Williams', 'Asset': 'Bulldozer 305', 'Late Starts': 1, 'Early Ends': 0, 'Not On Job': 0, 'Notes': ''},
            {'Driver': 'Lisa Brown', 'Asset': 'Loader 410', 'Late Starts': 0, 'Early Ends': 3, 'Not On Job': 0, 'Notes': 'Scheduled maintenance'},
            {'Driver': 'David Martinez', 'Asset': 'Truck 115', 'Late Starts': 0, 'Early Ends': 0, 'Not On Job': 0, 'Notes': ''}
        ]
    elif report_type == 'pm_allocation':
        return [
            {'Asset ID': 'EQ1001', 'Description': 'CAT 320 Excavator', 'Original': '$2,500.00', 'Updated': '$2,750.00', 'Difference': '$250.00', 'Notes': 'Additional parts required'},
            {'Asset ID': 'EQ1002', 'Description': 'John Deere Loader', 'Original': '$1,800.00', 'Updated': '$1,800.00', 'Difference': '$0.00', 'Notes': ''},
            {'Asset ID': 'EQ1003', 'Description': 'Komatsu Dozer', 'Original': '$3,200.00', 'Updated': '$2,950.00', 'Difference': '-$250.00', 'Notes': 'Reduced service scope'},
            {'Asset ID': 'EQ1004', 'Description': 'Ford F350', 'Original': '$850.00', 'Updated': '$920.00', 'Difference': '$70.00', 'Notes': 'Additional labor'},
            {'Asset ID': 'EQ1005', 'Description': 'Bobcat Skid Steer', 'Original': '$1,200.00', 'Updated': '$1,200.00', 'Difference': '$0.00', 'Notes': ''}
        ]
    elif report_type == 'asset_status':
        return [
            {'Asset ID': 'EQ1001', 'Name': 'CAT 320 Excavator', 'Status': 'Active', 'Location': 'Job Site 1', 'Last Updated': '2025-05-18 08:30:00', 'Driver': 'John Smith'},
            {'Asset ID': 'EQ1002', 'Name': 'John Deere Loader', 'Status': 'Maintenance', 'Location': 'Shop', 'Last Updated': '2025-05-17 15:45:00', 'Driver': 'N/A'},
            {'Asset ID': 'EQ1003', 'Name': 'Komatsu Dozer', 'Status': 'Active', 'Location': 'Job Site 3', 'Last Updated': '2025-05-18 10:15:00', 'Driver': 'Mike Williams'},
            {'Asset ID': 'EQ1004', 'Name': 'Ford F350', 'Status': 'Active', 'Location': 'Job Site 2', 'Last Updated': '2025-05-18 09:20:00', 'Driver': 'Lisa Brown'},
            {'Asset ID': 'EQ1005', 'Name': 'Bobcat Skid Steer', 'Status': 'Inactive', 'Location': 'Yard', 'Last Updated': '2025-05-16 17:30:00', 'Driver': 'N/A'}
        ]
    elif report_type == 'maintenance':
        return [
            {'Asset ID': 'EQ1001', 'Description': 'CAT 320 Excavator', 'Service Due': '2025-06-15', 'Last Service': '2025-03-15', 'Status': 'Scheduled', 'Assigned To': 'John Doe'},
            {'Asset ID': 'EQ1002', 'Description': 'John Deere Loader', 'Service Due': '2025-05-10', 'Last Service': '2025-02-10', 'Status': 'Overdue', 'Assigned To': 'Jane Smith'},
            {'Asset ID': 'EQ1003', 'Description': 'Komatsu Dozer', 'Service Due': '2025-07-05', 'Last Service': '2025-04-05', 'Status': 'Scheduled', 'Assigned To': 'Mike Johnson'},
            {'Asset ID': 'EQ1004', 'Description': 'Ford F350', 'Service Due': '2025-06-01', 'Last Service': '2025-05-01', 'Status': 'Complete', 'Assigned To': 'Sarah Williams'},
            {'Asset ID': 'EQ1005', 'Description': 'Bobcat Skid Steer', 'Service Due': '2025-05-20', 'Last Service': '2025-02-20', 'Status': 'Overdue', 'Assigned To': 'John Doe'}
        ]
    elif report_type == 'job_zone_efficiency':
        return [
            {'Job Site': 'Site A', 'Asset Type': 'Excavator', 'Time in Zone': '45.5 hrs', 'Expected Time': '50 hrs', 'Efficiency': '91%', 'Notes': 'Weather delays'},
            {'Job Site': 'Site B', 'Asset Type': 'Dozer', 'Time in Zone': '38.2 hrs', 'Expected Time': '40 hrs', 'Efficiency': '96%', 'Notes': ''},
            {'Job Site': 'Site C', 'Asset Type': 'Loader', 'Time in Zone': '32.5 hrs', 'Expected Time': '45 hrs', 'Efficiency': '72%', 'Notes': 'Equipment breakdown'},
            {'Job Site': 'Site A', 'Asset Type': 'Truck', 'Time in Zone': '42.0 hrs', 'Expected Time': '40 hrs', 'Efficiency': '105%', 'Notes': 'Above expected performance'},
            {'Job Site': 'Site D', 'Asset Type': 'Excavator', 'Time in Zone': '28.5 hrs', 'Expected Time': '35 hrs', 'Efficiency': '81%', 'Notes': 'Operator change midweek'}
        ]
    elif report_type == 'attendance_metrics':
        return [
            {'Driver': 'John Smith', 'Late Starts': 2, 'Early Ends': 1, 'Not On Job': 0, 'Total Incidents': 3, 'Trend': 'Improving'},
            {'Driver': 'Sarah Johnson', 'Late Starts': 0, 'Early Ends': 0, 'Not On Job': 1, 'Total Incidents': 1, 'Trend': 'Stable'},
            {'Driver': 'Mike Williams', 'Late Starts': 4, 'Early Ends': 2, 'Not On Job': 1, 'Total Incidents': 7, 'Trend': 'Declining'},
            {'Driver': 'Lisa Brown', 'Late Starts': 0, 'Early Ends': 0, 'Not On Job': 0, 'Total Incidents': 0, 'Trend': 'Excellent'},
            {'Driver': 'David Martinez', 'Late Starts': 1, 'Early Ends': 0, 'Not On Job': 0, 'Total Incidents': 1, 'Trend': 'Improving'}
        ]
    else:
        # Generic data for other report types
        return [
            {'Column 1': 'Data 1A', 'Column 2': 'Data 1B', 'Column 3': 'Data 1C'},
            {'Column 1': 'Data 2A', 'Column 2': 'Data 2B', 'Column 3': 'Data 2C'},
            {'Column 1': 'Data 3A', 'Column 2': 'Data 3B', 'Column 3': 'Data 3C'},
            {'Column 1': 'Data 4A', 'Column 2': 'Data 4B', 'Column 3': 'Data 4C'},
            {'Column 1': 'Data 5A', 'Column 2': 'Data 5B', 'Column 3': 'Data 5C'}
        ]
@report_generator_bp.route('/generator')
def generator():
    """Handler for /generator"""
    try:
        # Add your route handler logic here
        return render_template('report_generator/generator.html')
    except Exception as e:
        logger.error(f"Error in generator: {e}")
        return render_template('error.html', error=str(e)), 500

@report_generator_bp.route('/generate')
def generate():
    """Handler for /generate"""
    try:
        # Add your route handler logic here
        return render_template('report_generator/generate.html')
    except Exception as e:
        logger.error(f"Error in generate: {e}")
        return render_template('error.html', error=str(e)), 500

@report_generator_bp.route('/preview/<filename>')
def preview_<filename>():
    """Handler for /preview/<filename>"""
    try:
        # Add your route handler logic here
        return render_template('report_generator/preview_<filename>.html')
    except Exception as e:
        logger.error(f"Error in preview_<filename>: {e}")
        return render_template('error.html', error=str(e)), 500

@report_generator_bp.route('/download/<filename>')
def download_<filename>():
    """Handler for /download/<filename>"""
    try:
        # Add your route handler logic here
        return render_template('report_generator/download_<filename>.html')
    except Exception as e:
        logger.error(f"Error in download_<filename>: {e}")
        return render_template('error.html', error=str(e)), 500

@report_generator_bp.route('/recent')
def recent():
    """Handler for /recent"""
    try:
        # Add your route handler logic here
        return render_template('report_generator/recent.html')
    except Exception as e:
        logger.error(f"Error in recent: {e}")
        return render_template('error.html', error=str(e)), 500
