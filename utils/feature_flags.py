"""
Feature Flag Management System

This module provides functionality for managing feature flags in the TRAXORA application.
Feature flags allow for controlled rollout of new features and A/B testing.
"""

import os
from datetime import datetime
from app import db

class FeatureFlag(db.Model):
    """Model for managing feature flags"""
    __tablename__ = 'feature_flags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    enabled = db.Column(db.Boolean, default=False)
    
    # Optional organization-specific override
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    
    # Visibility control
    is_public = db.Column(db.Boolean, default=False)  # Whether users can see this feature in UI
    
    # Rollout configuration
    rollout_percentage = db.Column(db.Integer, default=0)  # 0-100% rollout
    
    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        status = "ENABLED" if self.enabled else "DISABLED"
        return f"<FeatureFlag {self.name}: {status}>"

# Default feature flags
DEFAULT_FLAGS = {
    # Multi-organization support
    'multi_org_support': {
        'description': 'Enable multi-organization support',
        'enabled': False,
        'is_public': False
    },
    
    # Driver Reports module
    'driver_reports': {
        'description': 'Enable Driver Reports module',
        'enabled': True,
        'is_public': True
    },
    
    # PM Billing module
    'pm_billing': {
        'description': 'Enable PM Billing module',
        'enabled': True,
        'is_public': True
    },
    
    # Work Zone GPS analysis
    'work_zone_gps': {
        'description': 'Enable Work Zone GPS efficiency analysis',
        'enabled': True,
        'is_public': True
    },
    
    # Timecard integration
    'timecard_import': {
        'description': 'Enable Timecard Import functionality',
        'enabled': False,
        'is_public': False
    },
    
    # CYA module (silent backup and audit)
    'cya_module': {
        'description': 'Enable CYA module for file backups and audit trails',
        'enabled': True,
        'is_public': False
    },
    
    # Select Maintenance organization
    'select_maintenance_org': {
        'description': 'Enable Select Maintenance organization',
        'enabled': False,
        'is_public': False
    },
    
    # Unified Specialties organization
    'unified_specialties_org': {
        'description': 'Enable Unified Specialties organization',
        'enabled': False,
        'is_public': False
    }
}

def init_feature_flags():
    """Initialize default feature flags in the database"""
    for flag_name, config in DEFAULT_FLAGS.items():
        # Check if flag already exists
        existing = FeatureFlag.query.filter_by(name=flag_name).first()
        if not existing:
            # Create new flag with default config
            flag = FeatureFlag(
                name=flag_name,
                description=config['description'],
                enabled=config['enabled'],
                is_public=config['is_public']
            )
            db.session.add(flag)
    
    # Commit all additions
    db.session.commit()

def is_feature_enabled(flag_name, organization_id=None):
    """
    Check if a feature flag is enabled
    
    Args:
        flag_name (str): The name of the feature flag
        organization_id (int, optional): Organization ID for org-specific flags
        
    Returns:
        bool: True if feature is enabled, False otherwise
    """
    # Handle development/testing environment override
    env_override = os.environ.get(f"ENABLE_{flag_name.upper()}")
    if env_override is not None:
        return env_override.lower() in ('true', '1', 'yes', 'y')
    
    # Check organization-specific flag first if org_id provided
    if organization_id:
        org_flag = FeatureFlag.query.filter_by(
            name=flag_name,
            organization_id=organization_id
        ).first()
        if org_flag:
            return org_flag.enabled
    
    # Fall back to global flag
    flag = FeatureFlag.query.filter_by(name=flag_name, organization_id=None).first()
    
    # Default to disabled if flag doesn't exist
    return flag.enabled if flag else False