"""
Configuration Settings

This module contains application-wide configuration settings
that can be imported by other modules.
"""

import os
import logging
from datetime import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application settings
APP_NAME = "TRAXORA"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Fleet Management and Equipment Tracking System"

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 5
DATABASE_POOL_RECYCLE = 300

# File paths and directories
EXPORTS_FOLDER = os.path.join(os.getcwd(), "exports")
UPLOADS_FOLDER = os.path.join(os.getcwd(), "uploads")
REPORTS_FOLDER = os.path.join(os.getcwd(), "reports")
BACKUP_FOLDER = os.path.join(os.getcwd(), "backups")

# Ensure required directories exist
for folder in [EXPORTS_FOLDER, UPLOADS_FOLDER, REPORTS_FOLDER, BACKUP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Email settings
EMAIL_SENDER = "noreply@traxora.com"
EMAIL_SIGNATURE = "TRAXORA Fleet Management Team"

# Driver module settings
DRIVER_EXPECTED_START_TIME = time(7, 0)  # 7:00 AM
DRIVER_EXPECTED_END_TIME = time(15, 30)  # 3:30 PM
DRIVER_LATE_THRESHOLD_MINUTES = 15  # 15 minutes grace period
DRIVER_EARLY_END_THRESHOLD_MINUTES = 15  # 15 minutes grace period

# Compatibility constants for driver module
DEFAULT_START_TIME = time(7, 0)  # Same as DRIVER_EXPECTED_START_TIME
DEFAULT_END_TIME = time(15, 30)  # Same as DRIVER_EXPECTED_END_TIME
DEFAULT_THRESHOLD_MINUTES = 15  # Same as DRIVER_LATE_THRESHOLD_MINUTES
SKIPROWS_DAILY_USAGE = 7  # Number of rows to skip when reading DailyUsage.csv

# Company names for filtering
COMPANY_FILTERS = {
    "all": "All Companies",
    "ragle": "Ragle Inc.",
    "select": "Select Contracting"
}

# Asset ID patterns
VEHICLE_PREFIXES = ["ET-", "PT-", "LT-", "CT-", "RT-", "HT-"]
EQUIPMENT_PREFIXES = ["EQ-", "FX-", "MD-", "ML-", "HV-"]

# Excel report settings
EXCEL_HEADER_STYLE = {
    "font": {"bold": True, "color": "FFFFFF"},
    "fill": {"patternType": "solid", "fgColor": "337AB7"},
    "alignment": {"horizontal": "center", "vertical": "center"}
}

EXCEL_SUBHEADER_STYLE = {
    "font": {"bold": True},
    "fill": {"patternType": "solid", "fgColor": "E6E6E6"},
    "alignment": {"horizontal": "center"}
}

# Gauge API integration settings
GAUGE_API_URL = os.environ.get("GAUGE_API_URL")
GAUGE_API_USERNAME = os.environ.get("GAUGE_API_USERNAME")
GAUGE_API_PASSWORD = os.environ.get("GAUGE_API_PASSWORD")
GAUGE_API_TIMEOUT = 30  # seconds

# Map and geolocation settings
DEFAULT_MAP_CENTER = (32.7767, -96.7970)  # Dallas, TX
DEFAULT_MAP_ZOOM = 10
GEOFENCE_ALERT_DISTANCE = 500  # meters

# Job site and driver settings
ATTENDANCE_WINDOW_DAYS = 90  # Keep attendance records for this many days
HISTORY_LIMIT_MONTHS = 6  # Show history for up to 6 months

# PM Billing settings
DEFAULT_COST_CODE = "9000 100F"
LEGACY_COST_CODE = "9000 100M"
LEGACY_JOB_THRESHOLD = "2023-014"  # Jobs before this use legacy cost code

# Calculate legacy job number as integer for comparison
def _parse_job_number(job_str):
    """Parse a job number string into a comparable integer value"""
    if not job_str:
        return 0
    
    try:
        # Split job number into year and sequence parts (e.g., "2023-014" -> "2023", "014")
        if "-" in job_str:
            year_str, seq_str = job_str.split("-", 1)
            year = int(year_str)
            sequence = int(seq_str)
            return (year * 1000) + sequence
        else:
            # If no hyphen, just try to convert the whole string
            return int(job_str)
    except (ValueError, TypeError):
        return 0

LEGACY_JOB_THRESHOLD_VALUE = _parse_job_number(LEGACY_JOB_THRESHOLD)

# Import local settings if they exist
try:
    from local_settings import *
    logger.info("Loaded local settings")
except ImportError:
    logger.info("No local settings found, using defaults")