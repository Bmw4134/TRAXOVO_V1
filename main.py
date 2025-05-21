"""
TRAXORA Fleet Management System - Main Application

This is the main entry point for the TRAXORA application.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify, flash, request, session
from flask_login import LoginManager, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, init_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for proper URL generation

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Adjust if using auth blueprint

# User loader function
@login_manager.user_loader
def load_user(user_id):
    from models import User
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

logger.info("Database tables created")

# Import and register blueprints
from routes.downloads import downloads_bp
app.register_blueprint(downloads_bp)
logger.info("Registered downloads blueprint")

# Import the driver module
try:
    from routes.drivers import driver_module_bp
    app.register_blueprint(driver_module_bp)
    logger.info("Registered Driver Module blueprint")
except ImportError:
    # Fall back to the fixed driver module if the new one isn't available
    from driver_module_fixed import driver_module_bp
    app.register_blueprint(driver_module_bp)
    logger.info("Registered Driver Module blueprint (fallback)")

# Register asset map blueprint
try:
    from routes.asset_map import asset_map_bp
    app.register_blueprint(asset_map_bp)
    logger.info("Registered Asset Map blueprint")
except ImportError:
    logger.info("Asset Map blueprint not available")

# Register PM allocation blueprint
try:
    from routes.pm_allocation import pm_allocation_bp
    app.register_blueprint(pm_allocation_bp)
    logger.info("Registered PM Allocation blueprint")
except ImportError:
    logger.info("PM Allocation blueprint not available")

# Register reports module blueprint
try:
    from routes.reports_fixed import reports_bp
    app.register_blueprint(reports_bp)
    logger.info("Registered Reports blueprint")
except ImportError:
    logger.info("Reports blueprint not available")

# Initialize lifecycle module
try:
    import equipment_lifecycle
    import lifecycle_integration
    logger.info("Initialized Equipment Lifecycle module")
except ImportError:
    logger.info("Equipment Lifecycle module not available")

# Temporary skip some modules
logger.info("Skipping asset_drivers blueprint temporarily")
logger.info("Skipping maintenance blueprint temporarily")

# Helper functions for the dashboard
def check_gauge_api_status():
    """Check the status of the Gauge API connection."""
    try:
        from gauge_api import GaugeAPI
        api = GaugeAPI()
        return api.check_connection()
    except Exception as e:
        logger.error(f"Failed to check Gauge API status: {str(e)}")
        return False

def check_database_status():
    """Check the status of the database connection."""
    try:
        with app.app_context():
            # Use text() from sqlalchemy to create a proper SQL expression
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Failed to check database status: {str(e)}")
        return False

def check_filesystem_status():
    """Check if required directories are available and writable."""
    required_dirs = ['data', 'reports', 'exports', 'uploads', 'templates', 'static']
    try:
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created missing directory: {directory}")
            
            # Try to create a test file to verify write permissions
            test_file = os.path.join(directory, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            if os.path.exists(test_file):
                os.remove(test_file)
        return True
    except Exception as e:
        logger.error(f"Failed to check filesystem status: {str(e)}")
        return False

def get_asset_count():
    """Get the total count of assets in the system."""
    try:
        from models import Asset
        with app.app_context():
            return Asset.query.count()
    except Exception as e:
        logger.error(f"Failed to get asset count: {str(e)}")
        # Fallback to direct data file check
        try:
            import glob
            asset_files = glob.glob('data/assets/*.json')
            if asset_files:
                return len(asset_files)
            return 0
        except Exception as inner_e:
            logger.error(f"Failed to get asset count from files: {str(inner_e)}")
            return 0

def get_driver_count():
    """Get the total count of drivers in the system."""
    try:
        from models import Driver
        with app.app_context():
            return Driver.query.count()
    except Exception as e:
        logger.error(f"Failed to get driver count: {str(e)}")
        # Fallback to direct data file check
        try:
            import csv
            driver_file = 'data/drivers.csv'
            if os.path.exists(driver_file):
                with open(driver_file, 'r') as f:
                    reader = csv.reader(f)
                    # Subtract 1 for header row
                    return max(0, sum(1 for _ in reader) - 1)
            return 0
        except Exception as inner_e:
            logger.error(f"Failed to get driver count from file: {str(inner_e)}")
            return 0

def get_last_sync_time():
    """Get the timestamp of the last data synchronization."""
    try:
        # Check multiple possible locations for sync timestamp
        possible_files = [
            os.path.join('data', 'last_sync.txt'),
            os.path.join('data', 'api_sync.log'),
            os.path.join('logs', 'sync.log')
        ]
        
        for sync_file in possible_files:
            if os.path.exists(sync_file):
                with open(sync_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return content
        
        # If no sync file found, check the modification time of data directory
        data_dir = 'data'
        if os.path.exists(data_dir):
            mtime = os.path.getmtime(data_dir)
            return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        return 'Never'
    except Exception as e:
        logger.error(f"Failed to get last sync time: {str(e)}")
        return 'Unknown'

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

@app.route('/asset-map')
def asset_map_redirect():
    """Direct access to the Asset Map"""
    return redirect(url_for('asset_map.asset_map'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'pass',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'TRAXORA Fleet Management System'
    })

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)