"""
TRAXOVO User Management Models
Enterprise-grade user authentication with role-based access control
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile settings
    profile_image_url = db.Column(db.String(200))
    dashboard_preferences = db.Column(db.Text)  # JSON string for user preferences
    notification_settings = db.Column(db.Text)  # JSON string for notification preferences
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has specific role"""
        if self.role == 'admin':
            return True  # Admin has all roles
        return self.role == role
    
    def has_admin_access(self):
        """Check if user has admin access"""
        return self.role in ['admin', 'executive']
    
    def get_display_name(self):
        """Get user's display name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'department': self.department,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'display_name': self.get_display_name()
        }

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

class UserActivity(db.Model):
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # login, logout, view_dashboard, etc.
    module = db.Column(db.String(50))  # which module was accessed
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # JSON string for additional details
    
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

# Role definitions
ROLES = {
    'admin': {
        'name': 'Administrator',
        'description': 'Full system access including user management and system configuration',
        'modules': ['all']
    },
    'executive': {
        'name': 'Executive',
        'description': 'Executive dashboard and high-level reporting access',
        'modules': ['executive_dashboard', 'executive_reports', 'analytics', 'billing']
    },
    'controller': {
        'name': 'Controller',
        'description': 'Financial reporting and billing management',
        'modules': ['billing', 'analytics', 'revenue_reports', 'asset_profitability']
    },
    'estimating': {
        'name': 'Estimating',
        'description': 'Project estimation and cost analysis',
        'modules': ['cost_analysis', 'project_estimation', 'asset_utilization']
    },
    'payroll': {
        'name': 'Payroll',
        'description': 'Attendance tracking and payroll management',
        'modules': ['attendance', 'driver_management', 'time_tracking']
    },
    'equipment': {
        'name': 'Equipment Manager',
        'description': 'Fleet and equipment management',
        'modules': ['fleet_map', 'asset_manager', 'equipment_lifecycle', 'maintenance']
    },
    'user': {
        'name': 'Standard User',
        'description': 'Basic dashboard access',
        'modules': ['dashboard', 'basic_reports']
    }
}

def create_default_admin():
    """Create default admin user if none exists"""
    try:
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@traxovo.com',
                first_name='System',
                last_name='Administrator',
                role='admin',
                department='IT',
                is_active=True
            )
            admin.set_password('TRAXOVOAdmin2025!')
            db.session.add(admin)
            db.session.commit()
            print(f"Created default admin user: admin / TRAXOVOAdmin2025!")
            return admin
        return admin
    except Exception as e:
        print(f"Error creating default admin: {e}")
        return None