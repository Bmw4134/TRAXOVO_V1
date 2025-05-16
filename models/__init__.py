"""
Models package for database models
"""
# Import all models from the models module and expose them at the package level
from models.models import User, Asset, AssetDriverMapping, APIConfig
from models.core import Driver

# Import maintenance models
from models.maintenance import (
    MaintenanceTask, MaintenanceHistory, MaintenanceSchedule, MaintenancePart,
    MaintenanceNotification, MaintenanceType, MaintenancePriority, MaintenanceStatus
)

# Also make db available through the models package
from db import db