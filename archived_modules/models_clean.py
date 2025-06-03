"""
Clean Models File - Simplified for Driver Attendance System
Removes circular dependencies and conflicting relationships
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import relationship, DeclarativeBase
from app import db

# Association tables for many-to-many relationships
driver_asset_association = Table(
    'driver_asset_association',
    db.metadata,
    Column('driver_id', Integer, ForeignKey('drivers.id')),
    Column('asset_id', Integer, ForeignKey('assets.id'))
)

class User(db.Model):
    """User model for authentication"""
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

class Driver(db.Model):
    """Driver model for attendance tracking"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    employee_id = Column(String(64), unique=True)
    phone = Column(String(32))
    email = Column(String(120))
    status = Column(String(32), default='active')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Clean relationships without circular dependencies
    assets = relationship('Asset', secondary=driver_asset_association, back_populates='drivers')
    
    def __repr__(self):
        return f"<Driver {self.name}>"

class Asset(db.Model):
    """Asset model for equipment tracking"""
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(String(64), nullable=False)
    name = Column(String(128))
    type = Column(String(64))
    make = Column(String(64))
    model = Column(String(64))
    year = Column(Integer)
    status = Column(String(32), default='active')
    is_active = Column(Boolean, default=True)
    last_latitude = Column(Float)
    last_longitude = Column(Float)
    last_location_update = Column(DateTime)
    notes = Column(String(512))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Clean relationships
    drivers = relationship('Driver', secondary=driver_asset_association, back_populates='assets')
    
    def __repr__(self):
        return f"<Asset {self.asset_id}>"

class AttendanceRecord(db.Model):
    """Attendance record for driver attendance tracking"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    date = Column(Date, nullable=False)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    location = Column(String(256))
    status = Column(String(32))  # present, absent, late, early
    notes = Column(String(512))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    driver = relationship('Driver')
    
    def __repr__(self):
        return f"<AttendanceRecord {self.driver_id} on {self.date}>"