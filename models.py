"""
Models for the SYSTEMSMITH application.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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