"""
Organization Models for TRAXORA

This module contains models for tracking organizations and related information.
"""
from datetime import datetime
from app import db

class Organization(db.Model):
    """
    Organization model for multi-tenant support
    """
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(16), unique=True, index=True)
    primary_contact = db.Column(db.String(128))
    primary_email = db.Column(db.String(128))
    primary_phone = db.Column(db.String(32))
    address = db.Column(db.String(256))
    city = db.Column(db.String(128))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(16))
    
    # Configuration
    active = db.Column(db.Boolean, default=True)
    features_enabled = db.Column(db.JSON)  # JSON object containing feature flags
    preferences = db.Column(db.JSON)  # JSON object containing organization preferences
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Organization {self.name} ({self.code})>'