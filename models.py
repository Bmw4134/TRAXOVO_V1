"""
TRAXOVO ∞ Clarity Core - Database Models
Enterprise user management and authentication system
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize database
db = SQLAlchemy()

class User(db.Model):
    """Enterprise user model for TRAXOVO authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class AssetData(db.Model):
    """Asset tracking data model"""
    __tablename__ = 'asset_data'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), unique=True, nullable=False)
    asset_name = db.Column(db.String(200), nullable=False)
    asset_type = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    sr_pm = db.Column(db.String(100), nullable=True)
    driver_name = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='active')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

def init_database(app):
    """Initialize database with default users"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if watson user exists
        watson_user = User.query.filter_by(username='watson').first()
        if not watson_user:
            # Create watson admin user
            watson_user = User(
                username='watson',
                email='watson@traxovo.com',
                role='admin'
            )
            watson_user.set_password('nexus')
            db.session.add(watson_user)
            db.session.commit()
            print("✓ Created watson admin user")
        
        print("✓ Database initialized successfully")