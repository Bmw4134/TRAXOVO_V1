"""
Application factory module for SYSTEMSMITH.

This module contains the create_app function which constructs and configures
the Flask application, avoiding circular imports by using the application factory pattern.
"""

import os
import logging
from flask import Flask
from flask_login import LoginManager
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "fleet-management-default-key")
    
    # Configure session timeout (30 minutes of inactivity)
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    
    # Configure database
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize database with the application
    from database import db
    db.init_app(app)
    
    # Import and register models to ensure they're created
    with app.app_context():
        from models import User, Asset, AssetHistory, MaintenanceRecord, APIConfig, Geofence
        db.create_all()
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    
    # User loader callback for Flask-Login
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register routes
    from routes import register_routes
    register_routes(app)
    
    # Register blueprints
    from blueprints.reports import reports_bp
    app.register_blueprint(reports_bp)
    
    # Register error handlers with improved fault tolerance
    from flask import request, jsonify
    
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 Error: {request.url} not found. Continuing pipeline execution.")
        
        # If the request is for an API endpoint, return a JSON response
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Resource not found',
                'status': 404,
                'path': request.path,
                'message': 'The requested resource could not be found but the application continues to function.'
            }), 404
        
        # For regular page requests, show a friendly message
        # This is a fallback - we would normally use a template
        return "Page not found - The system is still functioning and other modules are available.", 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 Error: {str(e)} at {request.url}. Continuing pipeline execution.")
        
        # If the request is for an API endpoint, return a JSON response
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Server error',
                'status': 500,
                'path': request.path,
                'message': 'The server encountered an error but the application continues to function.'
            }), 500
        
        # Log details for troubleshooting
        import traceback
        logger.error(f"Exception details: {traceback.format_exc()}")
        
        # For regular page requests, show a friendly message
        # This is a fallback - we would normally use a template
        return "Server error - The system is still functioning and other modules are available.", 500
    
    return app