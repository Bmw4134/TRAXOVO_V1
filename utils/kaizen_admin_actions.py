"""
TRAXORA Fleet Management System - Kaizen Admin Actions

This module provides functionality for tracking and managing admin actions
in the Kaizen Core administration system.
"""

import os
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Constants
ADMIN_ACTIONS_FILE = "data/admin_actions.json"

def get_admin_actions_path():
    """
    Get the path to the admin actions file.
    
    Returns:
        str: Path to the admin actions file
    """
    return ADMIN_ACTIONS_FILE

def ensure_admin_actions_file():
    """
    Ensure the admin actions file exists.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        actions_path = get_admin_actions_path()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(actions_path), exist_ok=True)
        
        # Create file if it doesn't exist
        if not os.path.exists(actions_path):
            with open(actions_path, 'w') as f:
                json.dump({'actions': []}, f)
                
        return True
    except Exception as e:
        logger.error(f"Failed to ensure admin actions file: {str(e)}")
        return False

def add_admin_action(action_type, message, category='system', user='system', status='success', details=None):
    """
    Add an admin action to the history.
    
    Args:
        action_type (str): Type of action
        message (str): Action message
        category (str): Action category (system, template, integrity, sync)
        user (str): User who performed the action
        status (str): Action status (success, warning, error)
        details (dict, optional): Additional details
        
    Returns:
        dict: The added action entry or None if failed
    """
    try:
        # Ensure admin actions file exists
        ensure_admin_actions_file()
        
        # Create admin action entry
        action_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        action_entry = {
            'id': action_id,
            'timestamp': timestamp,
            'action': action_type,
            'message': message,
            'category': category,
            'user': user,
            'status': status,
            'details': details or {}
        }
        
        # Load existing actions
        actions_path = get_admin_actions_path()
        with open(actions_path, 'r') as f:
            actions_data = json.load(f)
            
        # Add new action
        actions_data.setdefault('actions', []).insert(0, action_entry)
        
        # Save actions
        with open(actions_path, 'w') as f:
            json.dump(actions_data, f, indent=2)
            
        logger.info(f"Added admin action: {action_type} - {status} - {message}")
        return action_entry
    except Exception as e:
        logger.error(f"Failed to add admin action: {str(e)}")
        return None

def get_admin_actions(limit=20):
    """
    Get admin actions history.
    
    Args:
        limit (int or None, optional): Maximum number of actions to return.
                                      If None, return all actions.
        
    Returns:
        list: List of action entries
    """
    try:
        # Ensure admin actions file exists
        ensure_admin_actions_file()
        
        # Load actions if they exist
        actions_path = get_admin_actions_path()
        if os.path.exists(actions_path):
            with open(actions_path, 'r') as f:
                actions_data = json.load(f)
                
            # Get actions with limit
            actions = actions_data.get('actions', [])
            if limit is not None and limit > 0:
                actions = actions[:limit]
                
            return actions
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to get admin actions: {str(e)}")
        return []

def get_admin_action(action_id):
    """
    Get a specific admin action entry.
    
    Args:
        action_id (str): ID of the action entry
        
    Returns:
        dict: Action entry or None if not found
    """
    try:
        # Get all actions
        actions = get_admin_actions(limit=None)
        
        # Find the action with the given ID
        for action in actions:
            if action.get('id') == action_id:
                return action
                
        return None
    except Exception as e:
        logger.error(f"Failed to get admin action: {str(e)}")
        return None

def clear_admin_actions():
    """
    Clear all admin actions.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create empty actions file
        actions_path = get_admin_actions_path()
        with open(actions_path, 'w') as f:
            json.dump({'actions': []}, f)
            
        logger.info("Admin actions cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear admin actions: {str(e)}")
        return False