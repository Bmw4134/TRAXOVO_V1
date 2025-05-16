"""
Driver Report Processor

This module processes Activity Detail and Driving History data to generate
Late Start, Early End, and Not On Job reports for both prior day and current day.

The reports are saved to the reports directory with date-specific folders.
"""
import os
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
STANDARD_START_TIME = '08:30:00'  # Standard start time (8:30 AM)
STANDARD_END_TIME = '17:00:00'    # Standard end time (5:00 PM)
LATE_THRESHOLD_MINUTES = 15       # Minutes after standard start to be considered late
EARLY_END_THRESHOLD_MINUTES = 15  # Minutes before standard end to be considered early end
CENTRAL_TIMEZONE = pytz.timezone('US/Central')

def ensure_dir(directory):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    return directory

def parse_activity_detail(file_path):
    """
    Parse the Activity Detail CSV file and extract relevant data.
    
    Args:
        file_path: Path to the Activity Detail CSV file
        
    Returns:
        DataFrame with cleaned and formatted activity data
    """
    logger.info(f"Parsing Activity Detail file: {file_path}")
    
    try:
        # Skip the header rows which contain metadata
        df = pd.read_csv(file_path, skiprows=10)
        
        # Extract asset, driver, timestamp, activity type, and location columns
        # Your CSV might have different column names - adjust as needed
        columns_to_keep = [
            'Asset', 'Date & Time', 'Activity', 'Speed', 'Location', 'Latitude', 'Longitude'
        ]
        
        # Filter to keep only necessary columns
        df = df[columns_to_keep]
        
        # Parse dates
        df['Timestamp'] = pd.to_datetime(df['Date & Time'], errors='coerce')
        
        # Extract driver name if it's embedded in the Asset field
        # Format is often "Asset (Driver)" or similar
        df['Driver'] = df['Asset'].str.extract(r'\(([^)]+)\)')
        
        # Extract just the asset ID/name
        df['Asset_ID'] = df['Asset'].str.split('(').str[0].str.strip()
        
        # Extract date 
        df['Date'] = df['Timestamp'].dt.date
        
        # Extract time components for filtering
        df['Time'] = df['Timestamp'].dt.time
        df['Hour'] = df['Timestamp'].dt.hour
        df['Minute'] = df['Timestamp'].dt.minute
        
        # Filter relevant activities
        activity_filter = ['Key On', 'Key Off', 'Arrived', 'Departed', 'Ignition On', 'Ignition Off']
        df = df[df['Activity'].isin(activity_filter)]
        
        logger.info(f"Successfully parsed Activity Detail with {len(df)} relevant records")
        return df
    
    except Exception as e:
        logger.error(f"Error parsing Activity Detail file: {str(e)}")
        raise

def parse_driving_history(file_path):
    """
    Parse the Driving History CSV file and extract relevant data.
    
    Args:
        file_path: Path to the Driving History CSV file
        
    Returns:
        DataFrame with cleaned and formatted driving history data
    """
    logger.info(f"Parsing Driving History file: {file_path}")
    
    try:
        # Skip header rows
        df = pd.read_csv(file_path, skiprows=10)
        
        # Clean up column names (they might have spaces or special characters)
        df.columns = [col.strip() for col in df.columns]
        
        # Identify the driver name, timestamp, activity, and location columns
        # Adjust these column names based on your actual CSV format
        driver_col = [col for col in df.columns if 'Driver' in col or 'Employee' in col][0]
        timestamp_col = [col for col in df.columns if 'Time' in col or 'Date' in col][0]
        activity_col = [col for col in df.columns if 'Activity' in col or 'Action' in col][0]
        location_col = [col for col in df.columns if 'Location' in col or 'Address' in col][0]
        
        # Keep only necessary columns and rename them for consistency
        df = df[[driver_col, timestamp_col, activity_col, location_col]]
        df.columns = ['Driver', 'Timestamp', 'Activity', 'Location']
        
        # Parse dates
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        
        # Extract date
        df['Date'] = df['Timestamp'].dt.date
        
        # Extract time components
        df['Time'] = df['Timestamp'].dt.time
        df['Hour'] = df['Timestamp'].dt.hour
        df['Minute'] = df['Timestamp'].dt.minute
        
        # Filter relevant activities
        activity_filter = ['Key On', 'Key Off', 'Arrived', 'Departed', 'Ignition On', 'Ignition Off']
        df = df[df['Activity'].isin(activity_filter)]
        
        logger.info(f"Successfully parsed Driving History with {len(df)} relevant records")
        return df
    
    except Exception as e:
        logger.error(f"Error parsing Driving History file: {str(e)}")
        raise

def identify_job_sites(df):
    """
    Identify job sites from location data.
    
    Args:
        df: DataFrame with location data
        
    Returns:
        DataFrame with job site information added
    """
    # Extract job code from location if available
    # Format is often "JOB CODE, Address"
    df['Job'] = df['Location'].str.split(',').str[0].str.strip()
    
    # If no job code is found, mark as "UNKNOWN"
    df['Job'] = df['Job'].fillna("UNKNOWN")
    
    return df

def extract_first_last_entry(df, date, group_by='Driver'):
    """
    Extract first and last entry for each driver or asset on a specific date.
    
    Args:
        df: DataFrame with timestamp data
        date: Date to filter by
        group_by: Column to group by ('Driver' or 'Asset_ID')
        
    Returns:
        DataFrame with first and last entry information
    """
    # Filter by date
    day_df = df[df['Date'] == date]
    
    if len(day_df) == 0:
        logger.warning(f"No data found for date: {date}")
        return pd.DataFrame()
    
    # Group by driver or asset and find first/last timestamp
    result = day_df.groupby(group_by).agg({
        'Timestamp': ['min', 'max'],
        'Location': lambda x: x.iloc[0],  # First location
        'Job': lambda x: x.iloc[0]  # First job
    })
    
    # Flatten multi-index columns
    result.columns = ['FirstTimestamp', 'LastTimestamp', 'FirstLocation', 'FirstJob']
    result = result.reset_index()
    
    # Extract time components
    result['FirstTime'] = result['FirstTimestamp'].dt.time
    result['LastTime'] = result['LastTimestamp'].dt.time
    
    return result

def identify_late_start(first_entries, standard_start_time=STANDARD_START_TIME, threshold_minutes=LATE_THRESHOLD_MINUTES):
    """
    Identify drivers with late starts.
    
    Args:
        first_entries: DataFrame with first entry information
        standard_start_time: Standard start time (string format 'HH:MM:SS')
        threshold_minutes: Minutes after standard start to be considered late
        
    Returns:
        DataFrame with late start information
    """
    # Parse standard start time
    std_start = datetime.strptime(standard_start_time, '%H:%M:%S').time()
    
    # Calculate late threshold
    late_threshold = (datetime.combine(datetime.today(), std_start) + 
                      timedelta(minutes=threshold_minutes)).time()
    
    # Mark as late if first entry is after late threshold
    first_entries['LateStart'] = first_entries['FirstTime'] > late_threshold
    
    # Filter to only late starts
    late_starts = first_entries[first_entries['LateStart']].copy()
    
    # Calculate minutes late
    late_starts['MinutesLate'] = late_starts.apply(
        lambda row: (datetime.combine(datetime.today(), row['FirstTime']) - 
                    datetime.combine(datetime.today(), std_start)).total_seconds() / 60,
        axis=1
    )
    
    return late_starts

def identify_early_end(last_entries, standard_end_time=STANDARD_END_TIME, threshold_minutes=EARLY_END_THRESHOLD_MINUTES):
    """
    Identify drivers with early ends.
    
    Args:
        last_entries: DataFrame with last entry information
        standard_end_time: Standard end time (string format 'HH:MM:SS')
        threshold_minutes: Minutes before standard end to be considered early
        
    Returns:
        DataFrame with early end information
    """
    # Parse standard end time
    std_end = datetime.strptime(standard_end_time, '%H:%M:%S').time()
    
    # Calculate early threshold
    early_threshold = (datetime.combine(datetime.today(), std_end) - 
                      timedelta(minutes=threshold_minutes)).time()
    
    # Mark as early end if last entry is before early threshold
    last_entries['EarlyEnd'] = last_entries['LastTime'] < early_threshold
    
    # Filter to only early ends
    early_ends = last_entries[last_entries['EarlyEnd']].copy()
    
    # Calculate minutes early
    early_ends['MinutesEarly'] = early_ends.apply(
        lambda row: (datetime.combine(datetime.today(), std_end) - 
                    datetime.combine(datetime.today(), row['LastTime'])).total_seconds() / 60,
        axis=1
    )
    
    return early_ends

def identify_not_on_job(entries, known_job_sites):
    """
    Identify drivers not on a known job site.
    
    Args:
        entries: DataFrame with job site information
        known_job_sites: List of known job site codes/names
        
    Returns:
        DataFrame with not-on-job information
    """
    # Mark as not on job if job is not in known job sites
    entries['NotOnJob'] = ~entries['FirstJob'].isin(known_job_sites)
    
    # Filter to only not on job
    not_on_job = entries[entries['NotOnJob']].copy()
    
    return not_on_job

def generate_prior_day_report(activity_data, driving_data, report_date=None):
    """
    Generate the prior day report (Late Start, Early End, Not On Job).
    
    Args:
        activity_data: DataFrame with activity detail data
        driving_data: DataFrame with driving history data
        report_date: Date to generate report for (defaults to yesterday)
        
    Returns:
        Dictionary with report DataFrames
    """
    # Set report date to yesterday if not specified
    if report_date is None:
        report_date = (datetime.now(CENTRAL_TIMEZONE) - timedelta(days=1)).date()
    
    logger.info(f"Generating prior day report for: {report_date}")
    
    # Combine data sources
    combined_data = pd.concat([
        activity_data[['Driver', 'Asset_ID', 'Date', 'Timestamp', 'Time', 'Hour', 'Minute', 'Location', 'Job']],
        driving_data[['Driver', 'Date', 'Timestamp', 'Time', 'Hour', 'Minute', 'Location', 'Job']]
    ])
    
    # Process first and last entries by driver
    first_entries = extract_first_last_entry(combined_data, report_date, group_by='Driver')
    
    if len(first_entries) == 0:
        logger.warning(f"No data found for prior day report on {report_date}")
        return {
            'late_start': pd.DataFrame(),
            'early_end': pd.DataFrame(),
            'not_on_job': pd.DataFrame()
        }
    
    # Identify late starts
    late_starts = identify_late_start(first_entries)
    
    # Identify early ends
    early_ends = identify_early_end(first_entries)
    
    # Sample known job sites - in a real implementation, this should come from a database or config
    known_job_sites = ["DFW001", "HOU002", "WTX003", "TRAFFIC", "TEXDIST"]
    
    # Identify not on job
    not_on_job = identify_not_on_job(first_entries, known_job_sites)
    
    # Create report dictionary
    report = {
        'late_start': late_starts,
        'early_end': early_ends,
        'not_on_job': not_on_job
    }
    
    logger.info(f"Prior day report generated with {len(late_starts)} late starts, "
                f"{len(early_ends)} early ends, and {len(not_on_job)} not on job")
    
    return report

def generate_current_day_report(activity_data, driving_data, report_time=None):
    """
    Generate the current day report (Late Start, Not On Job).
    
    Args:
        activity_data: DataFrame with activity detail data
        driving_data: DataFrame with driving history data
        report_time: Time to generate report for (defaults to now)
        
    Returns:
        Dictionary with report DataFrames
    """
    # Set report time to now if not specified
    if report_time is None:
        now = datetime.now(CENTRAL_TIMEZONE)
        report_time = now
        report_date = now.date()
    else:
        report_date = report_time.date()
    
    logger.info(f"Generating current day report for: {report_date} at {report_time.time()}")
    
    # Combine data sources
    combined_data = pd.concat([
        activity_data[['Driver', 'Asset_ID', 'Date', 'Timestamp', 'Time', 'Hour', 'Minute', 'Location', 'Job']],
        driving_data[['Driver', 'Date', 'Timestamp', 'Time', 'Hour', 'Minute', 'Location', 'Job']]
    ])
    
    # Filter data up to report time
    current_data = combined_data[
        (combined_data['Date'] == report_date) & 
        (combined_data['Timestamp'] <= pd.Timestamp(report_time))
    ]
    
    # Process first entries by driver
    first_entries = extract_first_last_entry(current_data, report_date, group_by='Driver')
    
    if len(first_entries) == 0:
        logger.warning(f"No data found for current day report on {report_date}")
        return {
            'late_start': pd.DataFrame(),
            'not_on_job': pd.DataFrame()
        }
    
    # Identify late starts
    late_starts = identify_late_start(first_entries)
    
    # Sample known job sites - in a real implementation, this should come from a database or config
    known_job_sites = ["DFW001", "HOU002", "WTX003", "TRAFFIC", "TEXDIST"]
    
    # Identify not on job
    not_on_job = identify_not_on_job(first_entries, known_job_sites)
    
    # Create report dictionary
    report = {
        'late_start': late_starts,
        'not_on_job': not_on_job
    }
    
    logger.info(f"Current day report generated with {len(late_starts)} late starts and "
                f"{len(not_on_job)} not on job")
    
    return report

def save_report_to_csv(report, report_dir, report_type='prior_day'):
    """
    Save report DataFrames to CSV files.
    
    Args:
        report: Dictionary with report DataFrames
        report_dir: Directory to save reports in
        report_type: Type of report ('prior_day' or 'current_day')
        
    Returns:
        Dictionary with paths to saved files
    """
    # Ensure report directory exists
    ensure_dir(report_dir)
    
    saved_files = {}
    
    # Save each report component
    for report_name, df in report.items():
        if len(df) == 0:
            logger.warning(f"Empty report for {report_name}, skipping save")
            saved_files[report_name] = None
            continue
        
        filename = f"{report_type}_{report_name}.csv"
        file_path = os.path.join(report_dir, filename)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        saved_files[report_name] = file_path
        logger.info(f"Saved report to {file_path}")
    
    return saved_files

def generate_html_summary(reports, report_date):
    """
    Generate HTML summary of the reports.
    
    Args:
        reports: Dictionary with report paths
        report_date: Date of the report
        
    Returns:
        HTML string with report summary
    """
    # Create HTML header with dark theme friendly styles
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Driver Report Summary - {report_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #212529; color: #e9ecef; }}
        h1, h2 {{ color: #0dcaf0; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; border: 1px solid #495057; }}
        th, td {{ border: 1px solid #495057; padding: 10px; text-align: left; }}
        th {{ background-color: #343a40; color: #ffffff; border-bottom: 2px solid #0dcaf0; }}
        tr:nth-child(even) {{ background-color: rgba(255, 255, 255, 0.05); }}
        tr:hover {{ background-color: rgba(13, 202, 240, 0.1); }}
        .summary {{ background-color: #2c3034; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #0dcaf0; }}
        .late-start-row {{ border-left: 3px solid #dc3545; }}
        .early-end-row {{ border-left: 3px solid #ffc107; }}
        .not-on-job-row {{ border-left: 3px solid #6c757d; }}
        .driver-report-table {{ width: 100%; margin-bottom: 1.5rem; border: 1px solid #495057; }}
    </style>
</head>
<body>
    <h1>Driver Report Summary - {report_date}</h1>
    <div class="summary">
"""
    
    # Add summary counts
    for report_type, report_data in reports.items():
        html += f"<h2>{report_type.replace('_', ' ').title()} Report</h2>\n<ul>\n"
        
        for report_name, file_path in report_data.items():
            if file_path:
                # Count rows in the CSV (excluding header)
                with open(file_path, 'r') as f:
                    row_count = sum(1 for line in f) - 1
                
                html += f"<li><strong>{report_name.replace('_', ' ').title()}:</strong> {row_count} entries</li>\n"
            else:
                html += f"<li><strong>{report_name.replace('_', ' ').title()}:</strong> No data</li>\n"
        
        html += "</ul>\n"
    
    # Add table sections for each report
    for report_type, report_data in reports.items():
        for report_name, file_path in report_data.items():
            if file_path and os.path.exists(file_path):
                html += f"<h2>{report_type.replace('_', ' ').title()} - {report_name.replace('_', ' ').title()}</h2>\n"
                
                # Read the CSV and create a table with our custom styling
                df = pd.read_csv(file_path)
                
                # Determine report-specific class for styling
                report_class = 'driver-report-table'
                row_class = ''
                if 'late_start' in report_name:
                    row_class = 'late-start-row'
                elif 'early_end' in report_name:
                    row_class = 'early-end-row'
                elif 'not_on_job' in report_name:
                    row_class = 'not-on-job-row'
                
                # Generate HTML table with class for dark theme
                table_html = df.to_html(index=False, classes=[report_class])
                
                # Add row class to make different report types visually distinct
                if row_class:
                    # Add class to the first row (after the header row)
                    table_html = table_html.replace('<tbody>', f'<tbody class="{row_class}">')
                
                html += table_html
    
    # Close HTML
    html += """
</body>
</html>
"""
    
    return html

def save_html_summary(html, report_dir, filename="report_summary.html"):
    """
    Save HTML summary to a file.
    
    Args:
        html: HTML string
        report_dir: Directory to save the file in
        filename: Name of the HTML file
        
    Returns:
        Path to the saved file
    """
    file_path = os.path.join(report_dir, filename)
    
    with open(file_path, 'w') as f:
        f.write(html)
    
    logger.info(f"Saved HTML summary to {file_path}")
    return file_path

def process_driver_reports(activity_detail_path, driving_history_path, output_dir=None):
    """
    Process driver reports and save them to CSV files.
    
    Args:
        activity_detail_path: Path to the Activity Detail CSV file
        driving_history_path: Path to the Driving History CSV file
        output_dir: Directory to save reports in (defaults to 'reports/YYYY-MM-DD')
        
    Returns:
        Dictionary with paths to saved files
    """
    try:
        # Parse data files
        activity_data = parse_activity_detail(activity_detail_path)
        driving_data = parse_driving_history(driving_history_path)
        
        # Identify job sites
        activity_data = identify_job_sites(activity_data)
        driving_data = identify_job_sites(driving_data)
        
        # Set report date to yesterday
        report_date = (datetime.now(CENTRAL_TIMEZONE) - timedelta(days=1)).date()
        
        # Set output directory
        if output_dir is None:
            base_dir = os.path.join('reports', report_date.strftime('%Y-%m-%d'))
            output_dir = ensure_dir(base_dir)
        else:
            output_dir = ensure_dir(output_dir)
        
        logger.info(f"Saving reports to directory: {output_dir}")
        
        # Generate prior day report
        prior_day_report = generate_prior_day_report(activity_data, driving_data, report_date)
        
        # Save prior day report
        prior_day_files = save_report_to_csv(prior_day_report, output_dir, 'prior_day')
        
        # Generate current day report as of 8:30 AM
        current_day = datetime.now(CENTRAL_TIMEZONE).date()
        report_time = datetime.combine(current_day, datetime.strptime(STANDARD_START_TIME, '%H:%M:%S').time())
        report_time = CENTRAL_TIMEZONE.localize(report_time)
        
        current_day_report = generate_current_day_report(activity_data, driving_data, report_time)
        
        # Save current day report
        current_day_files = save_report_to_csv(current_day_report, output_dir, 'current_day')
        
        # Create summary reports dictionary
        reports = {
            'prior_day': prior_day_files,
            'current_day': current_day_files
        }
        
        # Generate and save HTML summary
        html_summary = generate_html_summary(reports, report_date)
        summary_path = save_html_summary(html_summary, output_dir)
        
        reports['summary'] = summary_path
        
        return reports
        
    except Exception as e:
        logger.error(f"Error processing driver reports: {str(e)}")
        raise

if __name__ == "__main__":
    # Default paths to the data files
    activity_detail_path = os.path.join('attached_assets', 'ActivityDetail (6).csv')
    driving_history_path = os.path.join('attached_assets', 'DrivingHistory.csv')
    
    # Process reports
    try:
        reports = process_driver_reports(activity_detail_path, driving_history_path)
        logger.info("Driver reports processed successfully")
        
        # Print summary of reports
        for report_type, files in reports.items():
            if isinstance(files, dict):
                for report_name, file_path in files.items():
                    if file_path:
                        logger.info(f"{report_type} - {report_name}: {file_path}")
            else:
                logger.info(f"{report_type}: {files}")
                
    except Exception as e:
        logger.error(f"Failed to process driver reports: {str(e)}")