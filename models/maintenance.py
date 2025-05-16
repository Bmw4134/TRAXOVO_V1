"""
Maintenance models for the SYSTEMSMITH fleet management system.

This module defines the database models for maintenance scheduling, tracking, and reporting.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from db import Base
import enum


class MaintenanceType(enum.Enum):
    """Types of maintenance tasks"""
    SERVICE = "service"
    REPAIR = "repair"
    INSPECTION = "inspection"
    OTHER = "other"


class MaintenancePriority(enum.Enum):
    """Priority levels for maintenance tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MaintenanceStatus(enum.Enum):
    """Status options for maintenance tasks"""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class MaintenanceTask(Base):
    """Model for maintenance tasks"""
    __tablename__ = 'maintenance_tasks'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    
    # Task classification
    maintenance_type = Column(Enum(MaintenanceType), nullable=False, default=MaintenanceType.SERVICE)
    priority = Column(Enum(MaintenancePriority), nullable=False, default=MaintenancePriority.MEDIUM)
    status = Column(Enum(MaintenanceStatus), nullable=False, default=MaintenanceStatus.SCHEDULED)
    
    # Scheduling
    scheduled_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, index=True)
    completed_date = Column(Date)
    
    # Assignment and cost tracking
    assigned_to = Column(String(128))
    technician_id = Column(Integer, ForeignKey('users.id'))
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    
    # Notes
    notes = Column(Text)
    completion_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship('Asset', backref='maintenance_tasks')
    technician = relationship('User', backref='assigned_maintenance')
    parts = relationship('MaintenancePart', back_populates='maintenance_task')
    
    def __repr__(self):
        return f"<MaintenanceTask(id={self.id}, asset_id={self.asset_id}, title='{self.title}')>"
    
    @property
    def is_overdue(self):
        """Check if the task is overdue"""
        if self.status == MaintenanceStatus.COMPLETED:
            return False
        
        if self.due_date:
            return self.due_date < datetime.utcnow().date()
        
        # If no due date, use scheduled date + 7 days as implicit due date
        implicit_due_date = self.scheduled_date + timedelta(days=7)
        return implicit_due_date < datetime.utcnow().date()
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.status == MaintenanceStatus.COMPLETED:
            return None
        
        if self.due_date:
            delta = self.due_date - datetime.utcnow().date()
            return delta.days
        
        # If no due date, use scheduled date + 7 days as implicit due date
        implicit_due_date = self.scheduled_date + timedelta(days=7)
        delta = implicit_due_date - datetime.utcnow().date()
        return delta.days


class MaintenancePart(Base):
    """Model for parts used in maintenance"""
    __tablename__ = 'maintenance_parts'
    
    id = Column(Integer, primary_key=True)
    maintenance_task_id = Column(Integer, ForeignKey('maintenance_tasks.id'), nullable=False)
    part_name = Column(String(128), nullable=False)
    part_number = Column(String(64))
    quantity = Column(Integer, default=1)
    unit_cost = Column(Float)
    vendor = Column(String(128))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    maintenance_task = relationship('MaintenanceTask', back_populates='parts')
    
    def __repr__(self):
        return f"<MaintenancePart(id={self.id}, part_name='{self.part_name}', quantity={self.quantity})>"
    
    @property
    def total_cost(self):
        """Calculate total cost for this part"""
        if self.unit_cost is None:
            return None
        return self.unit_cost * self.quantity


class MaintenanceHistory(Base):
    """Model for tracking maintenance history"""
    __tablename__ = 'maintenance_history'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, index=True)
    maintenance_task_id = Column(Integer, ForeignKey('maintenance_tasks.id'))
    
    date = Column(Date, nullable=False)
    service_type = Column(String(64), nullable=False)
    description = Column(Text)
    performed_by = Column(String(128))
    cost = Column(Float)
    odometer = Column(Integer)
    engine_hours = Column(Float)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset = relationship('Asset', backref='maintenance_history')
    maintenance_task = relationship('MaintenanceTask')
    
    def __repr__(self):
        return f"<MaintenanceHistory(id={self.id}, asset_id={self.asset_id}, date='{self.date}')>"


class MaintenanceSchedule(Base):
    """Model for recurring maintenance schedules"""
    __tablename__ = 'maintenance_schedules'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    
    # Schedule details
    maintenance_type = Column(Enum(MaintenanceType), nullable=False, default=MaintenanceType.SERVICE)
    frequency_type = Column(String(32), nullable=False)  # 'days', 'weeks', 'months', 'miles', 'hours'
    frequency_value = Column(Integer, nullable=False)    # Number of days/weeks/months/miles/hours
    last_performed = Column(Date)
    next_due = Column(Date, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Additional info
    estimated_cost = Column(Float)
    estimated_hours = Column(Float)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset = relationship('Asset', backref='maintenance_schedules')
    
    def __repr__(self):
        return f"<MaintenanceSchedule(id={self.id}, asset_id={self.asset_id}, title='{self.title}')>"
    
    def calculate_next_due(self, from_date=None):
        """Calculate the next due date based on frequency and last performed date"""
        if not self.last_performed:
            return None
        
        start_date = from_date or self.last_performed
        
        if self.frequency_type == 'days':
            return start_date + timedelta(days=self.frequency_value)
        elif self.frequency_type == 'weeks':
            return start_date + timedelta(weeks=self.frequency_value)
        elif self.frequency_type == 'months':
            # Simple approximation of months as 30 days
            return start_date + timedelta(days=30 * self.frequency_value)
        
        # For miles/hours, we can't calculate a specific date
        # These would need to be checked against asset odometer/hour readings
        return None


class MaintenanceNotification(Base):
    """Model for maintenance notifications and reminders"""
    __tablename__ = 'maintenance_notifications'
    
    id = Column(Integer, primary_key=True)
    maintenance_task_id = Column(Integer, ForeignKey('maintenance_tasks.id'), index=True)
    maintenance_schedule_id = Column(Integer, ForeignKey('maintenance_schedules.id'), index=True)
    
    # Notification details
    title = Column(String(128), nullable=False)
    message = Column(Text)
    notification_date = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Status
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    read_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_task = relationship('MaintenanceTask')
    maintenance_schedule = relationship('MaintenanceSchedule')
    user = relationship('User')
    
    def __repr__(self):
        return f"<MaintenanceNotification(id={self.id}, title='{self.title}')>"