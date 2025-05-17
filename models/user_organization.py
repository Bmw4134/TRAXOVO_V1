"""
User Organization Mapping

This module defines the relationship between users and organizations,
allowing users to belong to one or more organizations with different roles.
"""

from datetime import datetime
from app import db

class UserOrganization(db.Model):
    """
    Model for mapping users to organizations with roles
    """
    __tablename__ = 'user_organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # User's role within this organization
    role = db.Column(db.String(32), nullable=False, default='user')  # admin, manager, user
    
    # Access control
    is_active = db.Column(db.Boolean, default=True)
    can_view_assets = db.Column(db.Boolean, default=True)
    can_edit_assets = db.Column(db.Boolean, default=False)
    can_view_reports = db.Column(db.Boolean, default=True)
    can_generate_reports = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    
    # Meta information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('organization_mappings', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('user_mappings', lazy=True))
    
    # Ensure each user has only one mapping per organization
    __table_args__ = (
        db.UniqueConstraint('user_id', 'organization_id', name='unique_user_org'),
    )
    
    def __repr__(self):
        return f"<UserOrganization {self.user_id}:{self.organization_id} - {self.role}>"


def get_user_organizations(user_id):
    """
    Get all organizations a user belongs to
    
    Args:
        user_id (int): The user ID
        
    Returns:
        list: List of Organization objects
    """
    mappings = UserOrganization.query.filter_by(user_id=user_id, is_active=True).all()
    return [mapping.organization for mapping in mappings]


def get_user_primary_organization(user_id):
    """
    Get a user's primary organization
    
    Args:
        user_id (int): The user ID
        
    Returns:
        Organization: The primary organization
    """
    from models.organization import Organization
    
    # First check for explicit mapping
    mapping = UserOrganization.query.filter_by(user_id=user_id, is_active=True).first()
    if mapping:
        return mapping.organization
    
    # Fall back to default organization
    return Organization.get_default()


def is_user_admin(user_id, organization_id=None):
    """
    Check if a user is an admin for a specific organization
    
    Args:
        user_id (int): The user ID
        organization_id (int, optional): The organization ID. If None, checks for any admin role.
        
    Returns:
        bool: True if user is an admin, False otherwise
    """
    if organization_id:
        mapping = UserOrganization.query.filter_by(
            user_id=user_id, 
            organization_id=organization_id,
            role='admin',
            is_active=True
        ).first()
        return mapping is not None
    else:
        # Check if user is admin for any organization
        mapping = UserOrganization.query.filter_by(
            user_id=user_id,
            role='admin',
            is_active=True
        ).first()
        return mapping is not None


def assign_user_to_organization(user_id, organization_id, role='user'):
    """
    Assign a user to an organization
    
    Args:
        user_id (int): The user ID
        organization_id (int): The organization ID
        role (str, optional): The user's role. Defaults to 'user'.
        
    Returns:
        UserOrganization: The created or updated mapping
    """
    # Check if mapping already exists
    mapping = UserOrganization.query.filter_by(
        user_id=user_id,
        organization_id=organization_id
    ).first()
    
    if mapping:
        # Update existing mapping
        mapping.role = role
        mapping.is_active = True
        mapping.updated_at = datetime.utcnow()
    else:
        # Create new mapping
        mapping = UserOrganization(
            user_id=user_id,
            organization_id=organization_id,
            role=role
        )
        db.session.add(mapping)
    
    db.session.commit()
    return mapping


def remove_user_from_organization(user_id, organization_id):
    """
    Remove a user from an organization
    
    Args:
        user_id (int): The user ID
        organization_id (int): The organization ID
        
    Returns:
        bool: True if removed, False otherwise
    """
    mapping = UserOrganization.query.filter_by(
        user_id=user_id,
        organization_id=organization_id
    ).first()
    
    if mapping:
        # Instead of deleting, just mark as inactive
        mapping.is_active = False
        mapping.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    return False