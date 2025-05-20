"""
TRAXORA Fleet Management System - Main Application

This is the main entry point for the TRAXORA application.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Create tables
with app.app_context():
    # Import models here to avoid circular imports
    import models  # noqa: F401
    db.create_all()
    logger.info("Database tables created")

# Import and register blueprints
from routes.downloads import downloads_bp
app.register_blueprint(downloads_bp)
logger.info("Registered downloads blueprint")

# Import the fixed driver module
from routes.driver_module_fixed import driver_module_bp
app.register_blueprint(driver_module_bp)
logger.info("Registered Driver Module blueprint")

# Temporary skip some modules
logger.info("Skipping asset_drivers blueprint temporarily")
logger.info("Skipping maintenance blueprint temporarily")

@app.route('/')
def index():
    """Application home page"""
    return redirect(url_for('driver_module.daily_report'))

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