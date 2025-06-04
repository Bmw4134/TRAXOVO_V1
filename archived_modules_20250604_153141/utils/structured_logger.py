"""
Structured Logger

This module provides consistent logging formats across the application with
color-coded log levels and structured metadata for better filtering and analysis.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime

# Configure logging colors
COLORS = {
    'DEBUG': '\033[36m',  # Cyan
    'INFO': '\033[32m',   # Green
    'WARNING': '\033[33m', # Yellow
    'ERROR': '\033[31m',  # Red
    'CRITICAL': '\033[41m\033[37m', # White on Red background
    'RESET': '\033[0m'    # Reset
}

# Ensure logs directory exists
logs_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Define log file paths
SYSTEM_LOG_FILE = os.path.join(logs_dir, 'system.log')
API_LOG_FILE = os.path.join(logs_dir, 'api.log')
PIPELINE_LOG_FILE = os.path.join(logs_dir, 'pipeline.log')
ERROR_LOG_FILE = os.path.join(logs_dir, 'error.log')


class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages based on level."""
    
    def format(self, record):
        """Format log record with color."""
        # Apply color if output is to a terminal
        is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        # Get level name and appropriate color
        levelname = record.levelname
        color = COLORS.get(levelname, COLORS['RESET']) if is_tty else ''
        reset = COLORS['RESET'] if is_tty else ''
        
        # Apply color to level name
        record.levelname_colored = f"{color}{levelname}{reset}"
        
        # Format timestamp if needed
        if not hasattr(record, 'asctime'):
            record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Call the original formatter's format method
        return super().format(record)


class StructuredLogRecord(logging.LogRecord):
    """Custom LogRecord that adds structured metadata."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata = {}


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging with metadata."""
    
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, 
             stacklevel=1, metadata=None):
        """Add metadata to the log record."""
        if metadata is None:
            metadata = {}
        
        # Create or update extra
        extra_dict = {} if extra is None else extra
        extra_dict['metadata'] = metadata
        
        # Add timestamp to metadata
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        
        # Call the parent class's _log method with the updated extra
        super()._log(level, msg, args, exc_info, extra_dict, stack_info, stacklevel)
    
    def debug(self, msg, *args, **kwargs):
        """Log with DEBUG level."""
        metadata = kwargs.pop('metadata', {})
        self._log(logging.DEBUG, msg, args, metadata=metadata, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Log with INFO level."""
        metadata = kwargs.pop('metadata', {})
        self._log(logging.INFO, msg, args, metadata=metadata, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Log with WARNING level."""
        metadata = kwargs.pop('metadata', {})
        self._log(logging.WARNING, msg, args, metadata=metadata, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Log with ERROR level."""
        metadata = kwargs.pop('metadata', {})
        self._log(logging.ERROR, msg, args, metadata=metadata, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Log with CRITICAL level."""
        metadata = kwargs.pop('metadata', {})
        self._log(logging.CRITICAL, msg, args, metadata=metadata, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log with ERROR level including exception information."""
        metadata = kwargs.pop('metadata', {})
        if not metadata.get('exception_traceback') and exc_info:
            metadata['exception_traceback'] = traceback.format_exc()
        self._log(logging.ERROR, msg, args, exc_info=exc_info, metadata=metadata, **kwargs)


# Register the custom logger class
logging.setLoggerClass(StructuredLogger)


class JsonFormatter(logging.Formatter):
    """Format logs as JSON for structured storage and analysis."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            'timestamp': getattr(record, 'asctime', datetime.now().isoformat()),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'filename': record.filename,
            'lineno': record.lineno,
        }
        
        # Add metadata if available
        if hasattr(record, 'metadata') and record.metadata:
            log_data['metadata'] = record.metadata
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': str(record.exc_info[0].__name__),
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


def setup_console_handler(logger, level=logging.INFO):
    """Set up console handler with color formatting."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Define a format with colored level names
    formatter = ColorFormatter(
        '%(levelname_colored)s [%(name)s] %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return console_handler


def setup_file_handler(logger, file_path, level=logging.INFO, json_format=False):
    """Set up file handler with optional JSON formatting."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(level)
    
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return file_handler


def get_system_logger(name='system'):
    """Get a logger for system-wide events."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Only add handlers if they don't exist yet
    if not logger.handlers:
        setup_console_handler(logger, logging.INFO)
        setup_file_handler(logger, SYSTEM_LOG_FILE, logging.DEBUG)
        
        # Add JSON format for error log
        error_handler = setup_file_handler(
            logger, ERROR_LOG_FILE, logging.ERROR, json_format=True
        )
    
    return logger


def get_api_logger(name='api'):
    """Get a logger for API calls and responses."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Only add handlers if they don't exist yet
    if not logger.handlers:
        setup_console_handler(logger, logging.INFO)
        setup_file_handler(logger, API_LOG_FILE, logging.DEBUG)
        
        # Add JSON format for error log
        error_handler = setup_file_handler(
            logger, ERROR_LOG_FILE, logging.ERROR, json_format=True
        )
    
    return logger


def get_pipeline_logger(name='pipeline'):
    """Get a logger for data pipeline operations."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Only add handlers if they don't exist yet
    if not logger.handlers:
        setup_console_handler(logger, logging.INFO)
        setup_file_handler(logger, PIPELINE_LOG_FILE, logging.DEBUG)
        
        # Add JSON format for error log
        error_handler = setup_file_handler(
            logger, ERROR_LOG_FILE, logging.ERROR, json_format=True
        )
    
    return logger


# Initialize root logger
def init_root_logger():
    """Initialize root logger with basic configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Only add handler if it doesn't exist yet
    if not root_logger.handlers:
        setup_console_handler(root_logger, logging.INFO)
    
    return root_logger


# Initialize the root logger
init_root_logger()