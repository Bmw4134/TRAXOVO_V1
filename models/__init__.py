"""
Models Package

This module initializes all database models
"""

from app import db
from main import User, Asset, Driver, AssetDriverMapping

# Import models from modules
try:
    from models.asset_history import AssetHistory
except ImportError:
    pass

try:
    from models.maintenance import MaintenanceRecord, MaintenanceTask
except ImportError:
    pass

try:
    from models.alerts import EquipmentAlert, AlertNotification
except ImportError:
    pass