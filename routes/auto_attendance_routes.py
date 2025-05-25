"""
TRAXORA Fleet Management System - Automatic Attendance Routes

This module provides routes for the automatic attendance processing system,
allowing users to trigger and monitor automatic report generation.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, send_file

from utils.auto_attendance_processor import (
    AutoAttendanceProcessor,
    process_specific_date,
    process_yesterday,
    process_date_range
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auto_attendance_bp = Blueprint('auto_attendance_bp', __name__, url_prefix='/auto-attendance')

@auto_attendance_bp.route('/')
def dashboard():
    """Auto attendance dashboard"""
    try:
        # Get processing logs
        processor = AutoAttendanceProcessor()
        logs_dir = processor.logs_dir
        
        # Load processing logs
        processing_logs = []
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
            for log_file in sorted(log_files, reverse=True)[:10]:  # Show most recent 10 logs
                try:
                    with open(os.path.join(logs_dir, log_file), 'r') as f:
                        log_data = json.load(f)
                        processing_logs.append(log_data)
                except Exception as e:
                    logger.error(f"Error loading log file {log_file}: {str(e)}")
        
        # Get results directory
        results_dir = processor.results_dir
        
        # Get available reports
        available_reports = []
        if os.path.exists(results_dir):
            report_files = [f for f in os.listdir(results_dir) if f.endswith('.json') or f.endswith('.xlsx')]
            for report_file in sorted(report_files, reverse=True)[:20]:  # Show most recent 20 reports
                file_path = os.path.join(results_dir, report_file)
                file_stats = os.stat(file_path)
                report_date = None
                
                # Try to extract date from filename
                parts = report_file.split('_')
                if len(parts) > 1:
                    try:
                        date_part = parts[1].split('.')[0]
                        report_date = datetime.strptime(date_part, '%Y-%m-%d').strftime('%Y-%m-%d')
                    except:
                        report_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d')
                
                available_reports.append({
                    'filename': report_file,
                    'date': report_date or 'Unknown',
                    'size_kb': round(file_stats.st_size / 1024, 1),
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Default date range (last 7 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        return render_template(
            'auto_attendance/dashboard.html',
            processing_logs=processing_logs,
            available_reports=available_reports,
            default_start_date=start_date.strftime('%Y-%m-%d'),
            default_end_date=end_date.strftime('%Y-%m-%d')
        )
    
    except Exception as e:
        logger.error(f"Error displaying auto attendance dashboard: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return render_template('auto_attendance/dashboard.html', error=str(e))

@auto_attendance_bp.route('/process', methods=['POST'])
def process():
    """Process attendance data for a specific date or date range"""
    try:
        # Get form data
        process_type = request.form.get('process_type', 'single')
        force = request.form.get('force', 'false') == 'true'
        
        if process_type == 'single':
            # Process single date
            date_str = request.form.get('date')
            if not date_str:
                flash("Date is required", "danger")
                return redirect(url_for('auto_attendance_bp.dashboard'))
            
            result = process_specific_date(date_str, force)
            
            if result['success']:
                flash(f"Successfully processed attendance data for {date_str}", "success")
            else:
                flash(f"Error processing attendance data: {result.get('error', 'Unknown error')}", "danger")
                
        elif process_type == 'yesterday':
            # Process yesterday
            result = process_yesterday()
            
            if result['success']:
                flash(f"Successfully processed attendance data for yesterday", "success")
            else:
                flash(f"Error processing attendance data: {result.get('error', 'Unknown error')}", "danger")
                
        elif process_type == 'range':
            # Process date range
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
            if not start_date or not end_date:
                flash("Start date and end date are required", "danger")
                return redirect(url_for('auto_attendance_bp.dashboard'))
                
            results = process_date_range(start_date, end_date, force)
            
            success_count = sum(1 for r in results if r['success'])
            if success_count == len(results):
                flash(f"Successfully processed attendance data for all {len(results)} dates", "success")
            else:
                flash(f"Processed {success_count} of {len(results)} dates successfully", "warning")
        
        return redirect(url_for('auto_attendance_bp.dashboard'))
        
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('auto_attendance_bp.dashboard'))

@auto_attendance_bp.route('/download/<filename>')
def download_report(filename):
    """Download a report file"""
    try:
        processor = AutoAttendanceProcessor()
        file_path = os.path.join(processor.results_dir, filename)
        
        if not os.path.exists(file_path):
            flash(f"Report file not found: {filename}", "danger")
            return redirect(url_for('auto_attendance_bp.dashboard'))
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('auto_attendance_bp.dashboard'))

@auto_attendance_bp.route('/api/status')
def api_status():
    """API endpoint to get processor status"""
    try:
        processor = AutoAttendanceProcessor()
        
        # Get processing logs
        logs_dir = processor.logs_dir
        processing_logs = []
        
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
            for log_file in sorted(log_files, reverse=True)[:5]:  # Show most recent 5 logs
                try:
                    with open(os.path.join(logs_dir, log_file), 'r') as f:
                        log_data = json.load(f)
                        processing_logs.append(log_data)
                except Exception as e:
                    logger.error(f"Error loading log file {log_file}: {str(e)}")
        
        return jsonify({
            'status': 'active',
            'recent_logs': processing_logs,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting processor status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500