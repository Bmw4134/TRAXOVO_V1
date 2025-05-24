"""
TRAXORA Fleet Management System - Kaizen Sync History

This module provides utilities for tracking and managing sync history
between routes and templates.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

def get_history_path():
    """
    Get the path to the sync history file.
    
    Returns:
        str: Path to the sync history file
    """
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kaizen_sync_history.json')

def add_history_entry(entry_type, status, message, details=None):
    """
    Add an entry to the sync history.
    
    Args:
        entry_type (str): Type of entry (e.g., 'template_sync', 'route_sync')
        status (str): Status of the entry (e.g., 'success', 'warning', 'error')
        message (str): Message describing the entry
        details (dict, optional): Additional details about the entry
        
    Returns:
        str: ID of the new entry
    """
    try:
        # Ensure directory exists
        history_path = get_history_path()
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        # Load existing history or create new one
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
        else:
            history = {'entries': []}
            
        # Create new entry
        entry_id = str(uuid.uuid4())
        entry = {
            'id': entry_id,
            'timestamp': datetime.now().isoformat(),
            'type': entry_type,
            'status': status,
            'message': message
        }
        
        if details:
            entry['details'] = details
            
        # Add entry to history
        history['entries'].insert(0, entry)
        
        # Write history to file
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
            
        logger.info(f"Added sync history entry: {entry_type} - {status} - {message}")
        return entry_id
    except Exception as e:
        logger.error(f"Failed to add sync history entry: {str(e)}")
        return None

def get_history(limit=20):
    """
    Get the sync history.
    
    Args:
        limit (int, optional): Maximum number of entries to return
        
    Returns:
        list: List of history entries
    """
    try:
        # Load history if it exists
        history_path = get_history_path()
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
                
            # Get entries with limit
            entries = history.get('entries', [])
            if limit is not None and limit > 0:
                entries = entries[:limit]
                
            return entries
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to get sync history: {str(e)}")
        return []

def get_history_entry(entry_id):
    """
    Get a specific history entry.
    
    Args:
        entry_id (str): ID of the entry to get
        
    Returns:
        dict: History entry or None if not found
    """
    try:
        # Load history if it exists
        history_path = get_history_path()
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
                
            # Find entry with ID
            for entry in history.get('entries', []):
                if entry.get('id') == entry_id:
                    return entry
                    
        return None
    except Exception as e:
        logger.error(f"Failed to get sync history entry: {str(e)}")
        return None

def clear_history_entries():
    """
    Clear all history entries.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create empty history
        history_path = get_history_path()
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        with open(history_path, 'w') as f:
            json.dump({'entries': []}, f, indent=2)
            
        logger.info("Cleared sync history")
        return True
    except Exception as e:
        logger.error(f"Failed to clear sync history: {str(e)}")
        return False