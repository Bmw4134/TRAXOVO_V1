"""
Migration to create the geofence table

Run this script to create the geofence table:
$ python migrations/create_geofence_table.py
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import db
from models import Geofence

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_geofence_table():
    """Create the geofence table if it doesn't exist"""
    try:
        # Check if the table exists
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'geofence'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info("Geofence table already exists.")
            return
        
        # Table doesn't exist, create it via SQLAlchemy
        logger.info("Creating geofence table...")
        
        # Use SQLAlchemy to create the table
        db.metadata.create_all(db.engine, tables=[Geofence.__table__])
        
        logger.info("Geofence table created successfully.")
        
        # Populate with some default geofences
        default_geofences = [
            {
                'name': 'DFW Office',
                'latitude': 32.9483,
                'longitude': -96.7299,
                'radius': 500,
                'type': 'static'
            },
            {
                'name': 'Houston Office',
                'latitude': 29.7604,
                'longitude': -95.3698,
                'radius': 500,
                'type': 'static'
            },
            {
                'name': 'West Texas Office',
                'latitude': 31.9686,
                'longitude': -102.0878,
                'radius': 500,
                'type': 'static'
            }
        ]
        
        for gf_data in default_geofences:
            geofence = Geofence(
                name=gf_data['name'],
                latitude=gf_data['latitude'],
                longitude=gf_data['longitude'],
                radius=gf_data['radius'],
                type=gf_data['type'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(geofence)
        
        db.session.commit()
        logger.info(f"Added {len(default_geofences)} default geofences.")
        
    except Exception as e:
        logger.error(f"Error creating geofence table: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting geofence table migration...")
    create_geofence_table()
    logger.info("Migration completed.")