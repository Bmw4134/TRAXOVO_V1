"""
TRAXORA Fleet Management System - Simplified Application

This module provides a simplified approach to create the Flask application.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify, flash, request, session
from flask_login import LoginManager, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application
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
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader function
@login_manager.user_loader
def load_user(user_id):
    from models import User
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# Create tables
with app.app_context():
    # Import models here to avoid circular imports
    import models  # noqa: F401
    try:
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

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
        from sqlalchemy import text
        with app.app_context():
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
        return 0

def get_driver_count():
    """Get the total count of drivers in the system."""
    try:
        from models import Driver
        with app.app_context():
            return Driver.query.count()
    except Exception as e:
        logger.error(f"Failed to get driver count: {str(e)}")
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
        
        # If no sync file found, return current time
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Failed to get last sync time: {str(e)}")
        return 'Unknown'

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500

# Index route
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
        'status': 'ok',
        'database': check_database_status(),
        'gauge_api': check_gauge_api_status(),
        'filesystem': check_filesystem_status(),
        'timestamp': datetime.now().isoformat()
    })