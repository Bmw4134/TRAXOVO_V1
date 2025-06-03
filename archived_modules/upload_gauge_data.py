#!/usr/bin/env python3
"""
TRAXORA File Upload Processor

This script helps users upload and organize their GAUGE API data files
for the weekly driver report generator.
"""

import os
import sys
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define file types and their identification patterns
FILE_TYPES = {
    'driving_history': ['drivinghistory', 'driving_history', 'driving history'],
    'activity_detail': ['activitydetail', 'activity_detail', 'activity detail'],
    'assets_on_site': ['assetstimeonsite', 'assets_time_on_site', 'assets time on site'],
    'speeding_report': ['speedingreport', 'speeding_report', 'speeding report'],
    'timecard': ['timecard', 'time_card', 'timecards'],
    'quantities': ['quantities', 'quantity', 'quant']
}

def identify_file_type(filename):
    """Identify file type based on filename patterns"""
    filename_lower = filename.lower()
    
    for file_type, patterns in FILE_TYPES.items():
        if any(pattern in filename_lower.replace(' ', '') for pattern in patterns):
            return file_type
    
    return 'unknown'

def process_downloaded_files(download_dir, upload_dir):
    """Process downloaded files and organize them in the upload directory"""
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Check if download directory exists
    if not os.path.exists(download_dir):
        logger.error(f"Download directory '{download_dir}' not found")
        return
    
    # Process each file in the download directory
    processed_files = {file_type: [] for file_type in FILE_TYPES.keys()}
    processed_files['unknown'] = []
    
    for filename in os.listdir(download_dir):
        file_path = os.path.join(download_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Identify file type
        file_type = identify_file_type(filename)
        
        # Copy file to upload directory with categorized name
        if file_type != 'unknown':
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_filename = f"{file_type.upper()}_{timestamp}_{filename}"
        else:
            new_filename = filename
        
        new_file_path = os.path.join(upload_dir, new_filename)
        try:
            shutil.copy2(file_path, new_file_path)
            processed_files[file_type].append({
                'original_name': filename,
                'new_name': new_filename,
                'path': new_file_path
            })
            logger.info(f"Copied {filename} to {new_file_path}")
        except Exception as e:
            logger.error(f"Error copying file {filename}: {e}")
    
    return processed_files

def generate_report_script(processed_files, script_path):
    """Generate a shell script to run the weekly driver report generator"""
    driving_history = processed_files.get('driving_history', [])
    activity_detail = processed_files.get('activity_detail', [])
    assets_on_site = processed_files.get('assets_on_site', [])
    speeding_report = processed_files.get('speeding_report', [])
    timecard = processed_files.get('timecard', [])
    
    # Check if we have the required files
    if not driving_history:
        logger.warning("No driving history files found")
    if not activity_detail:
        logger.warning("No activity detail files found")
    
    # Create script content
    script_content = """#!/bin/bash
# Auto-generated script for TRAXORA weekly driver report generation

# Make script executable
chmod +x weekly_driver_report_generator.py

echo "Starting weekly driver report generation for May 18-24, 2025..."

python weekly_driver_report_generator.py \\
  --start-date 2025-05-18 \\
  --end-date 2025-05-24 \\
"""
    
    # Add driving history files
    if driving_history:
        script_content += f'  --driving-history-path "{driving_history[0]["path"]}" \\\n'
    
    # Add activity detail files
    if activity_detail:
        script_content += f'  --activity-detail-path "{activity_detail[0]["path"]}" \\\n'
    
    # Add assets on site files (if available)
    if assets_on_site:
        script_content += f'  --assets-on-site-path "{assets_on_site[0]["path"]}" \\\n'
    
    # Add speeding report files (if available)
    if speeding_report:
        script_content += f'  --speeding-report-path "{speeding_report[0]["path"]}" \\\n'
    
    # Add timecard files (if available)
    if timecard:
        script_content += f'  --timecard-path "{timecard[0]["path"]}" \\\n'
    
    # Add output directory
    script_content += '  --output-dir "reports/driver_reports"\n\n'
    script_content += 'echo "Weekly report generation complete!"'
    
    # Write script to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    logger.info(f"Generated report script at {script_path}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python upload_gauge_data.py /path/to/downloads")
        return
    
    download_dir = sys.argv[1]
    upload_dir = "uploads"
    
    logger.info(f"Processing files from {download_dir} to {upload_dir}")
    
    processed_files = process_downloaded_files(download_dir, upload_dir)
    if not processed_files:
        logger.error("No files were processed")
        return
    
    # Generate report script
    generate_report_script(processed_files, "run_weekly_report.sh")
    
    logger.info("File processing complete")
    print("\nTo run the weekly report, use the following command:")
    print("./run_weekly_report.sh")

if __name__ == "__main__":
    main()