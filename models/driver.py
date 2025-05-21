"""
Driver model definition.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app import db

class Driver(db.Model):
    """Driver model for personnel tracking"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    employee_id = Column(String(64), unique=True, nullable=False, index=True)
    department = Column(String(64))
    division = Column(String(64))
    region = Column(String(64))
    job_title = Column(String(64))
    phone = Column(String(32))
    email = Column(String(128))
    license_number = Column(String(64))
    license_class = Column(String(32))
    license_expiration = Column(Date)
    status = Column(String(32), default='Active')
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # GENIUS CORE CONTINUITY MODE fields
    job_site_id = Column(Integer, ForeignKey('job_sites.id'), nullable=True)
    last_known_latitude = Column(String(32), nullable=True)
    last_known_longitude = Column(String(32), nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # Organization relationship
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    organization = relationship('Organization', back_populates='drivers')
    job_site = relationship('JobSite', back_populates='drivers')
    reports = relationship('DriverReport', back_populates='driver')
    assigned_assets = relationship('Asset', back_populates='current_driver')
    
    def __repr__(self):
        return f'<Driver {self.name}>'