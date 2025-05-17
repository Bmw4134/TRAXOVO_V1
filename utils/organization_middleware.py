"""
Organization Middleware Module

This module provides middleware functionality for organization context management
without disrupting the existing UI or login flow.
"""

import logging
from functools import wraps
from flask import g, session, request, current_app, has_request_context
from flask_login import current_user

from utils.feature_flags import is_feature_enabled

logger = logging.getLogger(__name__)

def get_organization_from_request():
    """
    Extract organization context from request
    
    Three methods are supported:
    1. URL parameter: ?org=ragle
    2. Request header: X-Organization: ragle
    3. Subdomain: ragle.domain.com
    
    Returns:
        str: Organization slug or None
    """
    if not has_request_context():
        return None
        
    # Check if multi-org support is enabled
    if not is_feature_enabled('multi_org_support'):
        return None
    
    # Method 1: URL parameter
    org_slug = request.args.get('org')
    
    # Method 2: Header
    if not org_slug:
        org_slug = request.headers.get('X-Organization')
    
    # Method 3: Subdomain (assuming subdomain.domain.com)
    if not org_slug and request.host:
        parts = request.host.split('.')
        if len(parts) > 2 and parts[0] not in ('www', 'app', 'api'):
            org_slug = parts[0]
    
    return org_slug

def get_organization_id_from_slug(slug):
    """
    Get organization ID from slug
    
    Args:
        slug (str): Organization slug
        
    Returns:
        int: Organization ID or None
    """
    if not slug:
        return None
        
    try:
        from models.organization import Organization
        org = Organization.query.filter_by(slug=slug, active=True).first()
        return org.id if org else None
    except Exception as e:
        logger.error(f"Error fetching organization by slug: {e}")
        return None

def get_default_organization_id():
    """
    Get the default organization ID
    
    Returns:
        int: Default organization ID
    """
    try:
        from models.organization import Organization
        # Get default organization
        org = Organization.query.filter_by(is_default=True).first()
        # If no default org, get the first active org
        if not org:
            org = Organization.query.filter_by(active=True).first()
        return org.id if org else 1  # Fallback to ID 1
    except Exception as e:
        logger.error(f"Error fetching default organization: {e}")
        return 1  # Fallback to ID 1

def set_organization_context():
    """
    Set organization context for the current request
    """
    try:
        # Skip if multi-org support is disabled
        if not is_feature_enabled('multi_org_support'):
            g.organization_id = get_default_organization_id()
            return

        # Get organization slug from request
        org_slug = get_organization_from_request()
        
        # If slug is provided, try to get its ID
        if org_slug:
            org_id = get_organization_id_from_slug(org_slug)
            if org_id:
                g.organization_id = org_id
                session['organization_id'] = org_id
                return
        
        # If not found or not provided, check current user's context
        if current_user and current_user.is_authenticated:
            # Check if user has a stored organization context
            if 'organization_id' in session:
                g.organization_id = session['organization_id']
                return
                
            # Check if user has organizations through mapping
            try:
                from models.user_organization import get_user_primary_organization
                org = get_user_primary_organization(current_user.id)
                if org:
                    g.organization_id = org.id
                    session['organization_id'] = org.id
                    return
            except Exception as e:
                logger.warning(f"Failed to get user's primary organization: {e}")
        
        # Default fallback
        g.organization_id = get_default_organization_id()
        
    except Exception as e:
        logger.error(f"Error setting organization context: {e}")
        g.organization_id = get_default_organization_id()

def organization_required(f):
    """
    Decorator to ensure organization context is set
    
    This is a no-op if multi-org support is disabled
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip if multi-org support is disabled
        if not is_feature_enabled('multi_org_support'):
            return f(*args, **kwargs)
            
        # Check if organization context is set
        if not hasattr(g, 'organization_id'):
            set_organization_context()
            
        return f(*args, **kwargs)
    
    return decorated_function

def init_organization_middleware(app):
    """
    Initialize organization middleware
    
    Args:
        app: Flask app instance
    """
    # Register before_request handler to set organization context
    @app.before_request
    def before_request():
        set_organization_context()
    
    logger.info("Organization middleware initialized")
    return True