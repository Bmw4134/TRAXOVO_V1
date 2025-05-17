"""
Job Site Models for TRAXORA

This module contains models for tracking job sites and related information.
"""
from datetime import datetime
from app import db

class JobSite(db.Model):
    """
    Job Site model for tracking work locations
    """
    __tablename__ = 'job_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    job_number = db.Column(db.String(64), unique=True, index=True)
    address = db.Column(db.String(256))
    city = db.Column(db.String(128))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(16))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Job details
    client = db.Column(db.String(128))
    contract_number = db.Column(db.String(64))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Status
    active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(64), default='Active')  # Active, Completed, Pending, etc.
    
    # Metadata
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # job_zones relationship is defined in JobZone model
    
    def __repr__(self):
        return f'<JobSite {self.name} ({self.job_number})>'