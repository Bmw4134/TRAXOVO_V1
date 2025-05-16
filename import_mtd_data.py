"""
MTD Data Import Script

This script imports and processes all MTD reports to populate
historical attendance data and other tracking metrics.

Usage:
    python import_mtd_data.py

"""

import os
import logging
import json
from datetime import datetime
from flask import Flask
from app import db
from utils.data_importer import import_mtd_reports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to import MTD data"""
    try:
        logger.info("Starting MTD data import")
        
        # Path to MTD reports
        reports_dir = 'data/mtd_reports'
        
        # Import all MTD reports
        results = import_mtd_reports(reports_dir)
        
        if results['success']:
            # Log results summary
            summary = {}
            for report_type, report_result in results['results'].items():
                if report_result['success']:
                    summary[report_type] = 'Success'
                    if 'total_records' in report_result:
                        summary[f"{report_type}_records"] = report_result.get('total_records', 0)
                    if 'late_start_count' in report_result:
                        summary[f"{report_type}_late_starts"] = report_result.get('late_start_count', 0)
                    if 'early_end_count' in report_result:
                        summary[f"{report_type}_early_ends"] = report_result.get('early_end_count', 0)
                    if 'not_on_job_count' in report_result:
                        summary[f"{report_type}_not_on_job"] = report_result.get('not_on_job_count', 0)
                else:
                    summary[report_type] = f"Failed: {report_result.get('message', 'Unknown error')}"
            
            logger.info(f"Import summary: {json.dumps(summary, indent=2)}")
            print("\n=== MTD Data Import Summary ===")
            for key, value in summary.items():
                print(f"{key}: {value}")
            print("\nData import completed successfully!")
            
            # Save summary to file
            summary_file = os.path.join('data', f"mtd_import_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"Summary saved to: {summary_file}")
            return True
        else:
            logger.error(f"Import failed: {results.get('message', 'Unknown error')}")
            print(f"\nError: Import failed - {results.get('message', 'Unknown error')}")
            return False
    
    except Exception as e:
        logger.error(f"Error in MTD data import: {e}")
        print(f"\nError: {e}")
        return False

if __name__ == "__main__":
    with Flask(__name__).app_context():
        main()