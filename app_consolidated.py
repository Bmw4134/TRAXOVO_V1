"""
TRAXORA Fleet Management System - Application Factory

This module provides the application factory for creating the Flask application.
Consolidates functionality from multiple app files into a single, consistent implementation.
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models using the new-style declarative base."""
    pass

# Initialize database with the base class
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Set secret key for sessions
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(24)

# Use ProxyFix to handle reverse proxies (required for proper URL generation)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "pool_pre_ping": True,  # Verify connection is still valid before using
}

# Initialize extensions with the app
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    try:
        import models
        db.create_all()
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload size
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure runtime environment
app.config['RUNTIME_MODE'] = os.environ.get('RUNTIME_MODE', 'DEVELOPMENT').upper()
logger.info(f"TRAXORA running in {app.config['RUNTIME_MODE']} mode")

# Import and register routes if this is the main app file
if __name__ == 'app':
    try:
        from routes.basic_routes import register_basic_routes
        register_basic_routes(app)
    except ImportError:
        logger.warning("Basic routes not found")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    from flask import render_template
    return render_template('basic_error.html', 
                          error_code=404,
                          error_message="Page not found",
                          error_details="The requested page does not exist."), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    from flask import render_template
    logger.error(f"Server error: {str(e)}")
    return render_template('basic_error.html',
                          error_code=500,
                          error_message="Internal server error",
                          error_details="An unexpected error occurred on the server."), 500

# Run the app if executed directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)