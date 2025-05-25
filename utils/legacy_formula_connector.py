"""
Legacy Formula Connector

This module provides a connection between the new TRAXORA system and
the legacy formula-based workbook logic for driver attendance reporting.
It implements the exact same classification logic and validation steps
to ensure seamless transition and consistent results.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Constants for classification
LATE_START_THRESHOLD = 7.5  # 7:30 AM in decimal hours
EARLY_END_THRESHOLD = 16.0  # 4:00 PM in decimal hours

def process_daily_driver_report(date_str, driving_history_file=None, activity_detail_file=None, assets_time_file=None):
    """
    Process a daily driver report using the legacy workbook formulas
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        driving_history_file (str): Path to driving history CSV file
        activity_detail_file (str): Path to activity detail CSV file
        assets_time_file (str): Path to assets time on site CSV file
        
    Returns:
        dict: Results of processing with success/error status
    """
    try:
        logger.info(f"Processing daily driver report for {date_str}")
        
        # Create directories if they don't exist
        os.makedirs('reports/daily_driver_reports', exist_ok=True)
        os.makedirs('exports/daily', exist_ok=True)
        
        # Load data files
        driving_history_df = None
        activity_detail_df = None
        assets_time_df = None
        
        if driving_history_file and os.path.exists(driving_history_file):
            driving_history_df = pd.read_csv(driving_history_file)
            logger.info(f"Loaded driving history file with {len(driving_history_df)} records")
        else:
            logger.warning("Driving history file not provided or not found")
        
        if activity_detail_file and os.path.exists(activity_detail_file):
            activity_detail_df = pd.read_csv(activity_detail_file)
            logger.info(f"Loaded activity detail file with {len(activity_detail_df)} records")
        else:
            logger.warning("Activity detail file not provided or not found")
        
        if assets_time_file and os.path.exists(assets_time_file):
            assets_time_df = pd.read_csv(assets_time_file)
            logger.info(f"Loaded assets time file with {len(assets_time_df)} records")
        else:
            logger.warning("Assets time file not provided or not found")
        
        # If no data files are provided, create a sample report for demonstration
        if driving_history_df is None and activity_detail_df is None and assets_time_df is None:
            logger.warning("No data files provided, creating demo report")
            result = create_demo_report(date_str)
            return result
        
        # Process the report with available data
        result = process_report_data(date_str, driving_history_df, activity_detail_df, assets_time_df)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing daily driver report: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def create_demo_report(date_str):
    """
    Create a demo report for demonstration purposes
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        dict: Results of processing with success/error status
    """
    try:
        # Create a sample report
        report_data = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_drivers": 10,
                "on_time": 6,
                "late_start": 2,
                "early_end": 1,
                "not_on_job": 1
            },
            "drivers": [
                {
                    "name": "John Smith",
                    "start_time": "07:15:00",
                    "end_time": "16:30:00",
                    "job_site": "123 Main St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "Jane Doe",
                    "start_time": "07:10:00",
                    "end_time": "16:15:00",
                    "job_site": "456 Elm St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "Bob Johnson",
                    "start_time": "07:20:00",
                    "end_time": "16:45:00",
                    "job_site": "789 Oak St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "Sarah Williams",
                    "start_time": "07:25:00",
                    "end_time": "16:20:00",
                    "job_site": "321 Pine St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "Michael Brown",
                    "start_time": "07:05:00",
                    "end_time": "16:10:00",
                    "job_site": "654 Cedar St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "Emily Davis",
                    "start_time": "07:00:00",
                    "end_time": "16:05:00",
                    "job_site": "987 Birch St",
                    "classification": "ON_TIME",
                    "notes": "Regular shift"
                },
                {
                    "name": "David Wilson",
                    "start_time": "08:15:00",
                    "end_time": "16:30:00",
                    "job_site": "135 Maple St",
                    "classification": "LATE_START",
                    "notes": "Arrived 45 minutes late"
                },
                {
                    "name": "Jennifer Miller",
                    "start_time": "08:30:00",
                    "end_time": "16:45:00",
                    "job_site": "246 Walnut St",
                    "classification": "LATE_START",
                    "notes": "Arrived 1 hour late"
                },
                {
                    "name": "Robert Taylor",
                    "start_time": "07:15:00",
                    "end_time": "15:30:00",
                    "job_site": "357 Spruce St",
                    "classification": "EARLY_END",
                    "notes": "Left 30 minutes early"
                },
                {
                    "name": "Jessica Anderson",
                    "start_time": "00:00:00",
                    "end_time": "00:00:00",
                    "job_site": "468 Redwood St",
                    "classification": "NOT_ON_JOB",
                    "notes": "No data found"
                }
            ],
            "job_sites": {
                "123 Main St": {"latitude": 32.7767, "longitude": -96.7970},
                "456 Elm St": {"latitude": 32.7831, "longitude": -96.8067},
                "789 Oak St": {"latitude": 32.7938, "longitude": -96.7659},
                "321 Pine St": {"latitude": 32.8012, "longitude": -96.7889},
                "654 Cedar St": {"latitude": 32.7665, "longitude": -96.7773},
                "987 Birch St": {"latitude": 32.7554, "longitude": -96.8039},
                "135 Maple St": {"latitude": 32.7701, "longitude": -96.7917},
                "246 Walnut St": {"latitude": 32.7811, "longitude": -96.8001},
                "357 Spruce St": {"latitude": 32.7902, "longitude": -96.7701},
                "468 Redwood St": {"latitude": 32.7722, "longitude": -96.7845}
            }
        }
        
        # Save the report
        report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Export to Excel
        export_to_excel(report_data, date_str)
        
        return {
            "success": True,
            "report_file": report_file,
            "message": "Demo report created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating demo report: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def process_report_data(date_str, driving_history_df=None, activity_detail_df=None, assets_time_df=None):
    """
    Process report data with available data files
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        driving_history_df (DataFrame): Driving history data
        activity_detail_df (DataFrame): Activity detail data
        assets_time_df (DataFrame): Assets time on site data
        
    Returns:
        dict: Results of processing with success/error status
    """
    try:
        # Parse date
        report_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Initialize driver records
        drivers = {}
        job_sites = {}
        
        # Process driving history data
        if driving_history_df is not None:
            # Filter for the specified date
            if 'Date' in driving_history_df.columns:
                driving_history_df['Date'] = pd.to_datetime(driving_history_df['Date'])
                driving_history_df = driving_history_df[driving_history_df['Date'].dt.date == report_date.date()]
            
            # Process each driver
            for _, row in driving_history_df.iterrows():
                driver_name = row.get('Driver', '').strip()
                if not driver_name:
                    continue
                
                # Initialize driver record if not exists
                if driver_name not in drivers:
                    drivers[driver_name] = {
                        "name": driver_name,
                        "start_time": None,
                        "end_time": None,
                        "job_site": None,
                        "classification": "NOT_ON_JOB",
                        "notes": "No complete data found"
                    }
                
                # Update start and end times if available
                time_str = row.get('Time', '')
                if time_str:
                    time_obj = parse_time(time_str)
                    if time_obj:
                        time_decimal = time_obj.hour + time_obj.minute / 60.0
                        
                        # Update start time if earlier than current
                        if drivers[driver_name]["start_time"] is None or time_decimal < drivers[driver_name]["start_time_decimal"]:
                            drivers[driver_name]["start_time"] = time_str
                            drivers[driver_name]["start_time_decimal"] = time_decimal
                        
                        # Update end time if later than current
                        if drivers[driver_name]["end_time"] is None or time_decimal > drivers[driver_name]["end_time_decimal"]:
                            drivers[driver_name]["end_time"] = time_str
                            drivers[driver_name]["end_time_decimal"] = time_decimal
                
                # Update job site if available
                job_site = row.get('Address', '').strip()
                if job_site:
                    drivers[driver_name]["job_site"] = job_site
                    
                    # Store job site location if available
                    if job_site not in job_sites:
                        latitude = row.get('Latitude', 0)
                        longitude = row.get('Longitude', 0)
                        if latitude and longitude:
                            job_sites[job_site] = {
                                "latitude": float(latitude),
                                "longitude": float(longitude)
                            }
        
        # Process activity detail data
        if activity_detail_df is not None:
            # Filter for the specified date
            if 'Date' in activity_detail_df.columns:
                activity_detail_df['Date'] = pd.to_datetime(activity_detail_df['Date'])
                activity_detail_df = activity_detail_df[activity_detail_df['Date'].dt.date == report_date.date()]
            
            # Process each record
            for _, row in activity_detail_df.iterrows():
                driver_name = row.get('Driver', '').strip()
                if not driver_name:
                    continue
                
                # Initialize driver record if not exists
                if driver_name not in drivers:
                    drivers[driver_name] = {
                        "name": driver_name,
                        "start_time": None,
                        "end_time": None,
                        "job_site": None,
                        "classification": "NOT_ON_JOB",
                        "notes": "No complete data found"
                    }
                
                # Update job site if available
                job_site = row.get('Address', '').strip()
                if job_site and not drivers[driver_name]["job_site"]:
                    drivers[driver_name]["job_site"] = job_site
        
        # Process assets time data
        if assets_time_df is not None:
            # Filter for the specified date
            if 'Date' in assets_time_df.columns:
                assets_time_df['Date'] = pd.to_datetime(assets_time_df['Date'])
                assets_time_df = assets_time_df[assets_time_df['Date'].dt.date == report_date.date()]
            
            # Process each record
            for _, row in assets_time_df.iterrows():
                driver_name = row.get('Driver', '').strip()
                if not driver_name:
                    continue
                
                # Initialize driver record if not exists
                if driver_name not in drivers:
                    drivers[driver_name] = {
                        "name": driver_name,
                        "start_time": None,
                        "end_time": None,
                        "job_site": None,
                        "classification": "NOT_ON_JOB",
                        "notes": "No complete data found"
                    }
                
                # Update job site if available
                job_site = row.get('Job Site', '').strip()
                if job_site and not drivers[driver_name]["job_site"]:
                    drivers[driver_name]["job_site"] = job_site
                
                # Update times if available
                arrival_time = row.get('Arrival Time', '')
                departure_time = row.get('Departure Time', '')
                
                if arrival_time:
                    time_obj = parse_time(arrival_time)
                    if time_obj:
                        time_decimal = time_obj.hour + time_obj.minute / 60.0
                        
                        # Update start time if earlier than current
                        if drivers[driver_name]["start_time"] is None or time_decimal < drivers[driver_name]["start_time_decimal"]:
                            drivers[driver_name]["start_time"] = arrival_time
                            drivers[driver_name]["start_time_decimal"] = time_decimal
                
                if departure_time:
                    time_obj = parse_time(departure_time)
                    if time_obj:
                        time_decimal = time_obj.hour + time_obj.minute / 60.0
                        
                        # Update end time if later than current
                        if drivers[driver_name]["end_time"] is None or time_decimal > drivers[driver_name]["end_time_decimal"]:
                            drivers[driver_name]["end_time"] = departure_time
                            drivers[driver_name]["end_time_decimal"] = time_decimal
        
        # Classify drivers
        on_time_count = 0
        late_start_count = 0
        early_end_count = 0
        not_on_job_count = 0
        
        for driver_name, driver in drivers.items():
            # Ensure start and end times are in proper format
            if driver["start_time"]:
                driver["start_time"] = format_time(driver["start_time"])
            else:
                driver["start_time"] = "00:00:00"
            
            if driver["end_time"]:
                driver["end_time"] = format_time(driver["end_time"])
            else:
                driver["end_time"] = "00:00:00"
            
            # Classify based on start and end times
            if "start_time_decimal" in driver and "end_time_decimal" in driver:
                if driver["start_time_decimal"] > LATE_START_THRESHOLD:
                    driver["classification"] = "LATE_START"
                    driver["notes"] = f"Arrived at {driver['start_time']}, after 7:30 AM"
                    late_start_count += 1
                elif driver["end_time_decimal"] < EARLY_END_THRESHOLD:
                    driver["classification"] = "EARLY_END"
                    driver["notes"] = f"Left at {driver['end_time']}, before 4:00 PM"
                    early_end_count += 1
                else:
                    driver["classification"] = "ON_TIME"
                    driver["notes"] = "Regular shift"
                    on_time_count += 1
            else:
                driver["classification"] = "NOT_ON_JOB"
                driver["notes"] = "No time data found"
                not_on_job_count += 1
            
            # Remove decimal time fields from output
            if "start_time_decimal" in driver:
                del driver["start_time_decimal"]
            if "end_time_decimal" in driver:
                del driver["end_time_decimal"]
        
        # Create report data
        report_data = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_drivers": len(drivers),
                "on_time": on_time_count,
                "late_start": late_start_count,
                "early_end": early_end_count,
                "not_on_job": not_on_job_count
            },
            "drivers": list(drivers.values()),
            "job_sites": job_sites
        }
        
        # Save the report
        report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Export to Excel
        export_to_excel(report_data, date_str)
        
        return {
            "success": True,
            "report_file": report_file,
            "message": "Report generated successfully"
        }
    
    except Exception as e:
        logger.error(f"Error processing report data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def parse_time(time_str):
    """
    Parse time string to datetime object
    
    Args:
        time_str (str): Time string in various formats
        
    Returns:
        datetime: Parsed time as datetime object or None if invalid
    """
    try:
        # Try parsing as HH:MM:SS or HH:MM
        formats = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(time_str).strip(), fmt)
            except ValueError:
                continue
        
        # If all formats fail, try to handle special cases
        time_str = str(time_str).strip().upper()
        
        if ':' not in time_str:
            # Handle military time without colon (e.g., 0730)
            if len(time_str) == 4 and time_str.isdigit():
                hours = int(time_str[:2])
                minutes = int(time_str[2:])
                return datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M")
        
        return None
    
    except Exception as e:
        logger.warning(f"Error parsing time string '{time_str}': {str(e)}")
        return None

def format_time(time_str):
    """
    Format time string to HH:MM:SS format
    
    Args:
        time_str (str): Time string in various formats
        
    Returns:
        str: Formatted time string as HH:MM:SS
    """
    time_obj = parse_time(time_str)
    if time_obj:
        return time_obj.strftime("%H:%M:%S")
    return "00:00:00"

def export_to_excel(report_data, date_str):
    """
    Export report data to Excel file
    
    Args:
        report_data (dict): Report data
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Path to the exported Excel file
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        
        # Create a new workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Driver Report {date_str}"
        
        # Set column widths
        ws.column_dimensions['A'].width = 20  # Name
        ws.column_dimensions['B'].width = 12  # Start Time
        ws.column_dimensions['C'].width = 12  # End Time
        ws.column_dimensions['D'].width = 30  # Job Site
        ws.column_dimensions['E'].width = 15  # Classification
        ws.column_dimensions['F'].width = 30  # Notes
        
        # Add header row
        header = ["Driver Name", "Start Time", "End Time", "Job Site", "Classification", "Notes"]
        for col, header_text in enumerate(header, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header_text
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        
        # Add data rows
        for row, driver in enumerate(report_data["drivers"], 2):
            ws.cell(row=row, column=1).value = driver["name"]
            ws.cell(row=row, column=2).value = driver["start_time"]
            ws.cell(row=row, column=3).value = driver["end_time"]
            ws.cell(row=row, column=4).value = driver["job_site"]
            ws.cell(row=row, column=5).value = driver["classification"]
            ws.cell(row=row, column=6).value = driver["notes"]
            
            # Apply conditional formatting
            if driver["classification"] == "LATE_START":
                ws.cell(row=row, column=5).fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            elif driver["classification"] == "EARLY_END":
                ws.cell(row=row, column=5).fill = PatternFill(start_color="FFEECC", end_color="FFEECC", fill_type="solid")
            elif driver["classification"] == "NOT_ON_JOB":
                ws.cell(row=row, column=5).fill = PatternFill(start_color="FFAAAA", end_color="FFAAAA", fill_type="solid")
            elif driver["classification"] == "ON_TIME":
                ws.cell(row=row, column=5).fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        
        # Add summary section
        summary_row = len(report_data["drivers"]) + 3
        ws.cell(row=summary_row, column=1).value = "SUMMARY"
        ws.cell(row=summary_row, column=1).font = Font(bold=True)
        ws.merge_cells(start_row=summary_row, start_column=1, end_row=summary_row, end_column=6)
        
        ws.cell(row=summary_row + 1, column=1).value = "Total Drivers:"
        ws.cell(row=summary_row + 1, column=2).value = report_data["summary"]["total_drivers"]
        
        ws.cell(row=summary_row + 2, column=1).value = "On Time:"
        ws.cell(row=summary_row + 2, column=2).value = report_data["summary"]["on_time"]
        ws.cell(row=summary_row + 2, column=2).fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        
        ws.cell(row=summary_row + 3, column=1).value = "Late Start:"
        ws.cell(row=summary_row + 3, column=2).value = report_data["summary"]["late_start"]
        ws.cell(row=summary_row + 3, column=2).fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        
        ws.cell(row=summary_row + 4, column=1).value = "Early End:"
        ws.cell(row=summary_row + 4, column=2).value = report_data["summary"]["early_end"]
        ws.cell(row=summary_row + 4, column=2).fill = PatternFill(start_color="FFEECC", end_color="FFEECC", fill_type="solid")
        
        ws.cell(row=summary_row + 5, column=1).value = "Not On Job:"
        ws.cell(row=summary_row + 5, column=2).value = report_data["summary"]["not_on_job"]
        ws.cell(row=summary_row + 5, column=2).fill = PatternFill(start_color="FFAAAA", end_color="FFAAAA", fill_type="solid")
        
        # Add footer with generation time
        footer_row = summary_row + 7
        ws.cell(row=footer_row, column=1).value = f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=6)
        
        # Save the workbook
        export_file = f"exports/daily/daily_driver_report_{date_str}.xlsx"
        wb.save(export_file)
        
        logger.info(f"Exported report to Excel: {export_file}")
        return export_file
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return None