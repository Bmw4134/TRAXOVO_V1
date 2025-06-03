"""
Import Drivers Data

Script to import driver data from CSV reports and populate the database.
"""
from app import app, db
from models.driver_attendance import Driver, JobSite, AttendanceRecord
from utils.driver_data_importer import import_all_driver_data
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to import driver data"""
    with app.app_context():
        # Create tables if they don't exist
        logger.info("Creating database tables if they don't exist...")
        db.create_all()
        
        # Import driver data
        logger.info("Importing driver data...")
        import_all_driver_data()
        
        # Log completion
        logger.info("Data import completed!")
        
        # Log driver counts
        driver_count = Driver.query.count()
        job_site_count = JobSite.query.count()
        record_count = AttendanceRecord.query.count()
        logger.info(f"Imported {driver_count} drivers, {job_site_count} job sites, and {record_count} attendance records.")
        
        # Calculate summary statistics
        late_start_count = AttendanceRecord.query.filter_by(late_start=True).count()
        early_end_count = AttendanceRecord.query.filter_by(early_end=True).count()
        not_on_job_count = AttendanceRecord.query.filter_by(not_on_job=True).count()
        
        logger.info(f"Late starts: {late_start_count}")
        logger.info(f"Early ends: {early_end_count}")
        logger.info(f"Not on job: {not_on_job_count}")

if __name__ == "__main__":
    main()