"""
User Settings Models

This module provides functions for managing user settings in the database.
"""

import logging
import json
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

# In-memory storage for settings until database integration
SETTINGS_STORE = {}

# File-based storage path
SETTINGS_FILE = os.path.join('data', 'user_settings.json')

# Create directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Load settings from file if it exists
try:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            SETTINGS_STORE = json.load(f)
except Exception as e:
    logger.error(f"Error loading settings: {e}")

def get_user_setting(user_id, setting_name, default_value=None):
    """Get a user setting value"""
    try:
        # Convert user_id to string for consistency
        user_id = str(user_id)
        
        # Return from memory storage
        if user_id in SETTINGS_STORE and setting_name in SETTINGS_STORE[user_id]:
            return SETTINGS_STORE[user_id][setting_name]
            
        return default_value
    except Exception as e:
        logger.error(f"Error getting user setting {setting_name} for user {user_id}: {e}")
        return default_value

def set_user_setting(user_id, setting_name, setting_value):
    """Set a user setting value"""
    try:
        # Convert user_id to string for consistency
        user_id = str(user_id)
        
        # Ensure user has a settings object
        if user_id not in SETTINGS_STORE:
            SETTINGS_STORE[user_id] = {}
            
        # Update setting
        SETTINGS_STORE[user_id][setting_name] = setting_value
        
        # Save to file
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(SETTINGS_STORE, f)
        except Exception as e:
            logger.error(f"Error saving settings to file: {e}")
            
        return True
    except Exception as e:
        logger.error(f"Error setting user setting {setting_name} for user {user_id}: {e}")
        return False