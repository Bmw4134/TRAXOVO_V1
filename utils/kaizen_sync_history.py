"""
TRAXORA Fleet Management System - Kaizen Sync History

This module tracks the history of all sync-related activities,
including template generation, sync tests, and auto-patching operations.
"""

import os
import logging
import json
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread lock for file access
_lock = threading.Lock()

class SyncHistory:
    """Kaizen sync history manager"""
    
    HISTORY_FILE = os.path.join('logs', 'kaizen_sync_history.json')
    
    @staticmethod
    def add_entry(event_type, blueprint=None, endpoint=None, details=None, status='success'):
        """
        Add a new entry to the sync history
        
        Args:
            event_type (str): Type of event (e.g., 'sync_test', 'auto_patch', 'template_generation')
            blueprint (str, optional): Name of the affected blueprint
            endpoint (str, optional): Name of the affected endpoint
            details (dict, optional): Additional event details
            status (str, optional): Event status ('success', 'warning', 'error')
            
        Returns:
            dict: The created history entry
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(SyncHistory.HISTORY_FILE), exist_ok=True)
            
            # Create entry
            entry = {
                'id': SyncHistory._generate_id(),
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'blueprint': blueprint,
                'endpoint': endpoint,
                'details': details or {},
                'status': status
            }
            
            # Add entry to history file
            with _lock:
                history = SyncHistory.get_history()
                history.append(entry)
                
                with open(SyncHistory.HISTORY_FILE, 'w') as f:
                    json.dump(history, f, indent=2)
                    
            logger.info(f"Added sync history entry: {event_type} for {blueprint}.{endpoint}")
            return entry
        except Exception as e:
            logger.error(f"Error adding sync history entry: {str(e)}")
            return None
            
    @staticmethod
    def get_history(limit=100, event_type=None, blueprint=None, status=None):
        """
        Get sync history entries with optional filtering
        
        Args:
            limit (int, optional): Maximum number of entries to return
            event_type (str, optional): Filter by event type
            blueprint (str, optional): Filter by blueprint name
            status (str, optional): Filter by status
            
        Returns:
            list: Filtered history entries
        """
        try:
            with _lock:
                if not os.path.exists(SyncHistory.HISTORY_FILE):
                    return []
                    
                with open(SyncHistory.HISTORY_FILE, 'r') as f:
                    try:
                        history = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding JSON from {SyncHistory.HISTORY_FILE}")
                        return []
                    
            # Apply filters
            if event_type:
                history = [entry for entry in history if entry.get('event_type') == event_type]
                
            if blueprint:
                history = [entry for entry in history if entry.get('blueprint') == blueprint]
                
            if status:
                history = [entry for entry in history if entry.get('status') == status]
                
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Apply limit
            return history[:limit]
        except Exception as e:
            logger.error(f"Error getting sync history: {str(e)}")
            return []
            
    @staticmethod
    def get_entry(entry_id):
        """
        Get a specific history entry by ID
        
        Args:
            entry_id (str): ID of the entry to retrieve
            
        Returns:
            dict: The history entry or None if not found
        """
        try:
            history = SyncHistory.get_history(limit=None)
            
            for entry in history:
                if entry.get('id') == entry_id:
                    return entry
                    
            return None
        except Exception as e:
            logger.error(f"Error getting sync history entry: {str(e)}")
            return None
            
    @staticmethod
    def clear_history():
        """
        Clear all sync history entries
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with _lock:
                if os.path.exists(SyncHistory.HISTORY_FILE):
                    os.remove(SyncHistory.HISTORY_FILE)
                    
            logger.info("Cleared sync history")
            return True
        except Exception as e:
            logger.error(f"Error clearing sync history: {str(e)}")
            return False
            
    @staticmethod
    def get_stats():
        """
        Get statistics about the sync history
        
        Returns:
            dict: Statistics about the sync history
        """
        try:
            history = SyncHistory.get_history(limit=None)
            
            # Calculate stats
            stats = {
                'total_entries': len(history),
                'event_types': {},
                'blueprints': {},
                'statuses': {},
                'last_sync_test': None,
                'last_auto_patch': None,
                'last_template_generation': None
            }
            
            for entry in history:
                # Count event types
                event_type = entry.get('event_type')
                if event_type:
                    stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
                    
                # Count blueprints
                blueprint = entry.get('blueprint')
                if blueprint:
                    stats['blueprints'][blueprint] = stats['blueprints'].get(blueprint, 0) + 1
                    
                # Count statuses
                status = entry.get('status')
                if status:
                    stats['statuses'][status] = stats['statuses'].get(status, 0) + 1
                    
                # Track last events
                if event_type == 'sync_test' and (not stats['last_sync_test'] or entry.get('timestamp', '') > stats['last_sync_test'].get('timestamp', '')):
                    stats['last_sync_test'] = entry
                    
                if event_type == 'auto_patch' and (not stats['last_auto_patch'] or entry.get('timestamp', '') > stats['last_auto_patch'].get('timestamp', '')):
                    stats['last_auto_patch'] = entry
                    
                if event_type == 'template_generation' and (not stats['last_template_generation'] or entry.get('timestamp', '') > stats['last_template_generation'].get('timestamp', '')):
                    stats['last_template_generation'] = entry
                    
            return stats
        except Exception as e:
            logger.error(f"Error getting sync history stats: {str(e)}")
            return {}
            
    @staticmethod
    def _generate_id():
        """
        Generate a unique ID for a history entry
        
        Returns:
            str: Unique ID
        """
        import uuid
        return str(uuid.uuid4())