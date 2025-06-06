"""
TRAXOVO Database Models - Production Ready
Clean PostgreSQL schema for deployment success
"""

from app import db
from datetime import datetime
from sqlalchemy import JSON

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(32), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='ACTIVE')
    utilization = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OperationalMetrics(db.Model):
    __tablename__ = 'operational_metrics'
    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.Date, nullable=False)
    total_assets = db.Column(db.Integer, default=0)
    active_assets = db.Column(db.Integer, default=0)
    fleet_utilization = db.Column(db.Float, default=0.0)
    efficiency_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PlatformData(db.Model):
    __tablename__ = 'platform_data'
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)
    data_content = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)