"""
Configuration Settings

This module contains application-wide configuration settings
that can be imported by other modules.
"""

import os
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application Paths
UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
EXPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'exports')
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

# Ensure folders exist
for folder in [UPLOADS_FOLDER, EXPORTS_FOLDER, DATA_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Attendance Settings
EXPECTED_START_TIME = "07:00 AM"
EXPECTED_END_TIME = "03:30 PM"
LATE_GRACE_PERIOD = 15  # Minutes
EARLY_END_GRACE_PERIOD = 15  # Minutes

# For driver module routes
DEFAULT_START_TIME = "07:00 AM"  # Default expected start time
DEFAULT_THRESHOLD_MINUTES = 15  # Default threshold for late/early calculations
SKIPROWS_DAILY_USAGE = 7  # Number of header rows to skip in DailyUsage.csv

# Vehicle ID Patterns
EQUIPMENT_PATTERNS = [
    r'^ET-\d+',  # Excavation equipment
    r'^PT-\d+',  # Paving equipment
    r'^LT-\d+',  # Loader equipment
    r'^CT-\d+',  # Compaction equipment
    r'^RT-\d+',  # Roller equipment
    r'^HT-\d+',  # Heavy equipment
]

VEHICLE_PATTERNS = [
    r'RAM-\d+',
    r'F-\d+',
    r'CHEVY',
    r'GMC',
    r'FORD F\d+',
]

# Database Settings
DATABASE_URL = os.environ.get('DATABASE_URL')

# API Settings
GAUGE_API_URL = os.environ.get('GAUGE_API_URL')
GAUGE_API_USERNAME = os.environ.get('GAUGE_API_USERNAME')
GAUGE_API_PASSWORD = os.environ.get('GAUGE_API_PASSWORD')

# Job Site Settings
JOB_DIVISIONS = {
    'DFW': ['Dallas', 'Fort Worth', 'Arlington', 'Irving', 'Plano', 'Frisco', 'Grapevine', 'Southlake'],
    'HOU': ['Houston', 'The Woodlands', 'Sugar Land', 'Katy', 'Pearland'],
    'WT': ['Wichita Falls', 'Waco', 'Lubbock', 'Amarillo', 'Abilene', 'San Angelo']
}

# Regular expressions for parsing job numbers
JOB_NUMBER_PATTERN = r'(\d{4})-(\d{3})'

# Function to parse job numbers for sorting
def _parse_job_number(job_str):
    """Parse a job number string into a comparable integer value"""
    match = re.search(JOB_NUMBER_PATTERN, job_str)
    if match:
        year = int(match.group(1))
        sequence = int(match.group(2))
        return year * 1000 + sequence
    return 0

# Cost code defaults
LEGACY_COST_CODE = "9000 100M"
DEFAULT_COST_CODE = "9000 100F"
LEGACY_JOB_CUTOFF = "2023-014"  # Jobs before this use legacy cost code

# Try to import local settings
try:
    from local_settings import *
    logger.info("Loaded local settings")
except ImportError:
    logger.info("No local settings found, using defaults")