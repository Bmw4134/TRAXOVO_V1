"""
Asset History Model

This module defines the database model for tracking asset history records
"""

from datetime import datetime
from app import db

class AssetHistory(db.Model):
    """
    Model for tracking asset history records over time
    """
    __tablename__ = 'asset_history'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Event data
    event_type = db.Column(db.String(32), nullable=False)  # location_update, engine_hours_update, status_change
    event_date_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Asset metrics
    engine_hours = db.Column(db.Float, nullable=True)
    odometer = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(256), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(64), nullable=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON, nullable=True)  # Additional event details as JSON
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('history', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AssetHistory {self.id}: {self.event_type} for asset {self.asset_id}>"