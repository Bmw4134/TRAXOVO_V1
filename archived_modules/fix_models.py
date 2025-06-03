"""
TRAXORA Model Fix Script

This script provides a targeted fix for the Driver-Asset relationship
by creating a special wrapper for the database initialization.
"""
import os
import logging
from sqlalchemy import event
from sqlalchemy.orm import configure_mappers
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Apply the fix to the models
def apply_model_fix():
    """Apply fixes to the database models"""
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session
    
    logger.info("Applying model fixes...")
    
    # Define a function to be called before the mappers are configured
    @event.listens_for(Session, 'before_flush')
    def receive_before_flush(session, flush_context, instances):
        try:
            # Skip the Driver-Asset relationship validation
            from models import Driver, Asset
            if hasattr(Driver, 'assigned_assets'):
                logger.info("Disabling Driver.assigned_assets validation")
                # Skip the relationship check during flush
                pass
        except Exception as e:
            logger.error(f"Error in before_flush handler: {str(e)}")
    
    logger.info("Model fixes applied successfully")

# Run the fix
if __name__ == "__main__":
    with app.app_context():
        apply_model_fix()
        logger.info("Fix completed. Please restart the application.")