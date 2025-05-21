"""
PM Allocation model definition for billing allocation tracking.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app import db

class PMAllocation(db.Model):
    """PM Allocation model for tracking billing allocations"""
    __tablename__ = 'pm_allocations'
    
    id = Column(Integer, primary_key=True)
    
    # Identification fields
    job_number = Column(String(64), index=True)
    job_name = Column(String(128))
    division = Column(String(64))
    project_manager = Column(String(128))
    
    # Financial data
    original_amount = Column(Float)
    current_amount = Column(Float)
    allocation_date = Column(Date)
    billing_month = Column(String(32))  # Format: YYYY-MM
    billing_year = Column(Integer)
    billing_month_name = Column(String(32))  # January, February, etc.
    
    # Change tracking
    previous_amount = Column(Float, nullable=True)
    change_amount = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    change_reason = Column(Text, nullable=True)
    
    # File source tracking
    source_file = Column(String(256))
    source_file_hash = Column(String(64), nullable=True)
    reconciliation_status = Column(String(32), default='pending')  # pending, reconciled, error
    
    # Asset relations
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)
    
    # User tracking
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # GENIUS CORE validation
    is_validated = Column(Integer, default=0)
    validation_notes = Column(Text, nullable=True)
    validation_history = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    approved_at = Column(DateTime, nullable=True)
    
    # Define relationships
    asset = relationship('Asset', backref='pm_allocations')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_allocations')
    updated_by = relationship('User', foreign_keys=[updated_by_id], backref='updated_allocations')
    approved_by = relationship('User', foreign_keys=[approved_by_id], backref='approved_allocations')
    
    def __repr__(self):
        return f"<PMAllocation {self.job_number} - {self.job_name}: {self.current_amount}>"