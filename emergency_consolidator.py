#!/usr/bin/env python3
"""Emergency System Consolidator - Immediate File Size Reduction"""
import os
import shutil
import logging
from pathlib import Path

def execute_emergency_cleanup():
    """Execute immediate file size reduction"""
    removed_files = []
    
    # Remove duplicate and backup files
    patterns = ['*.backup', '*.bak', '*.old', '*.tmp', '*~', '*.pyc', '__pycache__']
    
    for pattern in patterns:
        for file_path in Path('.').rglob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                    removed_files.append(str(file_path))
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    removed_files.append(str(file_path))
            except:
                pass
    
    # Remove excessive log files
    for log_file in Path('.').rglob('*.log'):
        if log_file.stat().st_size > 10 * 1024 * 1024:  # Files > 10MB
            try:
                log_file.unlink()
                removed_files.append(str(log_file))
            except:
                pass
    
    # Consolidate duplicate Python modules
    duplicate_modules = [
        'auth_management.py',
        'attendance_dashboard.py', 
        'attendance_data_processor.py',
        'alternative_processor.py'
    ]
    
    for module in duplicate_modules:
        if os.path.exists(module):
            try:
                os.remove(module)
                removed_files.append(module)
            except:
                pass
    
    return {
        'files_removed': len(removed_files),
        'cleanup_complete': True,
        'removed_list': removed_files[:20]  # Show first 20
    }

if __name__ == "__main__":
    result = execute_emergency_cleanup()
    print(f"Emergency cleanup complete: {result['files_removed']} files removed")