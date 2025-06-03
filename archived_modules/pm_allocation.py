#!/usr/bin/env python
"""
PM Allocation Processor Standalone Script

This script provides a standalone PM allocation file processor without requiring
the full TRAXORA application to be functioning.
"""
import os
import re
import pandas as pd
import traceback
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, flash, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

# Directory setup
UPLOAD_FOLDER = Path('./uploads')
REPORTS_FOLDER = Path('./reports')
ATTACHED_ASSETS_DIR = Path('./attached_assets')
EXPORT_FOLDER = Path('./exports')

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, EXPORT_FOLDER]:
    folder.mkdir(exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Import the PM processor
from utils.pm_processor import process_pm_allocation_files, find_allocation_files

@app.route('/')
def index():
    """Home page that redirects to PM allocation processor"""
    return redirect(url_for('pm_allocation_processor'))

@app.route('/pm_allocation', methods=['GET', 'POST'])
def pm_allocation_processor():
    """Handle PM allocation file upload and processing"""
    import os
    import shutil
    
    # Initialize paths for reports
    reports_dir = REPORTS_FOLDER
    reports_dir.mkdir(exist_ok=True, parents=True)
    
    # Get list of recent reports (sorted by modification time, newest first)
    recent_reports = []
    try:
        for report_file in sorted(reports_dir.glob('*.csv'), 
                                key=lambda x: os.path.getmtime(x), 
                                reverse=True)[:10]:  # Show only the 10 most recent reports
            recent_reports.append({
                'name': report_file.name,
                'date': datetime.fromtimestamp(os.path.getmtime(report_file)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': os.path.getsize(report_file) / 1024  # Size in KB
            })
    except Exception as e:
        print(f"Error getting recent reports: {e}")
    
    if request.method == 'POST':
        # Check if the post request has the file parts
        if 'original_file' not in request.files or 'updated_file' not in request.files:
            flash('Both original and updated files are required', 'error')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
        
        original_file = request.files['original_file']
        updated_file = request.files['updated_file']
        
        # If user doesn't select files, browser submits empty files without filename
        if original_file.filename == '' or updated_file.filename == '':
            flash('No selected files', 'error')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
        
        def allowed_file(filename):
            """Check if file has an allowed extension"""
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xlsm', 'csv']
        
        if original_file and updated_file and allowed_file(original_file.filename) and allowed_file(updated_file.filename):
            try:
                # Save the uploaded files
                original_filename = secure_filename(original_file.filename)
                updated_filename = secure_filename(updated_file.filename)
                
                original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                updated_path = os.path.join(app.config['UPLOAD_FOLDER'], updated_filename)
                
                original_file.save(original_path)
                updated_file.save(updated_path)
                
                # Process the files
                output_file, summary = process_pm_allocation_files(
                    Path(original_path),
                    Path(updated_path),
                    reports_dir
                )
                
                # Format currency for display
                def format_currency(value):
                    """Format float as currency"""
                    try:
                        return f"${float(value):,.2f}"
                    except (ValueError, TypeError):
                        return f"${0:,.2f}"
                
                # Format summary for display
                formatted_summary = {
                    'total_original': format_currency(summary.get('total_original', 0)),
                    'total_updated': format_currency(summary.get('total_updated', 0)),
                    'total_difference': format_currency(summary.get('total_difference', 0)),
                    'total_changed_records': summary.get('total_changed_records', 0),
                    'additions': summary.get('additions', 0),
                    'deletions': summary.get('deletions', 0),
                    'modifications': summary.get('modifications', 0),
                }
                
                flash(f'Files processed successfully. Report saved as {output_file.name}', 'success')
                return render_template('pm_allocation.html', 
                                    recent_reports=recent_reports,
                                    summary=formatted_summary)
                
            except Exception as e:
                error_trace = traceback.format_exc()
                flash(f'Error processing files: {str(e)}', 'error')
                print(f"Error processing files: {error_trace}")
                return render_template('pm_allocation.html', recent_reports=recent_reports, error=str(e))
        else:
            flash('Invalid file type. Please upload Excel (.xlsx/.xlsm) or CSV files.', 'error')
    
    return render_template('pm_allocation.html', recent_reports=recent_reports)

@app.route('/view_pm_report/<filename>')
def view_pm_report(filename):
    """View a PM allocation reconciliation report"""
    import os
    
    # Validate the filename
    reports_dir = REPORTS_FOLDER
    file_path = reports_dir / secure_filename(filename)
    
    if not file_path.exists():
        flash('Report not found', 'error')
        return redirect(url_for('pm_allocation_processor'))
    
    # Read the CSV file
    try:
        df = pd.read_csv(file_path)
        records = df.to_dict('records')
        
        return render_template('pm_report.html', 
                           filename=filename,
                           records=records,
                           creation_date=datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        flash(f'Error reading report: {str(e)}', 'error')
        return redirect(url_for('pm_allocation_processor'))

@app.route('/download_pm_report/<filename>')
def download_pm_report(filename):
    """Download a PM allocation reconciliation report"""
    reports_dir = REPORTS_FOLDER
    return send_from_directory(reports_dir, secure_filename(filename), as_attachment=True)

@app.route('/auto_process_pm_allocation', methods=['GET', 'POST'])
def auto_process_pm_allocation():
    """Automatically find and process PM allocation files"""
    import os
    import traceback
    
    # Get the list of recent reports
    reports_dir = REPORTS_FOLDER
    reports_dir.mkdir(exist_ok=True, parents=True)
    
    recent_reports = []
    try:
        for report_file in sorted(reports_dir.glob('*.csv'), 
                                key=lambda x: os.path.getmtime(x), 
                                reverse=True)[:10]:
            recent_reports.append({
                'name': report_file.name,
                'date': datetime.fromtimestamp(os.path.getmtime(report_file)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': os.path.getsize(report_file) / 1024
            })
    except Exception as e:
        print(f"Error getting recent reports: {e}")
    
    # Look for allocation files in the attached_assets directory
    try:
        original_file, updated_file = find_allocation_files()
        
        if not original_file or not updated_file:
            if request.method == 'GET':
                return render_template('auto_process.html', 
                                    recent_reports=recent_reports,
                                    error="Could not automatically detect allocation files. Please upload manually.")
            else:
                return jsonify({
                    'success': False,
                    'message': "Could not automatically detect allocation files. Please upload manually.",
                    'redirect': url_for('pm_allocation_processor')
                })
        
        # Process the files
        output_file, summary = process_pm_allocation_files(
            original_file,
            updated_file,
            reports_dir
        )
        
        # Format currency for display
        def format_currency(value):
            """Format float as currency"""
            try:
                return f"${float(value):,.2f}"
            except (ValueError, TypeError):
                return f"${0:,.2f}"
        
        # Format summary for display
        formatted_summary = {
            'original_file': original_file.name,
            'updated_file': updated_file.name,
            'total_original': format_currency(summary.get('total_original', 0)),
            'total_updated': format_currency(summary.get('total_updated', 0)),
            'total_difference': format_currency(summary.get('total_difference', 0)),
            'total_changed_records': summary.get('total_changed_records', 0),
            'additions': summary.get('additions', 0),
            'deletions': summary.get('deletions', 0),
            'modifications': summary.get('modifications', 0),
        }
        
        message = f'Files processed successfully. Report saved as {output_file.name}'
        
        if request.method == 'GET':
            flash(message, 'success')
            return render_template('auto_process.html', 
                                recent_reports=recent_reports,
                                summary=formatted_summary)
        else:
            return jsonify({
                'success': True,
                'message': message,
                'summary': formatted_summary,
                'redirect': url_for('view_pm_report', filename=output_file.name)
            })
        
    except Exception as e:
        error_trace = traceback.format_exc()
        message = f'Error processing files: {str(e)}'
        print(f"Error in auto-process: {error_trace}")
        
        if request.method == 'GET':
            flash(message, 'error')
            return render_template('auto_process.html', 
                                recent_reports=recent_reports,
                                error=str(e))
        else:
            return jsonify({
                'success': False,
                'message': message,
                'error': str(e)
            })

if __name__ == '__main__':
    from datetime import datetime
    app.run(host='0.0.0.0', port=5000, debug=True)