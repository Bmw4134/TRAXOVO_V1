"""
System Logs Module

This module provides routes for viewing system logs and monitoring the application.
"""

import os
import re
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, abort, current_app
from flask_login import login_required, current_user

# Import structured logger
from utils.structured_logger import get_system_logger

# Set up logger for this module
logger = get_system_logger('system_logs')

# Create blueprint
system_logs_bp = Blueprint('system_logs', __name__, url_prefix='/system-logs')

# Constants
LOG_DIRECTORY = os.path.join(os.getcwd(), 'logs')
MAX_LOG_SIZE = 2 * 1024 * 1024  # 2MB max size for log display


def tail_file(file_path, lines=100, max_size=MAX_LOG_SIZE):
    """
    Read the last N lines from a file.
    
    Args:
        file_path (str): Path to the file
        lines (int): Number of lines to read
        max_size (int): Maximum size to read
        
    Returns:
        list: Last N lines
    """
    if not os.path.exists(file_path):
        return []
        
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Limit size for reading
    read_size = min(file_size, max_size)
    
    # Read the last part of the file
    with open(file_path, 'r') as f:
        if file_size > read_size:
            f.seek(file_size - read_size)
            # Skip partial line
            f.readline()
        
        # Read lines
        log_lines = f.readlines()
    
    # Return the last N lines
    return log_lines[-lines:]


def parse_log_line(line):
    """
    Parse a log line into structured data.
    
    Args:
        line (str): Log line
        
    Returns:
        dict: Structured log data
    """
    # Try to parse JSON format first
    if line.strip().startswith('{'):
        try:
            return json.loads(line.strip())
        except:
            pass
    
    # Try to parse standard log format
    timestamp_pattern = r'\[(.*?)\]'
    level_pattern = r'\[(.*?)\]\s+(\w+)'
    name_pattern = r'(\w+)\s+(.*)'
    
    timestamp_match = re.search(timestamp_pattern, line)
    level_match = re.search(level_pattern, line)
    
    if timestamp_match and level_match:
        timestamp = timestamp_match.group(1)
        level = level_match.group(2)
        
        # Extract message (everything after level and name)
        message_start = level_match.end()
        name_message = line[message_start:].strip()
        
        name_match = re.search(name_pattern, name_message)
        if name_match:
            name = name_match.group(1)
            message = name_match.group(2)
        else:
            name = ''
            message = name_message
        
        return {
            'timestamp': timestamp,
            'level': level,
            'logger': name,
            'message': message
        }
    
    # Fallback to raw line
    return {
        'timestamp': '',
        'level': 'INFO',
        'logger': '',
        'message': line.strip()
    }


def get_log_files():
    """
    Get available log files.
    
    Returns:
        list: Available log files
    """
    log_files = []
    
    if os.path.exists(LOG_DIRECTORY):
        for filename in os.listdir(LOG_DIRECTORY):
            if filename.endswith('.log'):
                log_path = os.path.join(LOG_DIRECTORY, filename)
                log_files.append({
                    'name': filename,
                    'path': log_path,
                    'size': os.path.getsize(log_path),
                    'modified': datetime.fromtimestamp(
                        os.path.getmtime(log_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return sorted(log_files, key=lambda x: x['modified'], reverse=True)


@system_logs_bp.route('/')
@login_required
def index():
    """Display log viewer dashboard"""
    # Check if user has admin access
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin:
        abort(403)  # Forbidden
        
    # Get available log files
    log_files = get_log_files()
    
    # Render template
    return render_template('logs/viewer.html', 
                          log_files=log_files)


@system_logs_bp.route('/api/entries')
@login_required
def get_entries():
    """API endpoint for fetching log entries"""
    # Check if user has admin access
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get query parameters
    log_file = request.args.get('log_file', 'system.log')
    max_entries = min(int(request.args.get('max_entries', 100)), 1000)
    level_filter = request.args.get('level', '').upper()
    search_term = request.args.get('search', '')
    
    # Validate log file (prevent path traversal)
    if '..' in log_file or '/' in log_file:
        return jsonify({'error': 'Invalid log file'}), 400
    
    # Get log file path
    log_path = os.path.join(LOG_DIRECTORY, log_file)
    
    # Check if file exists
    if not os.path.exists(log_path):
        return jsonify({'entries': [], 'error': 'Log file not found'})
    
    # Read log lines
    log_lines = tail_file(log_path, lines=max_entries)
    
    # Parse log entries
    entries = []
    for line in log_lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Parse the line
        entry = parse_log_line(line)
        
        # Apply level filter
        if level_filter and entry.get('level', '').upper() != level_filter:
            continue
            
        # Apply search filter
        if search_term and search_term.lower() not in line.lower():
            continue
            
        entries.append(entry)
    
    # Return JSON response
    return jsonify({
        'entries': entries,
        'count': len(entries),
        'log_file': log_file,
        'timestamp': datetime.now().isoformat()
    })
        
@system_logs_bp.route('/download/<log_file>')
@login_required
def download_log(log_file):
    """Download a log file"""
    # Check if user has admin access
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin:
        abort(403)
        
    # Validate log file name (prevent path traversal)
    if '..' in log_file or '/' in log_file:
        abort(400)
        
    # Get log file path
    log_path = os.path.join(LOG_DIRECTORY, log_file)
    
    # Check if file exists
    if not os.path.exists(log_path) or not os.path.isfile(log_path):
        abort(404)
        
    try:
        # Add timestamp to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f"{os.path.splitext(log_file)[0]}_{timestamp}.log"
        
        # Log download activity
        logger.info(f"Log file {log_file} downloaded by {current_user.username}",
                   metadata={"user_id": current_user.id, "log_file": log_file})
        
        # Return file
        return send_file(log_path, 
                        as_attachment=True, 
                        download_name=download_name,
                        mimetype='text/plain')
    except Exception as e:
        logger.error(f"Error downloading log file: {e}")
        abort(500)
    level_filter = request.args.get('level', '').upper()
    search_term = request.args.get('search', '')
    
    # Validate log file (prevent path traversal)
    if '..' in log_file or '/' in log_file:
        return jsonify({'error': 'Invalid log file'}), 400
    
    # Get log file path
    log_path = os.path.join(LOG_DIRECTORY, log_file)
    
    # Check if file exists
    if not os.path.exists(log_path):
        return jsonify({'entries': [], 'error': 'Log file not found'})
    
    # Read log lines
    log_lines = tail_file(log_path, lines=max_entries)
    
    # Parse log entries
    entries = []
    for line in log_lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Parse the line
        entry = parse_log_line(line)
        
        # Apply level filter
        if level_filter and entry.get('level', '').upper() != level_filter:
            continue
            
        # Apply search filter
        if search_term and search_term.lower() not in line.lower():
            continue
            
        entries.append(entry)
    
    # Return JSON response
    return jsonify({
        'entries': entries,
        'count': len(entries),
        'log_file': log_file,
        'timestamp': datetime.now().isoformat()
    })


def register_blueprint(app):
    """Register the blueprint with the application"""
    app.register_blueprint(system_logs_bp)
    app.logger.info("Registered System Logs blueprint")