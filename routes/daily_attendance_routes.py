"""
Daily Attendance Routes

This module provides routes for the daily driver attendance report system,
allowing users to view, generate, and download reports.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file

from utils.legacy_formula_connector import process_daily_driver_report

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
daily_attendance_bp = Blueprint('daily_attendance', __name__, url_prefix='/daily-attendance')

@daily_attendance_bp.route('/')
def index():
    """Display the daily attendance dashboard"""
    # Get available dates from the reports directory
    available_dates = get_available_report_dates()
    
    # Get selected date from query parameter or use the latest date
    selected_date = request.args.get('date')
    if not selected_date and available_dates:
        selected_date = available_dates[0]  # Most recent date
    
    # Load report data for the selected date
    report_data = load_report_data(selected_date)
    
    return render_template(
        'daily_attendance/index.html',
        available_dates=available_dates,
        selected_date=selected_date,
        report_data=report_data
    )

@daily_attendance_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new attendance report"""
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please select a date for the report', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    try:
        # Get file paths from the form
        driving_history_file = request.form.get('driving_history_file')
        activity_detail_file = request.form.get('activity_detail_file')
        assets_time_file = request.form.get('assets_time_file')
        
        # Process the report using the legacy formula connector
        result = process_daily_driver_report(
            date_str, 
            driving_history_file, 
            activity_detail_file, 
            assets_time_file
        )
        
        if result["success"]:
            flash(f'Successfully generated report for {date_str}', 'success')
        else:
            flash(f'Error generating report: {result.get("error", "Unknown error")}', 'danger')
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        flash(f'Error generating report: {str(e)}', 'danger')
    
    return redirect(url_for('daily_attendance.index', date=date_str))

@daily_attendance_bp.route('/download/json/<date_str>')
def download_json(date_str):
    """Download the JSON report for a specific date"""
    report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
    
    if not os.path.exists(report_file):
        flash(f'Report not found for {date_str}', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    return send_file(report_file, as_attachment=True, download_name=f"attendance_report_{date_str}.json")

@daily_attendance_bp.route('/download/excel/<date_str>')
def download_excel(date_str):
    """Download the Excel report for a specific date"""
    report_file = f"exports/daily/daily_driver_report_{date_str}.xlsx"
    
    if not os.path.exists(report_file):
        flash(f'Excel report not found for {date_str}', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    return send_file(report_file, as_attachment=True, download_name=f"daily_driver_report_{date_str}.xlsx")

@daily_attendance_bp.route('/api/dates')
def api_dates():
    """API endpoint to get available report dates"""
    available_dates = get_available_report_dates()
    return jsonify(available_dates)

@daily_attendance_bp.route('/api/report/<date_str>')
def api_report(date_str):
    """API endpoint to get report data for a specific date"""
    report_data = load_report_data(date_str)
    
    if not report_data:
        return jsonify({"error": "Report not found"}), 404
    
    return jsonify(report_data)

@daily_attendance_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload data files for report generation"""
    if request.method == 'POST':
        # Check if the Preview button was clicked
        if 'preview_files' in request.form:
            # Create a temporary directory for preview files
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # Check if files were uploaded
            if 'driving_history' not in request.files and 'activity_detail' not in request.files and 'assets_time' not in request.files:
                flash('No files selected for preview', 'warning')
                return redirect(request.url)
            
            # Get selected date
            date_str = request.form.get('date')
            process_all_dates = request.form.get('process_all_dates') == 'on'
            
            # Variables to store preview data
            previews = {}
            file_info = {}
            dates_detected = []
            
            # Process driving history file for preview
            if 'driving_history' in request.files and request.files['driving_history'].filename:
                file = request.files['driving_history']
                filename = file.filename
                temp_path = os.path.join(temp_dir, filename)
                file.save(temp_path)
                
                try:
                    import pandas as pd
                    # Try to read the file with different methods
                    try:
                        df = pd.read_csv(temp_path, on_bad_lines='skip')
                    except:
                        try:
                            df = pd.read_csv(temp_path, sep=None, engine='python', on_bad_lines='skip')
                        except:
                            df = pd.read_csv(temp_path, sep=',', engine='python', 
                                          on_bad_lines='skip', skipinitialspace=True, quotechar='"')
                    
                    # Get preview data
                    preview_rows = min(5, len(df))
                    previews['driving_history'] = df.head(preview_rows).to_html(classes='table table-sm table-striped table-dark')
                    file_info['driving_history'] = {
                        'filename': filename,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': list(df.columns)
                    }
                    
                    # Try to extract dates
                    if 'Date' in df.columns:
                        try:
                            df['Date'] = pd.to_datetime(df['Date'])
                            dates = df['Date'].dt.date.unique()
                            dates_str = [d.strftime('%Y-%m-%d') for d in dates]
                            dates_detected.extend(dates_str)
                            file_info['driving_history']['dates'] = dates_str
                        except Exception as e:
                            logger.warning(f"Error extracting dates: {str(e)}")
                except Exception as e:
                    previews['driving_history'] = f"<div class='alert alert-danger'>Error previewing file: {str(e)}</div>"
                    file_info['driving_history'] = {
                        'filename': filename,
                        'error': str(e)
                    }
            
            # Process activity detail file for preview
            if 'activity_detail' in request.files and request.files['activity_detail'].filename:
                file = request.files['activity_detail']
                filename = file.filename
                temp_path = os.path.join(temp_dir, filename)
                file.save(temp_path)
                
                try:
                    import pandas as pd
                    # Try to read the file with different methods
                    try:
                        df = pd.read_csv(temp_path, on_bad_lines='skip')
                    except:
                        try:
                            df = pd.read_csv(temp_path, sep=None, engine='python', on_bad_lines='skip')
                        except:
                            df = pd.read_csv(temp_path, sep=',', engine='python', 
                                          on_bad_lines='skip', skipinitialspace=True, quotechar='"')
                    
                    # Get preview data
                    preview_rows = min(5, len(df))
                    previews['activity_detail'] = df.head(preview_rows).to_html(classes='table table-sm table-striped table-dark')
                    file_info['activity_detail'] = {
                        'filename': filename,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': list(df.columns)
                    }
                except Exception as e:
                    previews['activity_detail'] = f"<div class='alert alert-danger'>Error previewing file: {str(e)}</div>"
                    file_info['activity_detail'] = {
                        'filename': filename,
                        'error': str(e)
                    }
            
            # Process assets time file for preview
            if 'assets_time' in request.files and request.files['assets_time'].filename:
                file = request.files['assets_time']
                filename = file.filename
                temp_path = os.path.join(temp_dir, filename)
                file.save(temp_path)
                
                try:
                    import pandas as pd
                    # Try to read the file with different methods
                    try:
                        df = pd.read_csv(temp_path, on_bad_lines='skip')
                    except:
                        try:
                            df = pd.read_csv(temp_path, sep=None, engine='python', on_bad_lines='skip')
                        except:
                            df = pd.read_csv(temp_path, sep=',', engine='python', 
                                          on_bad_lines='skip', skipinitialspace=True, quotechar='"')
                    
                    # Get preview data
                    preview_rows = min(5, len(df))
                    previews['assets_time'] = df.head(preview_rows).to_html(classes='table table-sm table-striped table-dark')
                    file_info['assets_time'] = {
                        'filename': filename,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': list(df.columns)
                    }
                except Exception as e:
                    previews['assets_time'] = f"<div class='alert alert-danger'>Error previewing file: {str(e)}</div>"
                    file_info['assets_time'] = {
                        'filename': filename,
                        'error': str(e)
                    }
            
            # Clean up the temporary directory
            import shutil
            shutil.rmtree(temp_dir)
            
            # If we detected dates from the files
            if dates_detected and not date_str:
                date_str = dates_detected[0]  # Use the first detected date
                
            # Pass everything to the template for preview
            return render_template(
                'daily_attendance/upload.html',
                date=date_str,
                process_all_dates=process_all_dates,
                previews=previews,
                file_info=file_info,
                dates_detected=dates_detected,
                is_preview=True
            )
        
        # Regular processing - files were uploaded and process button was clicked
        # Check if files were uploaded
        if 'driving_history' not in request.files and 'activity_detail' not in request.files and 'assets_time' not in request.files:
            flash('No files selected', 'warning')
            return redirect(request.url)
        
        # Get selected date
        date_str = request.form.get('date')
        process_all_dates = request.form.get('process_all_dates') == 'on'
        
        if not date_str and not process_all_dates:
            flash('Please select a date or choose to process all dates in the files', 'warning')
            return redirect(request.url)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Process driving history file
        driving_history_file = None
        if 'driving_history' in request.files and request.files['driving_history'].filename:
            file = request.files['driving_history']
            # Don't modify the original filename to keep all metadata
            filename = file.filename
            file_path = os.path.join('data', filename)
            file.save(file_path)
            driving_history_file = file_path
        
        # Process activity detail file
        activity_detail_file = None
        if 'activity_detail' in request.files and request.files['activity_detail'].filename:
            file = request.files['activity_detail']
            # Don't modify the original filename to keep all metadata
            filename = file.filename
            file_path = os.path.join('data', filename)
            file.save(file_path)
            activity_detail_file = file_path
        
        # Process assets time file
        assets_time_file = None
        if 'assets_time' in request.files and request.files['assets_time'].filename:
            file = request.files['assets_time']
            # Don't modify the original filename to keep all metadata
            filename = file.filename
            file_path = os.path.join('data', filename)
            file.save(file_path)
            assets_time_file = file_path
        
        # If processing all dates, discover dates from the files
        processed_dates = []
        if process_all_dates:
            # Try to extract dates from the driving history file
            try:
                import pandas as pd
                if driving_history_file:
                    try:
                        # Try different parsing options to handle various CSV formats
                        df = pd.read_csv(driving_history_file, on_bad_lines='skip')
                    except:
                        try:
                            # If that fails, try with more flexible parsing
                            df = pd.read_csv(driving_history_file, sep=None, engine='python', on_bad_lines='skip')
                        except:
                            # If all else fails, try the most permissive approach
                            df = pd.read_csv(driving_history_file, sep=',', engine='python', 
                                            on_bad_lines='skip', skipinitialspace=True, quotechar='"')
                        
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
                        dates = df['Date'].dt.date.unique()
                        for date in dates:
                            date_str = date.strftime('%Y-%m-%d')
                            logger.info(f"Processing detected date: {date_str}")
                            result = process_daily_driver_report(
                                date_str, 
                                driving_history_file, 
                                activity_detail_file, 
                                assets_time_file
                            )
                            if result["success"]:
                                processed_dates.append(date_str)
                                logger.info(f"Successfully processed date: {date_str}")
                            else:
                                logger.error(f"Error processing date {date_str}: {result.get('error')}")
                else:
                    flash('No driving history file provided for automatic date detection', 'warning')
                    return redirect(request.url)
                
                if processed_dates:
                    flash(f'Successfully processed reports for the following dates: {", ".join(processed_dates)}', 'success')
                else:
                    flash('No dates were processed successfully. Please check your files.', 'warning')
                
                # Redirect to the first processed date, or the index if none
                if processed_dates:
                    return redirect(url_for('daily_attendance.index', date=processed_dates[0]))
                else:
                    return redirect(url_for('daily_attendance.index'))
            
            except Exception as e:
                logger.error(f"Error during bulk processing: {str(e)}")
                flash(f'Error processing multiple dates: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            # Process a single date
            result = process_daily_driver_report(
                date_str, 
                driving_history_file, 
                activity_detail_file, 
                assets_time_file
            )
            
            if result["success"]:
                flash(f'Successfully generated report for {date_str}', 'success')
            else:
                flash(f'Error generating report: {result.get("error", "Unknown error")}', 'danger')
            
            return redirect(url_for('daily_attendance.index', date=date_str))
    
    # GET request - show upload form
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('daily_attendance/upload.html', date=today)

# Helper functions

def get_available_report_dates():
    """Get a list of available report dates"""
    reports_dir = "reports/daily_driver_reports"
    available_dates = []
    
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.startswith("attendance_report_") and filename.endswith(".json"):
                date_str = filename.replace("attendance_report_", "").replace(".json", "")
                try:
                    # Validate date format
                    datetime.strptime(date_str, "%Y-%m-%d")
                    available_dates.append(date_str)
                except ValueError:
                    continue
    
    # Sort dates in descending order (newest first)
    available_dates.sort(reverse=True)
    
    return available_dates

def load_report_data(date_str):
    """Load report data for a specific date"""
    if not date_str:
        return None
    
    report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
    
    if not os.path.exists(report_file):
        return None
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Ensure all required fields exist in the report data
        if "summary" not in report_data:
            report_data["summary"] = {}
            
        summary = report_data["summary"]
        # Ensure all required metrics exist
        if "total_drivers" not in summary:
            summary["total_drivers"] = len(report_data.get("drivers", []))
        if "on_time" not in summary:
            summary["on_time"] = sum(1 for d in report_data.get("drivers", []) if d.get("classification") == "ON_TIME")
        if "late_start" not in summary:
            summary["late_start"] = sum(1 for d in report_data.get("drivers", []) if d.get("classification") == "LATE_START")
        if "early_end" not in summary:
            summary["early_end"] = sum(1 for d in report_data.get("drivers", []) if d.get("classification") == "EARLY_END")
        if "not_on_job" not in summary:
            summary["not_on_job"] = sum(1 for d in report_data.get("drivers", []) if d.get("classification") == "NOT_ON_JOB")
            
        # For backward compatibility with old templates
        if "late" not in summary:
            summary["late"] = summary["late_start"]
        
        return report_data
    
    except Exception as e:
        logger.error(f"Error loading report data: {str(e)}")
        return None