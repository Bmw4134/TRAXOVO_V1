"""
User Settings Model

This module provides the database model for storing user preferences
and settings, including email configurations.
"""
from app import db
from datetime import datetime

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
    
    # Define a unique constraint on user_id and setting_key
    __table_args__ = (db.UniqueConstraint('user_id', 'setting_key', name='uq_user_setting'),)
    
    def __repr__(self):
        return f'<UserSetting {self.setting_key}>'