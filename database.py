"""
Database module for SQLAlchemy initialization

This module provides a consistent way to set up the database
connection throughout the application without circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass

# Create the SQLAlchemy instance to be used throughout the application
db = SQLAlchemy(model_class=Base)
migrate = None

def init_app(app):
    """Initialize the database with the Flask app"""
    global migrate
    
    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)