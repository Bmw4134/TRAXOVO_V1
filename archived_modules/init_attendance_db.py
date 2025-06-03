"""
Initialize Attendance Database Tables

This script creates the necessary database tables for attendance tracking
"""

from datetime import datetime
from flask import Flask
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a Flask app context for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create database engine and session
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=engine)
session = Session()

# Create base class for models
Base = declarative_base()

class Driver(Base):
    """Driver model for storing driver information"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    employee_id = Column(String(64), unique=True, nullable=False, index=True)
    department = Column(String(64))
    region = Column(String(64))
    asset_id = Column(Integer, ForeignKey('asset.id'))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the relationship with attendance records
    attendance_records = relationship('AttendanceRecord', backref='driver')

class JobSite(Base):
    """Job site model for storing job location information"""
    __tablename__ = 'job_sites'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    job_number = Column(String(64), unique=True, nullable=False, index=True)
    address = Column(String(256))
    city = Column(String(128))
    state = Column(String(64))
    zip_code = Column(String(16))
    latitude = Column(Float)
    longitude = Column(Float)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AttendanceRecord(Base):
    """Attendance record model for storing attendance events"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    report_date = Column(Date, nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'), nullable=False)
    status_type = Column(String(32), nullable=False, index=True)  # 'LATE_START', 'EARLY_END', 'NOT_ON_JOB'
    
    # Time-related fields for Late Start / Early End
    expected_start = Column(DateTime)
    actual_start = Column(DateTime)
    expected_end = Column(DateTime)
    actual_end = Column(DateTime)
    minutes_late = Column(Integer)
    minutes_early = Column(Integer)
    
    # Location-related fields for Not On Job
    expected_job_id = Column(Integer, ForeignKey('job_sites.id'))
    actual_job_id = Column(Integer, ForeignKey('job_sites.id'))
    
    # Common fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the relationships
    job_site = relationship('JobSite', foreign_keys=[job_site_id])
    expected_job = relationship('JobSite', foreign_keys=[expected_job_id])
    actual_job = relationship('JobSite', foreign_keys=[actual_job_id])

class AttendanceTrend(Base):
    """Attendance trend model for storing trend analysis data"""
    __tablename__ = 'attendance_trends'
    
    id = Column(Integer, primary_key=True)
    trend_date = Column(Date, nullable=False, index=True)
    trend_type = Column(String(32), nullable=False)  # 'DRIVER', 'JOB_SITE', 'DEPARTMENT', 'OVERALL'
    
    # Reference IDs (only one will be used depending on trend_type)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    department = Column(String(64))
    
    # Metrics
    late_start_count = Column(Integer, default=0)
    early_end_count = Column(Integer, default=0)
    not_on_job_count = Column(Integer, default=0)
    total_incidents = Column(Integer, default=0)
    
    # Weekly and monthly metrics (calculated)
    week_over_week_change = Column(Float)
    month_over_month_change = Column(Float)
    
    # Pattern indicators
    recurring_pattern = Column(Boolean, default=False)
    pattern_description = Column(String(256))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    """Create database tables"""
    try:
        # Create tables
        Base.metadata.create_all(engine)
        logger.info("Successfully created attendance database tables")
        return True
    except Exception as e:
        logger.error(f"Error creating attendance database tables: {e}")
        return False

if __name__ == "__main__":
    init_db()