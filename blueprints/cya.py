"""
CYA (Cover Your Assets) Blueprint

This Flask Blueprint provides routes for:
1. Viewing audit trail
2. Viewing backup history
3. Accessing file diffs
4. Managing the CYA system
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from utils.cya import (
    log_event, get_audit_trail, get_file_versions, backup_file, 
    backup_api_response, backup_report, reconcile_files, ensure_directories
)

# Create Blueprint
cya_bp = Blueprint('cya', __name__, url_prefix='/cya')

@cya_bp.route('/')
@login_required
def index():
    """CYA Dashboard"""
    # Get recent audit trail entries
    recent_events = get_audit_trail(limit=10)
    
    # Get directory stats
    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = f"backups/{today}"
    
    stats = {
        "api_backups": len(os.listdir(f"{backup_dir}/api")) if os.path.exists(f"{backup_dir}/api") else 0,
        "upload_backups": len(os.listdir(f"{backup_dir}/uploads")) if os.path.exists(f"{backup_dir}/uploads") else 0,
        "report_backups": len(os.listdir(f"{backup_dir}/reports")) if os.path.exists(f"{backup_dir}/reports") else 0,
        "reconciliations": len(os.listdir("reconcile")) if os.path.exists("reconcile") else 0
    }
    
    return render_template(
        'cya/index.html',
        title="CYA Dashboard",
        stats=stats,
        recent_events=recent_events
    )

@cya_bp.route('/audit')
@login_required
def audit_trail():
    """View audit trail"""
    # Get query parameters
    event_type = request.args.get('event_type')
    days = request.args.get('days', '7')
    limit = request.args.get('limit', '100')
    
    try:
        days = int(days)
        limit = int(limit)
    except ValueError:
        days = 7
        limit = 100
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    # Get audit trail
    events = get_audit_trail(
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    
    return render_template(
        'cya/audit.html',
        title="Audit Trail",
        events=events,
        event_type=event_type,
        days=days,
        limit=limit
    )

@cya_bp.route('/backups')
@login_required
def backups():
    """View backup files"""
    # Get query parameters
    date = request.args.get('date')
    category = request.args.get('category', 'all')
    
    # If no date specified, use today
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get backup files
    backup_dir = f"backups/{date}"
    
    if not os.path.exists(backup_dir):
        flash(f"No backups found for {date}", "warning")
        return redirect(url_for('cya.index'))
    
    files = []
    categories = ['api', 'uploads', 'reports']
    
    for cat in categories:
        if category == 'all' or category == cat:
            cat_dir = f"{backup_dir}/{cat}"
            if os.path.exists(cat_dir):
                for filename in os.listdir(cat_dir):
                    filepath = os.path.join(cat_dir, filename)
                    files.append({
                        'category': cat,
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    # Sort by modified time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template(
        'cya/backups.html',
        title="Backup Files",
        files=files,
        date=date,
        category=category,
        available_dates=get_available_dates()
    )

@cya_bp.route('/reconcile')
@login_required
def reconciliations():
    """View reconciliation files"""
    reconcile_dir = "reconcile"
    
    if not os.path.exists(reconcile_dir):
        flash("No reconciliation files found", "warning")
        return redirect(url_for('cya.index'))
    
    files = []
    for filename in os.listdir(reconcile_dir):
        filepath = os.path.join(reconcile_dir, filename)
        files.append({
            'filename': filename,
            'path': filepath,
            'size': os.path.getsize(filepath),
            'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Sort by modified time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template(
        'cya/reconcile.html',
        title="Reconciliation Files",
        files=files
    )

@cya_bp.route('/download/<path:filepath>')
@login_required
def download_file(filepath):
    """Download a file"""
    if not os.path.exists(filepath):
        flash("File not found", "danger")
        return redirect(url_for('cya.index'))
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=os.path.basename(filepath)
    )

@cya_bp.route('/view/<path:filepath>')
@login_required
def view_file(filepath):
    """View a file"""
    if not os.path.exists(filepath):
        flash("File not found", "danger")
        return redirect(url_for('cya.index'))
    
    # Check file type
    filename = os.path.basename(filepath)
    _, ext = os.path.splitext(filename)
    
    if ext.lower() in ['.json']:
        with open(filepath, 'r') as f:
            content = json.load(f)
        return render_template(
            'cya/view_json.html',
            title=f"View {filename}",
            content=content,
            filepath=filepath
        )
    elif ext.lower() in ['.txt', '.csv', '.log']:
        with open(filepath, 'r') as f:
            content = f.read()
        return render_template(
            'cya/view_text.html',
            title=f"View {filename}",
            content=content,
            filepath=filepath
        )
    else:
        flash(f"Cannot preview this file type: {ext}", "warning")
        return redirect(url_for('cya.download_file', filepath=filepath))

@cya_bp.route('/api/backup', methods=['POST'])
@login_required
def api_backup_file():
    """API endpoint to backup a file"""
    data = request.json
    if not data or 'file_path' not in data:
        return jsonify({'success': False, 'error': 'Missing file_path'}), 400
    
    file_path = data['file_path']
    category = data.get('category', 'uploads')
    user_id = current_user.id if current_user.is_authenticated else None
    operation = data.get('operation', 'UPLOAD')
    
    result = backup_file(file_path, category, user_id, operation)
    
    if result:
        return jsonify({'success': True, 'backup_path': result})
    else:
        return jsonify({'success': False, 'error': 'Backup failed'}), 500

@cya_bp.route('/api/reconcile', methods=['POST'])
@login_required
def api_reconcile_files():
    """API endpoint to reconcile files"""
    data = request.json
    if not data or 'generated_file' not in data or 'uploaded_file' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    generated_file = data['generated_file']
    uploaded_file = data['uploaded_file']
    output_name = data.get('output_name')
    
    result = reconcile_files(generated_file, uploaded_file, output_name)
    
    if result:
        return jsonify({'success': True, 'diff_path': result})
    else:
        return jsonify({'success': False, 'error': 'Reconciliation failed'}), 500

@cya_bp.route('/api/log', methods=['POST'])
@login_required
def api_log_event():
    """API endpoint to log an event"""
    data = request.json
    if not data or 'event_type' not in data or 'description' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    event_type = data['event_type']
    description = data['description']
    user_id = current_user.id if current_user.is_authenticated else None
    data_path = data.get('data_path')
    metadata = data.get('metadata')
    
    result = log_event(event_type, description, user_id, data_path, metadata)
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Logging failed'}), 500

def get_available_dates():
    """Get list of dates with backups"""
    if not os.path.exists("backups"):
        return []
    
    dates = []
    for date_dir in os.listdir("backups"):
        if os.path.isdir(os.path.join("backups", date_dir)):
            try:
                # Validate it's a date
                datetime.strptime(date_dir, "%Y-%m-%d")
                dates.append(date_dir)
            except ValueError:
                continue
    
    # Sort dates (newest first)
    dates.sort(reverse=True)
    return dates