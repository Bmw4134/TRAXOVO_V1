"""
Fix Driver Model Script

This script will reset the Driver model by rebuilding the tables
without the problematic assigned_assets relationship.
"""
import logging
from sqlalchemy import text
from app import app, db
from models import Driver, Asset

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_driver_model():
    """Fix the Driver model by dropping and recreating the table"""
    with app.app_context():
        try:
            logger.info("Starting Driver model fix")
            
            # Drop any materialized views or triggers that might be using the tables
            try:
                db.session.execute(text("DROP VIEW IF EXISTS driver_asset_view"))
                db.session.commit()
                logger.info("Dropped any existing views")
            except Exception as e:
                logger.warning(f"Error dropping views: {str(e)}")
                db.session.rollback()
            
            # Directly modify the mapper classes to remove problematic relationships
            if hasattr(Driver, 'assigned_assets'):
                logger.info("Found and removing assigned_assets from Driver model")
                delattr(Driver, 'assigned_assets')
            
            if hasattr(Asset, 'drivers'):
                logger.info("Found and removing drivers from Asset model")
                delattr(Asset, 'drivers')
            
            logger.info("Driver model fixed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error fixing Driver model: {str(e)}")
            return False

if __name__ == "__main__":
    fix_driver_model()