"""
Attendance Models Module

This module defines database models for tracking attendance data, including:
- Driver information and history
- Job site definitions and locations
- Attendance records (Late Start, Early End, Not On Job)
- Attendance trends for pattern analysis
"""

from datetime import datetime
from sqlalchemy import func, Index
from app import db


class Driver(db.Model):
    """Driver model for storing driver information"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    department = db.Column(db.String(64))
    region = db.Column(db.String(64))
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='driver', lazy='dynamic')
    
    def __repr__(self):
        return f"<Driver {self.name} ({self.employee_id})>"


class JobSite(db.Model):
    """Job site model for storing job location information"""
    __tablename__ = 'job_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    job_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    address = db.Column(db.String(256))
    city = db.Column(db.String(128))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(16))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', 
                                        foreign_keys='AttendanceRecord.job_site_id', 
                                        backref='job_site', 
                                        lazy='dynamic')
    expected_attendance = db.relationship('AttendanceRecord', 
                                         foreign_keys='AttendanceRecord.expected_job_id', 
                                         backref='expected_job', 
                                         lazy='dynamic')
    actual_attendance = db.relationship('AttendanceRecord', 
                                       foreign_keys='AttendanceRecord.actual_job_id', 
                                       backref='actual_job', 
                                       lazy='dynamic')
    
    def __repr__(self):
        return f"<JobSite {self.name} ({self.job_number})>"


class AttendanceRecord(db.Model):
    """Attendance record model for storing attendance events"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'), nullable=False)
    status_type = db.Column(db.String(32), nullable=False, index=True)  # 'LATE_START', 'EARLY_END', 'NOT_ON_JOB'
    
    # Time-related fields for Late Start / Early End
    expected_start = db.Column(db.DateTime)
    actual_start = db.Column(db.DateTime)
    expected_end = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    minutes_late = db.Column(db.Integer)
    minutes_early = db.Column(db.Integer)
    
    # Location-related fields for Not On Job
    expected_job_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    actual_job_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    
    # Common fields
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_driver_date', driver_id, report_date),
        Index('idx_job_date', job_site_id, report_date),
        Index('idx_status_date', status_type, report_date),
    )
    
    def __repr__(self):
        return f"<AttendanceRecord {self.driver_id} - {self.report_date} - {self.status_type}>"


class AttendanceTrend(db.Model):
    """Attendance trend model for storing trend analysis data"""
    __tablename__ = 'attendance_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    trend_date = db.Column(db.Date, nullable=False, index=True)
    trend_type = db.Column(db.String(32), nullable=False)  # 'DRIVER', 'JOB_SITE', 'DEPARTMENT', 'OVERALL'
    
    # Reference IDs (only one will be used depending on trend_type)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    department = db.Column(db.String(64))
    
    # Metrics
    late_start_count = db.Column(db.Integer, default=0)
    early_end_count = db.Column(db.Integer, default=0)
    not_on_job_count = db.Column(db.Integer, default=0)
    total_incidents = db.Column(db.Integer, default=0)
    
    # Weekly and monthly metrics (calculated)
    week_over_week_change = db.Column(db.Float)
    month_over_month_change = db.Column(db.Float)
    
    # Pattern indicators
    recurring_pattern = db.Column(db.Boolean, default=False)
    pattern_description = db.Column(db.String(256))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_trend_date_type', trend_date, trend_type),
        Index('idx_driver_trend', driver_id, trend_date),
        Index('idx_job_trend', job_site_id, trend_date),
    )
    
    def __repr__(self):
        if self.trend_type == 'DRIVER':
            return f"<AttendanceTrend {self.trend_date} - Driver {self.driver_id}>"
        elif self.trend_type == 'JOB_SITE':
            return f"<AttendanceTrend {self.trend_date} - Job Site {self.job_site_id}>"
        elif self.trend_type == 'DEPARTMENT':
            return f"<AttendanceTrend {self.trend_date} - Department {self.department}>"
        else:
            return f"<AttendanceTrend {self.trend_date} - Overall>"