"""
Maintenance Models

This module defines database models for equipment maintenance tracking
"""

from datetime import datetime
from app import db

class MaintenanceStatus(db.Model):
    """
    Model for tracking maintenance status options
    """
    __tablename__ = 'maintenance_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)  # e.g., Scheduled, In Progress, Completed
    description = db.Column(db.Text, nullable=True)
    color_code = db.Column(db.String(16), nullable=True)  # For UI display
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaintenanceStatus {self.id}: {self.name}>"

class MaintenancePriority(db.Model):
    """
    Model for defining maintenance priority levels
    """
    __tablename__ = 'maintenance_priorities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)  # e.g., Critical, High, Medium, Low
    description = db.Column(db.Text, nullable=True)
    color_code = db.Column(db.String(16), nullable=True)  # For UI display
    sla_hours = db.Column(db.Integer, nullable=True)      # Service Level Agreement in hours
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaintenancePriority {self.id}: {self.name}>"

class MaintenanceType(db.Model):
    """
    Model for categorizing different types of maintenance
    """
    __tablename__ = 'maintenance_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    interval_days = db.Column(db.Integer, nullable=True)  # Default interval in days
    interval_hours = db.Column(db.Float, nullable=True)   # Default interval in engine hours
    estimated_cost = db.Column(db.Float, nullable=True)   # Estimated cost
    active = db.Column(db.Boolean, default=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaintenanceType {self.id}: {self.name}>"

class MaintenanceNotification(db.Model):
    """
    Model for tracking maintenance notifications and alerts
    """
    __tablename__ = 'maintenance_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Notification details
    notification_type = db.Column(db.String(64), nullable=False)  # scheduled, alert, overdue
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(32), default='normal')  # low, normal, high, critical
    
    # Status
    status = db.Column(db.String(32), default='pending')  # pending, acknowledged, resolved
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('maintenance_notifications', lazy=True))
    
    def __repr__(self):
        return f"<MaintenanceNotification {self.id}: {self.title}>"

class MaintenancePart(db.Model):
    """
    Model for tracking maintenance parts inventory
    """
    __tablename__ = 'maintenance_parts'
    
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    quantity_on_hand = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=0)
    last_ordered = db.Column(db.Date, nullable=True)
    supplier = db.Column(db.String(128), nullable=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaintenancePart {self.id}: {self.name}>"

class MaintenanceSchedule(db.Model):
    """
    Model for tracking scheduled maintenance
    """
    __tablename__ = 'maintenance_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # Schedule details
    maintenance_type = db.Column(db.String(64), nullable=False)  # oil_change, inspection, etc
    scheduled_date = db.Column(db.Date, nullable=False)
    due_hours = db.Column(db.Float, nullable=True)  # Due at X engine hours
    interval_hours = db.Column(db.Float, nullable=True)  # Repeat every X engine hours
    interval_days = db.Column(db.Integer, nullable=True)  # Repeat every X days
    
    # Status
    status = db.Column(db.String(32), default='scheduled')  # scheduled, completed, overdue
    completed_date = db.Column(db.Date, nullable=True)
    completed_hours = db.Column(db.Float, nullable=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('maintenance_schedules', lazy=True))
    
    def __repr__(self):
        return f"<MaintenanceSchedule {self.id}: {self.maintenance_type} for asset {self.asset_id}>"

class MaintenanceHistory(db.Model):
    """
    Model for tracking equipment maintenance history
    """
    __tablename__ = 'maintenance_history'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # History details
    event_type = db.Column(db.String(64), nullable=False)  # maintenance, repair, inspection
    event_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    hours_at_event = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    performed_by = db.Column(db.String(128), nullable=True)
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('maintenance_history', lazy=True))
    
    def __repr__(self):
        return f"<MaintenanceHistory {self.id}: {self.event_type} for asset {self.asset_id}>"

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