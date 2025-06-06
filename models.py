"""
TRAXOVO Enterprise Data Models
Comprehensive database schema for operational intelligence
"""

from app import db
from datetime import datetime
from sqlalchemy import JSON

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(32), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class Asset(db.Model):
    __tablename__ = 'assets'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(20), default='ACTIVE')
    hours_operated = db.Column(db.Float, default=0.0)
    utilization = db.Column(db.Float, default=0.0)
    last_maintenance = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    asset_metadata = db.Column(JSON)

class OperationalMetrics(db.Model):
    __tablename__ = 'operational_metrics'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.Date, nullable=False)
    total_assets = db.Column(db.Integer, default=0)
    active_assets = db.Column(db.Integer, default=0)
    fleet_utilization = db.Column(db.Float, default=0.0)
    operational_hours = db.Column(db.Float, default=0.0)
    efficiency_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False)
    employee_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    hours_worked = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='PRESENT')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AutomationTask(db.Model):
    __tablename__ = 'automation_tasks'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='PENDING')
    priority = db.Column(db.String(10), default='MEDIUM')
    scheduled_time = db.Column(db.DateTime)
    execution_time = db.Column(db.DateTime)
    completion_time = db.Column(db.DateTime)
    result = db.Column(JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    log_level = db.Column(db.String(10), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GaugeData(db.Model):
    __tablename__ = 'gauge_data'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, nullable=False)
    quality_score = db.Column(db.Float, default=1.0)
    source = db.Column(db.String(50), default='GAUGE_API')
    raw_data = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)