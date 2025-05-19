"""
Email Configuration Model

This module provides the database model for storing email lists
and system-wide email configurations.
"""
from datetime import datetime
from app import db


class EmailRecipientList(db.Model):
    """
    Email Recipient List Model
    
    This model stores lists of email recipients for various system reports.
    """
    __tablename__ = 'email_recipient_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    recipients = db.Column(db.Text, nullable=False)  # Comma-separated email addresses
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<EmailRecipientList {self.list_name}>'
    
    def get_recipients_list(self):
        """
        Returns a list of email addresses from the comma-separated string
        """
        if not self.recipients:
            return []
        return [email.strip() for email in self.recipients.split(',') if email.strip()]
    
    def add_recipient(self, email):
        """
        Adds an email to the recipient list if not already present
        """
        current_recipients = self.get_recipients_list()
        if email not in current_recipients:
            current_recipients.append(email)
            self.recipients = ','.join(current_recipients)
            return True
        return False
    
    def remove_recipient(self, email):
        """
        Removes an email from the recipient list if present
        """
        current_recipients = self.get_recipients_list()
        if email in current_recipients:
            current_recipients.remove(email)
            self.recipients = ','.join(current_recipients)
            return True
        return False