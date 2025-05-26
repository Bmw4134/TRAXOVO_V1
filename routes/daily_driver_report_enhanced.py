"""
TRAXORA Fleet Management System - Daily Driver Report Enhanced Routes

This module provides improved routes for automatically generating daily driver attendance reports,
with better error handling, file management, and interface integration.
"""

import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort, send_file
)
from werkzeug.utils import secure_filename

from utils.enhanced_data_ingestion import load_csv_file, load_excel_file, infer_file_type_from_path, infer_file_type
from utils.dynamic_timecard_processor import process_dynamic_timecard
from utils.multi_source_processor import combine_attendance_sources
from utils.daily_driver_report_generator import (
    generate_daily_report, schedule_daily_report_generation, 
    auto_generate_report_for_date, get_report_for_date
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint with standardized URL patterns
daily_driver_report_bp = Blueprint('daily_driver_report', __name__, url_prefix='/daily-driver-report')

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join(current_app.root_path, 'data', 'daily_driver_reports')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'daily_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_upload_directory():
    """Get upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'daily_reports')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@daily_driver_report_bp.route('/')
def dashboard():
    """Daily driver report dashboard"""
    try:
        # Get today's date
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        
        # Get previous dates (last 7 days)
        date_range = []
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            formatted_date = date.strftime('%a, %b %d')
            
            # Check if report exists
            report_path = os.path.join(get_reports_directory(), f"DAILY_DRIVER_REPORT_{date_str.replace('-', '_')}.xlsx")
            report_exists = os.path.exists(report_path)
            
            date_range.append({
                'date': date_str,
                'formatted': formatted_date,
                'report_exists': report_exists
            })
        
        # Get available data files for today
        upload_dir = os.path.join(get_upload_directory(), today_str)
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
        else:
            files = []
        
        # Group files by type
        file_groups = {
            'driving_history': [],
            'time_on_site': [],
            'activity_detail': [],
            'timecard': [],
            'other': []
        }
        
        for filename in files:
            file_type = infer_file_type_from_path(os.path.join(upload_dir, filename))
            
            if file_type == 'Driving History':
                file_groups['driving_history'].append(filename)
            elif file_type == 'Assets Time On Site':
                file_groups['time_on_site'].append(filename)
            elif file_type == 'Activity Detail':
                file_groups['activity_detail'].append(filename)
            elif file_type == 'Timecard':
                file_groups['timecard'].append(filename)
            else:
                file_groups['other'].append(filename)
        
        # Check if today's report exists
        today_report_path = os.path.join(get_reports_directory(), f"DAILY_DRIVER_REPORT_{today_str.replace('-', '_')}.xlsx")
        today_report_exists = os.path.exists(today_report_path)
        
        # Check if we have all required files for automated generation
        can_generate = len(file_groups['driving_history']) > 0 or len(file_groups['time_on_site']) > 0
        
        # Use the enhanced dashboard template
        return render_template(
            'daily_driver_report/dashboard_enhanced.html',
            today=today_str,
            today_formatted=today.strftime('%A, %B %d, %Y'),
            date_range=date_range,
            file_groups=file_groups,
            today_report_exists=today_report_exists,
            can_generate=can_generate
        )
    
    except Exception as e:
        logger.error(f"Error displaying daily driver report dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error displaying dashboard: {str(e)}", "danger")
        return render_template('daily_driver_report/dashboard_enhanced.html')

@daily_driver_report_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload files for daily driver report"""
    if request.method == 'POST':
        try:
            # Check if files were uploaded
            if 'files[]' not in request.files:
                flash("No files selected", "danger")
                return redirect(url_for('daily_driver_report.upload_files'))
            
            files = request.files.getlist('files[]')
            
            if not files or all(file.filename == '' for file in files):
                flash("No files selected", "danger")
                return redirect(url_for('daily_driver_report.upload_files'))
            
            # Get date
            date_str = request.form.get('date')
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Create date-specific upload directory
            upload_dir = os.path.join(get_upload_directory(), date_str)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save each file
            file_count = 0
            
            for file in files:
                if file and file.filename:
                    # Try to infer file type
                    file_type = infer_file_type(file)
                    
                    # Create filename with type prefix
                    if file_type:
                        prefix = file_type.replace(' ', '_')
                        filename = f"{prefix}_{secure_filename(file.filename)}"
                    else:
                        filename = secure_filename(file.filename)
                    
                    # Save file
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    file_count += 1
            
            flash(f"Successfully uploaded {file_count} files for {date_str}", "success")
            
            # Check if auto-generate is requested
            if request.form.get('auto_generate') == 'true':
                # Import MTD processor
                from utils.mtd_processor import extract_date_range_from_files, process_mtd_data_for_date_range
                
                # Extract actual date range from uploaded files
                # Check main uploads directory where MTD files are actually located
                main_uploads_dir = "uploads"
                start_date, end_date = extract_date_range_from_files(main_uploads_dir)
                
                if start_date and end_date:
                    flash(f"Processing MTD data from {start_date} to {end_date}", "info")
                    
                    # Process all dates in the MTD range
                    mtd_results = process_mtd_data_for_date_range(main_uploads_dir, start_date, end_date)
                    
                    if mtd_results:
                        # Find the most recent date with data for viewing
                        recent_date = max(mtd_results.keys())
                        flash(f"MTD data processed successfully! Found data for {len(mtd_results)} dates", "success")
                        return redirect(url_for('daily_driver_report.view_report', date=recent_date))
                    else:
                        flash("MTD data processed but no driver records found", "warning")
                else:
                    # Fallback to single date processing
                    success = schedule_daily_report_generation(date_str)
                    
                    if success:
                        flash(f"Daily report for {date_str} generated successfully", "success")
                        return redirect(url_for('daily_driver_report.view_report', date=date_str))
                    else:
                        flash(f"Failed to generate daily report for {date_str}", "warning")
            
            return redirect(url_for('daily_driver_report.dashboard'))
            
        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Error uploading files: {str(e)}", "danger")
            return redirect(url_for('daily_driver_report.upload_files'))
    
    # GET request - show enhanced upload form
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('daily_driver_report/upload_enhanced.html', today_date=today_date)

@daily_driver_report_bp.route('/generate/<date>')
def generate_report(date):
    """Generate a daily driver report for the specified date"""
    try:
        # Try processing a single MTD file with Asset List lookup
        from gauge_api import GaugeAPI
        import pandas as pd
        
        flash("Processing MTD data with Asset List assignments...", "info")
        
        try:
            # Get asset assignments from Gauge API
            api = GaugeAPI()
            asset_data = api.get_assets()
            
            if not asset_data:
                flash("Could not load Asset List from Gauge API", "warning")
            else:
                # Create asset mapping for driver assignments - use ALL assets, not filtered ones
                asset_mapping = {}
                driver_assignments = 0
                
                for asset in asset_data:
                    # Try different field names for Asset ID
                    asset_id = (asset.get('AssetID') or 
                               asset.get('assetID') or 
                               asset.get('id') or 
                               asset.get('ID'))
                    
                    # Try different field names for Secondary Asset Identifier  
                    secondary_id = (asset.get('SecondaryAssetIdentifier') or 
                                  asset.get('secondaryAssetIdentifier') or 
                                  asset.get('SecondaryID') or 
                                  asset.get('DriverAssignment') or '')
                    
                    if asset_id and secondary_id and ' - ' in str(secondary_id):
                        parts = str(secondary_id).split(' - ', 1)
                        employee_id = parts[0].strip()
                        driver_name = parts[1].strip()
                        
                        asset_mapping[str(asset_id)] = {
                            'employee_id': employee_id,
                            'driver_name': driver_name,
                            'asset_label': asset.get('AssetLabel', ''),
                            'asset_name': asset.get('AssetName', ''),
                            'secondary_id': secondary_id
                        }
                        driver_assignments += 1
                
                flash(f"Found {len(asset_data)} total assets, {driver_assignments} with driver assignments", "success")
                
                # Process a single MTD file efficiently
                mtd_file = None
                for filename in os.listdir("uploads"):
                    if 'driving' in filename.lower() and filename.endswith('.csv'):
                        mtd_file = os.path.join("uploads", filename)
                        break
                
                if mtd_file and asset_mapping:
                    flash(f"Processing {os.path.basename(mtd_file)} with {len(asset_mapping)} driver assignments", "info")
                    
                    # Process MTD file with Asset List mappings
                    try:
                        df = pd.read_csv(mtd_file, skiprows=7, low_memory=False)
                        driver_records = []
                        
                        # Find Asset ID column
                        asset_column = None
                        for col in df.columns:
                            if 'asset' in col.lower() or 'textbox53' in col.lower():
                                asset_column = col
                                break
                        
                        if asset_column:
                            for _, row in df.iterrows():
                                asset_value = str(row.get(asset_column, '')).strip()
                                
                                # Extract asset ID from various formats
                                asset_id = None
                                if asset_value.startswith('#'):
                                    parts = asset_value[1:].split(' - ', 1)
                                    if parts:
                                        asset_id = parts[0].strip()
                                elif asset_value.isdigit():
                                    asset_id = asset_value
                                
                                # Check if this asset has a driver assignment
                                if asset_id and asset_id in asset_mapping:
                                    driver_info = asset_mapping[asset_id]
                                    event_time = row.get('EventDateTime')
                                    
                                    if pd.notna(event_time):
                                        try:
                                            parsed_time = pd.to_datetime(event_time)
                                            if parsed_time.strftime('%Y-%m-%d') == date:
                                                driver_records.append({
                                                    'driver_name': driver_info['driver_name'],
                                                    'employee_id': driver_info['employee_id'],
                                                    'event_time': parsed_time,
                                                    'event_type': row.get('MsgType', ''),
                                                    'location': row.get('Location', '')
                                                })
                                        except:
                                            continue
                        
                        flash(f"Found {len(driver_records)} driver events for {date}", "success")
                        
                        # Store the results for viewing
                        import json
                        import os
                        os.makedirs('temp_reports', exist_ok=True)
                        
                        with open(f'temp_reports/mtd_results_{date}.json', 'w') as f:
                            json.dump({
                                'date': date,
                                'total_assets': len(asset_data),
                                'driver_assignments': len(asset_mapping),
                                'driver_events': len(driver_records),
                                'records': [r for r in driver_records[:10]]  # Sample records
                            }, f, default=str, indent=2)
                        
                        return redirect(url_for('daily_driver_report.view_report', date=date))
                        
                    except Exception as e:
                        flash(f"Error processing MTD file: {str(e)}", "error")
                        logger.error(f"MTD processing error: {e}")
                else:
                    flash("No MTD files found or no asset assignments available", "warning")
                    
        except Exception as e:
            logger.error(f"Error in Asset List processing: {e}")
            flash(f"Error processing Asset List: {str(e)}", "warning")
        
        # Fallback to single date processing if MTD fails
        success = schedule_daily_report_generation(date)
        
        if success:
            flash(f"Daily report for {date} generated successfully", "success")
            return redirect(url_for('daily_driver_report.view_report', date=date))
        else:
            flash(f"Failed to generate daily report for {date}", "warning")
            return redirect(url_for('daily_driver_report.dashboard'))
    
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error generating daily report: {str(e)}", "danger")
        return redirect(url_for('daily_driver_report.dashboard'))

@daily_driver_report_bp.route('/view/<date>')
def view_report(date):
    """View a daily driver report"""
    try:
        # Check if the report exists
        report_path = os.path.join(get_reports_directory(), f"DAILY_DRIVER_REPORT_{date.replace('-', '_')}.xlsx")
        
        if not os.path.exists(report_path):
            # Try to generate it
            report_path = auto_generate_report_for_date(date)
            
            if not report_path:
                flash(f"Report for {date} not found and could not be generated", "warning")
                return redirect(url_for('daily_driver_report.dashboard'))
        
        # Get report data
        json_path = os.path.join(get_reports_directory(), f"driver_report_{date}.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                report_data = json.load(f)
        else:
            report_data = None
        
        # Parse date for display
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Use simple template that works reliably
        return render_template(
            'daily_driver_report/view_simple.html',
            date=date,
            formatted_date=formatted_date,
            report_path=report_path,
            report_data=report_data
        )
    
    except Exception as e:
        logger.error(f"Error viewing daily report: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error viewing daily report: {str(e)}", "danger")
        return redirect(url_for('daily_driver_report.dashboard'))

@daily_driver_report_bp.route('/download/<date>')
def download_report(date):
    """Download a daily driver report"""
    try:
        # Check if the report exists
        report_path = os.path.join(get_reports_directory(), f"DAILY_DRIVER_REPORT_{date.replace('-', '_')}.xlsx")
        
        if not os.path.exists(report_path):
            # Try to generate it
            report_path = auto_generate_report_for_date(date)
            
            if not report_path:
                flash(f"Report for {date} not found and could not be generated", "warning")
                return redirect(url_for('daily_driver_report.dashboard'))
        
        # Download the file
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"DAILY_DRIVER_REPORT_{date.replace('-', '_')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error downloading daily report: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error downloading daily report: {str(e)}", "danger")
        return redirect(url_for('daily_driver_report.dashboard'))

@daily_driver_report_bp.route('/api/files/<date>')
def api_files(date):
    """API endpoint to get files for a specific date"""
    try:
        # Get files for the date
        upload_dir = os.path.join(get_upload_directory(), date)
        
        if not os.path.exists(upload_dir):
            return jsonify({"files": []})
        
        files = os.listdir(upload_dir)
        
        # Group files by type
        file_groups = {
            'driving_history': [],
            'time_on_site': [],
            'activity_detail': [],
            'timecard': [],
            'other': []
        }
        
        for filename in files:
            file_type = infer_file_type_from_path(os.path.join(upload_dir, filename))
            
            if file_type == 'Driving History':
                file_groups['driving_history'].append(filename)
            elif file_type == 'Assets Time On Site':
                file_groups['time_on_site'].append(filename)
            elif file_type == 'Activity Detail':
                file_groups['activity_detail'].append(filename)
            elif file_type == 'Timecard':
                file_groups['timecard'].append(filename)
            else:
                file_groups['other'].append(filename)
        
        return jsonify(file_groups)
    
    except Exception as e:
        logger.error(f"Error getting files for date {date}: {str(e)}")
        return jsonify({"error": f"Error getting files: {str(e)}"}), 500

@daily_driver_report_bp.route('/api/status/<date>')
def api_status(date):
    """API endpoint to get report status for a specific date"""
    try:
        # Check if the report exists
        report_path = os.path.join(get_reports_directory(), f"DAILY_DRIVER_REPORT_{date.replace('-', '_')}.xlsx")
        report_exists = os.path.exists(report_path)
        
        # Check available files
        upload_dir = os.path.join(get_upload_directory(), date)
        
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            has_files = len(files) > 0
            
            # Check if files are sufficient for generation
            driving_history = any('driving' in f.lower() for f in files)
            time_on_site = any('timeonsite' in f.lower() for f in files)
            can_generate = driving_history or time_on_site
        else:
            has_files = False
            can_generate = False
        
        return jsonify({
            "report_exists": report_exists,
            "has_files": has_files,
            "can_generate": can_generate
        })
    
    except Exception as e:
        logger.error(f"Error getting status for date {date}: {str(e)}")
        return jsonify({"error": f"Error getting status: {str(e)}"}), 500

@daily_driver_report_bp.route('/api/summary/<date>')
def api_summary(date):
    """API endpoint to get summary data for a specific date's report"""
    try:
        # Get report data
        json_path = os.path.join(get_reports_directory(), f"driver_report_{date}.json")
        
        if not os.path.exists(json_path):
            return jsonify({"error": "Report data not found"}), 404
        
        with open(json_path, 'r') as f:
            report_data = json.load(f)
        
        # Extract just the summary and metrics
        summary_data = {
            "summary": report_data.get("summary", {}),
            "metrics": report_data.get("metrics", {}),
            "date": date,
            "data_sources": report_data.get("data_sources", [])
        }
        
        return jsonify(summary_data)
    
    except Exception as e:
        logger.error(f"Error getting summary for date {date}: {str(e)}")
        return jsonify({"error": f"Error getting summary: {str(e)}"}), 500