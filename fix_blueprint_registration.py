
import importlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_missing_blueprints():
    """Create missing blueprint files"""
    blueprint_dirs = [
        'blueprints/admin',
        'blueprints/api', 
        'blueprints/dashboard',
        'blueprints/maps'
    ]
    
    for blueprint_dir in blueprint_dirs:
        blueprint_path = Path(blueprint_dir)
        blueprint_path.mkdir(parents=True, exist_ok=True)
        
        init_file = blueprint_path / '__init__.py'
        if not init_file.exists():
            blueprint_name = blueprint_dir.split('/')[-1]
            
            blueprint_content = f'''from flask import Blueprint

{blueprint_name}_bp = Blueprint('{blueprint_name}', __name__)

@{blueprint_name}_bp.route('/')
def index():
    return f"{{'{blueprint_name}'.title()}} module - under development"

@{blueprint_name}_bp.route('/health')
def health():
    return {{"status": "ok", "module": "{blueprint_name}"}}
'''
            
            with open(init_file, 'w') as f:
                f.write(blueprint_content)
            
            logger.info(f"Created blueprint: {blueprint_dir}")

def fix_routes():
    """Apply route and blueprint fixes"""
    logger.info("Starting blueprint registration fixes")
    
    # Create missing blueprints
    create_missing_blueprints()
    
    # Test blueprint imports
    blueprint_configs = [
        ('blueprints.attendance', 'attendance_bp'),
        ('blueprints.billing', 'billing_bp'),
        ('blueprints.maintenance', 'maintenance_bp'),
        ('blueprints.reports', 'reports_bp'),
        ('blueprints.admin', 'admin_bp'),
        ('blueprints.api', 'api_bp'),
        ('blueprints.dashboard', 'dashboard_bp'),
        ('blueprints.maps', 'maps_bp')
    ]
    
    for module_name, blueprint_name in blueprint_configs:
        try:
            module = importlib.import_module(module_name)
            blueprint = getattr(module, blueprint_name)
            logger.info(f"✓ Blueprint {blueprint_name} is importable")
        except Exception as e:
            logger.error(f"✗ Blueprint {blueprint_name} error: {e}")
    
    logger.info("Blueprint registration fixes completed")

if __name__ == "__main__":
    fix_routes()
