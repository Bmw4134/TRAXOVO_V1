"""
TRAXOVO Backend Backup & Activity History Module
Comprehensive backup system for all fleet management data and activity tracking
"""

import os
import json
import csv
import shutil
import zipfile
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup_system', __name__)

class TRAXOVOBackupSystem:
    """Comprehensive backup system for TRAXOVO fleet management platform"""
    
    def __init__(self):
        self.backup_dir = 'backups'
        self.activity_dir = 'activity_logs'
        self.versions_dir = 'data_versions'
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary backup directories"""
        for directory in [self.backup_dir, self.activity_dir, self.versions_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                
    def log_activity(self, module_name, action, user_id=None, details=None):
        """Log activity across all TRAXOVO modules"""
        try:
            activity_log = {
                'timestamp': datetime.now().isoformat(),
                'module': module_name,
                'action': action,
                'user_id': user_id or getattr(current_user, 'id', 'system'),
                'user_email': getattr(current_user, 'email', 'system'),
                'details': details or {},
                'ip_address': request.remote_addr if request else 'localhost'
            }
            
            # Daily activity log file
            date_str = datetime.now().strftime('%Y-%m-%d')
            log_file = f'{self.activity_dir}/activity_{date_str}.json'
            
            # Load existing logs or create new list
            activities = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    activities = json.load(f)
            
            activities.append(activity_log)
            
            # Save updated logs
            with open(log_file, 'w') as f:
                json.dump(activities, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    def get_activity_history(self, days=30, module_filter=None):
        """Retrieve activity history across all modules"""
        activities = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            log_file = f'{self.activity_dir}/activity_{date_str}.json'
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        daily_activities = json.load(f)
                        
                    # Filter by module if specified
                    if module_filter:
                        daily_activities = [a for a in daily_activities if a.get('module') == module_filter]
                    
                    activities.extend(daily_activities)
                    
                except Exception as e:
                    logger.error(f"Error reading activity log {log_file}: {e}")
            
            current_date += timedelta(days=1)
        
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)
    
    def create_data_version(self, module_name, data_type, data_content, action="update"):
        """Create a versioned snapshot of data before modifications"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            user_id = getattr(current_user, 'id', 'system')
            user_email = getattr(current_user, 'email', 'system')
            
            version_data = {
                'version_id': f"{module_name}_{data_type}_{timestamp}",
                'timestamp': datetime.now().isoformat(),
                'module': module_name,
                'data_type': data_type,
                'action': action,
                'user_id': user_id,
                'user_email': user_email,
                'ip_address': request.remote_addr if request else 'localhost',
                'data_content': data_content,
                'restore_point': True
            }
            
            # Create module version directory
            module_version_dir = f'{self.versions_dir}/{module_name}'
            os.makedirs(module_version_dir, exist_ok=True)
            
            # Save version file
            version_file = f'{module_version_dir}/{version_data["version_id"]}.json'
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            # Log the versioning activity
            self.log_activity(module_name, f'data_version_created_{action}', details={
                'version_id': version_data['version_id'],
                'data_type': data_type,
                'action': action
            })
            
            return version_data['version_id']
            
        except Exception as e:
            logger.error(f"Error creating data version: {e}")
            return None
    
    def get_data_versions(self, module_name, data_type=None, days=30):
        """Get available data versions for restoration"""
        versions = []
        module_version_dir = f'{self.versions_dir}/{module_name}'
        
        if not os.path.exists(module_version_dir):
            return versions
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(module_version_dir):
                if filename.endswith('.json'):
                    version_file = f'{module_version_dir}/{filename}'
                    with open(version_file, 'r') as f:
                        version_data = json.load(f)
                    
                    # Filter by data type if specified
                    if data_type and version_data.get('data_type') != data_type:
                        continue
                    
                    # Filter by date range
                    version_date = datetime.fromisoformat(version_data['timestamp'])
                    if version_date < cutoff_date:
                        continue
                    
                    versions.append(version_data)
            
            return sorted(versions, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting data versions: {e}")
            return []
    
    def create_full_backup(self):
        """Create comprehensive backup of all TRAXOVO data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'traxovo_backup_{timestamp}'
        backup_path = f'{self.backup_dir}/{backup_name}'
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup activity logs
            if os.path.exists(self.activity_dir):
                shutil.copytree(self.activity_dir, f'{backup_path}/activity_logs')
            
            # Backup ideas (if exists)
            if os.path.exists('ideas'):
                shutil.copytree('ideas', f'{backup_path}/ideas')
            
            # Backup versions (if exists)
            if os.path.exists(self.versions_dir):
                shutil.copytree(self.versions_dir, f'{backup_path}/data_versions')
            
            # Create backup metadata
            metadata = {
                'backup_created': datetime.now().isoformat(),
                'created_by': getattr(current_user, 'email', 'system'),
                'modules_included': ['activity_logs', 'ideas', 'data_versions'],
                'backup_size_mb': self._get_directory_size(backup_path) / (1024 * 1024)
            }
            
            with open(f'{backup_path}/backup_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create ZIP archive
            zip_path = f'{backup_path}.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # Remove temporary directory
            shutil.rmtree(backup_path)
            
            # Log the backup creation
            self.log_activity('backup_system', 'full_backup_created', details={
                'backup_file': f'{backup_name}.zip',
                'backup_size_mb': round(metadata['backup_size_mb'], 2)
            })
            
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def _get_directory_size(self, directory):
        """Calculate directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def get_backup_statistics(self):
        """Get backup system statistics"""
        stats = {
            'total_backups': 0,
            'latest_backup': None,
            'total_activity_logs': 0,
            'activity_log_size_mb': 0,
            'modules_tracked': []
        }
        
        try:
            # Count backup files
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]
                stats['total_backups'] = len(backup_files)
                
                if backup_files:
                    backup_files.sort(reverse=True)
                    stats['latest_backup'] = backup_files[0]
            
            # Activity log statistics
            if os.path.exists(self.activity_dir):
                activity_files = [f for f in os.listdir(self.activity_dir) if f.endswith('.json')]
                stats['total_activity_logs'] = len(activity_files)
                stats['activity_log_size_mb'] = round(self._get_directory_size(self.activity_dir) / (1024 * 1024), 2)
                
                # Get unique modules from recent activities
                recent_activities = self.get_activity_history(days=7)
                modules = set(activity['module'] for activity in recent_activities)
                stats['modules_tracked'] = list(modules)
        
        except Exception as e:
            logger.error(f"Error getting backup statistics: {e}")
        
        return stats

# Global backup system instance
backup_system = TRAXOVOBackupSystem()

@backup_bp.route('/backup-system')
@login_required
def backup_dashboard():
    """Backup system dashboard"""
    stats = backup_system.get_backup_statistics()
    recent_activities = backup_system.get_activity_history(days=7)[:50]  # Last 50 activities
    return render_template('backup_dashboard.html', stats=stats, recent_activities=recent_activities)

@backup_bp.route('/create-backup', methods=['POST'])
@login_required
def create_backup():
    """Create a full system backup"""
    backup_file = backup_system.create_full_backup()
    
    if backup_file:
        flash(f'Backup created successfully: {os.path.basename(backup_file)}', 'success')
    else:
        flash('Error creating backup', 'error')
    
    return redirect(url_for('backup_system.backup_dashboard'))

@backup_bp.route('/export-activity', methods=['POST'])
@login_required
def export_activity():
    """Export activity history to CSV"""
    days = int(request.form.get('days', 30))
    module_filter = request.form.get('module_filter') or None
    
    activities = backup_system.get_activity_history(days, module_filter)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'{backup_system.backup_dir}/activity_export_{timestamp}.csv'
    
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'module', 'action', 'user_email', 'ip_address', 'details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for activity in activities:
                # Flatten details for CSV
                row = {
                    'timestamp': activity['timestamp'],
                    'module': activity['module'],
                    'action': activity['action'],
                    'user_email': activity.get('user_email', ''),
                    'ip_address': activity.get('ip_address', ''),
                    'details': json.dumps(activity.get('details', {}))
                }
                writer.writerow(row)
        
        return send_file(csv_filename, as_attachment=True, download_name=os.path.basename(csv_filename))
        
    except Exception as e:
        flash(f'Error exporting activity data: {e}', 'error')
        return redirect(url_for('backup_system.backup_dashboard'))

@backup_bp.route('/api/activity-summary')
@login_required
def activity_summary():
    """Get activity summary for dashboard"""
    activities = backup_system.get_activity_history(days=30)
    
    summary = {
        'total_activities': len(activities),
        'unique_users': len(set(a.get('user_email', '') for a in activities)),
        'module_breakdown': {},
        'daily_activity': {}
    }
    
    # Module breakdown
    for activity in activities:
        module = activity.get('module', 'unknown')
        summary['module_breakdown'][module] = summary['module_breakdown'].get(module, 0) + 1
    
    # Daily activity for last 7 days
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_activities = [a for a in activities if a['timestamp'].startswith(date)]
        summary['daily_activity'][date] = len(day_activities)
    
    return jsonify(summary)

def log_module_activity(module_name, action, details=None):
    """Helper function for other modules to log activities"""
    return backup_system.log_activity(module_name, action, details=details)

def create_data_version(module_name, data_type, data_content, action="update"):
    """Helper function for other modules to create data versions"""
    return backup_system.create_data_version(module_name, data_type, data_content, action)