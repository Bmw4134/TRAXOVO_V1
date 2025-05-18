"""
Maintenance Models

This module defines the database models for equipment maintenance scheduling and tracking.
"""

from datetime import datetime
from app import db

class MaintenanceSchedule(db.Model):
    """Model for equipment maintenance scheduling"""
    __tablename__ = 'maintenance_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), db.ForeignKey('assets.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    asset = db.relationship('Asset', backref='maintenance_schedules')
    
    def __repr__(self):
        return f'<MaintenanceSchedule {self.id} for asset {self.asset_id}>'

class MaintenanceRecord(db.Model):
    """Model for completed maintenance records"""
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), db.ForeignKey('assets.id'), nullable=False)
    maintenance_date = db.Column(db.DateTime, nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)
    performed_by = db.Column(db.String(100))
    hours = db.Column(db.Float, default=0)
    cost = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id'), nullable=True)
    
    # Relationships
    asset = db.relationship('Asset', backref='maintenance_records')
    schedule = db.relationship('MaintenanceSchedule', backref='completed_maintenance')
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id} for asset {self.asset_id}>'