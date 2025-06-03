"""
TRAXORA Fleet Management System - Model Fix

This script fixes the Driver model relationship with assets 
by defining a proper many-to-many relationship.
"""
import os
import sys
import logging
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app import db, app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_models():
    """Fix the Driver model and related association tables"""
    try:
        # Define association table between drivers and assets
        driver_asset_association = Table(
            'driver_asset_association',
            db.Model.metadata,
            Column('driver_id', Integer, ForeignKey('drivers.id')),
            Column('asset_id', Integer, ForeignKey('assets.id'))
        )
        
        # Create a minimal Driver model with corrected relationship
        class DriverFixed(db.Model):
            __tablename__ = 'drivers'
            id = Column(Integer, primary_key=True)
            name = Column(String(128))
            employee_id = Column(String(64))
            phone = Column(String(64))
            email = Column(String(128))
            license_number = Column(String(64))
            license_class = Column(String(32))
            license_expiration = Column(DateTime)
            is_active = Column(Boolean, default=True)
            created_at = Column(DateTime)
            updated_at = Column(DateTime)
            
            # Define many-to-many relationship with assets
            assigned_assets = relationship(
                'Asset', 
                secondary=driver_asset_association,
                backref='assigned_drivers'
            )
        
        # Create a minimal Asset model
        class AssetFixed(db.Model):
            __tablename__ = 'assets'
            id = Column(Integer, primary_key=True)
            name = Column(String(128))
            asset_id = Column(String(64))
            type = Column(String(64))
            model = Column(String(64))
            manufacturer = Column(String(64))
            year = Column(Integer)
            is_active = Column(Boolean, default=True)
            
        # Create database tables
        with app.app_context():
            db.create_all()
            logger.info("Models fixed and tables created")
        
        return True
    
    except Exception as e:
        logger.error(f"Error fixing models: {str(e)}")
        return False

if __name__ == "__main__":
    result = fix_models()
    print("Model fix completed" if result else "Model fix failed")
    sys.exit(0 if result else 1)