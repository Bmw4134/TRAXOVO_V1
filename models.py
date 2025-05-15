from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)


class Asset(db.Model):
    """Asset model for equipment data"""
    id = db.Column(db.Integer, primary_key=True)
    # Basic information
    asset_identifier = db.Column(db.String(64), unique=True, nullable=False, index=True)
    label = db.Column(db.String(128))
    asset_category = db.Column(db.String(64), index=True)
    asset_class = db.Column(db.String(64))
    asset_make = db.Column(db.String(64))
    asset_model = db.Column(db.String(64))
    serial_number = db.Column(db.String(128))
    device_serial_number = db.Column(db.String(128))
    
    # Status information
    active = db.Column(db.Boolean, default=False)
    days_inactive = db.Column(db.String(16))
    ignition = db.Column(db.Boolean)
    
    # Location information
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location = db.Column(db.String(256), index=True)
    site = db.Column(db.String(256))
    district = db.Column(db.String(64))
    sub_district = db.Column(db.String(64))
    
    # Technical information
    engine_hours = db.Column(db.Float)
    odometer = db.Column(db.Float)
    speed = db.Column(db.Float)
    speed_limit = db.Column(db.Float)
    heading = db.Column(db.String(16))
    backup_battery_pct = db.Column(db.Float)
    voltage = db.Column(db.Float)
    imei = db.Column(db.String(32))
    
    # Event information
    event_date_time = db.Column(db.DateTime)
    event_date_time_string = db.Column(db.String(64))
    reason = db.Column(db.String(64))
    time_zone = db.Column(db.String(8))
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    history = db.relationship('AssetHistory', backref='asset', lazy='dynamic')
    maintenance_records = db.relationship('MaintenanceRecord', backref='asset', lazy='dynamic')
    
    @property
    def formatted_date_time(self):
        """Return formatted date time for display"""
        if self.event_date_time:
            return self.event_date_time.strftime("%Y-%m-%d %H:%M:%S")
        elif self.event_date_time_string:
            return self.event_date_time_string
        else:
            return "No date available"
    
    @staticmethod
    def map_field_name(api_field):
        """
        Map API field names to database column names
        
        Args:
            api_field (str): API field name
            
        Returns:
            str: Database column name
        """
        mapping = {
            'AssetIdentifier': 'asset_identifier',
            'Label': 'label',
            'AssetCategory': 'asset_category',
            'AssetClass': 'asset_class',
            'AssetMake': 'asset_make',
            'AssetModel': 'asset_model',
            'SerialNumber': 'serial_number',
            'DeviceSerialNumber': 'device_serial_number',
            'Active': 'active',
            'DaysInactive': 'days_inactive',
            'Ignition': 'ignition',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Location': 'location',
            'Site': 'site',
            'District': 'district',
            'SubDistrict': 'sub_district',
            'Engine1Hours': 'engine_hours',
            'Odometer': 'odometer',
            'Speed': 'speed',
            'SpeedLimit': 'speed_limit',
            'Heading': 'heading',
            'BackupBatteryPct': 'backup_battery_pct',
            'Voltage': 'voltage',
            'IMEI': 'imei',
            'EventDateTime': 'event_date_time',
            'EventDateTimeString': 'event_date_time_string',
            'Reason': 'reason',
            'TimeZone': 'time_zone'
        }
        return mapping.get(api_field, api_field.lower())
    
    @staticmethod
    def convert_value(key, value):
        """
        Convert API values to appropriate database types
        
        Args:
            key (str): API field name
            value: API field value
            
        Returns:
            Value converted to appropriate type
        """
        # Handle None values
        if value is None:
            return None
            
        # Handle boolean values
        if key in ['Active', 'Ignition']:
            if isinstance(value, bool):
                return value
            return value == 'True' or value == 'true' or value == '1' or value == 1
            
        # Handle numeric values
        if key in ['Latitude', 'Longitude', 'Engine1Hours', 'Odometer', 'Speed', 
                   'SpeedLimit', 'BackupBatteryPct', 'Voltage']:
            try:
                if value == '':
                    return None
                return float(value)
            except (ValueError, TypeError):
                return None
                
        # Handle date values
        if key == 'EventDateTime':
            try:
                if isinstance(value, str):
                    # Try multiple date formats
                    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", 
                                "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"]:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                return None
            except Exception:
                return None
                
        # Return string values as is
        return value
    
    @classmethod
    def from_json(cls, data):
        """Create or update asset from JSON data"""
        asset = cls()
        
        # Set all fields from the data
        for key, value in data.items():
            field_name = cls.map_field_name(key)
            if hasattr(asset, field_name):
                converted_value = cls.convert_value(key, value)
                setattr(asset, field_name, converted_value)
        
        # Handle special case for event_date_time from EventDateTimeString
        if data.get('EventDateTimeString') and not asset.event_date_time:
            try:
                # Parse datetime in the format "MM/DD/YYYY HH:MM:SS AM/PM CT"
                dt_str = data.get('EventDateTimeString')
                dt_parts = dt_str.split(' ')
                if len(dt_parts) >= 3:
                    date_part = dt_parts[0]
                    time_part = dt_parts[1]
                    am_pm = dt_parts[2]
                    try:
                        date_obj = datetime.strptime(f"{date_part} {time_part} {am_pm}", "%m/%d/%Y %I:%M:%S %p")
                        asset.event_date_time = date_obj
                    except ValueError:
                        pass
            except Exception:
                pass
        
        return asset


class Geofence(db.Model):
    """Geofence model for job site boundaries"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)  # Radius in meters
    type = db.Column(db.String(16), default='static')  # 'static' or 'dynamic'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Geofence {self.name}>"


class AssetHistory(db.Model):
    """Historical records of asset updates"""
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    
    # Status snapshot
    active = db.Column(db.Boolean)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location = db.Column(db.String(256))
    engine_hours = db.Column(db.Float)
    odometer = db.Column(db.Float)
    speed = db.Column(db.Float)
    voltage = db.Column(db.Float)
    ignition = db.Column(db.Boolean)
    
    # Event information
    event_date_time = db.Column(db.DateTime)
    reason = db.Column(db.String(64))
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def from_asset(cls, asset):
        """Create history record from asset object"""
        history = cls()
        history.asset_id = asset.id
        history.active = asset.active
        history.latitude = asset.latitude
        history.longitude = asset.longitude
        history.location = asset.location
        history.engine_hours = asset.engine_hours
        history.odometer = asset.odometer
        history.speed = asset.speed
        history.voltage = asset.voltage
        history.ignition = asset.ignition
        history.event_date_time = asset.event_date_time
        history.reason = asset.reason
        
        return history


class MaintenanceRecord(db.Model):
    """Maintenance records for assets"""
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    
    # Maintenance details
    service_type = db.Column(db.String(64), nullable=False)
    service_date = db.Column(db.DateTime, nullable=False)
    engine_hours = db.Column(db.Float)
    performed_by = db.Column(db.String(128))
    cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User')


class APIConfig(db.Model):
    """API configuration settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)
    is_secret = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        """Get configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default
    
    @classmethod
    def set(cls, key, value, is_secret=False):
        """Set configuration value"""
        config = cls.query.filter_by(key=key).first()
        if not config:
            config = cls(key=key)
        config.value = value
        config.is_secret = is_secret
        db.session.add(config)
        db.session.commit()
        return config
