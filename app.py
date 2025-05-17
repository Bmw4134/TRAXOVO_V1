"""
SYSTEMSMITH: Fleet Management System - App Factory Module
"""
import os
import logging
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Create necessary directories
    for directory in ['uploads', 'extracted_data', 'exports', 'reports']:
        Path(directory).mkdir(exist_ok=True)
    
    # Register blueprints
    from routes.ocr import ocr_bp
    from routes.main import main_bp
    app.register_blueprint(ocr_bp)
    app.register_blueprint(main_bp)
    
    # Import models and create tables
    with app.app_context():
        import models  # noqa: F401
        
        # Create database tables
        db.create_all()
        logging.info("Database tables created")
    
    return app