"""
TRAXORA Fleet Management System - Application Factory

This module provides the application factory for creating the Flask application.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

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
login_manager.login_message = "Please log in to access this page."

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
    try:
        import models
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# System status helpers
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
    """Check database connection status"""
    try:
        from sqlalchemy import text
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
    try:
        from models import SystemConfiguration
        last_sync = SystemConfiguration.query.filter_by(key='last_sync_time').first()
        if last_sync:
            return last_sync.value
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Routes
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
    
    return render_template('basic_dashboard.html', 
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