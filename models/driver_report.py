"""
Driver Report model definition for daily attendance tracking.
"""
from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app import db

class DriverReport(db.Model):
    """Driver Report model for daily attendance tracking"""
    __tablename__ = 'driver_reports'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)
    report_date = Column(Date, nullable=False)
    
    # Schedule times
    scheduled_start_time = Column(Time)
    scheduled_end_time = Column(Time)
    
    # Actual recorded times
    actual_start_time = Column(Time, nullable=True)
    actual_end_time = Column(Time, nullable=True)
    
    # Time differences
    minutes_early = Column(Integer, nullable=True)
    minutes_late = Column(Integer, nullable=True)
    minutes_early_end = Column(Integer, nullable=True)
    
    # Job site info
    job_site_id = Column(Integer, ForeignKey('job_sites.id'), nullable=True)
    assigned_job_number = Column(String(64))
    
    # Status classifications
    status = Column(String(32))  # on_time, late, early_end, not_on_job
    classification = Column(String(64))  # GENIUS CORE classification
    
    # GPS data
    first_location_lat = Column(Float, nullable=True)
    first_location_lon = Column(Float, nullable=True)
    last_location_lat = Column(Float, nullable=True)
    last_location_lon = Column(Float, nullable=True)
    
    # Validation data
    data_sources = Column(String(256))  # Comma-separated list of data source files
    validation_status = Column(String(32), default='pending')  # pending, validated, error
    validation_notes = Column(Text, nullable=True)
    validation_timestamp = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=False)
    
    # Tracking metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Define relationships
    driver = relationship('Driver', back_populates='reports')
    asset = relationship('Asset', backref='driver_reports')
    job_site = relationship('JobSite', backref='driver_reports')
    created_by = relationship('User', backref='created_reports')
    
    def __repr__(self):
        return f"<DriverReport {self.driver.name if self.driver else 'Unknown'} on {self.report_date}>"