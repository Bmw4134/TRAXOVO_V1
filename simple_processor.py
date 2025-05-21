#!/usr/bin/env python3
"""
Simple Data Processor for Driver Reports

This script processes our sample data files directly without the complexity of the full
unified_data_processor.py module. It generates a report for May 16, 2025.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, time
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Constants for status determination
LATE_THRESHOLD_MINUTES = 15
EARLY_END_THRESHOLD_MINUTES = 30

def process_date(date_str):
    """Process data for a specific date and generate a report"""
    logger.info(f"Processing data for {date_str}")
    
    # Load baseline schedule data
    baseline_file = "data/start_time_job/baseline.csv"
    if not os.path.exists(baseline_file):
        logger.error(f"Baseline file not found: {baseline_file}")
        return None
    
    schedule_df = pd.read_csv(baseline_file)
    
    # Load driving history data
    driving_file = f"data/driving_history/driving_history_{date_str}.csv"
    if not os.path.exists(driving_file):
        logger.error(f"Driving history file not found: {driving_file}")
        return None
    
    driving_df = pd.read_csv(driving_file)
    
    # Load activity detail data
    activity_file = f"data/activity_detail/activity_detail_{date_str}.csv"
    if not os.path.exists(activity_file):
        logger.error(f"Activity detail file not found: {activity_file}")
        return None
    
    activity_df = pd.read_csv(activity_file)
    
    # Load assets onsite data
    assets_file = f"data/assets_time_on_site/assets_onsite_{date_str}.csv"
    if not os.path.exists(assets_file):
        logger.error(f"Assets onsite file not found: {assets_file}")
        return None
    
    assets_df = pd.read_csv(assets_file)
    
    # Process data and generate report
    drivers_data = []
    late_count = 0
    early_end_count = 0
    not_on_job_count = 0
    on_time_count = 0
    
    for _, schedule_row in schedule_df.iterrows():
        driver_name = schedule_row['driver_name']
        asset_id = schedule_row['asset_id']
        job_site = schedule_row['job_site']
        
        # Parse scheduled times
        scheduled_start = datetime.strptime(schedule_row['scheduled_start'], '%I:%M %p').time()
        scheduled_end = datetime.strptime(schedule_row['scheduled_end'], '%I:%M %p').time()
        
        # Find driver's data in driving history
        driver_driving = driving_df[driving_df['Driver'] == driver_name]
        
        # Default values
        actual_start = None
        actual_end = None
        location = "Unknown"
        status = "Unknown"
        status_reason = ""
        
        # Get key on/off times from driving history
        if not driver_driving.empty:
            key_on_records = driver_driving[driver_driving['EventType'] == 'Key On']
            key_off_records = driver_driving[driver_driving['EventType'] == 'Key Off']
            
            if not key_on_records.empty:
                actual_start = pd.to_datetime(key_on_records.iloc[0]['DateTime'])
                location = key_on_records.iloc[0]['Location']
            
            if not key_off_records.empty:
                actual_end = pd.to_datetime(key_off_records.iloc[0]['DateTime'])
        
        # Determine status
        if actual_start is None:
            status = "Not On Job"
            status_reason = "No activity detected"
            not_on_job_count += 1
        else:
            # Check for location match
            correct_location = location in job_site or job_site in location
            
            if not correct_location:
                status = "Not On Job"
                status_reason = f"At incorrect location: {location}"
                not_on_job_count += 1
            else:
                # Check for late arrival
                actual_start_time = actual_start.time()
                minutes_late = (actual_start_time.hour * 60 + actual_start_time.minute) - (scheduled_start.hour * 60 + scheduled_start.minute)
                
                if minutes_late > LATE_THRESHOLD_MINUTES:
                    status = "Late"
                    status_reason = f"{minutes_late} minutes late"
                    late_count += 1
                elif actual_end is not None:
                    # Check for early end
                    actual_end_time = actual_end.time()
                    minutes_early = (scheduled_end.hour * 60 + scheduled_end.minute) - (actual_end_time.hour * 60 + actual_end_time.minute)
                    
                    if minutes_early > EARLY_END_THRESHOLD_MINUTES:
                        status = "Early End"
                        status_reason = f"{minutes_early} minutes early"
                        early_end_count += 1
                    else:
                        status = "On Time"
                        on_time_count += 1
                else:
                    status = "On Time"
                    on_time_count += 1
        
        # Format display times
        actual_start_display = actual_start.strftime('%I:%M %p') if actual_start else "N/A"
        actual_end_display = actual_end.strftime('%I:%M %p') if actual_end else "N/A"
        
        # Add to drivers data
        driver_data = {
            'driver_name': driver_name,
            'asset_id': asset_id,
            'job_site': job_site,
            'scheduled_start': schedule_row['scheduled_start'],
            'scheduled_end': schedule_row['scheduled_end'],
            'actual_start': actual_start_display,
            'actual_end': actual_end_display,
            'status': status,
            'status_reason': status_reason
        }
        
        drivers_data.append(driver_data)
    
    # Create final report
    report = {
        'date': date_str,
        'drivers': drivers_data,
        'summary': {
            'total': len(drivers_data),
            'late': late_count,
            'early_end': early_end_count,
            'not_on_job': not_on_job_count,
            'on_time': on_time_count
        }
    }
    
    return report

def main():
    """Main function"""
    date_str = '2025-05-16'
    report = process_date(date_str)
    
    if report:
        # Create output directory
        output_dir = Path('reports/daily_drivers')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export directory for web interface compatibility
        export_dir = Path('exports/daily_reports')
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON to both locations
        with open(output_dir / f'daily_report_{date_str}.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        # Also save to exports directory for web interface
        with open(export_dir / f'daily_report_{date_str}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save as Excel to both locations
        df = pd.DataFrame(report['drivers'])
        df.to_excel(output_dir / f'daily_report_{date_str}.xlsx', index=False)
        df.to_excel(export_dir / f'daily_report_{date_str}.xlsx', index=False)
        
        # Generate PDF using our new PDF generator
        try:
            from utils.pdf_generator import generate_driver_report_pdf
            pdf_path = generate_driver_report_pdf(date_str)
            if pdf_path:
                logger.info(f"PDF report generated at {pdf_path}")
            else:
                logger.warning("PDF generation failed, please check logs")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
        
        logger.info(f"Report generated for {date_str}")
        logger.info(f"Total drivers: {report['summary']['total']}")
        logger.info(f"Late: {report['summary']['late']}")
        logger.info(f"Early End: {report['summary']['early_end']}")
        logger.info(f"Not On Job: {report['summary']['not_on_job']}")
        logger.info(f"On Time: {report['summary']['on_time']}")
    else:
        logger.error("Failed to generate report")

if __name__ == "__main__":
    main()