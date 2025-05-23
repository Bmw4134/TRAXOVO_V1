"""
TRAXORA Fleet Management System - Database Fix Utility

This module provides functions to fix the database relationship issues
with Driver.assigned_assets that are causing application errors.
"""
import os
import logging
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_driver_asset_relationship(db):
    """
    Fix the Driver.assigned_assets relationship by properly setting up
    the association table and relationships.
    
    Args:
        db: SQLAlchemy database instance
    
    Returns:
        bool: True if fix was successful, False otherwise
    """
    try:
        # Use SQL to check if driver_asset_association table exists
        inspector = inspect(db.engine)
        
        if not 'driver_asset_association' in inspector.get_table_names():
            # Create the association table if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS driver_asset_association (
                    driver_id INTEGER NOT NULL,
                    asset_id INTEGER NOT NULL,
                    primary key (driver_id, asset_id),
                    FOREIGN KEY(driver_id) REFERENCES drivers(id),
                    FOREIGN KEY(asset_id) REFERENCES assets(id)
                )
                '''))
                conn.commit()
                logger.info("Created driver_asset_association table")
        
        # Check if the assets table has the driver_id column and remove it if it exists
        # (since we're using an association table now)
        if 'driver_id' in [c['name'] for c in inspector.get_columns('assets')]:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE assets DROP COLUMN driver_id'))
                conn.commit()
                logger.info("Removed driver_id from assets table")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error fixing driver-asset relationship: {str(e)}")
        return False

def check_database_tables(db):
    """
    Check database tables and their relationships
    
    Args:
        db: SQLAlchemy database instance
    
    Returns:
        dict: Dictionary with database status information
    """
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table in tables:
            columns = [c['name'] for c in inspector.get_columns(table)]
            primary_keys = inspector.get_pk_constraint(table)
            foreign_keys = inspector.get_foreign_keys(table)
            
            table_info[table] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys
            }
        
        return {
            'status': 'success',
            'tables': tables,
            'table_info': table_info
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error checking database tables: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }