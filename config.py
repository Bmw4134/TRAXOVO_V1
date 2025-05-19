"""
Configuration Settings

This module contains application-wide configuration settings
that can be imported by other modules.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Basic application settings
APP_NAME = "TRAXORA"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "Fleet Management & Asset Tracking Platform"

# Directory paths (relative to application root)
UPLOADS_FOLDER = os.path.join('uploads')
EXPORTS_FOLDER = os.path.join('exports')
BACKUPS_FOLDER = os.path.join('backups')
TEMPLATES_FOLDER = os.path.join('templates')
STATIC_FOLDER = os.path.join('static')
REPORTS_FOLDER = os.path.join('reports')
DATA_FOLDER = os.path.join('data')
LOGS_FOLDER = os.path.join('logs')
ATTACHED_ASSETS_FOLDER = os.path.join('attached_assets')

# Create necessary directories if they don't exist
for folder in [UPLOADS_FOLDER, EXPORTS_FOLDER, BACKUPS_FOLDER, REPORTS_FOLDER, DATA_FOLDER, LOGS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# File upload settings
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'txt', 'pdf'}

# Database settings (for raw SQL operations)
DB_TIMEOUT = 60  # seconds

# Pagination settings
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 500

# Time settings
DEFAULT_START_TIME = "07:00 AM"  # Expected start time for drivers
DEFAULT_THRESHOLD_MINUTES = 5    # Grace period for lateness
DEFAULT_TIMEZONE = "America/Chicago"  # Central Time

# Driver attendance settings
SKIPROWS_DAILY_USAGE = 0  # Number of rows to skip when reading DailyUsage.csv

# Email settings
DEFAULT_EMAIL_FROM = "traxora-reports@example.com"
DEFAULT_EMAIL_SUBJECT_PREFIX = "[TRAXORA]"

# GeoLocation settings
DEFAULT_MAP_CENTER = [32.7555, -97.3308]  # Fort Worth, TX
DEFAULT_MAP_ZOOM = 12
MAP_REFRESH_INTERVAL = 60  # seconds

# PM Allocation settings
PM_ALLOCATION_SHEET_NAME = "EQ ALLOCATIONS - ALL DIV"
PM_ALLOCATION_HEADER_ROW = 3  # Row 4 in Excel (0-indexed)
PM_ALLOCATION_DATA_START_ROW = 4  # Row 5 in Excel (0-indexed)
PM_ALLOCATION_FIELDS = {
    'DIV': 'Division',
    'JOB': 'Job Number',
    'ASSET ID': 'Asset ID',
    'EQUIPMENT': 'Equipment',
    'DRIVER': 'Driver',
    'UNIT ALLOCATION': 'Units',
    'COST CODE': 'Cost Code',
    'REVISION': 'Revision',
    'NOTE / DETAIL': 'Notes'
}

# Feature flags
ENABLE_GEOLOCATION = True
ENABLE_DOCUMENT_OCR = False
ENABLE_EMAIL_REPORTS = True
ENABLE_AUTOMATIC_EXPORTS = True
ENABLE_VEHICLE_AUDIT = True
ENABLE_USER_SETTINGS = True
ENABLE_REALTIME_UPDATES = False

# API rate limiting
API_RATE_LIMIT = "100/minute"
API_RATE_LIMIT_EXEMPT_HOSTS = ['localhost', '127.0.0.1']

# Security settings
SESSION_TIMEOUT = 3600  # 1 hour in seconds
PASSWORD_RESET_EXPIRY = 24 * 3600  # 24 hours in seconds
REQUIRE_TWO_FACTOR = False

# Logging settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = logging.DEBUG  # Set to logging.INFO in production

# Try to load environment-specific settings
try:
    from local_settings import *
    logger.info("Loaded local settings")
except ImportError:
    logger.info("No local settings found, using defaults")