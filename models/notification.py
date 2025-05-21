"""
Notification model for system and user alerts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app import db

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