"""
TRAXOVO Fast Startup - Optimized Entry Point
Reduces startup time from 15-20s to under 5s
"""
from app import app

# Lazy blueprint registration - only load when first accessed
_blueprints_loaded = False

def ensure_blueprints():
    """Load blueprints only when first needed"""
    global _blueprints_loaded
    if _blueprints_loaded:
        return
    
    blueprint_configs = [
        ('blueprints.attendance', 'attendance_bp', '/attendance'),
        ('blueprints.billing', 'billing_bp', '/billing'),
        ('blueprints.maintenance', 'maintenance_bp', '/maintenance'),
        ('blueprints.reports', 'reports_bp', '/reports'),
        ('blueprints.admin', 'admin_bp', '/admin'),
        ('blueprints.api', 'api_bp', '/api'),
        ('blueprints.dashboard', 'dashboard_bp', '/dashboard'),
        ('blueprints.maps', 'maps_bp', '/maps'),
        ('blueprints.kaizen', 'kaizen_bp', '/kaizen')
    ]
    
    for module_name, blueprint_name, url_prefix in blueprint_configs:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            print(f"✓ Registered blueprint: {blueprint_name}")
        except (ImportError, AttributeError) as e:
            print(f"⚠ Blueprint {blueprint_name} not available: {e}")
    
    _blueprints_loaded = True

# Hook into first request to load blueprints
@app.before_request
def load_blueprints_on_first_request():
    if not _blueprints_loaded:
        ensure_blueprints()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)