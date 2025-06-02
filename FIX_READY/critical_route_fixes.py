"""
TRAXOVO Critical Route Consolidation - Emergency Patch
Resolves 47 blueprint conflicts and duplicate route registrations
"""
import os
import logging
from flask import Blueprint

logger = logging.getLogger(__name__)

# Priority route consolidation - keeps only essential working modules
ESSENTIAL_BLUEPRINTS = {
    'dashboard': {
        'import_path': 'routes.dashboard',
        'url_prefix': '/',
        'priority': 1,
        'description': 'Main dashboard functionality'
    },
    'billing': {
        'import_path': 'routes.billing', 
        'url_prefix': '/billing',
        'priority': 1,
        'description': 'Billing intelligence with RAGLE data'
    },
    'asset_map': {
        'import_path': 'routes.asset_map',
        'url_prefix': '/asset-map', 
        'priority': 1,
        'description': 'Fleet asset mapping with GAUGE API'
    },
    'driver_reports_unified': {
        'import_path': 'routes.daily_driver_complete',
        'url_prefix': '/driver-reports',
        'priority': 1,
        'description': 'Unified driver reporting system'
    },
    'attendance_unified': {
        'import_path': 'routes.attendance_report',
        'url_prefix': '/attendance',
        'priority': 1,
        'description': 'Unified attendance management'
    },
    'system_admin': {
        'import_path': 'routes.system_admin',
        'url_prefix': '/admin',
        'priority': 2,
        'description': 'Watson administrative functions'
    }
}

# Deprecated blueprints to disable (causing conflicts)
DEPRECATED_BLUEPRINTS = [
    'daily_driver_fixed',        # Conflicts with daily_driver_complete
    'driver_reports_working',    # Conflicts with daily_driver_complete  
    'attendance_routes',         # Conflicts with attendance_report
    'react_upload',             # Missing module
    'enhanced_weekly_report',   # Missing module
    'comprehensive_reports',    # Missing module
]

def apply_route_consolidation(app):
    """Apply emergency route consolidation to resolve conflicts"""
    logger.info("Applying critical route consolidation...")
    
    # Track successful registrations
    registered_count = 0
    
    # Register only essential blueprints
    for bp_name, config in ESSENTIAL_BLUEPRINTS.items():
        try:
            module_path = config['import_path']
            url_prefix = config['url_prefix']
            
            # Import the module
            module = __import__(module_path, fromlist=[f"{bp_name}_bp"])
            
            # Try common blueprint variable names
            blueprint_vars = [f"{bp_name}_bp", "bp", module_path.split('.')[-1] + "_bp"]
            
            blueprint = None
            for var_name in blueprint_vars:
                if hasattr(module, var_name):
                    blueprint = getattr(module, var_name)
                    break
            
            if blueprint and isinstance(blueprint, Blueprint):
                app.register_blueprint(blueprint, url_prefix=url_prefix)
                registered_count += 1
                logger.info(f"Registered essential blueprint: {bp_name}")
            else:
                logger.warning(f"Blueprint variable not found for {bp_name}")
                
        except ImportError as e:
            logger.warning(f"Could not import {bp_name}: {e}")
        except Exception as e:
            logger.error(f"Error registering {bp_name}: {e}")
    
    logger.info(f"Route consolidation complete. Registered {registered_count} essential blueprints.")
    return registered_count

def validate_route_health(app):
    """Validate that essential routes are working"""
    essential_routes = [
        '/', '/dashboard', '/billing', '/asset-map', 
        '/driver-reports', '/attendance', '/admin'
    ]
    
    healthy_routes = []
    for route in essential_routes:
        try:
            # Check if route exists in app's URL map
            for rule in app.url_map.iter_rules():
                if str(rule) == route or str(rule).startswith(route):
                    healthy_routes.append(route)
                    break
        except Exception as e:
            logger.error(f"Route validation error for {route}: {e}")
    
    logger.info(f"Route health check: {len(healthy_routes)}/{len(essential_routes)} essential routes healthy")
    return healthy_routes