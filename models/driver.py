"""
Driver model definition.
"""
from datetime import datetime
from app import db

class Driver(db.Model):
    """Driver model for personnel tracking"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    department = db.Column(db.String(64))
    division = db.Column(db.String(64))
    region = db.Column(db.String(64))
    job_title = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    license_number = db.Column(db.String(64))
    license_class = db.Column(db.String(32))
    license_expiration = db.Column(db.Date)
    status = db.Column(db.String(32), default='Active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Driver {self.name}>'