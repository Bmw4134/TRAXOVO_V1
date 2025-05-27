"""
Asset Location model definition.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app import db

class AssetLocation(db.Model):
    """Asset Location model for tracking equipment location history"""
    __tablename__ = 'asset_locations'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float, nullable=True)
    location_timestamp = Column(DateTime)
    location_source = Column(String(64))  # gps, manual, gauge_api
    job_site_id = Column(Integer, ForeignKey('job_sites.id'), nullable=True)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships temporarily removed to fix login blocking issue
    
    def __repr__(self):
        return f"<AssetLocation for Asset #{self.asset_id} at {self.location_timestamp}>"