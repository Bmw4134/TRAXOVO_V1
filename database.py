"""
TRAXORA Fleet Management System - Database Module

This module contains the database configuration and initialization.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create a database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

def init_app(app):
    """Initialize the database with the Flask app"""
    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    })
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database with app
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        try:
            # Import models here to avoid circular imports
            import models  # noqa: F401
            db.create_all()
            return db
        except Exception as e:
            import logging
            logging.error(f"Failed to create database tables: {str(e)}")
            # Return db even on error so the application can continue
            return db