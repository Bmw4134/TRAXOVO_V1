"""
Alert models for equipment and system notifications.
"""
from datetime import datetime
from app import db

class Alert(db.Model):
    """Generic alert model for system notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(64), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    severity = db.Column(db.String(32), default='info')  # info, warning, critical
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    
    # Optional foreign keys
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('alerts', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('alerts', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Alert {self.id}: {self.title}>'

class EquipmentAlert(db.Model):
    """Equipment-specific alert model"""
    __tablename__ = 'equipment_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    alert_type = db.Column(db.String(64), nullable=False)  # maintenance, idling, geofence, etc.
    severity = db.Column(db.String(32), default='warning')  # info, warning, critical
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    asset = db.relationship('Asset', backref=db.backref('equipment_alerts', lazy='dynamic'))
    acknowledger = db.relationship('User', backref=db.backref('acknowledged_alerts', lazy='dynamic'))
    
    def __repr__(self):
        return f'<EquipmentAlert {self.id}: {self.alert_type} - {self.asset_id}>'

class AlertNotification(db.Model):
    """Alert notification delivery tracking"""
    __tablename__ = 'alert_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('equipment_alerts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    method = db.Column(db.String(32), nullable=False)  # email, sms, push, etc.
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime)
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    alert = db.relationship('EquipmentAlert', backref=db.backref('notifications', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('alert_notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AlertNotification {self.id}: {self.method} - {self.alert_id}>'