"""
Activity Logger Utility

This module provides functions for logging user activities and system events
to maintain an audit trail of actions within the application.
"""

import logging
from datetime import datetime
from flask import session, request, g
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('utils.activity_logger')

# Constants
LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
ACTIVITY_LOG_FILE = os.path.join(LOG_FOLDER, 'activity.log')

# Create logs directory if it doesn't exist
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

def log_activity(activity_type, description=None, user_id=None, metadata=None):
    """
    Log a user activity or system event
    
    Args:
        activity_type (str): Type of activity (e.g., 'login', 'report_generation')
        description (str, optional): Description of the activity
        user_id (str, optional): ID of the user performing the activity
        metadata (dict, optional): Additional metadata about the activity
        
    Returns:
        bool: Success status
    """
    try:
        # Get current user from session if available
        if user_id is None:
            if hasattr(g, 'user') and g.user:
                user_id = g.user.id
            elif session.get('user_id'):
                user_id = session.get('user_id')
            else:
                user_id = 'admin'  # Default for system events or anonymous users
        
        # Create activity record
        activity = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'description': description,
            'user_id': user_id,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.user_agent.string if request and request.user_agent else None,
            'endpoint': request.endpoint if request else None,
            'metadata': metadata or {}
        }
        
        # Log to application logger
        logger.info(f"ACTIVITY: {activity_type} by {user_id}")
        
        # Write to activity log file
        with open(ACTIVITY_LOG_FILE, 'a') as log_file:
            log_file.write(f"{json.dumps(activity)}\n")
            
        return True
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        return False

def get_recent_activities(limit=100, activity_type=None, user_id=None):
    """
    Get recent activity logs
    
    Args:
        limit (int): Maximum number of activities to return
        activity_type (str, optional): Filter by activity type
        user_id (str, optional): Filter by user ID
        
    Returns:
        list: List of activity records
    """
    try:
        if not os.path.exists(ACTIVITY_LOG_FILE):
            return []
            
        activities = []
        with open(ACTIVITY_LOG_FILE, 'r') as log_file:
            # Start from the end and read the file backwards to get the most recent entries
            lines = log_file.readlines()
            for line in reversed(lines):
                try:
                    activity = json.loads(line.strip())
                    
                    # Apply filters
                    if activity_type and activity['activity_type'] != activity_type:
                        continue
                        
                    if user_id and activity['user_id'] != user_id:
                        continue
                        
                    activities.append(activity)
                    
                    if len(activities) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
                    
        return activities
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return []