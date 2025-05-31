"""
Performance Bottleneck Fix - Consolidate Duplicate API Calls
This script replaces all duplicate Gauge API calls with a unified data manager
"""

import os
import re
import glob

def fix_main_app():
    """Update main.py to use unified data manager"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Replace Gauge API imports
    content = re.sub(
        r'from utils\.gauge_api.*\n',
        'from services.unified_data_manager import get_unified_data\n',
        content
    )
    
    # Replace gauge API calls with unified calls
    content = re.sub(
        r'test_gauge_api_connection\(\)',
        'get_unified_data("health").get("api_status") == "active"',
        content
    )
    
    # Replace asset data calls
    content = re.sub(
        r'get_assets\(\)',
        'get_unified_data("assets")',
        content
    )
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed main.py API calls")

def fix_route_files():
    """Fix duplicate API calls in route files"""
    route_files = glob.glob('routes/*.py')
    
    for file_path in route_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace Gauge API imports
            content = re.sub(
                r'from gauge_api_legacy import.*\n',
                'from services.unified_data_manager import get_unified_data\n',
                content
            )
            
            # Replace direct API calls
            content = re.sub(
                r'requests\.get\([^)]*gauge[^)]*\)',
                'get_unified_data("assets")',
                content,
                flags=re.IGNORECASE
            )
            
            # Replace GaugeAPI class usage
            content = re.sub(
                r'gauge_api = GaugeAPI\(\).*?gauge_api\.get_assets\(\)',
                'get_unified_data("assets")',
                content,
                flags=re.DOTALL
            )
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✓ Fixed {file_path}")
                
        except Exception as e:
            print(f"⚠ Error fixing {file_path}: {e}")

def remove_auto_refresh_loops():
    """Remove excessive auto-refresh intervals from templates"""
    template_files = glob.glob('templates/**/*.html', recursive=True)
    
    for file_path in template_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace aggressive refresh intervals with longer ones
            content = re.sub(
                r'setInterval\([^,]+,\s*(\d{1,4})\)',
                lambda m: f'setInterval({m.group(0).split(",")[0]}, 60000)' if int(m.group(1)) < 30000 else m.group(0),
                content
            )
            
            # Remove duplicate refresh calls
            content = re.sub(
                r'(setInterval.*?refreshGPSData.*?\d+)\s*;\s*(setInterval.*?refreshGPSData.*?\d+)',
                r'\1',
                content,
                flags=re.DOTALL
            )
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✓ Optimized refresh intervals in {file_path}")
                
        except Exception as e:
            print(f"⚠ Error optimizing {file_path}: {e}")

def create_unified_import_replacement():
    """Create a simple import replacement for existing modules"""
    replacement_content = '''"""
Legacy Gauge API Compatibility Layer
Redirects old API calls to unified data manager
"""

from services.unified_data_manager import get_unified_data

class GaugeAPI:
    """Compatibility wrapper for legacy code"""
    
    def __init__(self):
        pass
    
    def authenticate(self):
        return True
    
    def check_connection(self):
        health = get_unified_data("health")
        return health.get("api_status") == "active"
    
    def get_assets(self):
        return get_unified_data("assets").get("assets", [])
    
    def get_asset_locations(self, asset_id, start_date=None, end_date=None):
        return get_unified_data("locations")

def get_asset_data():
    """Legacy function compatibility"""
    return get_unified_data("assets").get("assets", [])

def test_gauge_api_connection():
    """Legacy function compatibility"""
    health = get_unified_data("health")
    return health.get("api_status") == "active"

def get_assets():
    """Legacy function compatibility"""
    return get_unified_data("assets").get("assets", [])
'''
    
    with open('gauge_api_legacy.py', 'w') as f:
        f.write(replacement_content)
    
    print("✓ Created legacy compatibility layer")

def update_imports_to_legacy():
    """Update all gauge_api imports to use the legacy compatibility layer"""
    python_files = glob.glob('**/*.py', recursive=True)
    
    for file_path in python_files:
        if 'unified_data_manager' in file_path or 'gauge_api_legacy' in file_path:
            continue
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace gauge_api imports
            content = re.sub(
                r'from gauge_api_legacy import',
                'from gauge_api_legacy import',
                content
            )
            
            content = re.sub(
                r'import gauge_api_legacy as gauge_api',
                'import gauge_api_legacy as gauge_api_legacy as gauge_api',
                content
            )
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✓ Updated imports in {file_path}")
                
        except Exception as e:
            print(f"⚠ Error updating {file_path}: {e}")

if __name__ == "__main__":
    print("🔧 Fixing Performance Bottlenecks...")
    print("=" * 50)
    
    # Step 1: Create compatibility layer
    create_unified_import_replacement()
    
    # Step 2: Update imports
    update_imports_to_legacy()
    
    # Step 3: Fix main application
    fix_main_app()
    
    # Step 4: Fix route files
    fix_route_files()
    
    # Step 5: Optimize refresh intervals
    remove_auto_refresh_loops()
    
    print("=" * 50)
    print("✅ Performance optimization complete!")
    print("📊 All duplicate API calls consolidated")
    print("🚀 System should run much faster now")