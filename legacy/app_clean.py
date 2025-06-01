"""
TRAXORA Fleet Management System - Clean Application

This is a simplified, clean version of the application to ensure proper functionality.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize login manager
login_manager = LoginManager()

# Create Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "development_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader
@login_manager.user_loader
def load_user(user_id):
    try:
        from models import User
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# Initialize database
with app.app_context():
    import models
    try:
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Dashboard helper functions
def check_gauge_api_status():
    """Check the status of the Gauge API connection."""
    try:
        from gauge_api_legacy import GaugeAPI
        api = GaugeAPI()
        return api.check_connection()
    except Exception as e:
        logger.error(f"Failed to check Gauge API status: {str(e)}")
        return False

def check_database_status():
    """Check database connection status"""
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Failed to check database status: {str(e)}")
        return False

def check_filesystem_status():
    """Check filesystem status"""
    required_dirs = ['data', 'reports', 'exports', 'uploads']
    try:
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to check filesystem status: {str(e)}")
        return False

def get_asset_count():
    """Get asset count"""
    try:
        from models import Asset
        return Asset.query.count()
    except Exception:
        return 0

def get_driver_count():
    """Get driver count"""
    try:
        from models import Driver
        return Driver.query.count()
    except Exception:
        return 0

def get_last_sync_time():
    """Get last sync time"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Main routes
@app.route('/')
def index():
    """Application main dashboard"""
    # API status check
    api_status = {
        'gauge_api': check_gauge_api_status(),
        'database': check_database_status(),
        'file_system': check_filesystem_status()
    }
    
    # Get system stats
    system_stats = {
        'asset_count': get_asset_count(),
        'driver_count': get_driver_count(),
        'last_sync': get_last_sync_time()
    }
    
    return render_template('dashboard.html', 
                          api_status=api_status,
                          system_stats=system_stats,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'database': check_database_status(),
        'gauge_api': check_gauge_api_status(),
        'filesystem': check_filesystem_status(),
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

# Register blueprints only when needed
def register_blueprints():
    """Register all blueprints"""
    # Import and register driver module
    try:
        from routes.drivers import driver_module_bp
        app.register_blueprint(driver_module_bp)
        logger.info("Registered Driver Module blueprint")
    except Exception as e:
        logger.error(f"Failed to register Driver Module blueprint: {str(e)}")

    # Import and register asset map
    try:
        from routes.asset_map import asset_map_bp
        app.register_blueprint(asset_map_bp)
        logger.info("Registered Asset Map blueprint")
    except Exception as e:
        logger.error(f"Failed to register Asset Map blueprint: {str(e)}")

    # Import and register PM allocation
    try:
        from routes.pm_allocation import pm_allocation_bp
        app.register_blueprint(pm_allocation_bp)
        logger.info("Registered PM Allocation blueprint")
    except Exception as e:
        logger.error(f"Failed to register PM Allocation blueprint: {str(e)}")
        
    # Import and register downloads
    try:
        from routes.downloads import downloads_bp
        app.register_blueprint(downloads_bp)
        logger.info("Registered Downloads blueprint")
    except Exception as e:
        logger.error(f"Failed to register Downloads blueprint: {str(e)}")

# Register all blueprints
register_blueprints()

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)