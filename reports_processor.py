"""
Reports Processor Module

This module processes asset data to generate various reports and analytics
that will be displayed on the reports page.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reports directory
REPORTS_DIR = 'data/reports'
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR, exist_ok=True)


def parse_date(date_str):
    """Parse date string into datetime object"""
    try:
        # Handle various date formats
        formats = [
            "%m/%d/%Y %I:%M:%S %p %Z",  # Example: "5/15/2025 8:30:02 AM CT"
            "%m/%d/%Y %I:%M:%S %p"      # Example: "5/15/2025 8:30:02 AM"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.split(' CT')[0], fmt)
            except ValueError:
                continue
                
        # If all formats fail, raise exception
        raise ValueError(f"Could not parse date: {date_str}")
    except Exception as e:
        logger.warning(f"Date parsing error: {e}")
        return None


def calculate_activity_metrics(assets):
    """
    Calculate activity metrics for assets
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        dict: Dictionary with activity metrics
    """
    # Initialize metrics
    metrics = {
        "total_assets": len(assets),
        "active_assets": 0,
        "inactive_assets": 0,
        "activity_by_day": defaultdict(lambda: {"active": 0, "inactive": 0}),
        "activity_by_category": defaultdict(lambda: {"active": 0, "inactive": 0, "total": 0}),
        "activity_by_location": defaultdict(lambda: {"active": 0, "inactive": 0, "total": 0}),
        "utilization_rate": 0,
        "avg_engine_hours": 0,
        "inactive_durations": []
    }
    
    # Calculate metrics
    total_engine_hours = 0
    engine_hours_count = 0
    
    for asset in assets:
        # Status counts
        is_active = asset.get('Active', False)
        if is_active:
            metrics["active_assets"] += 1
        else:
            metrics["inactive_assets"] += 1
            
            # Track inactive durations
            days_inactive = asset.get('DaysInactive')
            if days_inactive and days_inactive != 'N/A':
                try:
                    metrics["inactive_durations"].append(int(days_inactive))
                except (ValueError, TypeError):
                    pass
        
        # Track by category
        category = asset.get('AssetCategory', 'Unknown')
        metrics["activity_by_category"][category]["total"] += 1
        if is_active:
            metrics["activity_by_category"][category]["active"] += 1
        else:
            metrics["activity_by_category"][category]["inactive"] += 1
            
        # Track by location
        location = asset.get('Location', 'Unknown')
        metrics["activity_by_location"][location]["total"] += 1
        if is_active:
            metrics["activity_by_location"][location]["active"] += 1
        else:
            metrics["activity_by_location"][location]["inactive"] += 1
            
        # Track by day (last 7 days)
        event_date_str = asset.get('EventDateTimeString')
        if event_date_str:
            event_date = parse_date(event_date_str)
            if event_date:
                date_key = event_date.strftime('%Y-%m-%d')
                if is_active:
                    metrics["activity_by_day"][date_key]["active"] += 1
                else:
                    metrics["activity_by_day"][date_key]["inactive"] += 1
        
        # Track engine hours
        engine_hours = asset.get('Engine1Hours')
        if engine_hours:
            try:
                engine_hours = float(engine_hours)
                total_engine_hours += engine_hours
                engine_hours_count += 1
            except (ValueError, TypeError):
                pass
    
    # Calculate derived metrics
    if metrics["total_assets"] > 0:
        metrics["utilization_rate"] = metrics["active_assets"] / metrics["total_assets"] * 100
        
    if engine_hours_count > 0:
        metrics["avg_engine_hours"] = total_engine_hours / engine_hours_count
        
    # Sort activity by days for the last 7 days
    today = datetime.now().date()
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    metrics["activity_by_day_sorted"] = [
        {
            "date": day,
            "active": metrics["activity_by_day"][day]["active"],
            "inactive": metrics["activity_by_day"][day]["inactive"]
        }
        for day in last_7_days
    ]
    
    # Calculate maintenance stats based on engine hours
    metrics["maintenance_due"] = []
    for asset in assets:
        engine_hours = asset.get('Engine1Hours')
        if engine_hours:
            try:
                engine_hours = float(engine_hours)
                # Assuming maintenance is due every 500 hours
                maintenance_threshold = 500
                hours_until_maintenance = maintenance_threshold - (engine_hours % maintenance_threshold)
                
                # If due for maintenance soon (within 50 hours)
                if hours_until_maintenance <= 50:
                    metrics["maintenance_due"].append({
                        "asset_id": asset.get('AssetIdentifier'),
                        "asset_label": asset.get('Label', ''),
                        "engine_hours": engine_hours,
                        "hours_until_maintenance": hours_until_maintenance
                    })
            except (ValueError, TypeError):
                pass
    
    return metrics


def generate_activity_report(assets):
    """
    Generate activity report for assets
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        dict: Report data
    """
    metrics = calculate_activity_metrics(assets)
    
    # Create report
    report = {
        "generated_at": datetime.now().isoformat(),
        "metrics": metrics,
        "top_categories": sorted(
            [
                {"category": category, "count": data["total"], "active": data["active"], "inactive": data["inactive"]}
                for category, data in metrics["activity_by_category"].items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:10],
        "top_locations": sorted(
            [
                {"location": location, "count": data["total"], "active": data["active"], "inactive": data["inactive"]}
                for location, data in metrics["activity_by_location"].items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
    }
    
    return report


def save_activity_report(report):
    """
    Save activity report to file
    
    Args:
        report (dict): Report data
    
    Returns:
        str: Path to the saved report file
    """
    filename = f"activity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved activity report to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save activity report: {e}")
        return None


def generate_maintenance_report(assets):
    """
    Generate maintenance report for assets
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        dict: Report data
    """
    maintenance_items = []
    
    for asset in assets:
        engine_hours = asset.get('Engine1Hours')
        if engine_hours:
            try:
                engine_hours = float(engine_hours)
                
                # Maintenance thresholds (in hours)
                oil_change = 250
                filter_change = 500
                major_service = 1000
                
                # Calculate hours until next maintenance
                hours_until_oil = oil_change - (engine_hours % oil_change)
                hours_until_filter = filter_change - (engine_hours % filter_change)
                hours_until_major = major_service - (engine_hours % major_service)
                
                # Add to maintenance items if due soon
                threshold = 50  # Consider "due soon" if within 50 hours
                
                maintenance_item = {
                    "asset_id": asset.get('AssetIdentifier'),
                    "asset_label": asset.get('Label', ''),
                    "asset_category": asset.get('AssetCategory', 'Unknown'),
                    "engine_hours": engine_hours,
                    "maintenance_items": []
                }
                
                if hours_until_oil <= threshold:
                    maintenance_item["maintenance_items"].append({
                        "type": "Oil Change",
                        "hours_remaining": hours_until_oil,
                        "priority": "High" if hours_until_oil <= 10 else "Medium"
                    })
                
                if hours_until_filter <= threshold:
                    maintenance_item["maintenance_items"].append({
                        "type": "Filter Change",
                        "hours_remaining": hours_until_filter,
                        "priority": "High" if hours_until_filter <= 10 else "Medium"
                    })
                
                if hours_until_major <= threshold:
                    maintenance_item["maintenance_items"].append({
                        "type": "Major Service",
                        "hours_remaining": hours_until_major,
                        "priority": "High" if hours_until_major <= 10 else "Medium"
                    })
                
                if maintenance_item["maintenance_items"]:
                    maintenance_items.append(maintenance_item)
                    
            except (ValueError, TypeError):
                pass
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "maintenance_items": maintenance_items,
        "total_items": len(maintenance_items),
        "maintenance_summary": {
            "high_priority": sum(1 for item in maintenance_items for maint in item["maintenance_items"] if maint["priority"] == "High"),
            "medium_priority": sum(1 for item in maintenance_items for maint in item["maintenance_items"] if maint["priority"] == "Medium"),
        }
    }
    
    return report


def get_latest_reports():
    """
    Get the latest generated reports
    
    Returns:
        dict: Dictionary with latest report data
    """
    try:
        # Find the latest activity report file
        activity_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith('activity_report_')]
        if not activity_files:
            return None
        
        latest_activity_file = sorted(activity_files)[-1]
        with open(os.path.join(REPORTS_DIR, latest_activity_file), 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load latest reports: {e}")
        return None


def generate_reports(assets):
    """
    Generate all reports for the assets data
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        bool: True if reports were generated successfully, False otherwise
    """
    try:
        # Generate and save activity report
        activity_report = generate_activity_report(assets)
        save_activity_report(activity_report)
        
        # Generate maintenance report
        maintenance_report = generate_maintenance_report(assets)
        
        # Combine reports
        combined_report = {
            "activity_report": activity_report,
            "maintenance_report": maintenance_report
        }
        
        # Save combined report
        combined_filepath = os.path.join(REPORTS_DIR, "latest_reports.json")
        with open(combined_filepath, 'w') as f:
            json.dump(combined_report, f, indent=2)
            
        logger.info(f"Generated and saved all reports")
        return True
    except Exception as e:
        logger.error(f"Failed to generate reports: {e}")
        return False


# Execute this if the script is run directly
if __name__ == "__main__":
    # Load data from the most recent file
    from gauge_api import get_asset_data
    
    print("Loading asset data...")
    assets = get_asset_data()
    
    if assets:
        print(f"Generating reports for {len(assets)} assets...")
        generate_reports(assets)
        print("Reports generated successfully!")