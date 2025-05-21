"""
TRAXORA Fleet Management System - Database Models

This module defines the SQLAlchemy ORM models for the application.
"""
import logging
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

logger = logging.getLogger(__name__)

class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to models"""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(UserMixin, TimestampMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256))
    first_name = Column(String(64))
    last_name = Column(String(64))
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    
    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Organization(TimestampMixin, db.Model):
    """Organization model for multi-tenancy support"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), unique=True)
    address = Column(String(256))
    city = Column(String(64))
    state = Column(String(32))
    zip_code = Column(String(16))
    country = Column(String(64), default='USA')
    phone = Column(String(32))
    email = Column(String(120))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship('User', secondary='organization_users', backref='organizations')
    assets = relationship('Asset', backref='organization')
    drivers = relationship('Driver', backref='organization')
    
    def __repr__(self):
        return f'<Organization {self.name}>'


class OrganizationUser(db.Model):
    """Join table for Organization-User many-to-many relationship"""
    __tablename__ = 'organization_users'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(32), default='user')  # 'admin', 'user', 'viewer', etc.
    is_primary = Column(Boolean, default=False)  # Whether this is the user's primary organization


class Asset(TimestampMixin, db.Model):
    """Asset model for tracking vehicles and equipment"""
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    asset_id = Column(String(64), nullable=False, index=True)  # External identifier
    name = Column(String(128), nullable=False)
    type = Column(String(64))  # Vehicle type (truck, forklift, etc.)
    model = Column(String(64))
    vin = Column(String(64))  # Vehicle Identification Number
    license_plate = Column(String(32))
    status = Column(String(32), default='active')  # active, inactive, maintenance, etc.
    acquisition_date = Column(DateTime)
    disposal_date = Column(DateTime)
    last_service_date = Column(DateTime)
    next_service_date = Column(DateTime)
    
    # GPS and location data
    last_latitude = Column(Float)
    last_longitude = Column(Float)
    last_location_update = Column(DateTime)
    
    # Gauge API identifiers
    gauge_id = Column(String(64))  # Identifier in the Gauge API
    
    # Additional data as JSON
    attributes = Column(JSON)
    
    # Relationships
    current_driver_id = Column(Integer, ForeignKey('drivers.id'))
    current_driver = relationship('Driver', foreign_keys=[current_driver_id], 
                                 back_populates='assigned_asset')
    
    locations = relationship('AssetLocation', backref='asset', 
                           cascade='all, delete-orphan')
                           
    maintenance_records = relationship('MaintenanceRecord', backref='asset',
                                      cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Asset {self.asset_id} - {self.name}>'
    
    @property
    def days_since_service(self):
        """Calculate days since last service"""
        if self.last_service_date:
            return (datetime.utcnow() - self.last_service_date).days
        return None
    
    @property
    def is_active(self):
        """Check if the asset is active"""
        return self.status == 'active'


class Driver(TimestampMixin, db.Model):
    """Driver model for tracking operators"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    driver_id = Column(String(64), nullable=False, index=True)  # External identifier
    first_name = Column(String(64))
    last_name = Column(String(64))
    email = Column(String(120))
    phone = Column(String(32))
    license_number = Column(String(64))
    license_expiry = Column(DateTime)
    status = Column(String(32), default='active')  # active, inactive, suspended, etc.
    
    # Driver-specific attributes (JSON for flexibility)
    attributes = Column(JSON)
    
    # Relationships
    assigned_asset = relationship('Asset', foreign_keys=[Asset.current_driver_id], 
                                back_populates='current_driver')
    attendance_records = relationship('AttendanceRecord', backref='driver',
                                    cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Driver {self.driver_id} - {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Get the driver's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        """Check if the driver is active"""
        return self.status == 'active'
    
    @property
    def days_until_license_expiry(self):
        """Calculate days until license expires"""
        if self.license_expiry:
            return (self.license_expiry - datetime.utcnow()).days
        return None


class AssetLocation(TimestampMixin, db.Model):
    """Asset location history model"""
    __tablename__ = 'asset_locations'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    speed = Column(Float)  # Speed in mph
    heading = Column(Float)  # Heading in degrees
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Location details
    location_name = Column(String(128))
    address = Column(String(256))
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    
    # Status data
    ignition_status = Column(Boolean)  # On/off
    engine_hours = Column(Float)
    
    def __repr__(self):
        return f'<AssetLocation Asset:{self.asset_id} @ {self.timestamp}>'


class JobSite(TimestampMixin, db.Model):
    """Job site model for tracking work locations"""
    __tablename__ = 'job_sites'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    job_number = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    address = Column(String(256))
    city = Column(String(64))
    state = Column(String(32))
    zip_code = Column(String(16))
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float, default=100.0)  # Geofence radius in meters
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Relationships
    locations = relationship('AssetLocation', backref='job_site')
    attendance_records = relationship('AttendanceRecord', backref='job_site')
    
    def __repr__(self):
        return f'<JobSite {self.job_number} - {self.name}>'


class AttendanceRecord(TimestampMixin, db.Model):
    """Attendance record model for tracking driver attendance"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    job_site_id = Column(Integer, ForeignKey('job_sites.id'))
    date = Column(DateTime, nullable=False)
    scheduled_start_time = Column(DateTime)
    scheduled_end_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    status = Column(String(32))  # on_time, late, early_end, not_on_job
    
    # Additional data
    notes = Column(Text)
    source = Column(String(64))  # Source of the record (driving_history, activity_detail, etc.)
    validation_status = Column(String(32), default='unverified')  # unverified, verified, rejected
    
    def __repr__(self):
        return f'<AttendanceRecord Driver:{self.driver_id} Date:{self.date}>'


class MaintenanceRecord(TimestampMixin, db.Model):
    """Maintenance record model for tracking asset maintenance"""
    __tablename__ = 'maintenance_records'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    type = Column(String(64))  # preventive, corrective, etc.
    date_performed = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    cost = Column(Float)
    provider = Column(String(128))
    invoice_number = Column(String(64))
    notes = Column(Text)
    
    def __repr__(self):
        return f'<MaintenanceRecord Asset:{self.asset_id} Type:{self.type}>'


class PMAllocation(TimestampMixin, db.Model):
    """PM Allocation model for tracking billing allocations"""
    __tablename__ = 'pm_allocations'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    job_number = Column(String(64), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    pm_name = Column(String(128))  # PM's name
    month = Column(String(32), nullable=False)  # Format: YYYY-MM
    original_amount = Column(Float, nullable=False)
    allocated_amount = Column(Float, nullable=False)
    status = Column(String(32), default='pending')  # pending, approved, rejected
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by])
    approver = relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<PMAllocation Job:{self.job_number} Month:{self.month}>'


class ActivityLog(TimestampMixin, db.Model):
    """Activity log for tracking user actions"""
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(64), nullable=False)
    object_type = Column(String(64))  # asset, driver, job_site, etc.
    object_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(64))
    
    # Relationship
    user = relationship('User')
    
    def __repr__(self):
        return f'<ActivityLog User:{self.user_id} Action:{self.action}>'


class SystemConfiguration(TimestampMixin, db.Model):
    """System configuration for storing application settings"""
    __tablename__ = 'system_configurations'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(128), nullable=False, unique=True)
    value = Column(Text)
    description = Column(Text)
    
    def __repr__(self):
        return f'<SystemConfiguration {self.key}>'