"""
TRAXORA Fleet Management System - Database Models

This module contains the SQLAlchemy database models for the TRAXORA system.
"""
import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, Date, Time, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app import db

# Association tables
driver_jobsite_association = Table(
    'driver_jobsite_association',
    db.Model.metadata,
    Column('driver_id', Integer, ForeignKey('drivers.id')),
    Column('job_site_id', Integer, ForeignKey('job_sites.id'))
)

asset_jobsite_association = Table(
    'asset_jobsite_association',
    db.Model.metadata,
    Column('asset_id', Integer, ForeignKey('assets.id')),
    Column('job_site_id', Integer, ForeignKey('job_sites.id'))
)

# Create a proper many-to-many association table for driver-asset relationship
driver_asset_association = Table(
    'driver_asset_association',
    db.Model.metadata,
    Column('driver_id', Integer, ForeignKey('drivers.id')),
    Column('asset_id', Integer, ForeignKey('assets.id'))
)

class User(UserMixin, db.Model):
    """User model for authentication and system access"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    is_admin = Column(Boolean, default=False)
    first_name = Column(String(64))
    last_name = Column(String(64))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    activity_logs = relationship('ActivityLog', back_populates='user')
    notifications = relationship('Notification', back_populates='user')
    
    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    @property
    def full_name(self):
        """Get the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def __repr__(self):
        return f"<User {self.username}>"

class Organization(db.Model):
    """Organization model for multi-tenant support"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    drivers = relationship('Driver', back_populates='organization')
    assets = relationship('Asset', back_populates='organization')
    job_sites = relationship('JobSite', back_populates='organization')
    pm_allocations = relationship('PMAllocation', back_populates='organization')
    
    def __repr__(self):
        return f"<Organization {self.name}>"

class Driver(db.Model):
    """Driver model for tracking personnel information"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    full_name = Column(String(128), nullable=False)
    employee_id = Column(String(32))
    status = Column(String(32), default='active')  # active, inactive, on_leave
    is_active = Column(Boolean, default=True)
    email = Column(String(120))
    phone = Column(String(32))
    license_number = Column(String(64))
    license_expiration = Column(Date)
    notes = Column(String(512))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    organization = relationship('Organization', back_populates='drivers')
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    job_site = relationship('JobSite', foreign_keys=[job_site_id])
    job_sites = relationship('JobSite', secondary=driver_jobsite_association, back_populates='drivers')
    driver_reports = relationship('DriverReport', back_populates='driver')
    # Add the relationship to assets
    assigned_assets = relationship('Asset', secondary=driver_asset_association, backref='assigned_drivers')
    
    def __repr__(self):
        return f"<Driver {self.full_name}>"

class Asset(db.Model):
    """Asset model for tracking equipment"""
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    asset_id = Column(String(64), nullable=False)
    name = Column(String(128))
    type = Column(String(64))
    make = Column(String(64))
    model = Column(String(64))
    year = Column(Integer)
    serial_number = Column(String(64))
    status = Column(String(32), default='active')  # active, maintenance, inactive, retired
    is_active = Column(Boolean, default=True)
    acquisition_date = Column(Date)
    disposal_date = Column(Date)
    last_service_date = Column(Date)
    next_service_date = Column(Date)
    last_latitude = Column(Float)
    last_longitude = Column(Float)
    last_location_update = Column(DateTime)
    # Removing direct foreign key as we're using the association table for driver-asset relationships
    notes = Column(String(512))
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    organization = relationship('Organization', back_populates='assets')
    # Remove the problematic relationship for now
    locations = relationship('AssetLocation', back_populates='asset')
    job_sites = relationship('JobSite', secondary=asset_jobsite_association, back_populates='assets')
    
    def __repr__(self):
        return f"<Asset {self.asset_id}>"

class AssetLocation(db.Model):
    """Asset location history model"""
    __tablename__ = 'asset_locations'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, name='location_timestamp')
    speed = Column(Float)
    heading = Column(Float)
    altitude = Column(Float, name='elevation')
    accuracy = Column(Float)
    ignition_status = Column(String(32), name='location_source')
    address = Column(String(256))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    asset = relationship('Asset', back_populates='locations')
    job_site = relationship('JobSite', back_populates='asset_locations')
    
    def __repr__(self):
        return f"<AssetLocation {self.asset_id} @ {self.timestamp}>"

class JobSite(db.Model):
    """Job site model for tracking locations"""
    __tablename__ = 'job_sites'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    name = Column(String(128), nullable=False)
    job_number = Column(String(64), nullable=False)
    address = Column(String(256))
    city = Column(String(64))
    state = Column(String(32))
    zipcode = Column(String(16), name='zip_code')
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)  # geofence radius in meters
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True, name='active')
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    organization = relationship('Organization', back_populates='job_sites')
    drivers = relationship('Driver', secondary=driver_jobsite_association, back_populates='job_sites')
    assets = relationship('Asset', secondary=asset_jobsite_association, back_populates='job_sites')
    asset_locations = relationship('AssetLocation', back_populates='job_site')
    driver_reports = relationship('DriverReport', back_populates='job_site')
    
    def __repr__(self):
        return f"<JobSite {self.name} ({self.job_number})>"

class DriverReport(db.Model):
    """Driver daily report model for attendance tracking"""
    __tablename__ = 'driver_reports'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    report_date = Column(Date, nullable=False)
    scheduled_start_time = Column(DateTime)
    scheduled_end_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    status = Column(String(32))  # on_time, late, early_end, not_on_job
    notes = Column(String(512))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    driver = relationship('Driver', back_populates='driver_reports')
    job_site = relationship('JobSite', back_populates='driver_reports')
    
    def __repr__(self):
        return f"<DriverReport {self.driver.full_name if self.driver else 'Unknown'} on {self.report_date}>"

class PMAllocation(db.Model):
    """PM allocation model for billing reconciliation"""
    __tablename__ = 'pm_allocations'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    job_number = Column(String(64), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM format
    pm_name = Column(String(64), nullable=False)
    original_amount = Column(Float, nullable=False, default=0.0)
    allocated_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), default='pending')  # pending, approved, rejected, updated
    notes = Column(String(512))
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    organization = relationship('Organization', back_populates='pm_allocations')
    creator = relationship('User', foreign_keys=[created_by])
    approver = relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<PMAllocation {self.job_number} - {self.month} - {self.pm_name}>"

class ActivityLog(db.Model):
    """Activity log model for system auditing"""
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(64), nullable=False)
    object_type = Column(String(64))
    object_id = Column(Integer)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='activity_logs')
    
    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user.username if self.user else 'System'} at {self.timestamp}>"

class Notification(db.Model):
    """Notification model for user alerts"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(128), nullable=False)
    message = Column(String(512), nullable=False)
    type = Column(String(32), default='info')  # info, warning, error
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f"<Notification {self.title} for {self.user.username if self.user else 'All Users'}>"

class SystemConfiguration(db.Model):
    """System configuration model for application settings"""
    __tablename__ = 'system_configurations'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(String(512))
    description = Column(String(256))
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<SystemConfiguration {self.key}>"