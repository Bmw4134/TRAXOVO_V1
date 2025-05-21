"""
System Configuration model for application settings and configurations.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app import db

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