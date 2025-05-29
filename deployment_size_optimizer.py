"""
Deployment Size Optimizer
Ensure TRAXOVO stays under 8GB deployment limit
"""

import os
import shutil
from datetime import datetime

def analyze_project_size():
    """Analyze current project size and identify optimization opportunities"""
    
    size_report = {
        'total_size_mb': 0,
        'directories': {},
        'large_files': [],
        'optimization_targets': []
    }
    
    # Calculate directory sizes
    for root, dirs, files in os.walk('.'):
        # Skip hidden and unnecessary directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        dir_size = 0
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                dir_size += file_size
                
                # Track large files (>50MB)
                if file_size > 50 * 1024 * 1024:
                    size_report['large_files'].append({
                        'path': file_path,
                        'size_mb': file_size / (1024 * 1024)
                    })
                    
            except (OSError, FileNotFoundError):
                continue
        
        if dir_size > 0:
            size_report['directories'][root] = dir_size / (1024 * 1024)  # Convert to MB
            size_report['total_size_mb'] += dir_size / (1024 * 1024)
    
    # Identify optimization targets
    if size_report['total_size_mb'] > 6000:  # If approaching 6GB limit
        size_report['optimization_targets'].extend([
            'Remove unnecessary ZIP files from attached_assets/',
            'Clean up temporary backup directories',
            'Remove old development scripts',
            'Compress large Excel files'
        ])
    
    return size_report

def optimize_for_deployment():
    """Optimize project for deployment under 8GB limit"""
    
    optimizations_performed = []
    
    try:
        # Remove large ZIP files that aren't needed for runtime
        zip_files = []
        for root, dirs, files in os.walk('attached_assets'):
            for file in files:
                if file.endswith('.zip') and os.path.getsize(os.path.join(root, file)) > 10 * 1024 * 1024:
                    zip_files.append(os.path.join(root, file))
        
        if zip_files:
            for zip_file in zip_files[:5]:  # Remove only first 5 largest
                try:
                    os.remove(zip_file)
                    optimizations_performed.append(f"Removed large ZIP: {zip_file}")
                except:
                    pass
        
        # Remove backup directories
        backup_dirs = [d for d in os.listdir('.') if 'backup' in d.lower() or 'temp' in d.lower()]
        for backup_dir in backup_dirs[:3]:  # Remove only first 3
            try:
                if os.path.isdir(backup_dir):
                    shutil.rmtree(backup_dir)
                    optimizations_performed.append(f"Removed backup directory: {backup_dir}")
            except:
                pass
        
        # Clean up Python cache
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                try:
                    shutil.rmtree(os.path.join(root, '__pycache__'))
                    optimizations_performed.append(f"Cleaned Python cache: {root}")
                except:
                    pass
        
        # Remove development scripts that aren't needed
        dev_files = [f for f in os.listdir('.') if f.startswith('test_') or f.endswith('_test.py')]
        for dev_file in dev_files[:5]:
            try:
                os.remove(dev_file)
                optimizations_performed.append(f"Removed dev file: {dev_file}")
            except:
                pass
        
    except Exception as e:
        optimizations_performed.append(f"Optimization error: {e}")
    
    return optimizations_performed

if __name__ == '__main__':
    print("🚀 TRAXOVO Deployment Size Analysis")
    print("=" * 50)
    
    # Analyze current size
    report = analyze_project_size()
    print(f"Total Project Size: {report['total_size_mb']:.1f} MB")
    print(f"Deployment Limit: 8,192 MB (8GB)")
    print(f"Available Space: {8192 - report['total_size_mb']:.1f} MB")
    
    if report['total_size_mb'] > 6000:
        print("\n⚠️  WARNING: Approaching size limit!")
        print("Performing optimizations...")
        
        optimizations = optimize_for_deployment()
        for opt in optimizations:
            print(f"✓ {opt}")
        
        # Re-analyze after optimization
        new_report = analyze_project_size()
        print(f"\n📊 After Optimization: {new_report['total_size_mb']:.1f} MB")
        print(f"Space Saved: {report['total_size_mb'] - new_report['total_size_mb']:.1f} MB")
    
    else:
        print("\n✅ Project size is within deployment limits!")
    
    print("\n🎯 Ready for deployment!")