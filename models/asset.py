"""
Asset Model

This module defines the Asset model for the TRAXORA system.
Based on Gauge Smart Hub structure for comprehensive asset management.
"""

from datetime import datetime
from app import db
from sqlalchemy import JSON, Text

class Asset(db.Model):
    """Asset model for equipment and vehicles tracked in the system"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), index=True)  # ID from external system (Gauge)
    name = db.Column(db.String(256), nullable=False)    # Asset name / identifier
    asset_number = db.Column(db.String(64), index=True) # Asset/Unit number
    
    # General Asset Information
    status = db.Column(db.String(32), default='active')   # active, inactive, maintenance, etc.
    category = db.Column(db.String(64))                   # Category
    class_type = db.Column(db.String(64))                 # Class
    model_year = db.Column(db.String(16))                 # Model Year
    make = db.Column(db.String(64))                       # Manufacturer
    model = db.Column(db.String(128))                     # Model
    type_tag = db.Column(db.String(64))                   # Asset Type
    description = db.Column(db.Text)                      # General description
    
    # Identifiers
    vin = db.Column(db.String(64), index=True)            # VIN for vehicles
    serial_number = db.Column(db.String(64), index=True)  # Serial number
    license_plate = db.Column(db.String(32))              # License plate number
    
    # Location & Assignment
    job_number = db.Column(db.String(32))                 # Current job number
    job_name = db.Column(db.String(256))                  # Current job name
    division = db.Column(db.String(64))                   # Division
    address = db.Column(db.String(256))                   # Current address
    latitude = db.Column(db.Float)                        # Current latitude
    longitude = db.Column(db.Float)                       # Current longitude
    last_known_location = db.Column(db.String(256))       # Last known location description
    
    # Ownership & Billing
    ownership_type = db.Column(db.String(32))             # owned, leased, rented
    billing_code = db.Column(db.String(64))               # Billing code
    asset_tags = db.Column(JSON)                          # Custom tags as JSON array
    
    # Metrics
    odometer = db.Column(db.Float)                        # Current odometer reading
    hour_meter = db.Column(db.Float)                      # Current hour meter reading
    fuel_level = db.Column(db.Float)                      # Current fuel level percentage
    
    # Dates
    date_of_purchase = db.Column(db.Date)                 # Purchase date
    date_of_sale = db.Column(db.Date)                     # Sale date if sold
    last_service_date = db.Column(db.Date)                # Last service date
    next_service_due = db.Column(db.Date)                 # Next service due date
    registration_expiration_date = db.Column(db.Date)     # Registration expiration date
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Capabilities
    payload_capacity = db.Column(db.Float)                # Payload capacity
    gvwr = db.Column(db.Float)                            # Gross vehicle weight rating
    
    # Image/Document
    primary_image_url = db.Column(db.String(512))         # Primary image URL
    has_documents = db.Column(db.Boolean, default=False)  # Flag for associated documents
    
    # External System Fields
    api_source = db.Column(db.String(64), default='gauge')  # Source API/system
    telematics_id = db.Column(db.String(128))             # ID in telematics system
    telematics_data = db.Column(JSON)                     # Latest telematics data as JSON
    
    # Service & Maintenance
    service_status = db.Column(db.String(32))             # Service status
    maintenance_alerts = db.Column(JSON)                  # Maintenance alerts as JSON
    recall_alerts = db.Column(JSON)                       # Recall alerts as JSON
    
    # Relationships
    # images = db.relationship('AssetImage', backref='asset', lazy='dynamic')
    # documents = db.relationship('AssetDocument', backref='asset', lazy='dynamic')
    # service_history = db.relationship('ServiceRecord', backref='asset', lazy='dynamic')
    
    def __repr__(self):
        return f'<Asset {self.name} ({self.asset_number})>'
    
    def to_dict(self):
        """Convert asset to dictionary for API responses"""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'name': self.name,
            'asset_number': self.asset_number,
            'status': self.status,
            'category': self.category,
            'class_type': self.class_type,
            'model_year': self.model_year,
            'make': self.make,
            'model': self.model,
            'type_tag': self.type_tag,
            'description': self.description,
            'vin': self.vin,
            'serial_number': self.serial_number,
            'license_plate': self.license_plate,
            'job_number': self.job_number,
            'job_name': self.job_name,
            'division': self.division,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'last_known_location': self.last_known_location,
            'ownership_type': self.ownership_type,
            'billing_code': self.billing_code,
            'asset_tags': self.asset_tags,
            'odometer': self.odometer,
            'hour_meter': self.hour_meter,
            'fuel_level': self.fuel_level,
            'date_of_purchase': self.date_of_purchase.isoformat() if self.date_of_purchase else None,
            'date_of_sale': self.date_of_sale.isoformat() if self.date_of_sale else None,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'next_service_due': self.next_service_due.isoformat() if self.next_service_due else None,
            'registration_expiration_date': self.registration_expiration_date.isoformat() if self.registration_expiration_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'payload_capacity': self.payload_capacity,
            'gvwr': self.gvwr,
            'primary_image_url': self.primary_image_url,
            'has_documents': self.has_documents,
            'api_source': self.api_source,
            'service_status': self.service_status,
            'has_recalls': bool(self.recall_alerts) if self.recall_alerts else False,
            'has_maintenance_alerts': bool(self.maintenance_alerts) if self.maintenance_alerts else False
        }


# Asset images for multiple images per asset
class AssetImage(db.Model):
    """Asset images for storing multiple images per asset"""
    __tablename__ = 'asset_images'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    image_url = db.Column(db.String(512), nullable=False)
    caption = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssetImage for Asset ID {self.asset_id}>'


# Asset documents for storing maintenance records, etc.
class AssetDocument(db.Model):
    """Asset documents for storing maintenance records, manuals, etc."""
    __tablename__ = 'asset_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    document_url = db.Column(db.String(512), nullable=False)
    document_type = db.Column(db.String(64))  # e.g., manual, service_record, registration
    title = db.Column(db.String(256))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssetDocument {self.title} for Asset ID {self.asset_id}>'


# Service records for tracking maintenance history
class ServiceRecord(db.Model):
    """Service records for tracking maintenance history"""
    __tablename__ = 'service_records'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(64))  # e.g., preventative, repair
    description = db.Column(db.Text)
    odometer = db.Column(db.Float)
    hour_meter = db.Column(db.Float)
    performed_by = db.Column(db.String(128))
    service_cost = db.Column(db.Float)
    parts_cost = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServiceRecord {self.service_date} - {self.service_type} for Asset ID {self.asset_id}>'