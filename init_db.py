"""
Database Initialization Script

This script initializes the database for TRAXORA system with both development and production
profiles, based on the runtime mode configuration.
"""
import os
import sys
import logging
import argparse
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Import runtime mode configuration
from runtime_mode import is_dev_mode, config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()

#
# Database Models
#
class Asset(Base):
    """Vehicle or equipment asset tracked by the system"""
    __tablename__ = 'assets'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(50))
    category = Column(String(50))
    is_on_road = Column(Boolean, default=True)
    is_pickup_truck = Column(Boolean, default=False)
    location_id = Column(String(50), ForeignKey('locations.id'), nullable=True)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=True)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    location = relationship("Location", back_populates="assets")
    driver = relationship("Driver", back_populates="assets")
    activity_records = relationship("ActivityRecord", back_populates="asset")

class Driver(Base):
    """Driver associated with assets"""
    __tablename__ = 'drivers'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True)
    status = Column(String(20), default='active')
    job_site_id = Column(String(50), ForeignKey('job_sites.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    assets = relationship("Asset", back_populates="driver")
    activity_records = relationship("ActivityRecord", back_populates="driver")
    job_site = relationship("JobSite", back_populates="drivers")

class JobSite(Base):
    """Work location or job site"""
    __tablename__ = 'job_sites'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    job_number = Column(String(50), unique=True)
    address = Column(String(200))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius = Column(Integer, default=200)  # Radius in meters
    foreman = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    drivers = relationship("Driver", back_populates="job_site")
    activity_records = relationship("ActivityRecord", back_populates="job_site")

class Location(Base):
    """GPS location record"""
    __tablename__ = 'locations'
    
    id = Column(String(50), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    assets = relationship("Asset", back_populates="location")

class ActivityRecord(Base):
    """Driver/Asset activity record"""
    __tablename__ = 'activity_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    driver_id = Column(String(50), ForeignKey('drivers.id'), nullable=True)
    asset_id = Column(String(50), ForeignKey('assets.id'), nullable=True)
    job_site_id = Column(String(50), ForeignKey('job_sites.id'), nullable=True)
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)
    status = Column(String(20), default='unknown')
    location_verified = Column(Boolean, default=False)
    time_on_site = Column(Float, default=0.0)  # Hours on site
    data_source = Column(String(50))
    validation_level = Column(String(20), default='unverified')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    driver = relationship("Driver", back_populates="activity_records")
    asset = relationship("Asset", back_populates="activity_records")
    job_site = relationship("JobSite", back_populates="activity_records")

class Report(Base):
    """Generated reports"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(DateTime, nullable=False, index=True)
    report_type = Column(String(50), nullable=False)
    report_data = Column(Text, nullable=False)  # JSON data
    data_sources = Column(String(200))
    driver_count = Column(Integer, default=0)
    jobsite_count = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)  # Seconds
    is_validated = Column(Boolean, default=False)
    validation_status = Column(String(50), default='Unvalidated')
    runtime_mode = Column(String(10), nullable=False)  # 'dev' or 'prod'
    creator_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class RuntimeConfig(Base):
    """Runtime configuration settings"""
    __tablename__ = 'runtime_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    mode = Column(String(10), nullable=False)  # 'dev', 'prod', or 'all'
    description = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db(connection_string=None, drop_existing=False):
    """
    Initialize the database with the appropriate schema.
    
    Args:
        connection_string (str): Database connection string (defaults to environment variable)
        drop_existing (bool): Whether to drop existing tables
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Use provided connection string or get from environment
    if connection_string is None:
        connection_string = os.environ.get('DATABASE_URL')
        
    if not connection_string:
        logger.error("No database connection string provided")
        return False
        
    try:
        # Create engine and connect to database
        engine = create_engine(connection_string)
        
        # Drop all tables if requested
        if drop_existing:
            logger.warning("Dropping all existing tables")
            Base.metadata.drop_all(engine)
            
        # Create all tables
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        
        # Initialize runtime config
        init_runtime_config(engine)
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def init_runtime_config(engine):
    """
    Initialize runtime configuration settings.
    
    Args:
        engine: SQLAlchemy engine
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Default runtime configurations for dev mode
        dev_configs = [
            ('log_level', 'DEBUG', 'dev', 'Logging level for development mode'),
            ('validation_strictness', 'low', 'dev', 'Validation strictness level'),
            ('allow_incomplete_data', 'true', 'dev', 'Whether to allow incomplete data'),
            ('max_report_items', '1000', 'dev', 'Maximum items to include in reports'),
            ('filter_zero_values', 'false', 'dev', 'Filter out zero values in reports')
        ]
        
        # Default runtime configurations for production mode
        prod_configs = [
            ('log_level', 'INFO', 'prod', 'Logging level for production mode'),
            ('validation_strictness', 'high', 'prod', 'Validation strictness level'),
            ('allow_incomplete_data', 'false', 'prod', 'Whether to allow incomplete data'),
            ('max_report_items', '500', 'prod', 'Maximum items to include in reports'),
            ('filter_zero_values', 'true', 'prod', 'Filter out zero values in reports')
        ]
        
        # Common configurations for both modes
        common_configs = [
            ('app_name', 'TRAXORA', 'all', 'Application name'),
            ('version', '1.0.0', 'all', 'Application version'),
            ('date_format', '%Y-%m-%d', 'all', 'Default date format'),
            ('time_format', '%H:%M:%S', 'all', 'Default time format'),
            ('default_report_limit', '100', 'all', 'Default number of items in reports')
        ]
        
        # Insert configurations for current mode
        configs_to_insert = common_configs
        if is_dev_mode():
            configs_to_insert.extend(dev_configs)
        else:
            configs_to_insert.extend(prod_configs)
            
        # Check if configs already exist
        existing_keys = [r[0] for r in session.query(RuntimeConfig.key).all()]
        
        # Insert new configurations
        for key, value, mode, description in configs_to_insert:
            if key not in existing_keys:
                config_entry = RuntimeConfig(
                    key=key,
                    value=value,
                    mode=mode,
                    description=description
                )
                session.add(config_entry)
                
        session.commit()
        # Use the imported config from runtime_mode to get current mode
        from runtime_mode import config as runtime_config
        logger.info(f"Initialized runtime configuration in {runtime_config['mode']} mode")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing runtime configuration: {str(e)}")
    finally:
        session.close()


def main():
    """Main function to initialize the database"""
    parser = argparse.ArgumentParser(description='Initialize TRAXORA database')
    parser.add_argument('--drop', action='store_true', help='Drop existing tables')
    parser.add_argument('--connection', type=str, help='Database connection string')
    args = parser.parse_args()
    
    # Log the mode we're running in
    if is_dev_mode():
        logger.info("Running database initialization in DEVELOPMENT mode")
    else:
        logger.info("Running database initialization in PRODUCTION mode")
    
    # Initialize the database
    success = init_db(args.connection, args.drop)
    
    if success:
        logger.info("Database initialization completed successfully")
        return 0
    else:
        logger.error("Database initialization failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())