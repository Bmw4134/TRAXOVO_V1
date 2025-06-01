"""
Template Cleanup Script

This script moves unused templates to a backup folder to avoid confusion during demos.
Only keeps the essential templates that are actively being used.
"""

import os
import shutil
from datetime import datetime

def cleanup_unused_templates():
    """Move unused templates to backup folder"""
    
    # Templates that are actively being used (keep these)
    active_templates = [
        'dashboard.html',
        'driver_reports_working.html',
        'driver_reports_clean.html',
        'driver_attendance/dashboard.html',
        'mtd_data_review/dashboard.html',
        'kaizen/dashboard.html',
        'weekly_report/dashboard.html',
        'weekly_driver_report/dashboard.html',
        'monthly_driver_report/dashboard.html',
        'base.html',
        'index.html'
    ]
    
    # Create backup directory
    backup_dir = f"templates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    moved_count = 0
    kept_count = 0
    
    # Walk through templates directory
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, 'templates')
                
                # Check if this template is in the active list
                is_active = any(active_template in relative_path for active_template in active_templates)
                
                if not is_active:
                    # Move to backup
                    backup_path = os.path.join(backup_dir, relative_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.move(file_path, backup_path)
                    print(f"Moved: {relative_path}")
                    moved_count += 1
                else:
                    print(f"Kept: {relative_path}")
                    kept_count += 1
    
    print(f"\nCleanup complete:")
    print(f"- Moved {moved_count} unused templates to {backup_dir}")
    print(f"- Kept {kept_count} active templates")
    print(f"- System ready for demo!")

if __name__ == "__main__":
    cleanup_unused_templates()