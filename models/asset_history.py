"""
Asset History and Trend Analysis Models

This module contains models for tracking historical data about assets
and analyzing trends over time.
"""

from datetime import datetime

from sqlalchemy import Index, ForeignKey

from app import db

class AssetSnapshot(db.Model):
    """
    Model for storing point-in-time snapshots of asset data
    for historical tracking and trend analysis.
    """
    __tablename__ = 'asset_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    snapshot_date = db.Column(db.Date, nullable=False)
    
    # Location data
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_name = db.Column(db.String(256))
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    
    # Status information
    status = db.Column(db.String(64))
    engine_hours = db.Column(db.Float)
    fuel_level = db.Column(db.Float)  # Percentage (0-100)
    
    # Operational data
    utilization_hours = db.Column(db.Float, default=0)  # Hours used that day
    idle_time = db.Column(db.Float, default=0)  # Hours idle that day
    distance_traveled = db.Column(db.Float, default=0)  # Miles/km traveled that day
    
    # Maintenance data
    maintenance_due = db.Column(db.Boolean, default=False)
    days_to_next_service = db.Column(db.Integer)
    
    # Financial data
    daily_cost = db.Column(db.Float, default=0)  # Cost for the day
    revenue_generated = db.Column(db.Float, default=0)  # Revenue attributed for the day
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref='historical_snapshots')
    job_site = db.relationship('JobSite', backref='asset_history')
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_asset_snapshot_date', asset_id, snapshot_date),
        Index('idx_org_snapshot_date', organization_id, snapshot_date),
    )
    
    def __repr__(self):
        return f"<AssetSnapshot {self.asset_id} on {self.snapshot_date}>"


class AssetTrend(db.Model):
    """
    Model for storing calculated trend data for assets.
    """
    __tablename__ = 'asset_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    trend_date = db.Column(db.Date, nullable=False)
    trend_period = db.Column(db.String(16), nullable=False)  # 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'
    
    # Core metrics
    utilization_rate = db.Column(db.Float)  # Percentage of available time used
    idle_percentage = db.Column(db.Float)  # Percentage of operation time spent idle
    efficiency_score = db.Column(db.Float)  # Calculated efficiency score (0-100)
    
    # Financial metrics
    cost_per_hour = db.Column(db.Float)
    revenue_per_hour = db.Column(db.Float)
    profit_margin = db.Column(db.Float)  # Percentage
    
    # Change metrics (compared to previous period)
    utilization_change = db.Column(db.Float)  # Percentage points change
    efficiency_change = db.Column(db.Float)  # Percentage points change
    cost_change = db.Column(db.Float)  # Percentage change
    
    # Maintenance metrics
    maintenance_compliance = db.Column(db.Float)  # Percentage of scheduled maintenance completed on time
    downtime_hours = db.Column(db.Float)  # Hours of unplanned downtime
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref='trends')
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_asset_trend_date', asset_id, trend_date, trend_period),
        Index('idx_org_trend_date', organization_id, trend_date, trend_period),
    )
    
    def __repr__(self):
        return f"<AssetTrend {self.asset_id} {self.trend_period} on {self.trend_date}>"


class FleetTrend(db.Model):
    """
    Model for storing trend data aggregated at the fleet level.
    """
    __tablename__ = 'fleet_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    category = db.Column(db.String(64))  # Asset category or NULL for all
    trend_date = db.Column(db.Date, nullable=False)
    trend_period = db.Column(db.String(16), nullable=False)  # 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'
    
    # Fleet size metrics
    total_assets = db.Column(db.Integer)
    active_assets = db.Column(db.Integer)
    inactive_assets = db.Column(db.Integer)
    maintenance_due_count = db.Column(db.Integer)
    
    # Utilization metrics
    average_utilization = db.Column(db.Float)  # Percentage
    average_idle_time = db.Column(db.Float)  # Percentage
    average_efficiency = db.Column(db.Float)  # Score (0-100)
    
    # Financial metrics
    total_cost = db.Column(db.Float)
    total_revenue = db.Column(db.Float)
    average_profit_margin = db.Column(db.Float)  # Percentage
    cost_per_operating_hour = db.Column(db.Float)
    
    # Change metrics (compared to previous period)
    utilization_change = db.Column(db.Float)  # Percentage points change
    cost_change = db.Column(db.Float)  # Percentage change
    efficiency_change = db.Column(db.Float)  # Percentage points change
    
    # Job site metrics
    job_site_count = db.Column(db.Integer)  # Number of job sites with assets
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_fleet_org_date', organization_id, trend_date, trend_period),
        Index('idx_fleet_category_date', organization_id, category, trend_date, trend_period),
    )
    
    def __repr__(self):
        cat_str = f" {self.category}" if self.category else ""
        return f"<FleetTrend {self.organization_id}{cat_str} {self.trend_period} on {self.trend_date}>"