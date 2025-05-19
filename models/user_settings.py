"""
User Settings Model

This module provides the database model for storing user preferences
and settings, including email configurations.
"""
from datetime import datetime
from app import db


class UserSettings(db.Model):
    """
    User Settings Model
    
    This model stores user-specific settings and preferences.
    """
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    setting_key = db.Column(db.String(50), nullable=False)
    setting_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'setting_key', name='uq_user_setting'),)
    
    def __repr__(self):
        return f'<UserSetting {self.user_id}:{self.setting_key}>'