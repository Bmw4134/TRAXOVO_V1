"""
TRAXORA Kaizen Watchdog

This module provides a file system monitoring service that watches for changes
to Python and HTML files, automatically running sync tests when changes are detected
to ensure backend/frontend synchronization.
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

# Import Kaizen modules
import kaizen_sync_tester
from utils.kaizen_integrity_audit import run_integrity_audit

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state to track last run time to prevent duplicate runs
last_sync_test_time = 0
last_integrity_audit_time = 0
COOLDOWN_PERIOD = 5  # seconds between runs

class KaizenFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler for monitoring file changes and
    triggering synchronization tests.
    """
    
    def __init__(self, app_root='.'):
        """
        Initialize the file handler with the application root directory.
        
        Args:
            app_root (str): Root directory of the application
        """
        self.app_root = Path(app_root)
        self.sync_lock = threading.Lock()
        self.audit_lock = threading.Lock()
        
    def _should_ignore(self, path):
        """
        Check if a path should be ignored.
        
        Args:
            path (str): File path
            
        Returns:
            bool: True if the path should be ignored
        """
        # Ignore static files, temp files, and non-Python/HTML files
        ignore_patterns = [
            '__pycache__', 
            '.git', 
            'static/assets',
            'node_modules',
            '.pytest_cache',
            '.vscode',
            '.idea',
            '.DS_Store'
        ]
        
        path_str = str(path).lower()
        
        # Check ignore patterns
        if any(pattern in path_str for pattern in ignore_patterns):
            return True
            
        # Only care about Python and HTML files
        if not path_str.endswith(('.py', '.html')):
            return True
            
        return False
        
    def on_any_event(self, event):
        """
        Handle any file system event.
        
        Args:
            event: Watchdog event
        """
        # Skip directories and ignored files
        if event.is_directory or self._should_ignore(event.src_path):
            return
            
        # Only care about file creation and modification
        if isinstance(event, (FileCreatedEvent, FileModifiedEvent)):
            # Log the change
            logger.info(f"Detected change in {event.src_path}")
            
            # Run the appropriate test based on file type
            path = event.src_path.lower()
            
            if path.endswith('.py'):
                # Python file changed (routes, controllers, models)
                self.trigger_sync_test()
                
                # Check if it's a model or database file
                if 'model' in path or 'db' in path or 'database' in path:
                    self.trigger_integrity_audit()
            
            elif path.endswith('.html'):
                # HTML file changed (templates)
                self.trigger_sync_test()
                
    def trigger_sync_test(self):
        """
        Trigger a sync test with cooldown period to avoid duplicate runs.
        """
        global last_sync_test_time
        current_time = time.time()
        
        # Check if we're in the cooldown period
        if current_time - last_sync_test_time < COOLDOWN_PERIOD:
            logger.debug("Skipping sync test due to cooldown period")
            return
            
        # Acquire lock to ensure only one sync test runs at a time
        if self.sync_lock.acquire(blocking=False):
            try:
                logger.info("Running sync test...")
                last_sync_test_time = current_time
                
                # Run the sync test
                kaizen_sync_tester.run_tests()
                
                logger.info("Sync test completed")
            except Exception as e:
                logger.error(f"Error running sync test: {str(e)}")
            finally:
                self.sync_lock.release()
        else:
            logger.debug("Sync test already running, skipping")
    
    def trigger_integrity_audit(self):
        """
        Trigger an integrity audit with cooldown period to avoid duplicate runs.
        """
        global last_integrity_audit_time
        current_time = time.time()
        
        # Check if we're in the cooldown period
        if current_time - last_integrity_audit_time < COOLDOWN_PERIOD * 3:  # Longer cooldown for audits
            logger.debug("Skipping integrity audit due to cooldown period")
            return
            
        # Acquire lock to ensure only one audit runs at a time
        if self.audit_lock.acquire(blocking=False):
            try:
                logger.info("Running integrity audit...")
                last_integrity_audit_time = current_time
                
                # Run the integrity audit
                run_integrity_audit()
                
                logger.info("Integrity audit completed")
            except Exception as e:
                logger.error(f"Error running integrity audit: {str(e)}")
            finally:
                self.audit_lock.release()
        else:
            logger.debug("Integrity audit already running, skipping")


class KaizenWatchdog:
    """
    Watchdog service for monitoring file changes and triggering synchronization tests.
    """
    
    def __init__(self, app_root='.'):
        """
        Initialize the watchdog service with the application root directory.
        
        Args:
            app_root (str): Root directory of the application
        """
        self.app_root = Path(app_root)
        self.event_handler = KaizenFileHandler(app_root)
        self.observer = Observer()
        
    def start(self):
        """
        Start the watchdog service.
        """
        logger.info(f"Starting Kaizen Watchdog monitoring {self.app_root}")
        
        # Start watching the application directory
        self.observer.schedule(self.event_handler, str(self.app_root), recursive=True)
        self.observer.start()
        
        # Run an initial sync test and integrity audit
        self.event_handler.trigger_sync_test()
        self.event_handler.trigger_integrity_audit()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """
        Stop the watchdog service.
        """
        logger.info("Stopping Kaizen Watchdog")
        self.observer.stop()
        self.observer.join()


def start_watchdog_service(app_root='.'):
    """
    Start the Kaizen Watchdog service in a background thread.
    
    Args:
        app_root (str): Root directory of the application
    """
    logger.info("Starting Kaizen Watchdog service...")
    
    # Create and start the watchdog in a daemon thread
    watchdog = KaizenWatchdog(app_root)
    
    thread = threading.Thread(target=watchdog.start, daemon=True)
    thread.start()
    
    return thread


if __name__ == '__main__':
    # When run directly, start the watchdog service
    app_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    watchdog = KaizenWatchdog(app_root)
    watchdog.start()