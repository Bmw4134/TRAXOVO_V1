"""
TRAXORA Fleet Management System - Main Entry Point

This is the main entry point for the application, connecting to app.py configuration.
"""
from app import app

# Register blueprints if needed
def register_blueprints():
    """Register all blueprints with the application"""
    try:
        # Import blueprints
        from routes.driver_reports import driver_reports_bp
        app.register_blueprint(driver_reports_bp)
    except ImportError:
        pass
    
    try:
        # Import asset map blueprint
        from routes.asset_map import asset_map_bp
        app.register_blueprint(asset_map_bp)
    except ImportError:
        pass
    
    try:
        # Import billing blueprint
        from routes.billing import billing_bp
        app.register_blueprint(billing_bp)
    except ImportError:
        pass

# Make the app accessible to Gunicorn
if __name__ == "__main__":
    # For local development
    app.run(host="0.0.0.0", port=5000, debug=True)