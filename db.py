"""
Database configuration and initialization module.

This module contains the database configuration and SQLAlchemy instance
that should be imported by other modules that need database access.
"""

import logging
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the base class for SQLAlchemy models
class Base(DeclarativeBase):
    """SQLAlchemy DeclarativeBase for ORM models"""
    pass

# Create a SQLAlchemy instance that can be imported by other modules
db = SQLAlchemy(model_class=Base)
migrate = None

def init_app(app: Flask):
    """
    Initialize the database with the Flask app.
    
    Args:
        app: Flask app instance
    """
    global migrate
    
    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables created or verified")