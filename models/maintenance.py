"""
Maintenance Models

This module defines database models for equipment maintenance tracking
"""

from datetime import datetime
from app import db

class MaintenanceRecord(db.Model):
    """
    Model for tracking equipment maintenance records
    """
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Maintenance details
    service_type = db.Column(db.String(64), nullable=False)  # oil_change, inspection, repair
    service_date = db.Column(db.Date, nullable=False)
    technician = db.Column(db.String(128), nullable=True)
    service_location = db.Column(db.String(128), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Service intervals
    last_service_hours = db.Column(db.Float, nullable=True)  # Engine hours at last service
    current_hours = db.Column(db.Float, nullable=True)       # Current engine hours
    hours_interval = db.Column(db.Integer, nullable=True)    # Service interval in hours
    days_interval = db.Column(db.Integer, nullable=True)     # Service interval in days
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('maintenance_records', lazy=True))
    
    def __repr__(self):
        return f"<MaintenanceRecord {self.id}: {self.service_type} for asset {self.asset_id}>"

class MaintenanceTask(db.Model):
    """
    Model for scheduled maintenance tasks
    """
    __tablename__ = 'maintenance_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Task details
    task_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(32), nullable=False, default='normal')  # low, normal, high, critical
    
    # Scheduling
    due_date = db.Column(db.Date, nullable=True)
    scheduled_date = db.Column(db.Date, nullable=True)
    completed_date = db.Column(db.Date, nullable=True)
    assigned_to = db.Column(db.String(128), nullable=True)
    
    # Status
    status = db.Column(db.String(32), nullable=False, default='pending')  # pending, scheduled, in_progress, completed, canceled
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('maintenance_tasks', lazy=True))
    
    def __repr__(self):
        return f"<MaintenanceTask {self.id}: {self.task_name} for asset {self.asset_id}>"