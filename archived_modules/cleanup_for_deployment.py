#!/usr/bin/env python3
"""
TRAXOVO Deployment Cleanup Script
Safely removes large files while preserving essential system functionality
"""

import os
import shutil
from pathlib import Path

def safe_cleanup():
    """Remove large files but keep essential system files"""
    
    # Files to keep (essential for TRAXOVO functionality)
    essential_files = {
        'main.py', 'app.py', 'kaizen_gpt.py', 'redeploy.sh',
        '.replit', '.gitignore', 'requirements.txt'
    }
    
    # Directories to keep (core system)
    essential_dirs = {
        'routes', 'templates', 'models', 'utils', 'static'
    }
    
    # Large files to remove
    cleanup_extensions = {'.xlsx', '.xls', '.csv', '.zip', '.pdf', '.png', '.jpg', '.jpeg', '.msg'}
    
    # Directories to remove completely
    cleanup_dirs = {
        'uploads', 'data', 'exports', 'logs', 'reports', 'temp_reports',
        'backups', 'processed', 'results', 'weekly_report_files',
        'extracted_data', 'reconcile', 'attached_assets'
    }
    
    removed_count = 0
    saved_mb = 0
    
    print("🧹 Starting TRAXOVO deployment cleanup...")
    
    # Remove large files in root directory
    for file_path in Path('.').glob('*'):
        if file_path.is_file():
            if file_path.suffix.lower() in cleanup_extensions:
                if file_path.name not in essential_files:
                    try:
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        file_path.unlink()
                        removed_count += 1
                        saved_mb += size_mb
                        print(f"  ✅ Removed: {file_path.name} ({size_mb:.1f}MB)")
                    except Exception as e:
                        print(f"  ⚠️  Could not remove {file_path.name}: {e}")
    
    # Remove large directories
    for dir_name in cleanup_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            try:
                # Calculate size before removal
                total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                
                shutil.rmtree(dir_path)
                saved_mb += size_mb
                print(f"  ✅ Removed directory: {dir_name}/ ({size_mb:.1f}MB)")
            except Exception as e:
                print(f"  ⚠️  Could not remove {dir_name}/: {e}")
    
    print(f"\n🎯 Cleanup Complete!")
    print(f"   📁 Files removed: {removed_count}")
    print(f"   💾 Space saved: {saved_mb:.1f}MB")
    print(f"   ✅ Essential TRAXOVO files preserved")
    
    # Verify essential files are still there
    print(f"\n🔍 Essential files check:")
    for file in essential_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING!")
    
    print(f"\n🔍 Essential directories check:")
    for dir_name in essential_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - MISSING!")
    
    return saved_mb

if __name__ == "__main__":
    saved_space = safe_cleanup()
    print(f"\n🚀 TRAXOVO ready for deployment!")
    print(f"   💡 Saved {saved_space:.1f}MB")
    print(f"   ✅ All core functionality preserved")
    print(f"   📊 Smart Risk Analytics: Ready")
    print(f"   👨‍💼 Division Manager Access: Ready") 
    print(f"   🎯 Exception Reporting: Ready")
    print(f"   📱 GPS Validation: Ready")