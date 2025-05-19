"""
User Settings Model

This module provides the UserSettings model for storing user-specific
settings and preferences.
"""

import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func

from app import db

# Set up logger
logger = logging.getLogger(__name__)

class UserSettings(db.Model):
    """Model for storing user settings"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    setting_key = Column(String(128), nullable=False)
    setting_value = Column(String(1024))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_setting(cls, user_id, key, default=None):
        """Get a user setting by key"""
        try:
            setting = cls.query.filter_by(
                user_id=user_id,
                setting_key=key
            ).first()
            
            if setting:
                return setting.setting_value
            return default
        except Exception as e:
            logger.error(f"Error getting setting {key} for user {user_id}: {e}")
            return default
    
    @classmethod
    def set_setting(cls, user_id, key, value):
        """Set a user setting"""
        try:
            # Check if setting exists
            setting = cls.query.filter_by(
                user_id=user_id,
                setting_key=key
            ).first()
            
            if setting:
                # Update existing setting
                setting.setting_value = value
                setting.updated_at = datetime.now()
            else:
                # Create new setting
                setting = cls(
                    user_id=user_id,
                    setting_key=key,
                    setting_value=value
                )
                db.session.add(setting)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting {key} for user {user_id}: {e}")
            return False