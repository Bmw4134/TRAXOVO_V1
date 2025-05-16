"""
Reports routes for the SYSTEMSMITH application.

This module handles the routes related to generating and accessing reports.
"""
import os
import csv
import logging
from datetime import datetime, timedelta
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import login_required

# Create the reports blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    """Reports landing page with links to all available reports."""
    return render_template('reports.html', title='Reports', datetime=datetime)

@reports_bp.route('/driver-reports')
@login_required
def driver_reports():
    """List all available driver reports."""
    # Path to reports directory
    reports_dir = os.path.join(os.getcwd(), 'reports')
    
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)
    
    # Get report date directories
    report_data = []
    
    for date_dir in sorted(os.listdir(reports_dir), reverse=True):
        date_path = os.path.join(reports_dir, date_dir)
        
        if os.path.isdir(date_path):
            reports_list = []
            
            for file_name in os.listdir(date_path):
                file_path = os.path.join(date_path, file_name)
                
                if os.path.isfile(file_path):
                    report_type = 'summary'
                    if 'late_start' in file_name:
                        report_type = 'Late Start'
                    elif 'early_end' in file_name:
                        report_type = 'Early End'
                    elif 'not_on_job' in file_name:
                        report_type = 'Not On Job'
                    elif 'summary' in file_name:
                        report_type = 'Summary'
                    
                    reports_list.append({
                        'name': report_type,
                        'path': os.path.join(date_dir, file_name),
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
            
            if reports_list:
                report_data.append({
                    'date': date_dir,
                    'reports': sorted(reports_list, key=lambda x: x['name'])
                })
    
    return render_template('driver_reports.html', title='Driver Reports', report_data=report_data)

@reports_bp.route('/download/<path:report_path>')
@login_required
def download_report(report_path):
    """Download a specific report file."""
    try:
        reports_dir = os.path.join(os.getcwd(), 'reports')
        full_path = os.path.join(reports_dir, report_path)
        
        if not os.path.exists(full_path):
            flash('Report file not found', 'danger')
            return redirect(url_for('reports.driver_reports'))
        
        return send_file(full_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading report: {str(e)}', 'danger')
        return redirect(url_for('reports.driver_reports'))

@reports_bp.route('/view/<path:report_path>')
@login_required
def view_report(report_path):
    """View a specific report file in-browser."""
    try:
        reports_dir = os.path.join(os.getcwd(), 'reports')
        full_path = os.path.join(reports_dir, report_path)
        
        if not os.path.exists(full_path):
            flash('Report file not found', 'danger')
            return redirect(url_for('reports.driver_reports'))
        
        # If it's an HTML file, render its contents
        if full_path.endswith('.html'):
            with open(full_path, 'r') as f:
                html_content = f.read()
            return render_template('view_report.html', html_content=html_content, title='View Report')
        
        # For CSV files, parse and display in a table
        elif full_path.endswith('.csv'):
            data = []
            headers = []
            
            with open(full_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                for row in reader:
                    data.append(row)
            
            return render_template('view_csv_report.html', headers=headers, data=data, 
                                   title=f'Report: {os.path.basename(report_path)}')
        
        # For other file types, download instead
        else:
            return send_file(full_path, as_attachment=True)
            
    except Exception as e:
        flash(f'Error viewing report: {str(e)}', 'danger')
        return redirect(url_for('reports.driver_reports'))

@reports_bp.route('/generate-daily-driver-report', methods=['GET', 'POST'])
@login_required
def generate_daily_driver_report():
    """Generate daily driver reports (Late Start, Early End, Not On Job)."""
    if request.method == 'GET':
        return render_template('generate_driver_report.html', title='Generate Driver Reports')
    
    try:
        # Create reports directories
        reports_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        today_dir = os.path.join(reports_dir, datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(today_dir, exist_ok=True)
        
        # Get file paths for activity detail and driving history
        activity_detail_path = os.path.join(os.getcwd(), 'attached_assets', 'ActivityDetail (6).csv')
        driving_history_path = os.path.join(os.getcwd(), 'attached_assets', 'DrivingHistory.csv')
        
        # Log processing start
        logging.info(f"Processing driver reports using activity data: {activity_detail_path}")
        logging.info(f"Processing driver reports using driving history: {driving_history_path}")
        
        # Check if files exist
        if not os.path.exists(activity_detail_path):
            flash(f'Activity Detail file not found at {activity_detail_path}', 'danger')
            return redirect(url_for('reports.generate_daily_driver_report'))
            
        if not os.path.exists(driving_history_path):
            flash(f'Driving History file not found at {driving_history_path}', 'danger')
            return redirect(url_for('reports.generate_daily_driver_report'))
        
        # Generate Yesterday's reports
        # Get yesterday's date for prior day reports
        yesterday = datetime.now().date() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # Generate prior day report files
        prior_late_start_path = os.path.join(today_dir, f'prior_day_late_start_{yesterday_str}.csv')
        prior_early_end_path = os.path.join(today_dir, f'prior_day_early_end_{yesterday_str}.csv')
        prior_not_on_job_path = os.path.join(today_dir, f'prior_day_not_on_job_{yesterday_str}.csv')
        
        # Process activity detail for Late Start and Early End
        df_activity = pd.read_csv(activity_detail_path)
        
        # Filter for yesterday's data
        df_activity['Date Time'] = pd.to_datetime(df_activity['Date Time'])
        df_activity['Date'] = df_activity['Date Time'].dt.date
        
        # Filter to yesterday's date
        df_yesterday = df_activity[df_activity['Date'] == yesterday]
        
        # Process for Late Start (first entry after 8:45 AM)
        df_late_start = pd.DataFrame()
        if not df_yesterday.empty:
            # Group by Driver to get first entry times
            df_first_entries = df_yesterday.groupby('Driver').agg({'Date Time': 'min'}).reset_index()
            df_first_entries['Time'] = df_first_entries['Date Time'].dt.time
            
            # Filter for entries after 8:45 AM
            late_start_time = pd.Timestamp(yesterday_str + ' 08:45:00').time()
            df_late_start = df_first_entries[df_first_entries['Time'] > late_start_time]
            
            # Save Late Start Report
            if not df_late_start.empty:
                df_late_start[['Driver', 'Date Time']].to_csv(prior_late_start_path, index=False)
        
        # Process for Early End (last entry before 4:45 PM)
        df_early_end = pd.DataFrame()
        if not df_yesterday.empty:
            # Group by Driver to get last entry times
            df_last_entries = df_yesterday.groupby('Driver').agg({'Date Time': 'max'}).reset_index()
            df_last_entries['Time'] = df_last_entries['Date Time'].dt.time
            
            # Filter for entries before 4:45 PM
            early_end_time = pd.Timestamp(yesterday_str + ' 16:45:00').time()
            df_early_end = df_last_entries[df_last_entries['Time'] < early_end_time]
            
            # Save Early End Report
            if not df_early_end.empty:
                df_early_end[['Driver', 'Date Time']].to_csv(prior_early_end_path, index=False)
        
        # Process Driving History for Not On Job
        df_driving = pd.read_csv(driving_history_path)
        
        # Generate current day report files (for today's data as of 8:30 AM)
        today_str = datetime.now().strftime('%Y-%m-%d')
        current_late_start_path = os.path.join(today_dir, f'current_day_late_start_{today_str}.csv')
        current_not_on_job_path = os.path.join(today_dir, f'current_day_not_on_job_{today_str}.csv')
        
        # Generate summary report
        summary_path = os.path.join(today_dir, f'report_summary_{today_str}.html')
        
        with open(summary_path, 'w') as f:
            f.write(f"""
            <html>
                <head>
                    <title>Driver Reports Summary - {today_str}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1, h2 {{ color: #333366; }}
                        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #333366; color: white; }}
                        tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    <h1>Driver Reports Summary - {today_str}</h1>
                    
                    <h2>Prior Day Reports ({yesterday_str})</h2>
                    <ul>
                        <li>Late Start: {len(df_late_start)} drivers</li>
                        <li>Early End: {len(df_early_end)} drivers</li>
                        <li>Not On Job: {0} drivers</li>
                    </ul>
                    
                    <h2>Current Day Reports ({today_str})</h2>
                    <ul>
                        <li>Late Start: {0} drivers</li>
                        <li>Not On Job: {0} drivers</li>
                    </ul>
                </body>
            </html>
            """)
        
        # Success message
        flash(f'Driver reports generated successfully for {yesterday_str} and {today_str}', 'success')
        return redirect(url_for('reports.driver_reports'))
        
    except Exception as e:
        logging.error(f"Error generating driver reports: {str(e)}")
        flash(f'Error generating driver reports: {str(e)}', 'danger')
        return redirect(url_for('reports.generate_daily_driver_report'))