"""
Task Scheduler Module

This module sets up a scheduler to automatically fetch data from the Gauge API
at regular intervals, ensuring the dashboard always has the most recent data.
"""
import time
import logging
import threading
import schedule
from datetime import datetime
from gauge_api import update_asset_data

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define update intervals
MORNING_UPDATE_TIME = "07:00"  # 7:00 AM
MIDDAY_UPDATE_TIME = "12:00"   # 12:00 PM
EVENING_UPDATE_TIME = "17:00"  # 5:00 PM


def scheduled_update():
    """Perform a scheduled update of the asset data"""
    logger.info(f"Running scheduled update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        assets = update_asset_data(force=True)
        logger.info(f"Scheduled update completed, retrieved {len(assets)} assets")
    except Exception as e:
        logger.error(f"Error during scheduled update: {e}")


def run_scheduler():
    """Set up and run the scheduler"""
    # Schedule updates at specific times
    schedule.every().day.at(MORNING_UPDATE_TIME).do(scheduled_update)
    schedule.every().day.at(MIDDAY_UPDATE_TIME).do(scheduled_update)
    schedule.every().day.at(EVENING_UPDATE_TIME).do(scheduled_update)
    
    logger.info(f"Scheduler initialized with updates at {MORNING_UPDATE_TIME}, {MIDDAY_UPDATE_TIME}, and {EVENING_UPDATE_TIME}")
    
    # Run the scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute between checks


def start_scheduler_thread():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")
    return scheduler_thread


# Execute this if the script is run directly
if __name__ == "__main__":
    print(f"Starting scheduler at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_scheduler()  # This will block indefinitely