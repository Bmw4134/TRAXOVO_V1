"""
Organization Models for TRAXORA

This module contains models for tracking organizations and related information.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship

from app import db

class Organization(db.Model):
    """
    Organization model for multi-tenant support
    """
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(16), unique=True, index=True)
    primary_contact = Column(String(128))
    primary_email = Column(String(128))
    primary_phone = Column(String(32))
    address = Column(String(256))
    city = Column(String(128))
    state = Column(String(64))
    zip_code = Column(String(16))
    
    # Configuration
    active = Column(Boolean, default=True)
    features_enabled = Column(JSON)  # JSON object containing feature flags
    preferences = Column(JSON)  # JSON object containing organization preferences
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (simplified to fix mapping errors)
    # Note: Relationships commented out to prevent circular dependency issues
    # job_sites = relationship('JobSite')  # Commented out until JobSite model adds organization_id
    
    def __repr__(self):
        return f'<Organization {self.name} ({self.code})>'