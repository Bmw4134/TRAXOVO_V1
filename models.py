"""
TRAXOVO Fleet Management Models
Core database models for user authentication and fleet operations
"""

from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Asset(db.Model):
    """Asset model for fleet equipment tracking"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    last_update = db.Column(db.DateTime, default=datetime.now)
    billable = db.Column(db.Boolean, default=True)
    revenue = db.Column(db.Float, default=0.0)
    
class Driver(db.Model):
    """Driver model for employee tracking"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(50))
    job_code = db.Column(db.String(20))
    active = db.Column(db.Boolean, default=True)
    
class AttendanceRecord(db.Model):
    """Attendance tracking for drivers"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='present')
    asset_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)