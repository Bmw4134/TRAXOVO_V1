"""
TRAXOVO Database Models
"""

from datetime import datetime
from app import db

class GroundWorksConnection(db.Model):
    """Store Ground Works API connection details"""
    __tablename__ = 'groundworks_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExtractedProject(db.Model):
    """Store extracted project data from Ground Works"""
    __tablename__ = 'extracted_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    client = db.Column(db.String(255))
    status = db.Column(db.String(100))
    contract_value = db.Column(db.Float)
    completion_percentage = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    manager = db.Column(db.String(255))
    raw_data = db.Column(db.Text)  # JSON data
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow)
    connection_id = db.Column(db.Integer, db.ForeignKey('groundworks_connections.id'))

class ExtractedAsset(db.Model):
    """Store extracted asset data from Ground Works"""
    __tablename__ = 'extracted_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(500))
    type = db.Column(db.String(255))
    status = db.Column(db.String(100))
    location = db.Column(db.String(500))
    assigned_project = db.Column(db.String(255))
    last_maintenance = db.Column(db.Date)
    next_maintenance = db.Column(db.Date)
    raw_data = db.Column(db.Text)  # JSON data
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow)
    connection_id = db.Column(db.Integer, db.ForeignKey('groundworks_connections.id'))

class ExtractedPersonnel(db.Model):
    """Store extracted personnel data from Ground Works"""
    __tablename__ = 'extracted_personnel'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(500))
    role = db.Column(db.String(255))
    department = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(100))
    status = db.Column(db.String(100))
    raw_data = db.Column(db.Text)  # JSON data
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow)
    connection_id = db.Column(db.Integer, db.ForeignKey('groundworks_connections.id'))

class ExtractionLog(db.Model):
    """Log extraction activities"""
    __tablename__ = 'extraction_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('groundworks_connections.id'))
    extraction_type = db.Column(db.String(100))  # full, incremental, refresh
    status = db.Column(db.String(100))  # success, error, partial
    records_extracted = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)