"""
TRAXORA Fleet Management System - Application Factory

This module provides the application factory pattern for creating
the Flask application with proper configuration.
"""
import os
import logging
from flask import Flask, render_template
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SESSION_SECRET", "development_key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_recycle": 300,
            "pool_pre_ping": True,
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Apply proxy fix for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'  # Adjust if using auth blueprint
    
    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        # Import here to avoid circular imports
        from models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Error loading user: {str(e)}")
            return None
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return render_template('500.html'), 500
    
    # Create tables
    with app.app_context():
        # Import models here to avoid circular imports
        import models  # noqa: F401
        
        try:
            db.create_all()
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    
    # Register blueprints
    from routes.downloads import downloads_bp
    app.register_blueprint(downloads_bp)
    logger.info("Registered downloads blueprint")
    
    from routes.drivers import driver_module_bp
    app.register_blueprint(driver_module_bp)
    logger.info("Registered Driver Module blueprint")
    
    from routes.asset_map import asset_map_bp
    app.register_blueprint(asset_map_bp)
    logger.info("Registered Asset Map blueprint")
    
    from routes.pm_allocation import pm_allocation_bp
    app.register_blueprint(pm_allocation_bp)
    logger.info("Registered PM Allocation blueprint")
    
    from routes.reports import reports_bp
    app.register_blueprint(reports_bp)
    logger.info("Registered Reports blueprint")
    
    # Initialize optional modules
    try:
        import equipment_lifecycle
        equipment_lifecycle.init_app(app)
        logger.info("Initialized Equipment Lifecycle module")
    except ImportError:
        logger.info("Equipment Lifecycle module not available")
    
    # Import views
    from views import register_views
    register_views(app)
    
    return app