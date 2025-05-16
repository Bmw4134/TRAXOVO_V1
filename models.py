"""
Database models for the application
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Import the db instance from our database.py module
from database import db


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Asset(db.Model):
    """Asset model for tracking equipment and vehicles"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_identifier = db.Column(db.String(64), index=True, unique=True, nullable=False)
    label = db.Column(db.String(256))
    description = db.Column(db.Text)
    asset_category = db.Column(db.String(64), index=True)
    location = db.Column(db.String(256), index=True)
    active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(64), default='Available')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    engine_hours = db.Column(db.Float)
    vin = db.Column(db.String(128))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    history = db.relationship('AssetHistory', backref='asset', lazy='dynamic')
    maintenance_records = db.relationship('MaintenanceRecord', backref='asset', lazy='dynamic')
    
    def __repr__(self):
        return f'<Asset {self.asset_identifier}>'


class AssetHistory(db.Model):
    """Asset activity history for tracking"""
    __tablename__ = 'asset_history'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    event_time = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(256))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssetHistory {self.event_type} - {self.event_time}>'


class MaintenanceRecord(db.Model):
    """Records of maintenance performed on assets"""
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    maintenance_type = db.Column(db.String(64), nullable=False)
    date_performed = db.Column(db.DateTime, nullable=False)
    performed_by = db.Column(db.String(128))
    cost = db.Column(db.Float)
    hours_at_service = db.Column(db.Float)
    description = db.Column(db.Text)
    next_service_date = db.Column(db.DateTime)
    next_service_hours = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.maintenance_type} - {self.date_performed}>'


class APIConfig(db.Model):
    """API Configuration for external integrations"""
    __tablename__ = 'api_config'
    
    id = db.Column(db.Integer, primary_key=True)
    api_name = db.Column(db.String(64), unique=True, nullable=False)
    api_url = db.Column(db.String(256))
    username = db.Column(db.String(64))
    password_hash = db.Column(db.String(256))
    api_key = db.Column(db.String(256))
    last_sync = db.Column(db.DateTime)
    sync_frequency_minutes = db.Column(db.Integer, default=60)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<APIConfig {self.api_name}>'


class Geofence(db.Model):
    """Geofence boundaries for job sites and yards"""
    __tablename__ = 'geofences'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    site_type = db.Column(db.String(64))  # 'job_site', 'yard', 'restricted', etc.
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float)  # For circular geofences (meters)
    polygon_points = db.Column(db.Text)  # JSON string for polygon vertices
    active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    alert_on_entry = db.Column(db.Boolean, default=False)
    alert_on_exit = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Geofence {self.name}>'