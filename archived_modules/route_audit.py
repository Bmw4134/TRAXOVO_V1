#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | System Route Audit

This script performs a comprehensive audit of all registered routes in the application
to identify and fix any routing issues, missing handlers, or blueprint registration problems.
"""

import os
import sys
import inspect
import importlib
import logging
from datetime import datetime
from flask import Flask, Blueprint
from werkzeug.routing import Rule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs', exist_ok=True)
audit_log = logging.FileHandler('logs/system_route_audit.log')
audit_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(audit_log)

def extract_app():
    """Extract the Flask app from main.py"""
    try:
        # Import main module to get app
        sys.path.insert(0, os.getcwd())
        import main
        
        # Find Flask app instance
        for name, obj in inspect.getmembers(main):
            if isinstance(obj, Flask):
                return obj
        
        # If we couldn't find it as a member, try the 'app' attribute
        if hasattr(main, 'app') and isinstance(main.app, Flask):
            return main.app
            
        logger.error("Could not find Flask app in main.py")
        return None
    except Exception as e:
        logger.error(f"Error extracting app: {e}")
        return None

def scan_routes(app):
    """Scan all routes registered with the app"""
    if not app:
        logger.error("No app provided to scan routes")
        return None
    
    routes = []
    
    for rule in app.url_map.iter_rules():
        route_info = {
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'url': str(rule),
            'blueprint': rule.endpoint.split('.')[0] if '.' in rule.endpoint else None,
            'handler': None,
            'file': None,
            'line': None,
            'status': 'Unknown'
        }
        
        # Try to find the handler function
        try:
            if '.' in rule.endpoint:
                blueprint_name, view_func_name = rule.endpoint.split('.')
                
                # Check if blueprint exists in app
                if blueprint_name in app.blueprints:
                    blueprint = app.blueprints[blueprint_name]
                    
                    # Try to get the view function
                    view_func = blueprint.view_functions.get(view_func_name)
                    
                    if view_func:
                        route_info['handler'] = view_func.__name__
                        
                        # Get file and line number
                        try:
                            file_path = inspect.getfile(view_func)
                            route_info['file'] = os.path.relpath(file_path)
                            
                            _, line_no = inspect.getsourcelines(view_func)
                            route_info['line'] = line_no
                            
                            route_info['status'] = 'Active'
                        except Exception as e:
                            logger.warning(f"Could not get source for {view_func_name}: {e}")
            else:
                # Main app route
                view_func = app.view_functions.get(rule.endpoint)
                
                if view_func:
                    route_info['handler'] = view_func.__name__
                    
                    # Get file and line number
                    try:
                        file_path = inspect.getfile(view_func)
                        route_info['file'] = os.path.relpath(file_path)
                        
                        _, line_no = inspect.getsourcelines(view_func)
                        route_info['line'] = line_no
                        
                        route_info['status'] = 'Active'
                    except Exception as e:
                        logger.warning(f"Could not get source for {rule.endpoint}: {e}")
        except Exception as e:
            logger.warning(f"Error getting handler for {rule.endpoint}: {e}")
        
        routes.append(route_info)
    
    return routes

def scan_blueprints(app):
    """Scan all blueprints registered with the app"""
    if not app:
        logger.error("No app provided to scan blueprints")
        return None
    
    blueprints = []
    
    for name, blueprint in app.blueprints.items():
        blueprint_info = {
            'name': name,
            'url_prefix': blueprint.url_prefix,
            'static_folder': blueprint.static_folder,
            'template_folder': blueprint.template_folder,
            'registered': True,
            'source_file': None,
            'routes_count': 0
        }
        
        # Try to find source file
        try:
            module = inspect.getmodule(blueprint)
            if module:
                blueprint_info['source_file'] = inspect.getfile(module)
                
                # Count routes in this blueprint
                for rule in app.url_map.iter_rules():
                    if rule.endpoint.startswith(f"{name}."):
                        blueprint_info['routes_count'] += 1
        except Exception as e:
            logger.warning(f"Could not get source for blueprint {name}: {e}")
        
        blueprints.append(blueprint_info)
    
    return blueprints

def scan_modules_for_blueprints():
    """Scan all modules for blueprints that might not be registered"""
    unregistered_blueprints = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                module_name = os.path.splitext(file_path)[0].replace('/', '.').replace('./', '')
                
                try:
                    # Try to import the module
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for blueprint instances
                    for name, obj in inspect.getmembers(module):
                        if isinstance(obj, Blueprint):
                            unregistered_blueprints.append({
                                'name': obj.name,
                                'variable': name,
                                'source_file': file_path,
                                'url_prefix': obj.url_prefix
                            })
                except Exception as e:
                    # Ignore import errors, just looking for potential blueprints
                    pass
    
    return unregistered_blueprints

def check_template_references(app, routes):
    """Check if templates exist for routes that use render_template"""
    if not app:
        logger.error("No app provided to check templates")
        return
        
    for route in routes:
        if not route['file'] or not route['handler']:
            continue
            
        try:
            # Get the source code of the handler
            module_path = route['file']
            module_name = module_path.replace('/', '.').replace('.py', '')
            
            # Try to import the module
            module = importlib.import_module(module_name)
            
            # Get the handler function
            handler = getattr(module, route['handler'])
            
            # Get the source code
            source_code = inspect.getsource(handler)
            
            # Check if it uses render_template
            if 'render_template' in source_code:
                # TODO: Extract template name from source code
                # This is a complex task that would require parsing the Python code
                # For now, just mark the route as potentially using templates
                route['uses_templates'] = True
        except Exception as e:
            logger.warning(f"Error checking templates for {route['endpoint']}: {e}")

def check_static_files(app):
    """Check if static directories exist and have files"""
    if not app:
        logger.error("No app provided to check static files")
        return None
    
    static_info = {
        'app_static': {
            'path': app.static_folder,
            'exists': os.path.exists(app.static_folder) if app.static_folder else False,
            'file_count': 0
        },
        'blueprints': {}
    }
    
    # Check app static folder
    if app.static_folder and os.path.exists(app.static_folder):
        for root, dirs, files in os.walk(app.static_folder):
            static_info['app_static']['file_count'] += len(files)
    
    # Check blueprint static folders
    for name, blueprint in app.blueprints.items():
        if blueprint.static_folder:
            static_path = blueprint.static_folder
            
            # If it's a relative path, make it absolute
            if not os.path.isabs(static_path):
                static_path = os.path.join(os.path.dirname(blueprint.root_path), static_path)
            
            exists = os.path.exists(static_path)
            file_count = 0
            
            if exists:
                for root, dirs, files in os.walk(static_path):
                    file_count += len(files)
            
            static_info['blueprints'][name] = {
                'path': static_path,
                'exists': exists,
                'file_count': file_count
            }
    
    return static_info

def audit_routes():
    """Run a complete route audit and generate a report"""
    logger.info("Starting route audit")
    
    # Extract app
    app = extract_app()
    if not app:
        logger.error("Could not extract app, aborting audit")
        return
    
    # Scan routes
    routes = scan_routes(app)
    if not routes:
        logger.error("Could not scan routes, aborting audit")
        return
    
    # Scan blueprints
    blueprints = scan_blueprints(app)
    if not blueprints:
        logger.error("Could not scan blueprints, aborting audit")
        return
    
    # Scan for unregistered blueprints
    unregistered_blueprints = scan_modules_for_blueprints()
    
    # Check template references
    check_template_references(app, routes)
    
    # Check static files
    static_info = check_static_files(app)
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'app_name': app.name,
        'debug_mode': app.debug,
        'routes_count': len(routes),
        'blueprints_count': len(blueprints),
        'routes': routes,
        'blueprints': blueprints,
        'unregistered_blueprints': unregistered_blueprints,
        'static_info': static_info
    }
    
    # Save report to file
    report_path = 'logs/route_audit_report.json'
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Audit complete, report saved to {report_path}")
    
    # Generate text report
    text_report_path = 'logs/route_audit_report.txt'
    with open(text_report_path, 'w') as f:
        f.write("TRAXORA GENIUS CORE | SYSTEM ROUTE AUDIT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("APPLICATION SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"App Name: {app.name}\n")
        f.write(f"Debug Mode: {app.debug}\n")
        f.write(f"Total Routes: {len(routes)}\n")
        f.write(f"Total Blueprints: {len(blueprints)}\n")
        f.write(f"Potential Unregistered Blueprints: {len(unregistered_blueprints)}\n\n")
        
        f.write("REGISTERED BLUEPRINTS\n")
        f.write("=" * 80 + "\n")
        for bp in blueprints:
            f.write(f"Blueprint: {bp['name']}\n")
            f.write(f"  URL Prefix: {bp['url_prefix']}\n")
            f.write(f"  Routes Count: {bp['routes_count']}\n")
            f.write(f"  Source File: {bp['source_file']}\n")
            f.write("\n")
        
        if unregistered_blueprints:
            f.write("UNREGISTERED BLUEPRINTS\n")
            f.write("=" * 80 + "\n")
            for bp in unregistered_blueprints:
                f.write(f"Blueprint: {bp['name']}\n")
                f.write(f"  Variable Name: {bp['variable']}\n")
                f.write(f"  URL Prefix: {bp['url_prefix']}\n")
                f.write(f"  Source File: {bp['source_file']}\n")
                f.write("\n")
        
        f.write("REGISTERED ROUTES\n")
        f.write("=" * 80 + "\n")
        for route in routes:
            f.write(f"Route: {route['url']}\n")
            f.write(f"  Endpoint: {route['endpoint']}\n")
            f.write(f"  Methods: {', '.join(route['methods'])}\n")
            f.write(f"  Blueprint: {route['blueprint'] or 'main app'}\n")
            f.write(f"  Handler: {route['handler']}\n")
            f.write(f"  File: {route['file']}:{route['line']}\n")
            f.write(f"  Status: {route['status']}\n")
            f.write("\n")
        
        f.write("STATIC FILE INFO\n")
        f.write("=" * 80 + "\n")
        f.write(f"App Static Folder: {static_info['app_static']['path']}\n")
        f.write(f"  Exists: {static_info['app_static']['exists']}\n")
        f.write(f"  File Count: {static_info['app_static']['file_count']}\n\n")
        
        for name, info in static_info['blueprints'].items():
            f.write(f"Blueprint {name} Static Folder: {info['path']}\n")
            f.write(f"  Exists: {info['exists']}\n")
            f.write(f"  File Count: {info['file_count']}\n")
            f.write("\n")
    
    logger.info(f"Text report saved to {text_report_path}")
    return {
        'report': report,
        'json_path': report_path,
        'text_path': text_report_path
    }

def suggest_route_fixes(report):
    """Suggest fixes for route issues"""
    if not report:
        logger.error("No report provided to suggest fixes")
        return None
    
    fixes = []
    
    # Check for 404 routes
    for route in report['routes']:
        if route['status'] != 'Active':
            fixes.append({
                'type': 'route_inactive',
                'route': route['url'],
                'endpoint': route['endpoint'],
                'suggestion': f"Check handler function for {route['endpoint']} in {route['file']}"
            })
    
    # Check for unregistered blueprints
    for bp in report['unregistered_blueprints']:
        # Check if this blueprint name is not already registered
        if not any(registered['name'] == bp['name'] for registered in report['blueprints']):
            fixes.append({
                'type': 'unregistered_blueprint',
                'blueprint': bp['name'],
                'source_file': bp['source_file'],
                'suggestion': f"Register blueprint {bp['variable']} from {bp['source_file']}"
            })
    
    # Check for empty blueprints
    for bp in report['blueprints']:
        if bp['routes_count'] == 0:
            fixes.append({
                'type': 'empty_blueprint',
                'blueprint': bp['name'],
                'source_file': bp['source_file'],
                'suggestion': f"Blueprint {bp['name']} has no routes, check {bp['source_file']}"
            })
    
    # Generate fix script
    fix_script_path = 'fix_routes.py'
    with open(fix_script_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
TRAXORA GENIUS CORE | Route Fix Script

This script applies fixes to route issues identified in the route audit.
\"\"\"

import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_routes():
    \"\"\"Apply route fixes\"\"\"
    logger.info("Applying route fixes")
    
    # Add your fix code here
    # Example:
    # from app import app
    # from missing_module import missing_blueprint
    # app.register_blueprint(missing_blueprint)
    
""")
        
        # Add fix code
        for fix in fixes:
            if fix['type'] == 'unregistered_blueprint':
                f.write(f"""
    # Fix for unregistered blueprint {fix['blueprint']}
    try:
        # Import blueprint from {fix['source_file']}
        module_path = "{fix['source_file'].replace('/', '.').replace('.py', '')}"
        module = importlib.import_module(module_path)
        
        # Get blueprint
        blueprint = getattr(module, "{fix['blueprint']}")
        
        # Register blueprint
        from main import app
        app.register_blueprint(blueprint)
        
        logger.info("Registered blueprint {fix['blueprint']}")
    except Exception as e:
        logger.error(f"Error registering blueprint {fix['blueprint']}: {{e}}")
""")
        
        # Add main call
        f.write("""
if __name__ == "__main__":
    fix_routes()
""")
    
    logger.info(f"Fix script generated at {fix_script_path}")
    return {
        'fixes': fixes,
        'fix_script': fix_script_path
    }

def main():
    """Main function"""
    # Run audit
    audit_result = audit_routes()
    
    if audit_result:
        # Suggest fixes
        fix_result = suggest_route_fixes(audit_result['report'])
        
        if fix_result:
            print("\nRoute Audit Complete")
            print("=" * 80)
            print(f"Audit report saved to {audit_result['text_path']}")
            print(f"Fix script generated at {fix_result['fix_script']}")
            print("\nSuggested Fixes:")
            
            for i, fix in enumerate(fix_result['fixes'], 1):
                print(f"{i}. {fix['suggestion']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())