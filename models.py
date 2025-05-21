"""
Models for the TRAXORA Fleet Management System.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from database import db

class Organization(db.Model):
    """Organizations or departments in the system"""
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=True, unique=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(256))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(20))
    contact_name = db.Column(db.String(128))
    contact_email = db.Column(db.String(128))
    contact_phone = db.Column(db.String(20))
    division = db.Column(db.String(64))  # DFW, Houston, West Texas, etc.
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Organization {self.name}>'


class Role(db.Model):
    """User roles for permission management"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    # Permissions as boolean flags
    can_view_reports = db.Column(db.Boolean, default=True)
    can_export_reports = db.Column(db.Boolean, default=False)
    can_manage_assets = db.Column(db.Boolean, default=False)
    can_manage_drivers = db.Column(db.Boolean, default=False)
    can_process_pm = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    # Add role relationship
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))
    # Department/organization relationship
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    organization = db.relationship('Organization', backref=db.backref('users', lazy='dynamic'))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Permission check methods
    def can_view_reports(self):
        # Admins always have full access
        if self.is_admin:
            return True
        # Check role permission if role exists
        return self.role.can_view_reports if self.role else False
        
    def can_export_reports(self):
        if self.is_admin:
            return True
        return self.role.can_export_reports if self.role else False
    
    def can_manage_assets(self):
        if self.is_admin:
            return True
        return self.role.can_manage_assets if self.role else False
    
    def can_manage_drivers(self):
        if self.is_admin:
            return True
        return self.role.can_manage_drivers if self.role else False
        
    def can_process_pm(self):
        if self.is_admin:
            return True
        return self.role.can_process_pm if self.role else False
    
    def can_manage_users(self):
        if self.is_admin:
            return True
        return self.role.can_manage_users if self.role else False
    
    def get_display_name(self):
        """Return user's full name or username if no name is set"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __repr__(self):
        return f'<User {self.username}>'


class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    asset_identifier = db.Column(db.String(64), index=True, unique=True, nullable=False)
    label = db.Column(db.String(256))
    description = db.Column(db.Text)
    asset_category = db.Column(db.String(64), index=True)
    location = db.Column(db.String(256), index=True)
    active = db.Column(db.Boolean, default=True)
    
    # Add organization relationship
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    organization = db.relationship('Organization', backref=db.backref('asset_list', lazy=True))
    status = db.Column(db.String(64), default='Available')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    engine_hours = db.Column(db.Float)
    vin = db.Column(db.String(128))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Asset {self.asset_identifier}>'


class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    department = db.Column(db.String(64))
    region = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Driver {self.name}>'


class AssetDriverMapping(db.Model):
    __tablename__ = 'asset_driver_mappings'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = db.relationship('Asset', backref=db.backref('driver_assignments', lazy='dynamic'))
    driver = db.relationship('Driver', backref=db.backref('asset_assignments', lazy='dynamic'))

    def __repr__(self):
        return f'<AssetDriverMapping {self.asset.asset_identifier} - {self.driver.name}>'


class DocumentExtraction(db.Model):
    """Model for storing OCR extraction results"""
    __tablename__ = 'document_extractions'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(512))
    extracted_path = db.Column(db.String(512))
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_type = db.Column(db.String(50))
    pages = db.Column(db.Integer, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    
    # Relationship with User who performed the extraction
    user = db.relationship('User', backref=db.backref('extractions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<DocumentExtraction {self.filename}>'


class Alert(db.Model):
    """Model for storing equipment alerts and notifications"""
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(64), index=True)
    severity = db.Column(db.String(20), index=True)  # critical, warning, info
    alert_type = db.Column(db.String(50), index=True)
    description = db.Column(db.String(256))
    location = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    details = db.Column(db.JSON)
    
    # Relationships
    acknowledged_user = db.relationship('User', foreign_keys=[acknowledged_by], 
                                        backref=db.backref('acknowledged_alerts', lazy='dynamic'))
    resolved_user = db.relationship('User', foreign_keys=[resolved_by], 
                                    backref=db.backref('resolved_alerts', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Alert {self.id}: {self.severity} - {self.alert_type}>'


class ActivityLog(db.Model):
    """Model for tracking user activity and system interactions"""
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(50), index=True)
    resource_id = db.Column(db.String(64), index=True)
    action = db.Column(db.String(50))
    description = db.Column(db.String(256))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    success = db.Column(db.Boolean, default=True)
    
    # Relationship with the user who performed the action
    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic'))
    
    @staticmethod
    def log_activity(user_id, event_type, resource_type=None, resource_id=None, 
                     action=None, description=None, details=None, ip_address=None, success=True):
        """
        Helper method to create an activity log entry
        
        Args:
            user_id (int): ID of the user performing the action
            event_type (str): Type of event (api_pull, document_upload, report_view, report_export, asset_update, etc.)
            resource_type (str, optional): Type of resource being accessed (asset, report, document, etc.)
            resource_id (str, optional): Identifier for the specific resource
            action (str, optional): Action performed (view, create, update, delete, export)
            description (str, optional): Human-readable description of the activity
            details (dict, optional): Additional JSON details about the activity
            ip_address (str, optional): IP address of the user
            success (bool, optional): Whether the action was successful
            
        Returns:
            ActivityLog: The created log entry
        """
        log_entry = ActivityLog(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            details=details,
            ip_address=ip_address,
            success=success
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.event_type} - {self.resource_type}>'