"""
TRAXORA GENIUS CORE | Weekly Driver Summary Agent

This agent summarizes driver attendance data on a weekly basis,
with support for grouping by job number, zone, and division.
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union, Tuple
from utils.attendance_summary import classify_day
from utils.jobsite_catalog_loader import get_jobsite_by_number, validate_jobsite_reference

# Configure logging
logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> Optional[datetime.date]:
    """
    Parse a date string in various formats
    
    Args:
        date_str (str): Date string to parse
        
    Returns:
        datetime.date: Parsed date or None if parsing failed
    """
    formats = [
        "%m/%d/%Y",  # 05/22/2025
        "%Y-%m-%d",  # 2025-05-22
        "%d-%m-%Y",  # 22-05-2025
        "%b %d %Y",  # May 22 2025
        "%d %b %Y"   # 22 May 2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def enrich_with_jobsite_info(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a record with job site information
    
    Args:
        record (dict): Record to enrich
        
    Returns:
        dict: Enriched record
    """
    # Copy the record to avoid modifying the original
    enriched = record.copy()
    
    # Find job site reference
    reference_fields = ['JobSite', 'jobsite', 'job_site', 'JobNumber', 'job_number']
    jobsite_reference = None
    
    for field in reference_fields:
        if field in record and record[field]:
            jobsite_reference = record[field]
            break
    
    if not jobsite_reference:
        # Default values if no jobsite reference found
        enriched['normalized_job_number'] = 'Unknown'
        enriched['job_description'] = 'Unknown'
        enriched['division'] = 'Unknown'
        enriched['zone'] = None
        enriched['category'] = 'Unknown'
        return enriched
    
    # Try to validate and get jobsite info
    validation = validate_jobsite_reference(jobsite_reference)
    
    if validation['valid'] and validation['jobsite']:
        jobsite = validation['jobsite']
        enriched['normalized_job_number'] = jobsite['job_number']
        enriched['job_description'] = jobsite['description']
        enriched['division'] = jobsite.get('division', 'Unknown')
        enriched['zone'] = jobsite.get('zone')
        enriched['category'] = jobsite.get('category', 'Unknown')
    else:
        # Keep original reference but mark as unknown for other fields
        enriched['normalized_job_number'] = jobsite_reference
        enriched['job_description'] = 'Unknown'
        enriched['division'] = 'Unknown'
        enriched['zone'] = None
        enriched['category'] = 'Unknown'
    
    return enriched

def summarize_week(data: List[Dict[str, Any]], start_date: Optional[datetime.date] = None, group_by: str = 'driver') -> Dict[str, Any]:
    """
    Summarize weekly attendance data with support for different grouping options
    
    Args:
        data (list): List of attendance data records
        start_date (datetime.date, optional): Start date to filter records
        group_by (str): Grouping option ('driver', 'job_number', 'division', 'zone')
        
    Returns:
        dict: Summary results with grouped attendance data
    """
    # Determine grouping field based on group_by option
    group_field_map = {
        'driver': lambda r: r.get('Driver') or r.get('driver_name') or r.get('Asset') or 'Unknown',
        'job_number': lambda r: r.get('normalized_job_number', 'Unknown'),
        'division': lambda r: r.get('division', 'Unknown'),
        'zone': lambda r: str(r.get('zone') or 'No Zone')
    }
    
    if group_by not in group_field_map:
        group_by = 'driver'  # Default to driver if invalid option
    
    group_field = group_field_map[group_by]
    
    # Initialize data structures
    summary = defaultdict(lambda: defaultdict(list))
    all_dates = set()
    
    # Process each record
    for row in data:
        try:
            # Parse date
            raw_date = row.get('Date')
            if not raw_date:
                continue
                
            date = parse_date(raw_date)
            if not date:
                continue
            
            # Skip if before start date
            if start_date and date < start_date:
                continue
            
            # Enrich with jobsite information
            enriched_row = enrich_with_jobsite_info(row)
            
            # Get grouping key
            group_key = group_field(enriched_row)
            
            # Classify the day
            classification = classify_day(enriched_row)
            
            # Add to summary
            summary[group_key]["daily"].append({
                "date": str(date),
                "status": classification,
                "row": enriched_row
            })
            
            # Increment classification counter
            summary[group_key][classification] = summary[group_key].get(classification, 0) + 1
            
            # Track all dates
            all_dates.add(date)
        except Exception as e:
            logger.error(f"Error processing row: {str(e)}")
            continue
    
    # Create final report
    report = []
    
    if group_by == 'driver':
        key_name = 'driver'
    else:
        key_name = group_by
    
    for key, record in summary.items():
        total_days = len(record["daily"])
        if total_days == 0:
            continue
            
        report_item = {
            key_name: key,
            "total_days": total_days,
            "on_time": record.get("On Time", 0),
            "late": record.get("Late", 0),
            "early_end": record.get("Early End", 0),
            "no_show": record.get("No Show", 0),
            "unknown": record.get("Unknown", 0),
            "attendance_rate": round((record.get("On Time", 0) / total_days) * 100 if total_days > 0 else 0, 1),
            "daily_breakdown": record["daily"]
        }
        
        # Add additional metadata based on grouping
        if group_by == 'job_number' and record["daily"]:
            sample_row = record["daily"][0]["row"]
            report_item["job_description"] = sample_row.get("job_description", "Unknown")
            report_item["division"] = sample_row.get("division", "Unknown")
            report_item["zone"] = sample_row.get("zone")
        elif group_by == 'division' and record["daily"]:
            # Count unique job numbers in this division
            job_numbers = set()
            for day in record["daily"]:
                job_num = day["row"].get("normalized_job_number")
                if job_num:
                    job_numbers.add(job_num)
            report_item["job_count"] = len(job_numbers)
        
        report.append(report_item)
    
    # Default sort by name/key
    sorted_report = sorted(report, key=lambda x: x[key_name])
    
    return {
        "group_by": group_by,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(max(all_dates)) if all_dates else None,
        "total_entries": len(data),
        "summary_items": len(sorted_report),
        "all_dates": [str(d) for d in sorted(all_dates)],
        "report": sorted_report
    }

def get_date_range(data: List[Dict[str, Any]], weeks: int = 1) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """
    Determine the date range for the report
    
    Args:
        data (list): List of attendance data records
        weeks (int): Number of weeks to include
        
    Returns:
        tuple: (start_date, end_date)
    """
    dates = []
    for row in data:
        raw_date = row.get('Date')
        if raw_date:
            date = parse_date(raw_date)
            if date:
                dates.append(date)
    
    if not dates:
        # Default to current week
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    # Find max date and calculate start date
    max_date = max(dates)
    start_date = max_date - timedelta(days=7 * weeks - 1)
    
    return start_date, max_date

def handle(data: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a batch of records for weekly driver summary
    
    Args:
        data (list): List of records to summarize
        options (dict, optional): Processing options
            - group_by (str): Grouping option ('driver', 'job_number', 'division', 'zone')
            - weeks (int): Number of weeks to include
            - start_date (str): Start date for filtering (overrides weeks)
            
    Returns:
        dict: Summary results with grouped attendance data
    """
    if options is None:
        options = {}
    
    # Get processing options
    group_by = options.get('group_by', 'driver')
    weeks = int(options.get('weeks', 1))
    
    # Determine date range
    if 'start_date' in options:
        start_date = parse_date(options['start_date'])
    else:
        start_date, _ = get_date_range(data, weeks)
    
    # Generate summary
    summary = summarize_week(data, start_date, group_by)
    
    return summary