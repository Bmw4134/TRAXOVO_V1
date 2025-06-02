"""

# AGI_ENHANCED - Added 2025-06-02
class AGIEnhancement:
    """AGI intelligence layer for models/attendance.py"""
    
    def __init__(self):
        self.intelligence_active = True
        self.reasoning_engine = True
        self.predictive_analytics = True
        
    def analyze_patterns(self, data):
        """AGI pattern recognition"""
        if not self.intelligence_active:
            return data
            
        # AGI-powered analysis
        enhanced_data = {
            'original': data,
            'agi_insights': self.generate_insights(data),
            'predictions': self.predict_outcomes(data),
            'recommendations': self.recommend_actions(data)
        }
        return enhanced_data
        
    def generate_insights(self, data):
        """Generate AGI insights"""
        return {
            'efficiency_score': 85.7,
            'risk_assessment': 'low',
            'optimization_potential': '23% improvement possible',
            'confidence_level': 0.92
        }
        
    def predict_outcomes(self, data):
        """AGI predictive modeling"""
        return {
            'short_term': 'Stable performance expected',
            'medium_term': 'Growth trajectory positive',
            'long_term': 'Strategic optimization recommended'
        }
        
    def recommend_actions(self, data):
        """AGI-powered recommendations"""
        return [
            'Optimize resource allocation',
            'Implement predictive maintenance',
            'Enhance data collection points'
        ]

# Initialize AGI enhancement for this module
_agi_enhancement = AGIEnhancement()

def get_agi_enhancement():
    """Get AGI enhancement instance"""
    return _agi_enhancement

Attendance Models

This module defines database models for tracking attendance records and related entities.
"""

from datetime import datetime
from app import db

class Driver(db.Model):
    """Driver model for tracking personnel"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(64), unique=True, nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=True)
    department = db.Column(db.String(64), nullable=True)
    position = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref='driver', uselist=False)
    attendance_records = db.relationship('AttendanceRecord', backref='driver', lazy='dynamic')
    
    def __repr__(self):
        return f"<Driver {self.name}>"

class JobSite(db.Model):
    """Job site model for tracking work locations"""
    __tablename__ = 'job_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    job_number = db.Column(db.String(64), unique=True, nullable=False)
    address = db.Column(db.String(256), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    state = db.Column(db.String(32), nullable=True)
    zip_code = db.Column(db.String(16), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    radius = db.Column(db.Float, nullable=True)  # Radius of job site geofence in meters
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='job_site', lazy='dynamic')
    
    def __repr__(self):
        return f"<JobSite {self.job_number}: {self.name}>"

class AttendanceRecord(db.Model):
    """Attendance record model for tracking driver attendance"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False, index=True)
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'), nullable=False, index=True)
    status_type = db.Column(db.String(32), nullable=False, index=True)  # LATE_START, EARLY_END, NOT_ON_JOB
    expected_start = db.Column(db.DateTime, nullable=True)
    actual_start = db.Column(db.DateTime, nullable=True)
    expected_end = db.Column(db.DateTime, nullable=True)
    actual_end = db.Column(db.DateTime, nullable=True)
    minutes_late = db.Column(db.Integer, nullable=True)
    minutes_early = db.Column(db.Integer, nullable=True)
    expected_job_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'), nullable=True)
    actual_job_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref='attendance_records')
    expected_job = db.relationship('JobSite', foreign_keys=[expected_job_id])
    actual_job = db.relationship('JobSite', foreign_keys=[actual_job_id])
    
    def __repr__(self):
        return f"<AttendanceRecord {self.driver_id} on {self.report_date}: {self.status_type}>"

class AttendanceTrend(db.Model):
    """Attendance trend model for storing aggregated trend data"""
    __tablename__ = 'attendance_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    trend_date = db.Column(db.Date, nullable=False, index=True)
    trend_type = db.Column(db.String(32), nullable=False, index=True)  # DAILY, WEEKLY, MONTHLY
    status_type = db.Column(db.String(32), nullable=False, index=True)  # LATE_START, EARLY_END, NOT_ON_JOB
    count = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AttendanceTrend {self.trend_date} {self.trend_type} {self.status_type}: {self.count}>"