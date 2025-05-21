"""
Asset model definition.
"""
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app import db
from models.associations import asset_jobsite_association

# Association table is defined in models/associations.py

class Asset(db.Model):
    """Asset model for equipment tracking"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # GENIUS CORE CONTINUITY MODE fields - main identifiers
    asset_id = db.Column(db.String(64), index=True, unique=True, nullable=False)
    name = db.Column(db.String(128))
    
    # Original fields
    asset_identifier = db.Column(db.String(64), index=True, unique=True)
    label = db.Column(db.String(128))
    type = db.Column(db.String(64))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    serial_number = db.Column(db.String(64))
    department = db.Column(db.String(64))
    division = db.Column(db.String(64))
    location = db.Column(db.String(128))
    status = db.Column(db.String(32), default='active')  # active, maintenance, inactive, retired
    is_active = db.Column(db.Boolean, default=True)
    
    # Location tracking fields
    last_latitude = db.Column(db.Float)
    last_longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    
    # Original location fields
    last_reported = db.Column(db.DateTime)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    job_site = db.Column(db.String(128))
    
    # Maintenance fields
    engine_hours = db.Column(db.Float)
    fuel_level = db.Column(db.Float)
    acquisition_date = db.Column(db.Date)
    disposal_date = db.Column(db.Date)
    last_service_date = db.Column(db.Date)
    next_service_date = db.Column(db.Date)
    last_maintenance = db.Column(db.DateTime)
    next_maintenance_due = db.Column(db.DateTime)
    
    # Additional fields
    notes = db.Column(db.String(512))
    properties = db.Column(db.JSON)
    
    # Relationships
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    current_driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    organization = db.relationship('Organization', back_populates='assets')
    current_driver = db.relationship('Driver', back_populates='assigned_assets')
    locations = db.relationship('AssetLocation', back_populates='asset')
    job_sites = db.relationship('JobSite', secondary=asset_jobsite_association, back_populates='assets')
    
    def __repr__(self):
        return f'<Asset {self.asset_id}>'