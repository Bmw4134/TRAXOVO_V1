"""
Driver Attendance Models

This module defines the database models for tracking driver attendance and job site data.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app import db


class DriverAttendance(db.Model):
    """
    Model representing a driver/equipment operator for attendance tracking
    """
    __tablename__ = 'driver_attendance'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(20), nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    division = Column(String(50))
    department = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="driver_attendance")
    
    @property
    def full_name(self):
        """Get the driver's full name"""
        return f"{self.first_name} {self.last_name}"


class JobSiteAttendance(db.Model):
    """
    Model representing a job site/location for attendance tracking
    """
    __tablename__ = 'job_site_attendance'
    
    id = Column(Integer, primary_key=True)
    job_number = Column(String(20), index=True)
    name = Column(String(100))
    location = Column(String(255))
    division = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    assigned_records = relationship("AttendanceRecord", foreign_keys="AttendanceRecord.assigned_job_id", back_populates="assigned_job")
    actual_records = relationship("AttendanceRecord", foreign_keys="AttendanceRecord.actual_job_id", back_populates="actual_job")


class AttendanceRecord(db.Model):
    """
    Model representing a daily attendance record for a driver
    """
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('driver_attendance.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    assigned_job_id = Column(Integer, ForeignKey('job_site_attendance.id'), index=True)
    actual_job_id = Column(Integer, ForeignKey('job_site_attendance.id'), index=True)
    asset_id = Column(String(50))
    
    # Timestamps
    expected_start_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    expected_end_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    
    # Flags
    late_start = Column(Boolean, default=False, index=True)
    early_end = Column(Boolean, default=False, index=True)
    not_on_job = Column(Boolean, default=False, index=True)
    
    # Metadata
    notes = Column(Text)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    driver_attendance = relationship("DriverAttendance", back_populates="attendance_records")
    assigned_job = relationship("JobSiteAttendance", foreign_keys=[assigned_job_id], back_populates="assigned_records")
    actual_job = relationship("JobSiteAttendance", foreign_keys=[actual_job_id], back_populates="actual_records")


class AttendanceImportLog(db.Model):
    """
    Model for tracking attendance data imports
    """
    __tablename__ = 'attendance_import_logs'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    import_date = Column(DateTime, default=datetime.now)
    record_count = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    imported_by = Column(Integer, ForeignKey('users.id'))
    
    @property
    def import_summary(self):
        """Get a summary of the import"""
        status = "Successful" if self.success else "Failed"
        return f"{status} import of {self.record_count} records from {self.file_name} on {self.import_date.strftime('%Y-%m-%d %H:%M')}"