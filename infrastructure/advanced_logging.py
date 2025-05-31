"""
TRAXOVO Advanced Logging Framework
Cost-optimized structured logging with rotation and performance monitoring
"""

import logging
import logging.handlers
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
import psutil
from collections import defaultdict, deque

class PerformanceMetrics:
    """Real-time performance tracking for cost optimization"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.error_count = defaultdict(int)
        self.api_calls = defaultdict(int)
        self.memory_usage = deque(maxlen=100)
        self.cpu_usage = deque(maxlen=100)
        self._lock = threading.Lock()
        
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record request performance metrics"""
        with self._lock:
            self.request_times.append({
                'endpoint': endpoint,
                'duration': duration,
                'status_code': status_code,
                'timestamp': datetime.now()
            })
            
            if status_code >= 400:
                self.error_count[endpoint] += 1
    
    def record_api_call(self, service: str, success: bool):
        """Record external API call metrics"""
        with self._lock:
            self.api_calls[f"{service}_{'success' if success else 'failure'}"] += 1
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        with self._lock:
            self.memory_usage.append({
                'percent': psutil.virtual_memory().percent,
                'timestamp': datetime.now()
            })
            self.cpu_usage.append({
                'percent': psutil.cpu_percent(),
                'timestamp': datetime.now()
            })
    
    def get_metrics_summary(self) -> Dict:
        """Get performance metrics summary"""
        with self._lock:
            recent_requests = [r for r in self.request_times 
                             if r['timestamp'] > datetime.now() - timedelta(minutes=5)]
            
            avg_response_time = (sum(r['duration'] for r in recent_requests) / 
                               len(recent_requests)) if recent_requests else 0
            
            return {
                'avg_response_time_5min': round(avg_response_time, 3),
                'total_requests': len(self.request_times),
                'error_rate': sum(self.error_count.values()) / max(len(self.request_times), 1),
                'api_calls': dict(self.api_calls),
                'memory_usage': self.memory_usage[-1]['percent'] if self.memory_usage else 0,
                'cpu_usage': self.cpu_usage[-1]['percent'] if self.cpu_usage else 0,
                'timestamp': datetime.now().isoformat()
            }

class TRAXOVOLogger:
    """Advanced logging system with cost optimization and structured output"""
    
    def __init__(self, log_level=logging.INFO):
        self.metrics = PerformanceMetrics()
        self.log_dir = "logs"
        self.ensure_log_directory()
        self.setup_loggers(log_level)
        self.start_metrics_thread()
    
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def setup_loggers(self, log_level):
        """Setup multiple specialized loggers"""
        
        # Main application logger
        self.app_logger = logging.getLogger('traxovo.app')
        self.app_logger.setLevel(log_level)
        
        # API performance logger
        self.api_logger = logging.getLogger('traxovo.api')
        self.api_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('traxovo.errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Security logger
        self.security_logger = logging.getLogger('traxovo.security')
        self.security_logger.setLevel(logging.WARNING)
        
        # Setup handlers with rotation for cost control
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup rotating file handlers to control log size and costs"""
        
        # Custom formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # App logs (rotating, 10MB max, keep 5 files)
        app_handler = logging.handlers.RotatingFileHandler(
            f"{self.log_dir}/traxovo_app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        app_handler.setFormatter(formatter)
        self.app_logger.addHandler(app_handler)
        
        # API performance logs (smaller rotation for cost control)
        api_handler = logging.handlers.RotatingFileHandler(
            f"{self.log_dir}/traxovo_api.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3
        )
        api_handler.setFormatter(formatter)
        self.api_logger.addHandler(api_handler)
        
        # Error logs (keep longer for debugging)
        error_handler = logging.handlers.RotatingFileHandler(
            f"{self.log_dir}/traxovo_errors.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10
        )
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        
        # Security logs (minimal rotation)
        security_handler = logging.handlers.RotatingFileHandler(
            f"{self.log_dir}/traxovo_security.log",
            maxBytes=2*1024*1024,   # 2MB
            backupCount=5
        )
        security_handler.setFormatter(formatter)
        self.security_logger.addHandler(security_handler)
        
        # Console handler for development
        if os.environ.get('FLASK_ENV') == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.app_logger.addHandler(console_handler)
    
    def start_metrics_thread(self):
        """Start background thread for system metrics collection"""
        def metrics_worker():
            while True:
                try:
                    self.metrics.update_system_metrics()
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    self.error_logger.error(f"Metrics collection failed: {e}")
                    time.sleep(60)
        
        metrics_thread = threading.Thread(target=metrics_worker, daemon=True)
        metrics_thread.start()
    
    def log_request(self, endpoint: str, method: str, duration: float, 
                   status_code: int, user_id: str = None):
        """Log HTTP request with performance metrics"""
        self.metrics.record_request(endpoint, duration, status_code)
        
        log_data = {
            'endpoint': endpoint,
            'method': method,
            'duration': duration,
            'status_code': status_code,
            'user_id': user_id
        }
        
        if status_code >= 400:
            self.api_logger.error(f"Request failed: {json.dumps(log_data)}")
        else:
            self.api_logger.info(f"Request: {json.dumps(log_data)}")
    
    def log_gauge_api_call(self, success: bool, response_time: float, 
                          asset_count: int = None, error: str = None):
        """Log GAUGE API interactions with cost tracking"""
        self.metrics.record_api_call('gauge', success)
        
        log_data = {
            'service': 'gauge_api',
            'success': success,
            'response_time': response_time,
            'asset_count': asset_count,
            'error': error
        }
        
        if success:
            self.api_logger.info(f"GAUGE API success: {json.dumps(log_data)}")
        else:
            self.error_logger.error(f"GAUGE API failure: {json.dumps(log_data)}")
    
    def log_authentication(self, user_id: str, action: str, success: bool, 
                          ip_address: str = None):
        """Log authentication events for security monitoring"""
        log_data = {
            'user_id': user_id,
            'action': action,
            'success': success,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.security_logger.info(f"Auth success: {json.dumps(log_data)}")
        else:
            self.security_logger.warning(f"Auth failure: {json.dumps(log_data)}")
    
    def log_background_task(self, task_name: str, status: str, 
                           duration: float = None, error: str = None):
        """Log background task execution"""
        log_data = {
            'task_name': task_name,
            'status': status,
            'duration': duration,
            'error': error
        }
        
        if status == 'failed':
            self.error_logger.error(f"Background task failed: {json.dumps(log_data)}")
        else:
            self.app_logger.info(f"Background task: {json.dumps(log_data)}")
    
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        metrics = self.metrics.get_metrics_summary()
        
        # Add log file sizes for cost monitoring
        log_sizes = {}
        for log_file in os.listdir(self.log_dir):
            if log_file.endswith('.log'):
                path = os.path.join(self.log_dir, log_file)
                log_sizes[log_file] = os.path.getsize(path)
        
        return {
            'performance_metrics': metrics,
            'log_file_sizes': log_sizes,
            'total_log_size_mb': sum(log_sizes.values()) / (1024 * 1024),
            'generated_at': datetime.now().isoformat()
        }

# Global logger instance
traxovo_logger = TRAXOVOLogger()

def log_request_middleware(app):
    """Flask middleware for automatic request logging"""
    
    @app.before_request
    def before_request():
        from flask import request
        request._start_time = time.time()
    
    @app.after_request
    def after_request(response):
        from flask import request
        
        duration = time.time() - getattr(request, '_start_time', time.time())
        user_id = getattr(request, 'user_id', None)
        
        traxovo_logger.log_request(
            endpoint=request.endpoint or request.path,
            method=request.method,
            duration=duration,
            status_code=response.status_code,
            user_id=user_id
        )
        
        return response
    
    return app

def get_logger(name: str = 'traxovo.app'):
    """Get a configured logger instance"""
    return logging.getLogger(name)