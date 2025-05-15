"""
Task Scheduler Module

This module sets up a scheduler to automatically fetch data from the Gauge API
at regular intervals, ensuring the dashboard always has the most recent data.
"""
import os
import time
import json
import logging
import threading
import schedule
import traceback
from datetime import datetime
from gauge_api import update_asset_data, get_asset_data

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
SCHEDULE_CONFIG_FILE = os.path.join(DATA_DIR, 'schedule_config.json')

# Default update times
DEFAULT_SCHEDULE = {
    "morning_update": "07:00",    # 7:00 AM
    "midday_update": "12:00",     # 12:00 PM
    "evening_update": "17:00",    # 5:00 PM
    "weekend_update": "08:00",    # 8:00 AM on weekends
    "max_age_hours": 4            # Maximum age of data before forcing update
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
    except Exception as e:
        logger.error(f"Failed to save scheduler run info: {e}")

def scheduled_update(force=True, sync_db=True):
    """
    Perform a scheduled update of the asset data
    
    Args:
        force (bool): Whether to force the update even if cache is fresh
        sync_db (bool): Whether to sync with database after update
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

def run_scheduler():
    """Set up and run the scheduler"""
    # Load configuration
    config = load_schedule_config()
    
    # Get schedule times from config
    morning = config.get("morning_update", "07:00")
    midday = config.get("midday_update", "12:00")
    evening = config.get("evening_update", "17:00")
    weekend = config.get("weekend_update", "08:00")
    
    # Schedule daily updates for weekdays
    schedule.every().monday.at(morning).do(scheduled_update)
    schedule.every().tuesday.at(morning).do(scheduled_update)
    schedule.every().wednesday.at(morning).do(scheduled_update)
    schedule.every().thursday.at(morning).do(scheduled_update)
    schedule.every().friday.at(morning).do(scheduled_update)
    
    schedule.every().monday.at(midday).do(scheduled_update)
    schedule.every().tuesday.at(midday).do(scheduled_update)
    schedule.every().wednesday.at(midday).do(scheduled_update)
    schedule.every().thursday.at(midday).do(scheduled_update)
    schedule.every().friday.at(midday).do(scheduled_update)
    
    schedule.every().monday.at(evening).do(scheduled_update)
    schedule.every().tuesday.at(evening).do(scheduled_update)
    schedule.every().wednesday.at(evening).do(scheduled_update)
    schedule.every().thursday.at(evening).do(scheduled_update)
    schedule.every().friday.at(evening).do(scheduled_update)
    
    # Schedule once a day on weekends
    schedule.every().saturday.at(weekend).do(scheduled_update)
    schedule.every().sunday.at(weekend).do(scheduled_update)
    
    # Add a daily job to ensure we didn't miss any updates
    schedule.every().day.at("23:45").do(lambda: scheduled_update(force=False))
    
    logger.info(f"Scheduler initialized with weekday updates at {morning}, {midday}, and {evening}")
    logger.info(f"Weekend updates scheduled for {weekend}")
    
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
        scheduler_thread.name = "GaugeAPIScheduler"
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