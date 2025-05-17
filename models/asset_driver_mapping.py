"""
Asset-Driver mapping model definition.
"""
from datetime import datetime
from app import db

class AssetDriverMapping(db.Model):
    """Asset-Driver relationship model for tracking assignments"""
    __tablename__ = 'asset_driver_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    asset = db.relationship('Asset', backref=db.backref('driver_assignments', lazy='dynamic'))
    driver = db.relationship('Driver', backref=db.backref('asset_assignments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AssetDriverMapping {self.asset_id}-{self.driver_id}>'