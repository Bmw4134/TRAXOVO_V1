"""
Task Scheduler Module

This module manages automated data pulls from the Gauge API and schedules
daily reports for fleet management.
"""
import os
import time
import json
import logging
import threading
import schedule
import traceback
from datetime import datetime, timedelta
from gauge_api import update_asset_data, get_asset_data, save_asset_data

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data directory setup
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)
    
CYA_BACKUP_DIR = os.path.join(DATA_DIR, 'cya_backup')
if not os.path.exists(CYA_BACKUP_DIR):
    os.makedirs(CYA_BACKUP_DIR)

SCHEDULE_CONFIG_FILE = os.path.join(DATA_DIR, 'schedule_config.json')

# Default update times based on business requirements
DEFAULT_SCHEDULE = {
    "early_morning_update": "06:45",  # 6:45 AM - Pull GaugeSmart data for same-day report
    "morning_report": "08:30",        # 8:30 AM - Run same-day report (LS/NOJ)
    "prior_day_report": "09:30",      # 9:30 AM - Run prior day report (LS/EE/NOJ)
    "midday_update": "12:00",         # 12:00 PM - Additional data update
    "evening_update": "17:00",        # 5:00 PM - Evening data update
    "weekend_update": "08:00",        # 8:00 AM - Weekend update
    "max_age_hours": 4                # Maximum age of data before forcing update
}

# Load schedule configuration
def load_schedule_config():
    """Load schedule configuration from file or use defaults"""
    if os.path.exists(SCHEDULE_CONFIG_FILE):
        try:
            with open(SCHEDULE_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded schedule configuration from {SCHEDULE_CONFIG_FILE}")
                return config
        except Exception as e:
            logger.error(f"Error loading schedule configuration: {e}")
    
    # Use defaults if file doesn't exist or loading fails
    logger.info("Using default schedule configuration")
    return DEFAULT_SCHEDULE


def save_last_run_info(success, message, asset_count=0):
    """Save information about the last scheduler run"""
    try:
        run_info = {
            "last_run": datetime.now().isoformat(),
            "success": success,
            "message": message,
            "asset_count": asset_count
        }
        
        run_info_file = os.path.join(DATA_DIR, 'scheduler_last_run.json')
        with open(run_info_file, 'w') as f:
            json.dump(run_info, f, indent=2)
            
        logger.debug(f"Saved scheduler run info: {success}")
        return True
    except Exception as e:
        logger.error(f"Failed to save scheduler run info: {e}")
        return False


def scheduled_update(force=True, sync_db=True):
    """
    Perform a scheduled update of the asset data
    
    Args:
        force (bool): Whether to force the update even if cache is fresh
        sync_db (bool): Whether to sync with database after update
    
    Returns:
        list: List of asset dictionaries
    """
    start_time = datetime.now()
    logger.info(f"Running scheduled update at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = load_schedule_config()
        max_age_hours = config.get("max_age_hours", 4)
        
        # Perform the update
        assets = update_asset_data(force=force, max_age_hours=max_age_hours)
        
        if assets:
            # Save a date-stamped version of the data for historical reference
            datestamp = datetime.now().strftime('%Y-%m-%d')
            date_stamped_file = os.path.join(DATA_DIR, f'gauge_{datestamp}.json')
            
            # Save a copy with today's date
            with open(date_stamped_file, 'w') as f:
                json.dump(assets, f, indent=2)
            logger.info(f"Saved date-stamped API data to {date_stamped_file}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Scheduled update completed in {duration:.2f} seconds, retrieved {len(assets)} assets")
            save_last_run_info(True, f"Successfully updated {len(assets)} assets", len(assets))
            return assets
        else:
            logger.error("Scheduled update failed: No assets returned")
            save_last_run_info(False, "No assets returned")
            return []
            
    except Exception as e:
        logger.error(f"Error during scheduled update: {e}")
        logger.debug(traceback.format_exc())
        save_last_run_info(False, f"Error: {str(e)}")
        return []


def run_same_day_report():
    """
    Run the same-day late start and not on job report
    This report flags drivers who are late to start or not on job site
    based on the current day's data (pulled at 6:45 AM).
    """
    from reports.attendance import generate_same_day_report
    from utils.email_sender import send_report_email
    
    logger.info("Running same-day LS/NOJ report at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # Get the latest data
        assets = get_asset_data(force_update=False)
        
        if not assets:
            logger.error("No asset data available for same-day report")
            return False
        
        # Generate the report
        report_data = generate_same_day_report(assets)
        
        if not report_data:
            logger.error("Failed to generate same-day report data")
            return False
            
        # Store backup for CYA
        datestamp = datetime.now().strftime('%Y%m%d')
        backup_path = os.path.join(CYA_BACKUP_DIR, f'same_day_report_{datestamp}.json')
        
        with open(backup_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Same-day report CYA backup saved to {backup_path}")
        
        # Create human-readable summary for the logs
        flagged_count = len(report_data.get('flagged_drivers', []))
        log_summary = f"Same-day report generated. Flagged {flagged_count} drivers for LS/NOJ issues."
        logger.info(log_summary)
        
        # Send email report
        subject = f"DAILY REPORT: Same-Day Late Start & Not On Job Report - {datetime.now().strftime('%m/%d/%Y')}"
        send_report_email(subject, report_data['email_body'], report_data['recipients'])
        
        logger.info("Same-day report completed and email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to run same-day report: {e}")
        logger.debug(traceback.format_exc())
        return False


def run_prior_day_report():
    """
    Run the prior day late start, early end, and not on job report
    This report analyzes yesterday's data to find attendance issues.
    """
    from reports.attendance import generate_prior_day_report
    from utils.email_sender import send_report_email
    
    logger.info("Running prior-day LS/EE/NOJ report at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # Get yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_file = os.path.join(DATA_DIR, f'gauge_{yesterday}.json')
        
        # Try to load yesterday's data from the date-stamped file
        if os.path.exists(yesterday_file):
            with open(yesterday_file, 'r') as f:
                yesterday_data = json.load(f)
                logger.info(f"Loaded yesterday's data from {yesterday_file}")
        else:
            # Fall back to the latest data if we don't have yesterday's data
            logger.warning(f"No data file found for yesterday ({yesterday}). Using latest data instead.")
            yesterday_data = get_asset_data(force_update=False)
        
        if not yesterday_data:
            logger.error("No asset data available for prior-day report")
            return False
        
        # Generate the report
        report_data = generate_prior_day_report(yesterday_data)
        
        if not report_data:
            logger.error("Failed to generate prior-day report data")
            return False
            
        # Store backup for CYA
        datestamp = datetime.now().strftime('%Y%m%d')
        backup_path = os.path.join(CYA_BACKUP_DIR, f'prior_day_report_{datestamp}.json')
        
        with open(backup_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Prior-day report CYA backup saved to {backup_path}")
        
        # Create human-readable summary for the logs
        flagged_count = len(report_data.get('flagged_drivers', []))
        log_summary = f"Prior-day report generated. Flagged {flagged_count} drivers for LS/EE/NOJ issues."
        logger.info(log_summary)
        
        # Send email report
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
        subject = f"DAILY REPORT: Prior-Day (Late Start, Early End, Not On Job) - {yesterday_date}"
        send_report_email(subject, report_data['email_body'], report_data['recipients'])
        
        logger.info("Prior-day report completed and email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to run prior-day report: {e}")
        logger.debug(traceback.format_exc())
        return False


def run_scheduler():
    """Set up and run the scheduler"""
    # Load configuration
    config = load_schedule_config()
    
    # Extract report times from config
    early_morning_time = config.get("early_morning_update", DEFAULT_SCHEDULE["early_morning_update"])
    morning_report_time = config.get("morning_report", DEFAULT_SCHEDULE["morning_report"])
    prior_day_report_time = config.get("prior_day_report", DEFAULT_SCHEDULE["prior_day_report"])
    midday_time = config.get("midday_update", DEFAULT_SCHEDULE["midday_update"])
    evening_time = config.get("evening_update", DEFAULT_SCHEDULE["evening_update"])
    weekend_time = config.get("weekend_update", DEFAULT_SCHEDULE["weekend_update"])
    
    # Clear any existing schedules
    schedule.clear()
    
    # Schedule API data pulls and reports for weekdays
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        # Early morning update (6:45 AM) - GaugeSmart data pull for same-day report
        getattr(schedule.every(), day).at(early_morning_time).do(
            scheduled_update, force=True, sync_db=True
        )
        
        # Same-day report generation (8:30 AM)
        getattr(schedule.every(), day).at(morning_report_time).do(run_same_day_report)
        
        # Prior-day report generation (9:30 AM)
        getattr(schedule.every(), day).at(prior_day_report_time).do(run_prior_day_report)
        
        # Additional data updates throughout the day
        getattr(schedule.every(), day).at(midday_time).do(
            scheduled_update, force=True, sync_db=True
        )
        getattr(schedule.every(), day).at(evening_time).do(
            scheduled_update, force=True, sync_db=True
        )
    
    # Weekend data updates
    schedule.every().saturday.at(weekend_time).do(scheduled_update, force=True, sync_db=True)
    schedule.every().sunday.at(weekend_time).do(scheduled_update, force=True, sync_db=True)
    
    # Ensure we save the current timestamp
    save_last_run_info(True, "Scheduler initialized", 0)
    
    logger.info(f"Scheduler initialized with data pulls at {early_morning_time}, {midday_time}, and {evening_time}")
    logger.info(f"Reports scheduled at {morning_report_time} (same-day) and {prior_day_report_time} (prior-day)")
    logger.info(f"Weekend updates scheduled for {weekend_time}")
    
    # Run an initial update to ensure we have fresh data
    logger.info("Running initial data update...")
    scheduled_update()
    
    # Run the scheduler loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Sleep for 1 minute between checks
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            logger.debug(traceback.format_exc())
            time.sleep(300)  # Sleep for 5 minutes on error


def start_scheduler_thread():
    """Start the scheduler in a background thread"""
    try:
        # Create a new scheduler thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.name = "FleetReportScheduler"
        scheduler_thread.start()
        logger.info("Scheduler thread started")
        
        # Save status
        thread_info = {
            "started_at": datetime.now().isoformat(),
            "thread_name": scheduler_thread.name,
            "status": "running",
        }
        
        thread_info_file = os.path.join(DATA_DIR, 'scheduler_thread.json')
        with open(thread_info_file, 'w') as f:
            json.dump(thread_info, f, indent=2)
        
        return scheduler_thread
    except Exception as e:
        logger.error(f"Failed to start scheduler thread: {e}")
        logger.debug(traceback.format_exc())
        return None


# Execute this if the script is run directly
if __name__ == "__main__":
    print(f"Starting scheduler at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_scheduler()  # This will block indefinitely