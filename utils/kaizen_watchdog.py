"""
TRAXORA Fleet Management System - Kaizen Watchdog

This module provides a file monitoring system that triggers sync tests
when files are modified, ensuring real-time synchronization between
backend routes and frontend UI components.
"""

import os
import logging
import time
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
_observer = None
_watchdog_thread = None
_stop_event = threading.Event()

class KaizenFileHandler(FileSystemEventHandler):
    """File system event handler for Kaizen"""
    
    def __init__(self):
        """Initialize the handler"""
        self.last_triggered = {}
        self.cooldown = 2  # seconds between triggers for the same file
        
    def on_modified(self, event):
        """
        Handle file modification events
        
        Args:
            event: The file system event
        """
        if event.is_directory:
            return
            
        # Check if this is a relevant file
        file_path = event.src_path
        
        # Skip if not a Python file or HTML template
        if not self._is_relevant_file(file_path):
            return
            
        # Check cooldown to avoid multiple triggers for the same file
        current_time = time.time()
        if file_path in self.last_triggered:
            if current_time - self.last_triggered[file_path] < self.cooldown:
                return
                
        self.last_triggered[file_path] = current_time
        
        # Log the event
        logger.info(f"File modified: {file_path}")
        
        # Trigger the appropriate action based on file type
        if file_path.endswith('.py'):
            self._handle_python_file_change(file_path)
        elif file_path.endswith('.html'):
            self._handle_template_file_change(file_path)
            
    def _is_relevant_file(self, file_path):
        """
        Check if a file is relevant for Kaizen
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file is relevant, False otherwise
        """
        # Check file extension
        if not (file_path.endswith('.py') or file_path.endswith('.html')):
            return False
            
        # For Python files, only routes and models are relevant
        if file_path.endswith('.py'):
            file_path_lower = file_path.lower()
            if 'routes' in file_path_lower or 'model' in file_path_lower or 'db' in file_path_lower or 'database' in file_path_lower:
                return True
            return False
            
        # For HTML files, only templates are relevant
        if file_path.endswith('.html'):
            if '/templates/' in file_path:
                return True
            return False
            
        return False
        
    def _handle_python_file_change(self, file_path):
        """
        Handle changes to Python files
        
        Args:
            file_path (str): Path to the modified file
        """
        try:
            # If it's a route file, trigger sync test
            if 'routes' in file_path.lower():
                logger.info(f"Route file modified, triggering sync test: {file_path}")
                self._run_sync_test()
                
            # If it's a model file, check database schema
            if 'model' in file_path.lower() or 'db' in file_path.lower() or 'database' in file_path.lower():
                logger.info(f"Model file modified, checking database schema: {file_path}")
                self._check_database_schema()
        except Exception as e:
            logger.error(f"Error handling Python file change: {str(e)}")
            
    def _handle_template_file_change(self, file_path):
        """
        Handle changes to template files
        
        Args:
            file_path (str): Path to the modified file
        """
        try:
            logger.info(f"Template file modified, checking template integrity: {file_path}")
            self._check_template_integrity(file_path)
        except Exception as e:
            logger.error(f"Error handling template file change: {str(e)}")
            
    def _run_sync_test(self):
        """Run the Kaizen sync test"""
        try:
            import kaizen_sync_tester
            kaizen_sync_tester.run_tests()
            
            # Log to sync history
            try:
                from utils.kaizen_sync_history import SyncHistory
                SyncHistory.add_entry(
                    event_type='sync_test_auto',
                    details={
                        'triggered_by': 'watchdog',
                        'triggered_at': datetime.now().isoformat()
                    }
                )
            except ImportError:
                pass
        except ImportError:
            logger.error("kaizen_sync_tester module not found")
        except Exception as e:
            logger.error(f"Error running sync test: {str(e)}")
            
    def _check_database_schema(self):
        """Check database schema after model changes"""
        try:
            # This would typically use a schema migration tool
            # or database introspection to check schema
            logger.info("Database schema check not implemented yet")
        except Exception as e:
            logger.error(f"Error checking database schema: {str(e)}")
            
    def _check_template_integrity(self, template_path):
        """
        Check template integrity
        
        Args:
            template_path (str): Path to the template file
        """
        try:
            # Parse the template to check for syntax errors
            with open(template_path, 'r') as f:
                template_content = f.read()
                
            # Check for common template issues
            self._check_template_syntax(template_content, template_path)
            
            # Check for broken links
            self._check_template_links(template_content, template_path)
            
            # Log to sync history
            try:
                from utils.kaizen_sync_history import SyncHistory
                SyncHistory.add_entry(
                    event_type='template_check',
                    details={
                        'template_path': template_path,
                        'checked_at': datetime.now().isoformat()
                    }
                )
            except ImportError:
                pass
        except Exception as e:
            logger.error(f"Error checking template integrity: {str(e)}")
            
    def _check_template_syntax(self, content, path):
        """
        Check template syntax
        
        Args:
            content (str): Template content
            path (str): Path to the template file
        """
        # Check for unclosed tags
        open_tags = content.count('{% block')
        close_tags = content.count('{% endblock')
        if open_tags != close_tags:
            logger.warning(f"Template has {open_tags} block tags and {close_tags} endblock tags: {path}")
            
        # Check for unclosed if statements
        open_ifs = content.count('{% if')
        close_ifs = content.count('{% endif')
        if open_ifs != close_ifs:
            logger.warning(f"Template has {open_ifs} if tags and {close_ifs} endif tags: {path}")
            
        # Check for unclosed for loops
        open_fors = content.count('{% for')
        close_fors = content.count('{% endfor')
        if open_fors != close_fors:
            logger.warning(f"Template has {open_fors} for tags and {close_fors} endfor tags: {path}")
            
    def _check_template_links(self, content, path):
        """
        Check template links
        
        Args:
            content (str): Template content
            path (str): Path to the template file
        """
        # Check for url_for calls
        import re
        url_for_matches = re.findall(r"url_for\s*\(\s*['\"]([^'\"]+)['\"]", content)
        
        for match in url_for_matches:
            # Skip external links
            if not '.' in match:
                continue
                
            # Skip static routes
            if match.endswith('.static'):
                continue
                
            # TODO: Check if the endpoint exists
            # This would require access to the Flask app
            pass

def start_watchdog():
    """Start the Kaizen watchdog service"""
    global _observer, _watchdog_thread, _stop_event
    
    if _observer is not None:
        logger.warning("Watchdog already running, stopping first")
        stop_watchdog()
        
    try:
        # Reset the stop event
        _stop_event.clear()
        
        # Create and start the observer in a separate thread
        def run_observer():
            try:
                event_handler = KaizenFileHandler()
                _observer = Observer()
                
                # Watch the routes directory
                routes_dir = os.path.join('.', 'routes')
                if os.path.exists(routes_dir):
                    _observer.schedule(event_handler, routes_dir, recursive=True)
                    logger.info(f"Watching directory: {routes_dir}")
                    
                # Watch the templates directory
                templates_dir = os.path.join('.', 'templates')
                if os.path.exists(templates_dir):
                    _observer.schedule(event_handler, templates_dir, recursive=True)
                    logger.info(f"Watching directory: {templates_dir}")
                    
                # Watch the models directory
                models_dir = os.path.join('.', 'models')
                if os.path.exists(models_dir):
                    _observer.schedule(event_handler, models_dir, recursive=True)
                    logger.info(f"Watching directory: {models_dir}")
                    
                # Start the observer
                _observer.start()
                logger.info("Watchdog started")
                
                # Run until stopped
                while not _stop_event.is_set():
                    time.sleep(1)
                    
                # Stop the observer
                _observer.stop()
                _observer.join()
                logger.info("Watchdog stopped")
            except Exception as e:
                logger.error(f"Error in watchdog thread: {str(e)}")
                
        # Start the observer thread
        _watchdog_thread = threading.Thread(target=run_observer)
        _watchdog_thread.daemon = True
        _watchdog_thread.start()
        
        logger.info("Kaizen watchdog service started")
        
        # Log to sync history
        try:
            from utils.kaizen_sync_history import SyncHistory
            SyncHistory.add_entry(
                event_type='watchdog_start',
                details={
                    'started_at': datetime.now().isoformat()
                }
            )
        except ImportError:
            pass
            
        return True
    except Exception as e:
        logger.error(f"Error starting watchdog: {str(e)}")
        return False
        
def stop_watchdog():
    """Stop the Kaizen watchdog service"""
    global _observer, _watchdog_thread, _stop_event
    
    try:
        # Signal the thread to stop
        if _watchdog_thread is not None and _watchdog_thread.is_alive():
            _stop_event.set()
            
            # Wait for the thread to stop
            _watchdog_thread.join(timeout=5)
            
            # Reset variables
            _observer = None
            _watchdog_thread = None
            
            logger.info("Kaizen watchdog service stopped")
            
            # Log to sync history
            try:
                from utils.kaizen_sync_history import SyncHistory
                SyncHistory.add_entry(
                    event_type='watchdog_stop',
                    details={
                        'stopped_at': datetime.now().isoformat()
                    }
                )
            except ImportError:
                pass
                
            return True
        else:
            logger.warning("Watchdog not running")
            return False
    except Exception as e:
        logger.error(f"Error stopping watchdog: {str(e)}")
        return False
        
def is_watchdog_running():
    """
    Check if the watchdog is running
    
    Returns:
        bool: True if the watchdog is running, False otherwise
    """
    global _watchdog_thread
    
    return _watchdog_thread is not None and _watchdog_thread.is_alive()