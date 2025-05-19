"""
Email Configuration Models

This module provides models for storing email configuration settings.
"""

import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func

from app import db

# Set up logger
logger = logging.getLogger(__name__)

class EmailRecipientList(db.Model):
    """Model for storing email recipient lists"""
    __tablename__ = 'email_recipient_lists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    list_name = Column(String(128), nullable=False)
    recipients = Column(String(2048))  # Comma-separated list of email addresses
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_recipients(cls, user_id, list_name, default=""):
        """Get recipients for a specific list"""
        try:
            recipient_list = cls.query.filter_by(
                user_id=user_id,
                list_name=list_name
            ).first()
            
            if recipient_list and recipient_list.recipients:
                return recipient_list.recipients
            return default
        except Exception as e:
            logger.error(f"Error getting recipients for {list_name}, user {user_id}: {e}")
            return default
    
    @classmethod
    def set_recipients(cls, user_id, list_name, recipients):
        """Set recipients for a specific list"""
        try:
            # Check if list exists
            recipient_list = cls.query.filter_by(
                user_id=user_id,
                list_name=list_name
            ).first()
            
            if recipient_list:
                # Update existing list
                recipient_list.recipients = recipients
                recipient_list.updated_at = datetime.now()
            else:
                # Create new list
                recipient_list = cls(
                    user_id=user_id,
                    list_name=list_name,
                    recipients=recipients
                )
                db.session.add(recipient_list)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting recipients for {list_name}, user {user_id}: {e}")
            return False