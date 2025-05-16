"""
System models and database structure for the SYSTEMSMITH application

This module defines the database models used by the application, including asset information,
user authentication, and configuration settings.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from db import Base

class User(Base, UserMixin):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_supervisor = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class Asset(Base):
    """Asset model for storing equipment details"""
    __tablename__ = 'asset'
    
    id = Column(Integer, primary_key=True)
    asset_identifier = Column(String(64), unique=True, nullable=False, index=True)
    label = Column(String(128))
    serial_number = Column(String(64))
    make = Column(String(64))
    model = Column(String(64))
    asset_type = Column(String(64))
    status = Column(String(32))
    latitude = Column(Float)
    longitude = Column(Float)
    last_updated = Column(DateTime)
    last_location_update = Column(DateTime)
    active = Column(Boolean, default=True)
    region = Column(String(32))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships
    driver_assignments = relationship('AssetDriverMapping', back_populates='asset')
    
    def __repr__(self):
        return f'<Asset {self.asset_identifier}>'

class AssetDriverMapping(Base):
    """Asset-Driver relationship model for tracking assignments"""
    __tablename__ = 'asset_driver_mappings'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('asset.id'), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    asset = relationship('Asset', back_populates='driver_assignments')
    driver = relationship('Driver', back_populates='asset_assignments')
    
    def __repr__(self):
        return f'<AssetDriverMapping {self.asset_id}-{self.driver_id}>'

class APIConfig(Base):
    """API configuration settings"""
    __tablename__ = 'api_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(String(256))
    description = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        """Get config value by key"""
        from app import db
        config = db.session.query(cls).filter_by(key=key).first()
        return config.value if config else default
    
    @classmethod
    def set(cls, key, value, description=None):
        """Set config value"""
        from app import db
        config = db.session.query(cls).filter_by(key=key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = cls(key=key, value=value, description=description)
            db.session.add(config)
        db.session.commit()
        
    def __repr__(self):
        return f'<APIConfig {self.key}>'