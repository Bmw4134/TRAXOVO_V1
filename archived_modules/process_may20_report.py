#!/usr/bin/env python3
"""
Process May 20 Report

This script is a one-time execution script to process the May 20 report.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function
    """
    logger.info("Starting process for May 20 report")
    
    # Target date
    target_date = '2025-05-20'
    
    # Run auto daily report script
    logger.info(f"Running auto daily report for {target_date}")
    os.system(f"python auto_daily_report.py {target_date}")
    
    logger.info("Process completed")

if __name__ == "__main__":
    main()
