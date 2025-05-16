"""
Core models for the application

These models represent the foundation of the application's data structure.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from db import Base

class Driver(Base):
    """Driver model for storing driver information"""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    employee_id = Column(String(64), unique=True, nullable=False, index=True)
    department = Column(String(64))
    region = Column(String(64))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define the relationships
    asset_assignments = relationship('AssetDriverMapping', back_populates='driver')
    
    def __repr__(self):
        return f"<Driver {self.name}>"