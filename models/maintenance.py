"""
Maintenance Module Models

This module defines the database models for the maintenance scheduling system.
It tracks maintenance schedules, history, and integrates with the asset tracking system.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import db


class MaintenanceStatus(enum.Enum):
    """Status enum for maintenance tasks"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELED = "canceled"


class MaintenanceType(enum.Enum):
    """Types of maintenance"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"


class MaintenanceSchedule(db.Model):
    """Model for scheduled maintenance tasks"""
    __tablename__ = 'maintenance_schedules'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('asset.id'), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    
    # Schedule details
    scheduled_date = Column(DateTime, nullable=False, index=True)
    estimated_duration_hours = Column(Float, default=1.0)
    recurrence_interval_days = Column(Integer, default=0)  # 0 = no recurrence
    
    # Maintenance metadata
    maintenance_type = Column(Enum(MaintenanceType), default=MaintenanceType.PREVENTIVE)
    priority = Column(Integer, default=3)  # 1=highest, 5=lowest
    
    # Allocation and assignment
    assigned_technician_id = Column(Integer, ForeignKey('users.id'))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    estimated_cost = Column(Float)
    
    # Status tracking
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED)
    notification_sent = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    asset = relationship('Asset', backref='maintenance_schedules')
    technician = relationship('User', foreign_keys=[assigned_technician_id], 
                             backref='assigned_maintenance_tasks')
    created_by = relationship('User', foreign_keys=[created_by_id])
    job_site = relationship('JobSite', backref='maintenance_tasks')
    maintenance_records = relationship('MaintenanceRecord', backref='schedule')


class MaintenanceRecord(db.Model):
    """Model for completed maintenance records"""
    __tablename__ = 'maintenance_records'

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('maintenance_schedules.id'), nullable=True)
    asset_id = Column(Integer, ForeignKey('asset.id'), nullable=False, index=True)
    
    # Record details
    title = Column(String(128), nullable=False)
    description = Column(Text)
    maintenance_type = Column(Enum(MaintenanceType))
    
    # Timestamps and duration
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    actual_duration_hours = Column(Float)
    
    # Cost and resources
    actual_cost = Column(Float)
    parts_used = Column(Text)
    technician_id = Column(Integer, ForeignKey('users.id'))
    
    # Location and notes
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    notes = Column(Text)
    findings = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    asset = relationship('Asset', backref='maintenance_records')
    technician = relationship('User', foreign_keys=[technician_id], 
                             backref='completed_maintenance_tasks')
    submitted_by = relationship('User', foreign_keys=[submitted_by_id])
    job_site = relationship('JobSite', backref='maintenance_records')


class MaintenancePart(db.Model):
    """Model for maintenance parts inventory"""
    __tablename__ = 'maintenance_parts'

    id = Column(Integer, primary_key=True)
    part_number = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    
    # Inventory details
    quantity_on_hand = Column(Integer, default=0)
    unit_cost = Column(Float, default=0.0)
    reorder_level = Column(Integer, default=5)
    reorder_quantity = Column(Integer, default=10)
    
    # Metadata
    category = Column(String(64))
    location = Column(String(128))
    supplier = Column(String(128))
    manufacturer = Column(String(128))
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage tracking
    maintenance_part_usages = relationship('MaintenancePartUsage', backref='part')


class MaintenancePartUsage(db.Model):
    """Model for tracking parts used in maintenance"""
    __tablename__ = 'maintenance_part_usages'

    id = Column(Integer, primary_key=True)
    maintenance_record_id = Column(Integer, ForeignKey('maintenance_records.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('maintenance_parts.id'), nullable=False)
    
    # Usage details
    quantity = Column(Integer, default=1)
    cost_per_unit = Column(Float)
    total_cost = Column(Float)
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_record = relationship('MaintenanceRecord', 
                                     backref='part_usages')