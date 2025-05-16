"""
Models package for database models
"""
# Import all models from the core module and expose them at the package level
from models.core import (
    User,
    Asset,
    AssetHistory,
    MaintenanceRecord,
    APIConfig,
    Geofence,
)

# Also make db available through the models package
from database import db