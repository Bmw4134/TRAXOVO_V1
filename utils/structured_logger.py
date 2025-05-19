"""
Structured Logger

This module provides unified logging functionality across the application,
with consistent formatting, levels, and output destinations.
"""

import os
import logging
import json
from datetime import datetime
import traceback
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# Ensure log directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logger with colored output and file handler
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output based on log level"""
    
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[41m\033[97m' # White on Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            log_message = f"{self.COLORS[record.levelname]}{log_message}{self.RESET}"
        return log_message

# Configure a custom JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format"""
    
    def format(self, record):
        # Create a structured log record
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def get_logger(name, enable_console=True):
    """
    Get a configured logger instance with both file and console handlers.
    
    Args:
        name (str): Name of the logger, usually __name__ of the module
        enable_console (bool): Whether to enable console output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # Remove existing handlers (to avoid duplicates if called multiple times)
    if logger.handlers:
        logger.handlers = []
    
    # Create formatter
    console_formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # JSON formatter for file logging
    json_formatter = JsonFormatter()
    
    # Create console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        f"logs/{name.replace('.', '_')}.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5              # Keep 5 backup files
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Create a separate handler for errors
    error_handler = RotatingFileHandler(
        "logs/error.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5              # Keep 5 backup files
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)
    
    return logger


# Pre-configured loggers for different subsystems
def get_pipeline_logger():
    """Get logger specifically configured for data pipeline operations"""
    return get_logger("pipeline")


def get_api_logger():
    """Get logger specifically configured for API endpoint operations"""
    return get_logger("api")


def get_trend_logger():
    """Get logger specifically configured for trend analysis operations"""
    return get_logger("trend_analysis")


def get_billing_logger():
    """Get logger specifically configured for billing operations"""
    return get_logger("billing")


# Simple log viewing function to display logs from a file
def get_log_entries(log_file="error.log", max_entries=100, level=None):
    """
    Get log entries from a log file.
    
    Args:
        log_file (str): Name of the log file to read (relative to logs directory)
        max_entries (int): Maximum number of entries to return
        level (str): Filter by log level (INFO, ERROR, etc.)
        
    Returns:
        list: List of parsed log entries
    """
    entries = []
    
    try:
        with open(f"logs/{log_file}", "r") as f:
            for line in f:
                try:
                    # Parse JSON log entry
                    entry = json.loads(line.strip())
                    
                    # Apply level filter if specified
                    if level and entry.get('level') != level:
                        continue
                    
                    entries.append(entry)
                    
                    # Limit to max entries
                    if len(entries) >= max_entries:
                        break
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
                    
        # Return most recent entries first
        return list(reversed(entries))
    except FileNotFoundError:
        return []