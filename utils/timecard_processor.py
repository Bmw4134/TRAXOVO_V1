"""
Timecard Processor Module

This module provides functions for processing timecard data from Ground Works
and comparing it with GPS data to verify accuracy and track driver attendance.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_timecard(file_path):
    """
    Process a timecard file and return structured data
    
    Args:
        file_path (str): Path to the timecard Excel file
        
    Returns:
        dict: Dictionary with success status and message
    """
    try:
        logger.info(f"Processing timecard file: {file_path}")
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join('reports', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Load the timecard data
        timecard_data = load_timecard_data(file_path)
        
        if "error" in timecard_data:
            return {
                "success": False,
                "message": f"Error processing timecard: {timecard_data['error']}"
            }
            
        # Generate attendance report
        report_file = os.path.join(reports_dir, f"attendance_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
        generate_attendance_report(timecard_data, output_path=report_file)
        
        # Return success message with stats
        driver_count = len(timecard_data["drivers"])
        job_count = len(timecard_data["jobs"])
        total_hours = timecard_data["summary"]["total_hours"]
        
        return {
            "success": True,
            "message": f"Processed timecard with {driver_count} drivers, {job_count} jobs, and {total_hours} total hours.",
            "report_file": report_file,
            "data": timecard_data
        }
        
    except Exception as e:
        logger.error(f"Error in process_timecard: {e}")
        return {
            "success": False,
            "message": f"Error processing timecard: {str(e)}"
        }

def load_timecard_data(file_path):
    """
    Load timecard data from Ground Works Excel file
    
    Args:
        file_path (str): Path to the Excel timecard file
        
    Returns:
        dict: Processed timecard data with driver stats
    """
    try:
        # Load Excel file
        logger.info(f"Loading timecard data from: {file_path}")
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Check if file loaded properly
        if df.empty:
            logger.error("Timecard file appears to be empty")
            return {"error": "Empty timecard file"}
        
        # Log column names for debugging
        logger.info(f"Columns found: {df.columns.tolist()}")
        
        # Process the data into a structured format
        timecard_data = process_timecard_entries(df)
        
        return timecard_data
        
    except Exception as e:
        logger.error(f"Error processing timecard file: {e}")
        return {"error": str(e)}

def process_timecard_entries(df):
    """
    Process timecard entries into structured format
    
    Args:
        df (DataFrame): pandas DataFrame containing timecard data
        
    Returns:
        dict: Processed data with driver stats
    """
    # Initialize results
    result = {
        "drivers": {},
        "jobs": {},
        "summary": {
            "total_entries": 0,
            "total_hours": 0,
            "missing_gps": 0,
            "pto_entries": 0,
            "late_starts": 0
        },
        "date_range": {
            "start": None,
            "end": None
        }
    }
    
    # Try to determine if this is the Ground Works format
    # Check if this is the Ground Works format (has specific columns)
    if 'ProjectNo' in df.columns and 'EmployeeNo' in df.columns and 'Employee' in df.columns:
        logger.info("Detected Ground Works timecard format")
        
        # Map columns to our standard format
        column_mapping = {
            "Employee": "Employee",
            "Job": "ProjectNo",
            "Date": "Date",
            "Hours": "Hours"
        }
        
        # Time In/Out might not be available in this format, but we can still process other data
        # We'll use the date without specific times
    else:
        # Standard format - try to determine column mapping
        required_columns = ["Employee", "Job", "Date", "Hours"]
        optional_columns = ["In", "Out"]
        
        # Create normalized column mapping (handle various column name formats)
        column_mapping = {}
        for col in df.columns:
            for req_col in required_columns + optional_columns:
                if req_col.lower() in col.lower():
                    column_mapping[req_col] = col
                    break
        
        # Ensure we have all required columns
        missing_cols = [col for col in required_columns if col not in column_mapping]
        if missing_cols:
            logger.warning(f"Missing columns: {missing_cols}")
            
            # Try alternative column names
            alt_mappings = {
                "Employee": ["Name", "Employee Name", "Driver", "Worker", "EmployeeNo"],
                "Job": ["Job Name", "Job Number", "JobID", "Project", "Task", "ProjectNo", "ProjectDescription"],
                "Date": ["Work Date", "Time Date", "Entry Date"],
                "Hours": ["Total Hours", "Work Hours", "Duration"],
                "In": ["Time In", "Clock In", "Start Time"],
                "Out": ["Time Out", "Clock Out", "End Time"]
            }
            
            for req_col in missing_cols:
                for alt_col in alt_mappings.get(req_col, []):
                    for df_col in df.columns:
                        if alt_col.lower() in df_col.lower():
                            column_mapping[req_col] = df_col
                            logger.info(f"Found alternative mapping: {req_col} -> {df_col}")
                            break
        
        # Final check for required columns
        missing_cols = [col for col in required_columns if col not in column_mapping]
        if missing_cols:
            logger.error(f"Still missing required columns: {missing_cols}")
            return {"error": f"Missing required columns: {missing_cols}"}
    
    # Normalize column names
    df_processed = df.rename(columns={column_mapping[col]: col for col in column_mapping})
    
    # Process date range
    try:
        date_col = df_processed['Date']
        if pd.api.types.is_datetime64_any_dtype(date_col):
            min_date = date_col.min()
            max_date = date_col.max()
        else:
            # Try to convert to datetime
            date_col = pd.to_datetime(date_col, errors='coerce')
            min_date = date_col.min()
            max_date = date_col.max()
        
        result["date_range"]["start"] = min_date.strftime('%Y-%m-%d') if not pd.isnull(min_date) else None
        result["date_range"]["end"] = max_date.strftime('%Y-%m-%d') if not pd.isnull(max_date) else None
    except Exception as e:
        logger.error(f"Error processing date range: {e}")
    
    # Process entries
    for _, row in df_processed.iterrows():
        try:
            # Extract basic info
            employee = str(row.get('Employee', '')).strip()
            job = str(row.get('Job', '')).strip()
            date = row.get('Date')
            hours = float(row.get('Hours', 0))
            
            # Ground Works format may not have Time In/Out explicitly
            time_in = row.get('In') if 'In' in row else None
            time_out = row.get('Out') if 'Out' in row else None
            
            # Check for ProjectDescription as a fallback for job name
            if job == '' and 'ProjectDescription' in df_processed.columns:
                job = str(row.get('ProjectDescription', '')).strip()
            
            # Skip empty rows
            if pd.isnull(employee) or pd.isnull(job) or pd.isnull(date):
                continue
                
            # Convert date to string format if it's a datetime
            if isinstance(date, pd.Timestamp):
                date_str = date.strftime('%Y-%m-%d')
            else:
                # Try to convert string to datetime
                try:
                    date = pd.to_datetime(date)
                    date_str = date.strftime('%Y-%m-%d')
                except:
                    date_str = str(date)
            
            # Process time in/out
            time_in_str = None
            time_out_str = None
            
            if not pd.isnull(time_in):
                if isinstance(time_in, datetime) or isinstance(time_in, pd.Timestamp):
                    time_in_str = time_in.strftime('%H:%M')
                else:
                    # Try to parse time string
                    try:
                        time_in_str = str(time_in)
                    except:
                        time_in_str = None
            
            if not pd.isnull(time_out):
                if isinstance(time_out, datetime) or isinstance(time_out, pd.Timestamp):
                    time_out_str = time_out.strftime('%H:%M')
                else:
                    # Try to parse time string
                    try:
                        time_out_str = str(time_out)
                    except:
                        time_out_str = None
            
            # Check if this is PTO
            is_pto = False
            if job.lower().startswith('pto') or 'pto' in job.lower() or 'sick' in job.lower() or 'vacation' in job.lower():
                is_pto = True
                result["summary"]["pto_entries"] += 1
            
            # Check for late start (after 7:00 AM)
            is_late = False
            if time_in_str and not is_pto:
                try:
                    # Parse the time string
                    time_format = '%H:%M'
                    # Convert AM/PM format if needed
                    if 'am' in time_in_str.lower() or 'pm' in time_in_str.lower():
                        time_format = '%I:%M %p'
                    
                    time_in_obj = datetime.strptime(time_in_str, time_format).time()
                    start_threshold = datetime.strptime('07:00', '%H:%M').time()
                    
                    if time_in_obj > start_threshold:
                        is_late = True
                        result["summary"]["late_starts"] += 1
                except Exception as e:
                    logger.error(f"Error parsing time: {time_in_str} - {e}")
            
            # Update driver stats
            if employee not in result["drivers"]:
                result["drivers"][employee] = {
                    "total_hours": 0,
                    "job_entries": {},
                    "days_worked": set(),
                    "late_starts": 0,
                    "pto_hours": 0
                }
            
            # Update total hours
            if is_pto:
                result["drivers"][employee]["pto_hours"] += hours
            else:
                result["drivers"][employee]["total_hours"] += hours
            
            # Track days worked
            result["drivers"][employee]["days_worked"].add(date_str)
            
            # Track job entries
            if job not in result["drivers"][employee]["job_entries"]:
                result["drivers"][employee]["job_entries"][job] = {
                    "total_hours": 0,
                    "entries": []
                }
            
            # Add this entry
            result["drivers"][employee]["job_entries"][job]["total_hours"] += hours
            result["drivers"][employee]["job_entries"][job]["entries"].append({
                "date": date_str,
                "hours": hours,
                "time_in": time_in_str,
                "time_out": time_out_str,
                "is_pto": is_pto,
                "is_late": is_late
            })
            
            # Track late starts
            if is_late:
                result["drivers"][employee]["late_starts"] += 1
            
            # Update job stats
            if job not in result["jobs"]:
                result["jobs"][job] = {
                    "total_hours": 0,
                    "employees": set(),
                    "entries": []
                }
            
            result["jobs"][job]["total_hours"] += hours
            result["jobs"][job]["employees"].add(employee)
            result["jobs"][job]["entries"].append({
                "employee": employee,
                "date": date_str,
                "hours": hours,
                "time_in": time_in_str,
                "time_out": time_out_str
            })
            
            # Update summary stats
            result["summary"]["total_entries"] += 1
            result["summary"]["total_hours"] += hours
            
        except Exception as e:
            logger.error(f"Error processing row: {e}")
    
    # Convert sets to lists for JSON serialization
    for employee in result["drivers"]:
        result["drivers"][employee]["days_worked"] = list(result["drivers"][employee]["days_worked"])
    
    for job in result["jobs"]:
        result["jobs"][job]["employees"] = list(result["jobs"][job]["employees"])
    
    return result

def cross_reference_with_gps(timecard_data, gps_data):
    """
    Cross-reference timecard data with GPS data
    
    Args:
        timecard_data (dict): Processed timecard data
        gps_data (dict): GPS location data
        
    Returns:
        dict: Analysis results with discrepancies
    """
    # Placeholder for implementation
    result = {
        "matched_entries": 0,
        "missing_gps": 0,
        "time_discrepancies": 0,
        "location_discrepancies": 0,
        "entries": []
    }
    
    return result

def generate_attendance_report(timecard_data, output_path=None, include_asset_data=True):
    """
    Generate attendance report from timecard data
    
    Args:
        timecard_data (dict): Processed timecard data
        output_path (str, optional): Path to save Excel report
        include_asset_data (bool): Whether to include asset-driver relationships
        
    Returns:
        dict: Report summary
    """
    # Import here to avoid circular imports
    try:
        from models import Driver, Asset
        from utils.asset_driver_mapper import extract_asset_driver_mappings
        db_access = True
    except ImportError:
        logger.warning("Could not import database models, asset data will be limited")
        db_access = False
    
    # Create summary dataframes
    driver_summary = []
    for driver, data in timecard_data["drivers"].items():
        # Try to find asset assigned to this driver if db_access is available
        asset_id = None
        asset_name = None
        
        if db_access and include_asset_data:
            try:
                # Look up driver in database by name
                driver_obj = Driver.query.filter(Driver.name.ilike(f"%{driver}%")).first()
                if driver_obj and driver_obj.asset_id:
                    asset = Asset.query.get(driver_obj.asset_id)
                    if asset:
                        asset_id = asset.asset_identifier
                        asset_name = asset.label or asset.asset_identifier
            except Exception as e:
                logger.warning(f"Error looking up driver asset: {e}")
        
        driver_summary.append({
            "Driver": driver,
            "Total Hours": data["total_hours"],
            "PTO Hours": data["pto_hours"],
            "Days Worked": len(data["days_worked"]),
            "Late Starts": data["late_starts"],
            "Jobs Worked": len(data["job_entries"]),
            "Asset ID": asset_id,
            "Asset Name": asset_name
        })
    
    job_summary = []
    for job, data in timecard_data["jobs"].items():
        job_summary.append({
            "Job": job,
            "Total Hours": data["total_hours"],
            "Employee Count": len(data["employees"]),
            "Entry Count": len(data["entries"]),
            "Avg Hours Per Employee": round(data["total_hours"] / len(data["employees"]), 2) if data["employees"] else 0
        })
    
    # Convert to DataFrames
    driver_df = pd.DataFrame(driver_summary)
    job_df = pd.DataFrame(job_summary)
    
    # Add additional calculations to driver summary
    if not driver_df.empty:
        if "Total Hours" in driver_df.columns and "Days Worked" in driver_df.columns:
            driver_df["Avg Hours Per Day"] = driver_df.apply(
                lambda row: round(row["Total Hours"] / row["Days Worked"], 2) if row["Days Worked"] > 0 else 0, 
                axis=1
            )
    
    # Generate Excel report if output path provided
    if output_path:
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Create overview sheet with explanation
                overview_data = {
                    "Report Section": [
                        "Overview",
                        "Driver Summary",
                        "Job Summary", 
                        "Detailed Entries",
                        "Late Starts",
                        "PTO Summary"
                    ],
                    "Description": [
                        "This report summarizes timecard data for the period " + 
                        f"{timecard_data['date_range']['start']} to {timecard_data['date_range']['end']}",
                        "Shows total hours, PTO, and attendance patterns for each driver",
                        "Breaks down hours worked by job site",
                        "Contains individual timecard entries with dates and hours",
                        "Lists all instances where drivers started after 7:00 AM",
                        "Summarizes PTO usage by driver"
                    ]
                }
                
                # Add report statistics
                overview_stats = {
                    "Statistic": [
                        "Total Entries",
                        "Total Hours",
                        "PTO Hours",
                        "Late Starts",
                        "Unique Drivers",
                        "Unique Job Sites"
                    ],
                    "Value": [
                        timecard_data["summary"]["total_entries"],
                        timecard_data["summary"]["total_hours"],
                        sum(data["pto_hours"] for data in timecard_data["drivers"].values()),
                        timecard_data["summary"]["late_starts"],
                        len(timecard_data["drivers"]),
                        len(timecard_data["jobs"])
                    ]
                }
                
                # Write overview and stats to Excel
                pd.DataFrame(overview_data).to_excel(writer, sheet_name='Report Guide', index=False, startrow=1)
                pd.DataFrame(overview_stats).to_excel(writer, sheet_name='Report Guide', index=False, startrow=10)
                
                # Format the overview sheet
                workbook = writer.book
                overview_sheet = writer.sheets['Report Guide']
                
                # Add title
                overview_sheet['A1'] = "Timecard Analysis Report"
                overview_sheet['A1'].font = workbook.add_format({'bold': True, 'size': 16}).font
                
                # Write main summary sheets
                driver_df.to_excel(writer, sheet_name='Driver Summary', index=False)
                job_df.to_excel(writer, sheet_name='Job Summary', index=False)
                
                # Create detailed entries sheet
                detailed_entries = []
                for driver, data in timecard_data["drivers"].items():
                    for job, job_data in data["job_entries"].items():
                        for entry in job_data["entries"]:
                            detailed_entries.append({
                                "Driver": driver,
                                "Job": job,
                                "Date": entry["date"],
                                "Hours": entry["hours"],
                                "Time In": entry["time_in"],
                                "Time Out": entry["time_out"],
                                "Is PTO": "Yes" if entry["is_pto"] else "No",
                                "Is Late": "Yes" if entry["is_late"] else "No"
                            })
                
                entries_df = pd.DataFrame(detailed_entries)
                entries_df.to_excel(writer, sheet_name='Detailed Entries', index=False)
                
                # Create late starts sheet
                late_entries = [entry for entry in detailed_entries if entry["Is Late"] == "Yes"]
                if late_entries:
                    late_df = pd.DataFrame(late_entries)
                    late_df.to_excel(writer, sheet_name='Late Starts', index=False)
                
                # Create PTO summary sheet
                pto_entries = [entry for entry in detailed_entries if entry["Is PTO"] == "Yes"]
                if pto_entries:
                    pto_df = pd.DataFrame(pto_entries)
                    pto_df.to_excel(writer, sheet_name='PTO Summary', index=False)
                
                # Try to add asset data from most recent monthly billing if available
                if include_asset_data:
                    try:
                        # Look for billing files
                        billing_files = []
                        for root, dirs, files in os.walk("attached_assets"):
                            for file in files:
                                if "MONTHLY BILLINGS" in file.upper() and file.endswith((".xlsx", ".xlsm")):
                                    billing_files.append(os.path.join(root, file))
                        
                        if billing_files:
                            # Use the most recent file
                            billing_files.sort(key=os.path.getmtime, reverse=True)
                            recent_file = billing_files[0]
                            
                            # Extract asset-driver mappings
                            mappings_result = extract_asset_driver_mappings(recent_file, sheet_name="DRIVERS")
                            
                            if mappings_result.get("status") == "success":
                                # Create asset mapping sheet
                                mapping_data = []
                                for asset_id, data in mappings_result.get("mappings", {}).items():
                                    mapping_data.append({
                                        "Asset ID": asset_id,
                                        "Driver Name": data.get("employee_name"),
                                        "Employee ID": data.get("employee_id")
                                    })
                                
                                mapping_df = pd.DataFrame(mapping_data)
                                mapping_df.to_excel(writer, sheet_name='Asset-Driver Mapping', index=False)
                                
                                logger.info(f"Added asset-driver mapping from {recent_file}")
                    except Exception as e:
                        logger.warning(f"Error adding asset-driver mapping: {e}")
            
            return {
                "status": "success",
                "report_path": output_path,
                "driver_count": len(driver_summary),
                "job_count": len(job_summary),
                "total_hours": timecard_data["summary"]["total_hours"],
                "message": "Report generated with enhanced data visualization and explanations"
            }
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
            return {"status": "error", "message": str(e)}
    
    return {
        "status": "success",
        "driver_summary": driver_summary,
        "job_summary": job_summary,
        "total_hours": timecard_data["summary"]["total_hours"]
    }