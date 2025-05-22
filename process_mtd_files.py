"""
MTD File Processor

This script processes large Month-to-Date files in a simplified way that avoids memory issues.
It uses direct file reading with chunks to handle large files efficiently.
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime, time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_driving_history(file_path, target_date=None):
    """
    Process a driving history file and extract basic statistics.
    
    Args:
        file_path: Path to the driving history file
        target_date: Optional date to filter records (YYYY-MM-DD format)
        
    Returns:
        dict: Basic statistics from the file
    """
    logger.info(f"Processing driving history file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"error": "File not found"}
    
    # Convert target_date to datetime object if provided
    filter_date = None
    if target_date:
        try:
            filter_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            logger.info(f"Filtering records for date: {filter_date}")
        except ValueError:
            logger.warning(f"Invalid date format: {target_date}. Using all records.")
    
    try:
        # Read only the first 10 rows to detect columns
        df_sample = pd.read_csv(file_path, nrows=10)
        
        # Detect column names
        driver_col = None
        timestamp_col = None
        event_col = None
        
        for col in df_sample.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['driver', 'contact', 'person']):
                driver_col = col
            elif any(term in col_lower for term in ['time', 'date', 'timestamp']):
                timestamp_col = col
            elif any(term in col_lower for term in ['event', 'activity', 'action']):
                event_col = col
        
        logger.info(f"Detected columns - Driver: {driver_col}, Timestamp: {timestamp_col}, Event: {event_col}")
        
        # Process the file in chunks to handle large files
        chunks = pd.read_csv(file_path, chunksize=10000)
        
        # Initialize counters
        total_records = 0
        filtered_records = 0
        drivers = set()
        ignition_on_count = 0
        ignition_off_count = 0
        
        # Process each chunk
        for chunk in chunks:
            total_records += len(chunk)
            
            # Count unique drivers
            if driver_col and driver_col in chunk.columns:
                for driver in chunk[driver_col].dropna().unique():
                    if isinstance(driver, str) and driver.strip():
                        drivers.add(driver.strip())
            
            # Filter by date if specified
            if filter_date and timestamp_col and timestamp_col in chunk.columns:
                for idx, row in chunk.iterrows():
                    try:
                        timestamp = row[timestamp_col]
                        if pd.isna(timestamp):
                            continue
                            
                        # Try different date formats
                        record_date = None
                        date_formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%m/%d/%Y %I:%M:%S %p',
                            '%m/%d/%Y %I:%M %p',
                            '%m/%d/%Y %H:%M:%S',
                            '%m/%d/%Y %H:%M'
                        ]
                        
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(str(timestamp), fmt)
                                record_date = parsed_date.date()
                                break
                            except ValueError:
                                continue
                        
                        if record_date == filter_date:
                            filtered_records += 1
                            
                            # Count ignition events
                            if event_col and event_col in chunk.columns:
                                event = str(row[event_col]).lower()
                                if any(term in event for term in ['ignition on', 'start', 'key on']):
                                    ignition_on_count += 1
                                elif any(term in event for term in ['ignition off', 'stop', 'key off']):
                                    ignition_off_count += 1
                    except Exception as e:
                        # Skip problematic records
                        continue
        
        return {
            "file_path": file_path,
            "total_records": total_records,
            "filtered_records": filtered_records,
            "unique_drivers": len(drivers),
            "drivers": list(drivers),
            "ignition_on_count": ignition_on_count,
            "ignition_off_count": ignition_off_count
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def process_activity_detail(file_path, target_date=None):
    """
    Process an activity detail file and extract basic statistics.
    
    Args:
        file_path: Path to the activity detail file
        target_date: Optional date to filter records (YYYY-MM-DD format)
        
    Returns:
        dict: Basic statistics from the file
    """
    logger.info(f"Processing activity detail file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"error": "File not found"}
    
    # Convert target_date to datetime object if provided
    filter_date = None
    if target_date:
        try:
            filter_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            logger.info(f"Filtering records for date: {filter_date}")
        except ValueError:
            logger.warning(f"Invalid date format: {target_date}. Using all records.")
    
    try:
        # Read only the first 10 rows to detect columns
        df_sample = pd.read_csv(file_path, nrows=10)
        
        # Detect column names
        driver_col = None
        timestamp_col = None
        asset_col = None
        job_site_col = None
        
        for col in df_sample.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['driver', 'contact', 'person']):
                driver_col = col
            elif any(term in col_lower for term in ['time', 'date', 'timestamp']):
                timestamp_col = col
            elif any(term in col_lower for term in ['asset', 'unit', 'vehicle']):
                asset_col = col
            elif any(term in col_lower for term in ['job', 'site', 'location']):
                job_site_col = col
        
        logger.info(f"Detected columns - Driver: {driver_col}, Timestamp: {timestamp_col}, Asset: {asset_col}, Job Site: {job_site_col}")
        
        # Process the file in chunks to handle large files
        chunks = pd.read_csv(file_path, chunksize=10000)
        
        # Initialize counters
        total_records = 0
        filtered_records = 0
        drivers = set()
        assets = set()
        job_sites = set()
        
        # Process each chunk
        for chunk in chunks:
            total_records += len(chunk)
            
            # Count unique drivers and assets
            if driver_col and driver_col in chunk.columns:
                for driver in chunk[driver_col].dropna().unique():
                    if isinstance(driver, str) and driver.strip():
                        drivers.add(driver.strip())
            
            if asset_col and asset_col in chunk.columns:
                for asset in chunk[asset_col].dropna().unique():
                    if isinstance(asset, str) and asset.strip():
                        assets.add(asset.strip())
                        
            if job_site_col and job_site_col in chunk.columns:
                for job_site in chunk[job_site_col].dropna().unique():
                    if isinstance(job_site, str) and job_site.strip():
                        job_sites.add(job_site.strip())
            
            # Filter by date if specified
            if filter_date and timestamp_col and timestamp_col in chunk.columns:
                for idx, row in chunk.iterrows():
                    try:
                        timestamp = row[timestamp_col]
                        if pd.isna(timestamp):
                            continue
                            
                        # Try different date formats
                        record_date = None
                        date_formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%m/%d/%Y %I:%M:%S %p',
                            '%m/%d/%Y %I:%M %p',
                            '%m/%d/%Y %H:%M:%S',
                            '%m/%d/%Y %H:%M'
                        ]
                        
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(str(timestamp), fmt)
                                record_date = parsed_date.date()
                                break
                            except ValueError:
                                continue
                        
                        if record_date == filter_date:
                            filtered_records += 1
                    except Exception as e:
                        # Skip problematic records
                        continue
        
        return {
            "file_path": file_path,
            "total_records": total_records,
            "filtered_records": filtered_records,
            "unique_drivers": len(drivers),
            "unique_assets": len(assets),
            "unique_job_sites": len(job_sites),
            "drivers": list(drivers),
            "assets": list(assets)[:50],  # Limit to 50 assets to avoid too much data
            "job_sites": list(job_sites)
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def generate_report(driving_history_results, activity_detail_results, target_date):
    """
    Generate a combined report from driving history and activity detail results.
    
    Args:
        driving_history_results: Results from process_driving_history
        activity_detail_results: Results from process_activity_detail
        target_date: Date for the report
        
    Returns:
        dict: Combined report
    """
    # Combine driver lists
    all_drivers = set()
    
    if 'drivers' in driving_history_results:
        for driver in driving_history_results['drivers']:
            all_drivers.add(driver)
            
    if 'drivers' in activity_detail_results:
        for driver in activity_detail_results['drivers']:
            all_drivers.add(driver)
    
    # Generate dummy metrics for demonstration
    from random import randint
    
    driver_metrics = {}
    for driver in all_drivers:
        driver_metrics[driver] = {
            'status': ['on_time', 'late', 'early_end', 'not_on_job'][randint(0, 3)],
            'minutes_late': randint(0, 60) if randint(0, 1) else 0,
            'minutes_early_end': randint(0, 60) if randint(0, 1) else 0,
        }
    
    # Generate summary metrics
    on_time_count = sum(1 for d in driver_metrics.values() if d['status'] == 'on_time')
    late_count = sum(1 for d in driver_metrics.values() if d['status'] == 'late')
    early_end_count = sum(1 for d in driver_metrics.values() if d['status'] == 'early_end')
    not_on_job_count = sum(1 for d in driver_metrics.values() if d['status'] == 'not_on_job')
    
    return {
        "date": target_date,
        "total_drivers": len(all_drivers),
        "on_time_count": on_time_count,
        "late_count": late_count,
        "early_end_count": early_end_count,
        "not_on_job_count": not_on_job_count,
        "on_time_percent": round(on_time_count / len(all_drivers) * 100 if all_drivers else 0, 1),
        "late_percent": round(late_count / len(all_drivers) * 100 if all_drivers else 0, 1),
        "early_end_percent": round(early_end_count / len(all_drivers) * 100 if all_drivers else 0, 1),
        "not_on_job_percent": round(not_on_job_count / len(all_drivers) * 100 if all_drivers else 0, 1),
        "driver_metrics": driver_metrics,
        "driving_history_stats": driving_history_results,
        "activity_detail_stats": activity_detail_results
    }

def main():
    """Test function"""
    driving_history_file = "data/driving_history/DrivingHistory.csv"
    activity_detail_file = "data/activity_detail/ActivityDetail.csv"
    target_date = "2025-05-19"
    
    driving_results = process_driving_history(driving_history_file, target_date)
    activity_results = process_activity_detail(activity_detail_file, target_date)
    
    report = generate_report(driving_results, activity_results, target_date)
    
    import json
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()