"""
Alerts Models

This module defines the database models for equipment alerts.
"""

from datetime import datetime
from app import db
from main import Asset, User

class EquipmentAlert(db.Model):
    """
    Model for equipment alerts
    """
    __tablename__ = 'equipment_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Alert details
    asset_id = db.Column(db.String(64), db.ForeignKey('asset.asset_identifier'), nullable=False)
    alert_type = db.Column(db.String(32), nullable=False)  # inactivity, unusual_pattern, maintenance
    level = db.Column(db.String(16), nullable=False)  # critical, warning, info
    description = db.Column(db.String(256), nullable=False)
    details = db.Column(db.JSON, nullable=True)  # Additional details as JSON
    
    # Related entity info
    location = db.Column(db.String(128), nullable=True)
    region = db.Column(db.String(64), nullable=True)
    
    # Status tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('alerts', lazy=True))
    acknowledging_user = db.relationship('User', foreign_keys=[acknowledged_by], backref=db.backref('acknowledged_alerts', lazy=True))
    resolving_user = db.relationship('User', foreign_keys=[resolved_by], backref=db.backref('resolved_alerts', lazy=True))
    
    def __repr__(self):
        return f"<EquipmentAlert {self.id}: {self.level}:{self.alert_type} for {self.asset_id}>"
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'alert_type': self.alert_type,
            'level': self.level,
            'description': self.description,
            'details': self.details,
            'location': self.location,
            'region': self.region,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S') if self.acknowledged_at else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'resolution_notes': self.resolution_notes
        }
    
    @classmethod
    def create_from_alert_dict(cls, alert_dict):
        """Create an EquipmentAlert from an alert dictionary"""
        alert = cls(
            asset_id=alert_dict.get('asset_id'),
            alert_type=alert_dict.get('type', 'other'),
            level=alert_dict.get('level', 'info'),
            description=alert_dict.get('description', 'No description provided'),
            details=alert_dict,
            location=alert_dict.get('location')
        )
        
        # Try to determine region from location
        location = alert_dict.get('location', '').upper()
        if 'DFW' in location:
            alert.region = 'DFW'
        elif 'HOU' in location:
            alert.region = 'HOU'
        elif 'WT' in location:
            alert.region = 'WT'
        
        return alert
    
    @classmethod
    def get_active_alerts(cls, include_acknowledged=False):
        """Get all active (unresolved) alerts"""
        query = cls.query.filter_by(resolved=False)
        if not include_acknowledged:
            query = query.filter_by(acknowledged=False)
        return query.order_by(cls.level.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_by_level(cls, level, include_resolved=False):
        """Get alerts by severity level"""
        query = cls.query.filter_by(level=level)
        if not include_resolved:
            query = query.filter_by(resolved=False)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_by_asset(cls, asset_id, include_resolved=False):
        """Get alerts for a specific asset"""
        query = cls.query.filter_by(asset_id=asset_id)
        if not include_resolved:
            query = query.filter_by(resolved=False)
        return query.order_by(cls.level.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_by_type(cls, alert_type, include_resolved=False):
        """Get alerts by type"""
        query = cls.query.filter_by(alert_type=alert_type)
        if not include_resolved:
            query = query.filter_by(resolved=False)
        return query.order_by(cls.level.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_summary(cls):
        """Get summary of alerts grouped by level, type, and location"""
        # Count by level
        level_counts = db.session.query(
            cls.level, db.func.count(cls.id)
        ).filter_by(resolved=False).group_by(cls.level).all()
        
        # Count by type
        type_counts = db.session.query(
            cls.alert_type, db.func.count(cls.id)
        ).filter_by(resolved=False).group_by(cls.alert_type).all()
        
        # Count by location
        location_counts = db.session.query(
            cls.location, db.func.count(cls.id)
        ).filter_by(resolved=False).group_by(cls.location).all()
        
        # Return summary
        return {
            'level_counts': dict(level_counts),
            'type_counts': dict(type_counts),
            'location_counts': dict(location_counts),
            'total_alerts': cls.query.filter_by(resolved=False).count(),
            'unacknowledged_alerts': cls.query.filter_by(resolved=False, acknowledged=False).count()
        }
    
    def acknowledge(self, user_id):
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        db.session.commit()
        return True
    
    def resolve(self, user_id, notes=None):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        if notes:
            self.resolution_notes = notes
        db.session.commit()
        return True
    
class AlertNotification(db.Model):
    """
    Model for tracking alert notifications sent to users
    """
    __tablename__ = 'alert_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('equipment_alerts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(32), nullable=False)  # email, sms, app
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered = db.Column(db.Boolean, default=False)
    delivery_status = db.Column(db.String(64), nullable=True)
    
    # Relationships
    alert = db.relationship('EquipmentAlert', backref=db.backref('notifications', lazy=True))
    user = db.relationship('User', backref=db.backref('alert_notifications', lazy=True))
    
    def __repr__(self):
        return f"<AlertNotification {self.id}: {self.notification_type} for alert {self.alert_id}>"