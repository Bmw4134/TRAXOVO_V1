"""
Driver Attendance Models

This module defines the database models for tracking driver attendance, including
late starts, early ends, and instances where drivers were not on their assigned job sites.
"""
from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Driver(db.Model):
    """Driver model for storing driver information"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    division = Column(String(20))
    department = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="driver")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Driver {self.first_name} {self.last_name} ({self.employee_id})>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class JobSite(db.Model):
    """Job site model for storing job site information"""
    __tablename__ = 'job_sites'
    
    id = Column(Integer, primary_key=True)
    job_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))
    location = Column(String(100))
    division = Column(String(20))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="job_site")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<JobSite {self.job_number} - {self.name}>"


class AttendanceRecord(db.Model):
    """Attendance record model for tracking driver attendance"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    asset_id = Column(String(20))
    
    # Job assignment info
    assigned_job_id = Column(Integer, ForeignKey('job_sites.id'), nullable=False)
    actual_job_id = Column(Integer, ForeignKey('job_sites.id'), nullable=True)
    
    # Time info
    expected_start_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    expected_end_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    
    # Issue flags
    late_start = Column(Boolean, default=False)
    early_end = Column(Boolean, default=False)
    not_on_job = Column(Boolean, default=False)
    
    # Relationships
    driver = relationship("Driver", back_populates="attendance_records")
    job_site = relationship("JobSite", foreign_keys=[assigned_job_id], back_populates="attendance_records")
    actual_job_site = relationship("JobSite", foreign_keys=[actual_job_id])
    
    # Metadata
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<AttendanceRecord {self.driver.full_name} {self.date.strftime('%Y-%m-%d')}>"
    
    @property
    def late_minutes(self):
        """Calculate minutes late if there was a late start"""
        if self.late_start and self.expected_start_time and self.actual_start_time:
            delta = self.actual_start_time - self.expected_start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def early_minutes(self):
        """Calculate minutes early if there was an early end"""
        if self.early_end and self.expected_end_time and self.actual_end_time:
            delta = self.expected_end_time - self.actual_end_time
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def issue_type(self):
        """Return the primary issue type for this attendance record"""
        if self.not_on_job:
            return "Not On Job"
        if self.late_start:
            return "Late Start"
        if self.early_end:
            return "Early End"
        return "On Time"
    
    @property
    def issue_details(self):
        """Return detailed information about the issue"""
        if self.not_on_job:
            return f"Expected {self.job_site.job_number}, Found {self.actual_job_site.job_number if self.actual_job_site else 'Unknown'}"
        if self.late_start:
            return f"{self.late_minutes} mins late"
        if self.early_end:
            return f"{self.early_minutes} mins early"
        return "No issues"


class AttendanceStats(db.Model):
    """Model for storing pre-calculated attendance statistics"""
    __tablename__ = 'attendance_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=True)
    job_site_id = Column(Integer, ForeignKey('job_sites.id'), nullable=True)
    division = Column(String(20))
    
    # Daily counts
    total_records = Column(Integer, default=0)
    late_starts = Column(Integer, default=0)
    early_ends = Column(Integer, default=0)
    not_on_job = Column(Integer, default=0)
    on_time = Column(Integer, default=0)
    
    # Performance
    attendance_score = Column(Float, default=0.0)  # Percentage
    
    # Trends (compared to previous period)
    trend_late = Column(Float, default=0.0)  # Positive = worse, negative = better
    trend_early = Column(Float, default=0.0)
    trend_not_on_job = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)  # Positive = better
    
    # Relationships
    driver = relationship("Driver", foreign_keys=[driver_id])
    job_site = relationship("JobSite", foreign_keys=[job_site_id])
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        scope = f"Driver {self.driver_id}" if self.driver_id else f"Job {self.job_site_id}" if self.job_site_id else "Division"
        return f"<AttendanceStats {scope} {self.date.strftime('%Y-%m-%d')}>"