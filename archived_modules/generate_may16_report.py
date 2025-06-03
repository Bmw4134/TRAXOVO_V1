#!/usr/bin/env python3
"""
Generate May 16 Report

This script generates the driver attendance report for May 16, 2025,
using our new unified data processor and data files.
"""
import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import our custom modules
sys.path.append('.')
from utils.unified_data_processor import generate_daily_driver_report

def main():
    """Main function to generate the May 16 report"""
    date_str = '2025-05-16'
    logger.info(f"Generating daily driver report for {date_str}")
    
    try:
        # Generate the report using our unified data processor
        report_data = generate_daily_driver_report(date_str)
        
        # Create output directory if it doesn't exist
        output_dir = Path('reports/daily_drivers')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the report as JSON
        with open(output_dir / f'daily_report_{date_str}.json', 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Convert to DataFrame for Excel export
        if 'drivers' in report_data:
            df = pd.DataFrame(report_data['drivers'])
            df.to_excel(output_dir / f'daily_report_{date_str}.xlsx', index=False)
            logger.info(f"Saved report to {output_dir}/daily_report_{date_str}.xlsx")
        
        # Print summary information
        logger.info(f"Report summary: {report_data['summary'] if 'summary' in report_data else 'No summary available'}")
        logger.info(f"Total drivers: {len(report_data['drivers']) if 'drivers' in report_data else 0}")
        
        if 'drivers' in report_data and len(report_data['drivers']) > 0:
            late_count = sum(1 for d in report_data['drivers'] if d.get('status') == 'Late')
            early_end = sum(1 for d in report_data['drivers'] if d.get('status') == 'Early End')
            not_on_job = sum(1 for d in report_data['drivers'] if d.get('status') == 'Not On Job')
            on_time = sum(1 for d in report_data['drivers'] if d.get('status') == 'On Time')
            
            logger.info(f"Late: {late_count}")
            logger.info(f"Early End: {early_end}")
            logger.info(f"Not On Job: {not_on_job}")
            logger.info(f"On Time: {on_time}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()