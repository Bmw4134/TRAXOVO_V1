"""
Activity Log Model

This module defines the ActivityLog model for tracking user and system activities
throughout the application.
"""

from datetime import datetime
import json

from app import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import current_user


class ActivityLog(db.Model):
    """Activity log model for tracking user and system actions"""
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    activity_type = Column(String(64), index=True)
    description = Column(Text)
    meta_data = Column(Text)  # Stored as JSON string
    ip_address = Column(String(45))  # IPv6 compatible length
    source = Column(String(64))  # Web, API, System, etc.
    success = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', backref='activities')
    
    def __repr__(self):
        return f'<ActivityLog {self.id} - {self.activity_type}>'
        
    def to_dict(self):
        """
        Convert the activity log to a dictionary for serialization
        """
        result = {
            'id': self.id,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'source': self.source,
            'success': self.success
        }
        
        # Add username if user exists
        if self.user:
            result['username'] = self.user.username
            
        # Parse metadata if it exists
        if self.meta_data:
            try:
                result['metadata'] = json.loads(self.meta_data)
            except:
                result['metadata'] = {}
                
        return result