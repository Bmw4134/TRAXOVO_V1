"""
TRAXOVO Live Deployment Monitor
Real-time error tracking and user interaction logging for production deployment
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, session, g
from functools import wraps
import traceback
import psutil

class DeploymentMonitor:
    def __init__(self, app=None):
        self.app = app
        self.error_log = []
        self.user_interactions = []
        self.performance_metrics = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring with Flask app"""
        app.config.setdefault('MONITOR_ENABLED', True)
        app.config.setdefault('LOG_INTERACTIONS', True)
        app.config.setdefault('PERFORMANCE_TRACKING', True)
        
        # Set up logging
        self.setup_logging()
        
        # Register monitoring hooks
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
        
        # Register error handlers
        app.errorhandler(Exception)(self.handle_exception)
        
        # Add monitoring routes
        app.add_url_rule('/monitor/status', 'monitor_status', self.status_endpoint)
        app.add_url_rule('/monitor/errors', 'monitor_errors', self.errors_endpoint)
        app.add_url_rule('/monitor/interactions', 'monitor_interactions', self.interactions_endpoint)
        app.add_url_rule('/monitor/health', 'monitor_health', self.health_endpoint)
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure deployment logger
        self.logger = logging.getLogger('deployment_monitor')
        self.logger.setLevel(logging.INFO)
        
        # File handler for deployment logs
        file_handler = logging.FileHandler('logs/deployment.log')
        file_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def before_request(self):
        """Track request start time and user context"""
        g.start_time = datetime.now()
        g.user_id = session.get('username', 'anonymous')
        g.session_id = session.get('session_id', 'no-session')
        
        # Log user interaction
        if self.app.config['LOG_INTERACTIONS']:
            interaction = {
                'timestamp': g.start_time.isoformat(),
                'user_id': g.user_id,
                'session_id': g.session_id,
                'method': request.method,
                'url': request.url,
                'endpoint': request.endpoint,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'referrer': request.referrer
            }
            self.user_interactions.append(interaction)
            
            # Keep only last 1000 interactions
            if len(self.user_interactions) > 1000:
                self.user_interactions = self.user_interactions[-1000:]
    
    def after_request(self, response):
        """Track response and performance metrics"""
        if hasattr(g, 'start_time'):
            duration = (datetime.now() - g.start_time).total_seconds()
            
            if self.app.config['PERFORMANCE_TRACKING']:
                metric = {
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'status_code': response.status_code,
                    'duration_seconds': duration,
                    'user_id': g.user_id,
                    'content_length': response.content_length or 0
                }
                self.performance_metrics.append(metric)
                
                # Keep only last 500 metrics
                if len(self.performance_metrics) > 500:
                    self.performance_metrics = self.performance_metrics[-500:]
                
                # Log slow requests
                if duration > 2.0:
                    self.logger.warning(f"Slow request: {request.endpoint} took {duration:.2f}s")
        
        return response
    
    def teardown_request(self, exception=None):
        """Clean up request context"""
        if exception:
            self.log_error(exception, 'Request teardown error')
    
    def handle_exception(self, e):
        """Handle and log all exceptions"""
        self.log_error(e, 'Unhandled exception')
        
        # Return JSON error for API endpoints
        if request.path.startswith('/api/'):
            return {'error': 'Internal server error', 'timestamp': datetime.now().isoformat()}, 500
        
        # Return HTML error page for regular requests
        return f"""
        <h1>Application Error</h1>
        <p>An error occurred. The error has been logged and will be investigated.</p>
        <p>Error ID: {datetime.now().isoformat()}</p>
        <a href="/dashboard">Return to Dashboard</a>
        """, 500
    
    def log_error(self, exception, context=''):
        """Log error with full context"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'context': context,
            'endpoint': getattr(request, 'endpoint', 'unknown'),
            'url': getattr(request, 'url', 'unknown'),
            'method': getattr(request, 'method', 'unknown'),
            'user_id': getattr(g, 'user_id', 'unknown'),
            'session_id': getattr(g, 'session_id', 'unknown'),
            'traceback': traceback.format_exc()
        }
        
        self.error_log.append(error_data)
        
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
        
        # Log to file
        self.logger.error(f"Error in {context}: {exception}", exc_info=True)
    
    def status_endpoint(self):
        """Get overall system status"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(self.error_log),
            'total_interactions': len(self.user_interactions),
            'total_metrics': len(self.performance_metrics),
            'recent_errors': len([e for e in self.error_log if 
                                (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 3600])
        }
    
    def errors_endpoint(self):
        """Get recent errors"""
        return {
            'errors': self.error_log[-20:],  # Last 20 errors
            'total_count': len(self.error_log)
        }
    
    def interactions_endpoint(self):
        """Get recent user interactions"""
        return {
            'interactions': self.user_interactions[-50:],  # Last 50 interactions
            'total_count': len(self.user_interactions)
        }
    
    def health_endpoint(self):
        """Get detailed system health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'available_memory_mb': memory.available / 1024 / 1024
                },
                'application': {
                    'total_errors': len(self.error_log),
                    'recent_errors_1h': len([e for e in self.error_log if 
                                           (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 3600]),
                    'active_sessions': len(set(i.get('session_id') for i in self.user_interactions[-100:])),
                    'avg_response_time': self.get_avg_response_time()
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_avg_response_time(self):
        """Calculate average response time from recent metrics"""
        if not self.performance_metrics:
            return 0
        
        recent_metrics = self.performance_metrics[-100:]
        total_time = sum(m['duration_seconds'] for m in recent_metrics)
        return total_time / len(recent_metrics)

# Monitor decorator for critical functions
def monitor_function(func):
    """Decorator to monitor specific functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logging.info(f"Function {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logging.error(f"Function {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Initialize global monitor instance
monitor = DeploymentMonitor()