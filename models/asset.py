"""
Asset model definition.
"""
from datetime import datetime
from app import db

class Asset(db.Model):
    """Asset model for equipment tracking"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_identifier = db.Column(db.String(64), index=True, unique=True, nullable=False)
    label = db.Column(db.String(128))
    type = db.Column(db.String(64))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    serial_number = db.Column(db.String(64))
    department = db.Column(db.String(64))
    division = db.Column(db.String(64))
    location = db.Column(db.String(128))
    status = db.Column(db.String(32), default='Active')
    last_reported = db.Column(db.DateTime)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    job_site = db.Column(db.String(128))
    engine_hours = db.Column(db.Float)
    fuel_level = db.Column(db.Float)
    last_maintenance = db.Column(db.DateTime)
    next_maintenance_due = db.Column(db.DateTime)
    
    # Organization relationship
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    organization = db.relationship('Organization', backref=db.backref('assets', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Asset {self.asset_identifier}>'