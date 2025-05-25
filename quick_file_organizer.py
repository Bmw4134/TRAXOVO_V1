"""
Quick File Organizer for Weekly Report Files

This script quickly organizes CSV and Excel files by type for weekly reporting needs.
"""

import os
import shutil
import re
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main file categories needed for reporting
FILE_CATEGORIES = {
    'driving_history': ['DrivingHistory', 'driving', 'history'],
    'activity_detail': ['ActivityDetail', 'activity'],
    'assets_time': ['AssetsTimeOnSite', 'assets', 'time', 'site'],
    'daily_usage': ['DailyUsage', 'daily']
}

def extract_date_from_filename(filename):
    """Extract date from filename using patterns"""
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
        r'_(\d{8})_',  # _YYYYMMDD_
        r'MAY[-_ ](\d{1,2})',  # MAY DD
        r'(\d{2})[-_\.](\d{2})[-_\.](\d{4})',  # MM-DD-YYYY with separators
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if pattern == r'(\d{4}-\d{2}-\d{2})':
                    return match.group(1)
                elif pattern == r'(\d{2}-\d{2}-\d{4})':
                    parts = match.group(1).split('-')
                    return f"{parts[2]}-{parts[0]}-{parts[1]}"
                elif pattern == r'MAY[-_ ](\d{1,2})':
                    day = match.group(1).zfill(2)
                    return f"2025-05-{day}"
                elif pattern == r'(\d{2})[-_\.](\d{2})[-_\.](\d{4})':
                    m, d, y = match.groups()
                    return f"{y}-{m}-{d}"
                else:
                    return None
            except:
                continue
    return None

def categorize_file(filename):
    """Determine file category based on filename"""
    for category, keywords in FILE_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in filename.lower():
                return category
    return "uncategorized"

def organize_weekly_files():
    """Organize files relevant for weekly reports into folders by type and date"""
    source_dir = "attached_assets"
    target_dir = "weekly_report_files"
    
    # Create the target directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Create directories for each category
    for category in FILE_CATEGORIES.keys():
        os.makedirs(os.path.join(target_dir, category), exist_ok=True)
    
    # Organize files by type
    organized_files = 0
    for file in os.listdir(source_dir):
        if file.endswith(('.csv', '.xlsx', '.xls')):
            # Skip some known non-report files
            if "EQMO" in file or "BILLING" in file:
                continue
                
            file_path = os.path.join(source_dir, file)
            category = categorize_file(file)
            date = extract_date_from_filename(file)
            
            if category != "uncategorized":
                target_path = os.path.join(target_dir, category, file)
                shutil.copy2(file_path, target_path)
                organized_files += 1
                logger.info(f"Copied {file} to {category}" + (f" (Date: {date})" if date else ""))
    
    # Create a summary file
    with open(os.path.join(target_dir, "report_files_summary.txt"), "w") as f:
        f.write(f"Weekly Report Files Organized: {organized_files}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Files by category:\n")
        for category in FILE_CATEGORIES.keys():
            category_dir = os.path.join(target_dir, category)
            if os.path.exists(category_dir):
                files = os.listdir(category_dir)
                f.write(f"- {category}: {len(files)} files\n")
                for file in files:
                    f.write(f"  - {file}\n")
    
    print(f"\nOrganized {organized_files} weekly report files into {target_dir}")
    print("Categories created:")
    for category in FILE_CATEGORIES.keys():
        category_dir = os.path.join(target_dir, category)
        if os.path.exists(category_dir):
            print(f"- {category}: {len(os.listdir(category_dir))} files")
    
    print(f"\nSee {os.path.join(target_dir, 'report_files_summary.txt')} for details")

if __name__ == "__main__":
    organize_weekly_files()