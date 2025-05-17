"""
Organization model for multi-organization support in TRAXORA.

This module defines the Organization model and related functionality
to support multiple organizations within the application.
"""

from datetime import datetime
from app import db

class Organization(db.Model):
    """
    Organization model for multi-organization support.
    
    Each organization represents a separate business entity (e.g., Ragle Inc, 
    Select Maintenance, Unified Specialties) with its own assets, employees,
    and reporting structure.
    """
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(256), nullable=True)
    primary_color = db.Column(db.String(16), nullable=True, default="#00457c")  # Default TRAXORA blue
    
    # Contact details
    contact_email = db.Column(db.String(128), nullable=True)
    contact_phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.String(256), nullable=True)
    city = db.Column(db.String(128), nullable=True)
    state = db.Column(db.String(64), nullable=True)
    zip_code = db.Column(db.String(16), nullable=True)
    
    # Configuration options stored as JSON
    config_options = db.Column(db.JSON, nullable=True)
    
    # Status flags
    active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Meta information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships defined in their respective models
    # users = db.relationship('User', backref='organization')
    # assets = db.relationship('Asset', backref='organization')
    # drivers = db.relationship('Driver', backref='organization')
    # job_sites = db.relationship('JobSite', backref='organization')
    
    def __repr__(self):
        return f"<Organization {self.id}: {self.name}>"
    
    @classmethod
    def get_default(cls):
        """Get the default organization, creating Ragle Inc if none exists."""
        default_org = cls.query.filter_by(is_default=True).first()
        
        if not default_org:
            # Create the default Ragle Inc organization
            default_org = cls(
                name="Ragle Inc",
                slug="ragle",
                description="Ragle Inc - Construction Equipment Management",
                is_default=True,
                active=True
            )
            db.session.add(default_org)
            
            # Create additional organizations but set as inactive
            select_org = cls(
                name="Select Maintenance",
                slug="select",
                description="Select Maintenance - Equipment Service Division",
                is_default=False,
                active=False  # Inactive until explicitly enabled
            )
            db.session.add(select_org)
            
            unified_org = cls(
                name="Unified Specialties",
                slug="unified",
                description="Unified Specialties - Specialized Equipment Division",
                is_default=False,
                active=False  # Inactive until explicitly enabled
            )
            db.session.add(unified_org)
            
            db.session.commit()
        
        return default_org