"""
Job Site Models for TRAXORA

This module contains models for tracking job sites and related information.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app import db
from models.associations import asset_jobsite_association

class JobSite(db.Model):
    """
    Job Site model for tracking work locations
    """
    __tablename__ = 'job_sites'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    job_number = Column(String(64), unique=True, index=True)
    address = Column(String(256))
    city = Column(String(128))
    state = Column(String(64))
    zip_code = Column(String(16))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Geofence data for GENIUS CORE tracking
    radius = Column(Float, default=500.0)  # Radius in meters for geofence
    geofence_enabled = Column(Boolean, default=True)
    geofence_config = Column(JSON, nullable=True)  # Custom geofence configuration
    
    # Job details
    client = Column(String(128))
    contract_number = Column(String(64))
    start_date = Column(Date)
    end_date = Column(Date)
    
    # Schedule information
    work_start_time = Column(String(8), default='07:00')  # Format: HH:MM (24-hour)
    work_end_time = Column(String(8), default='17:00')  # Format: HH:MM (24-hour)
    days_of_week = Column(String(32), default='0,1,2,3,4')  # 0=Monday, 6=Sunday
    
    # Status
    active = Column(Boolean, default=True)
    status = Column(String(64), default='Active')  # Active, Completed, Pending, etc.
    
    # Metadata
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships temporarily removed to fix login blocking issue
    # job_zones relationship is maintained in the JobZone model
    
    def __repr__(self):
        return f'<JobSite {self.name} ({self.job_number})>'