#!/usr/bin/env python3
"""
Create May 20 Report

Quick script to create a report for May 20, 2025 using the processed driving history data.
"""

import os
import json
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATA_FILE = 'processed/driving_history_2025-05-20.json'
EXPORT_DIR = Path('exports/daily_reports')
EXPORT_DIR.mkdir(exist_ok=True, parents=True)

def main():
    """Main function to create the May 20 report"""
    try:
        # Load the processed data
        logger.info(f"Loading data from {DATA_FILE}")
        with open(DATA_FILE, 'r') as f:
            drivers = json.load(f)
        
        logger.info(f"Loaded {len(drivers)} driver records")
        
        # Create structured report data
        report_data = {
            'date': '2025-05-20',
            'drivers': drivers,
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': [],
            'total_drivers': len(drivers)
        }
        
        # Standard work hours
        work_start = pd.to_datetime('2025-05-20 07:00:00')
        work_end = pd.to_datetime('2025-05-20 17:00:00')
        
        # Process each driver to identify late starts and early ends
        for driver in drivers:
            first_activity = None
            last_activity = None
            
            # Extract activity times
            if 'first_activity' in driver and driver['first_activity']:
                first_activity = pd.to_datetime(driver['first_activity'])
            
            if 'last_activity' in driver and driver['last_activity']:
                last_activity = pd.to_datetime(driver['last_activity'])
            
            # Check for late start
            if first_activity and first_activity > work_start:
                late_minutes = int((first_activity - work_start).total_seconds() / 60)
                if late_minutes > 10:  # Only count if more than 10 minutes late
                    late_record = {
                        'driver_name': driver['driver_name'],
                        'asset_id': driver.get('asset_id', ''),
                        'late_minutes': late_minutes,
                        'scheduled_start': '07:00',
                        'actual_start': first_activity.strftime('%H:%M'),
                        'job_site': driver.get('locations', '').split(';')[0] if driver.get('locations') else 'Unknown'
                    }
                    report_data['late_start_records'].append(late_record)
            
            # Check for early end
            if last_activity and last_activity < work_end:
                early_minutes = int((work_end - last_activity).total_seconds() / 60)
                if early_minutes > 10:  # Only count if more than 10 minutes early
                    early_record = {
                        'driver_name': driver['driver_name'],
                        'asset_id': driver.get('asset_id', ''),
                        'early_minutes': early_minutes,
                        'scheduled_end': '17:00',
                        'actual_end': last_activity.strftime('%H:%M'),
                        'job_site': driver.get('locations', '').split(';')[0] if driver.get('locations') else 'Unknown'
                    }
                    report_data['early_end_records'].append(early_record)
        
        # Sort records
        report_data['late_start_records'] = sorted(
            report_data['late_start_records'],
            key=lambda x: x.get('late_minutes', 0),
            reverse=True
        )
        
        report_data['early_end_records'] = sorted(
            report_data['early_end_records'],
            key=lambda x: x.get('early_minutes', 0),
            reverse=True
        )
        
        # Update counts
        report_data['late_count'] = len(report_data['late_start_records'])
        report_data['early_count'] = len(report_data['early_end_records'])
        report_data['missing_count'] = len(report_data['not_on_job_records'])
        
        # Calculate on-time percentage
        on_time = report_data['total_drivers'] - report_data['late_count'] - report_data['missing_count']
        report_data['on_time_percent'] = round(100 * on_time / max(1, report_data['total_drivers']), 1)
        
        # Save report data
        json_path = EXPORT_DIR / 'attendance_data_2025-05-20.json'
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        logger.info(f"Saved JSON report to {json_path}")
        
        # Create Excel report
        excel_path = EXPORT_DIR / 'daily_report_2025-05-20.xlsx'
        df_drivers = pd.DataFrame(drivers)
        df_late = pd.DataFrame(report_data['late_start_records']) if report_data['late_start_records'] else pd.DataFrame()
        df_early = pd.DataFrame(report_data['early_end_records']) if report_data['early_end_records'] else pd.DataFrame()
        
        with pd.ExcelWriter(excel_path) as writer:
            df_drivers.to_excel(writer, sheet_name='All Drivers', index=False)
            df_late.to_excel(writer, sheet_name='Late Starts', index=False)
            df_early.to_excel(writer, sheet_name='Early Ends', index=False)
        
        logger.info(f"Saved Excel report to {excel_path}")
        
        # Also save with standardized name for downloads
        std_path = EXPORT_DIR / '2025-05-20_DailyDriverReport.xlsx'
        import shutil
        shutil.copy2(excel_path, std_path)
        logger.info(f"Saved standardized report to {std_path}")
        
        # Generate PDF
        pdf_path = EXPORT_DIR / '2025-05-20_DailyDriverReport.pdf'
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            
            # Set up fonts
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'Daily Driver Report: May 20, 2025', 0, 1, 'C')
            pdf.ln(5)
            
            # Summary section
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"Total Drivers: {report_data['total_drivers']}", 0, 1)
            pdf.cell(0, 10, f"Late Drivers: {report_data['late_count']}", 0, 1)
            pdf.cell(0, 10, f"Early End: {report_data['early_count']}", 0, 1)
            pdf.cell(0, 10, f"On-Time Percentage: {report_data['on_time_percent']}%", 0, 1)
            pdf.ln(5)
            
            # Late drivers section
            if report_data['late_start_records']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Late Drivers', 0, 1)
                
                # Column headers
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(60, 7, 'Driver Name', 1)
                pdf.cell(30, 7, 'Late (min)', 1)
                pdf.cell(25, 7, 'Actual Start', 1)
                pdf.cell(75, 7, 'Job Site', 1)
                pdf.ln()
                
                # Late driver rows
                pdf.set_font('Arial', '', 10)
                for late in report_data['late_start_records'][:10]:  # Show first 10
                    pdf.cell(60, 7, late['driver_name'][:28], 1)
                    pdf.cell(30, 7, str(late['late_minutes']), 1)
                    pdf.cell(25, 7, late['actual_start'], 1)
                    pdf.cell(75, 7, (late['job_site'] or 'Unknown')[:35], 1)
                    pdf.ln()
            
            pdf.save(pdf_path)
            logger.info(f"Saved PDF report to {pdf_path}")
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
        
        logger.info("May 20 report creation complete")
        return True
        
    except Exception as e:
        logger.error(f"Error creating May 20 report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()