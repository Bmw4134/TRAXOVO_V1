"""
Models Package

This module initializes all database models
"""

from app import db

# Import models for use throughout the application
from models.user import User
from models.asset import Asset
from models.driver import Driver
from models.asset_driver_mapping import AssetDriverMapping

# Import optional models that may not be available in all deployments
try:
    from models.asset_history import AssetHistory
except ImportError:
    pass

try:
    from models.maintenance import MaintenanceRecord, MaintenanceTask
except ImportError:
    pass

try:
    from models.alerts import EquipmentAlert, AlertNotification, Alert
except ImportError:
    pass