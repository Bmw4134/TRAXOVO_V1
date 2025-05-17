"""
Equipment Alerts Processor

This module analyzes equipment data to detect inactivity and unusual patterns,
generates alerts, and provides notification capabilities.

Alerts are categorized by severity:
- Critical: Immediate attention required (e.g., equipment inactive for >7 days)
- Warning: Potential issues that need monitoring (e.g., unusual usage patterns)
- Info: Informational alerts (e.g., scheduled maintenance coming up)
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

# Import needed modules only when functions are called
# to avoid circular imports
def analyze_equipment_inactivity(days_threshold=3, critical_days=7):
    """
    Analyze equipment data to detect inactive equipment
    
    Args:
        days_threshold (int): Number of days threshold for warning alerts
        critical_days (int): Number of days threshold for critical alerts
        
    Returns:
        dict: Dictionary of inactive equipment alerts
    """
    try:
        # Import here to avoid circular imports
        from gauge_api import get_asset_data
        from models import Asset, AssetHistory, db
        
        # Get current datetime
        now = datetime.now()
        
        # Get asset data from database and API
        assets_data = get_asset_data(use_db=True)
        
        # Initialize alerts list
        inactivity_alerts = []
        
        logger.info(f"Analyzing {len(assets_data)} assets for inactivity")
        
        # Process each asset
        for asset in assets_data:
            # Skip assets that aren't tracked for activity
            if asset.get('AssetCategory') in ['Trailers', 'Attachments']:
                continue
                
            # Get event datetime
            last_activity = None
            if asset.get('EventDateTimeString'):
                try:
                    dt_str = asset.get('EventDateTimeString')
                    dt_parts = dt_str.split(' ')
                    if len(dt_parts) >= 3:
                        date_part = dt_parts[0]
                        time_part = dt_parts[1]
                        am_pm = dt_parts[2]
                        date_obj = datetime.strptime(f"{date_part} {time_part} {am_pm}", "%m/%d/%Y %I:%M:%S %p")
                        last_activity = date_obj
                except Exception as e:
                    logger.warning(f"Could not parse datetime for asset {asset.get('AssetIdentifier')}: {e}")
            
            # Check for inactive assets
            if not last_activity:
                # Try to get the last activity from asset history
                try:
                    asset_id = asset.get('AssetIdentifier')
                    db_asset = Asset.query.filter_by(asset_identifier=asset_id).first()
                    if db_asset:
                        latest_history = AssetHistory.query.filter_by(
                            asset_id=db_asset.id
                        ).order_by(AssetHistory.created_at.desc()).first()
                        
                        if latest_history and latest_history.event_date_time:
                            last_activity = latest_history.event_date_time
                except Exception as e:
                    logger.warning(f"Error retrieving history for {asset.get('AssetIdentifier')}: {e}")
            
            # If we still don't have activity data, use days_inactive if available
            if not last_activity and asset.get('DaysInactive') is not None:
                # Create a date based on days inactive
                try:
                    days_inactive = float(asset.get('DaysInactive'))
                    last_activity = now - timedelta(days=days_inactive)
                except (ValueError, TypeError):
                    pass
            
            # Skip if we have no activity data
            if not last_activity:
                continue
                
            # Calculate days inactive
            days_inactive = (now - last_activity).total_seconds() / (3600 * 24)
            
            # Generate alert if inactive beyond threshold
            if days_inactive >= critical_days:
                alert_level = 'critical'
            elif days_inactive >= days_threshold:
                alert_level = 'warning'
            else:
                continue  # No alert needed
                
            # Create alert
            alert = {
                'asset_id': asset.get('AssetIdentifier'),
                'asset_label': asset.get('Label'),
                'type': 'inactivity',
                'level': alert_level,
                'days_inactive': round(days_inactive, 1),
                'last_activity': last_activity.strftime('%Y-%m-%d %H:%M:%S') if last_activity else 'Unknown',
                'location': asset.get('Location'),
                'description': f"Equipment inactive for {round(days_inactive, 1)} days",
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            inactivity_alerts.append(alert)
        
        logger.info(f"Generated {len(inactivity_alerts)} inactivity alerts")
        return inactivity_alerts
        
    except Exception as e:
        logger.error(f"Error analyzing equipment inactivity: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_unusual_patterns(variance_threshold=2.0):
    """
    Analyze equipment usage patterns to detect unusual activity
    
    Args:
        variance_threshold (float): Threshold for standard deviation significance
        
    Returns:
        dict: Dictionary of unusual pattern alerts
    """
    try:
        # Import here to avoid circular imports
        from models import Asset, AssetHistory, db
        
        # Initialize alerts list
        pattern_alerts = []
        
        # Get current datetime
        now = datetime.now()
        
        # Query assets with history
        assets_with_history = db.session.query(Asset).join(
            AssetHistory, Asset.id == AssetHistory.asset_id
        ).group_by(Asset.id).having(
            func.count(AssetHistory.id) > 5  # Need enough data points
        ).all()
        
        logger.info(f"Analyzing {len(assets_with_history)} assets for unusual patterns")
        
        # Process each asset
        for asset in assets_with_history:
            # Get history for this asset
            history = AssetHistory.query.filter_by(
                asset_id=asset.id
            ).order_by(AssetHistory.created_at.desc()).limit(30).all()
            
            # Skip if not enough history
            if len(history) < 5:
                continue
                
            # Analyze engine hours changes
            try:
                # Extract engine hours
                hours_data = [h.engine_hours for h in history if h.engine_hours is not None]
                
                # Calculate daily change in engine hours
                if len(hours_data) >= 2:
                    hour_changes = []
                    for i in range(len(hours_data) - 1):
                        change = hours_data[i] - hours_data[i+1]
                        if change >= 0:  # Ensure not negative (time moves forward)
                            hour_changes.append(change)
                    
                    # Calculate statistics
                    if hour_changes:
                        avg_change = np.mean(hour_changes)
                        std_dev = np.std(hour_changes)
                        latest_change = hours_data[0] - hours_data[1] if len(hours_data) >= 2 else 0
                        
                        # Check for unusual activity
                        if std_dev > 0 and avg_change > 0:
                            z_score = (latest_change - avg_change) / std_dev
                            
                            # Alert on unusually high or low activity
                            if abs(z_score) > variance_threshold:
                                alert_level = 'warning'
                                
                                if latest_change > avg_change + std_dev * variance_threshold:
                                    pattern_type = "high_usage"
                                    description = f"Unusually high usage detected: {round(latest_change, 1)} hours vs avg {round(avg_change, 1)} hours"
                                else:
                                    pattern_type = "low_usage"
                                    description = f"Unusually low usage detected: {round(latest_change, 1)} hours vs avg {round(avg_change, 1)} hours"
                                
                                # Create alert
                                alert = {
                                    'asset_id': asset.asset_identifier,
                                    'asset_label': asset.label,
                                    'type': pattern_type, 
                                    'level': alert_level,
                                    'latest_value': round(latest_change, 1),
                                    'average_value': round(avg_change, 1),
                                    'z_score': round(z_score, 2),
                                    'description': description,
                                    'location': asset.location,
                                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                pattern_alerts.append(alert)
            except Exception as e:
                logger.warning(f"Error analyzing patterns for asset {asset.asset_identifier}: {e}")
        
        logger.info(f"Generated {len(pattern_alerts)} pattern alerts")
        return pattern_alerts
        
    except Exception as e:
        logger.error(f"Error analyzing equipment patterns: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_maintenance_needs():
    """
    Analyze equipment to detect upcoming maintenance needs
    
    Returns:
        dict: Dictionary of maintenance alerts
    """
    try:
        # Import here to avoid circular imports
        from gauge_api import get_asset_data
        from models import Asset, AssetHistory, MaintenanceRecord, db
        
        # Get current datetime
        now = datetime.now()
        
        # Initialize alerts list
        maintenance_alerts = []
        
        # Get all assets with maintenance schedules
        assets_with_maintenance = db.session.query(Asset).join(
            MaintenanceRecord, Asset.id == MaintenanceRecord.asset_id
        ).all()
        
        logger.info(f"Analyzing {len(assets_with_maintenance)} assets for maintenance needs")
        
        # Process each asset
        for asset in assets_with_maintenance:
            # Get latest maintenance record
            latest_maintenance = MaintenanceRecord.query.filter_by(
                asset_id=asset.id
            ).order_by(MaintenanceRecord.service_date.desc()).first()
            
            if not latest_maintenance:
                continue
                
            # Check for maintenance intervals (hours-based)
            if latest_maintenance.hours_interval and asset.engine_hours:
                hours_since_maintenance = asset.engine_hours - latest_maintenance.last_service_hours
                hours_remaining = latest_maintenance.hours_interval - hours_since_maintenance
                
                # Alert if within 10% of maintenance interval
                if hours_remaining <= 0:
                    alert_level = 'critical'
                    description = f"Maintenance overdue by {abs(round(hours_remaining, 1))} engine hours"
                elif hours_remaining <= latest_maintenance.hours_interval * 0.1:
                    alert_level = 'warning'
                    description = f"Maintenance due soon: {round(hours_remaining, 1)} engine hours remaining"
                else:
                    continue  # No alert needed
                    
                # Create alert
                alert = {
                    'asset_id': asset.asset_identifier,
                    'asset_label': asset.label,
                    'type': 'maintenance_hours',
                    'level': alert_level, 
                    'hours_remaining': round(hours_remaining, 1),
                    'last_service_date': latest_maintenance.service_date.strftime('%Y-%m-%d'),
                    'description': description,
                    'location': asset.location,
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                maintenance_alerts.append(alert)
            
            # Check for maintenance intervals (date-based)
            if latest_maintenance.days_interval and latest_maintenance.service_date:
                days_since_maintenance = (now.date() - latest_maintenance.service_date).days
                days_remaining = latest_maintenance.days_interval - days_since_maintenance
                
                # Alert if within 10% of maintenance interval
                if days_remaining <= 0:
                    alert_level = 'critical'
                    description = f"Maintenance overdue by {abs(days_remaining)} days"
                elif days_remaining <= latest_maintenance.days_interval * 0.1:
                    alert_level = 'warning'
                    description = f"Maintenance due soon: {days_remaining} days remaining"
                else:
                    continue  # No alert needed
                    
                # Create alert
                alert = {
                    'asset_id': asset.asset_identifier,
                    'asset_label': asset.label,
                    'type': 'maintenance_days',
                    'level': alert_level,
                    'days_remaining': days_remaining,
                    'last_service_date': latest_maintenance.service_date.strftime('%Y-%m-%d'),
                    'description': description,
                    'location': asset.location,
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                maintenance_alerts.append(alert)
        
        logger.info(f"Generated {len(maintenance_alerts)} maintenance alerts")
        return maintenance_alerts
        
    except Exception as e:
        logger.error(f"Error analyzing maintenance needs: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_equipment_alerts():
    """
    Generate all equipment alerts by calling the analysis functions
    
    Returns:
        list: Combined list of all equipment alerts
    """
    all_alerts = []
    
    # Generate inactivity alerts
    inactivity_alerts = analyze_equipment_inactivity()
    all_alerts.extend(inactivity_alerts)
    
    # Generate pattern alerts
    pattern_alerts = analyze_unusual_patterns()
    all_alerts.extend(pattern_alerts)
    
    # Generate maintenance alerts
    maintenance_alerts = analyze_maintenance_needs()
    all_alerts.extend(maintenance_alerts)
    
    # Save alerts to file
    save_alerts_to_file(all_alerts)
    
    return all_alerts

def save_alerts_to_file(alerts):
    """
    Save alerts to a JSON file for persistence
    
    Args:
        alerts (list): List of alert dictionaries
        
    Returns:
        bool: Success status
    """
    try:
        # Ensure directory exists
        alerts_dir = os.path.join('data', 'alerts')
        os.makedirs(alerts_dir, exist_ok=True)
        
        # Generate filename with date
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(alerts_dir, f'equipment_alerts_{date_str}.json')
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(alerts, f, indent=2)
            
        logger.info(f"Saved {len(alerts)} alerts to {filename}")
        
        # Also save latest alerts to a fixed filename
        latest_file = os.path.join(alerts_dir, 'latest_equipment_alerts.json')
        with open(latest_file, 'w') as f:
            json.dump(alerts, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error saving alerts to file: {e}")
        return False

def load_alerts_from_file():
    """
    Load alerts from the latest JSON file
    
    Returns:
        list: List of alert dictionaries
    """
    try:
        # Check for latest alerts file
        latest_file = os.path.join('data', 'alerts', 'latest_equipment_alerts.json')
        
        if not os.path.exists(latest_file):
            logger.warning(f"No alerts file found at {latest_file}")
            return []
            
        # Load from file
        with open(latest_file, 'r') as f:
            alerts = json.load(f)
            
        logger.info(f"Loaded {len(alerts)} alerts from {latest_file}")
        return alerts
    except Exception as e:
        logger.error(f"Error loading alerts from file: {e}")
        return []

def get_alerts_by_severity(alerts=None):
    """
    Group alerts by severity level
    
    Args:
        alerts (list, optional): List of alert dictionaries, if None will load from file
        
    Returns:
        dict: Dictionary of alerts grouped by severity
    """
    if alerts is None:
        alerts = load_alerts_from_file()
        
    # Group by severity
    severity_groups = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    for alert in alerts:
        level = alert.get('level', 'info')
        if level in severity_groups:
            severity_groups[level].append(alert)
    
    return severity_groups

def get_alerts_by_type(alerts=None):
    """
    Group alerts by type
    
    Args:
        alerts (list, optional): List of alert dictionaries, if None will load from file
        
    Returns:
        dict: Dictionary of alerts grouped by type
    """
    if alerts is None:
        alerts = load_alerts_from_file()
        
    # Group by type
    type_groups = defaultdict(list)
    
    for alert in alerts:
        alert_type = alert.get('type', 'other')
        type_groups[alert_type].append(alert)
    
    return dict(type_groups)

def get_alerts_by_location(alerts=None):
    """
    Group alerts by location
    
    Args:
        alerts (list, optional): List of alert dictionaries, if None will load from file
        
    Returns:
        dict: Dictionary of alerts grouped by location
    """
    if alerts is None:
        alerts = load_alerts_from_file()
        
    # Group by location
    location_groups = defaultdict(list)
    
    for alert in alerts:
        location = alert.get('location', 'Unknown')
        location_groups[location].append(alert)
    
    return dict(location_groups)

def get_alerts_summary():
    """
    Generate a summary of all alerts
    
    Returns:
        dict: Summary of alerts by severity, type, and location
    """
    # Load alerts from file
    alerts = load_alerts_from_file()
    
    # Group by severity
    by_severity = get_alerts_by_severity(alerts)
    
    # Group by type
    by_type = get_alerts_by_type(alerts)
    
    # Group by location
    by_location = get_alerts_by_location(alerts)
    
    # Count alerts
    severity_counts = {level: len(alerts) for level, alerts in by_severity.items()}
    type_counts = {alert_type: len(alerts) for alert_type, alerts in by_type.items()}
    location_counts = {location: len(alerts) for location, alerts in by_location.items()}
    
    # Return summary
    return {
        'total_alerts': len(alerts),
        'severity_counts': severity_counts,
        'type_counts': type_counts,
        'location_counts': location_counts,
        'alerts_by_severity': by_severity,
        'alerts_by_type': by_type,
        'alerts_by_location': by_location,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Generate equipment alerts
    alerts = generate_equipment_alerts()
    
    # Print summary
    summary = get_alerts_summary()
    print(f"Generated {summary['total_alerts']} alerts:")
    print(f"  Critical: {summary['severity_counts'].get('critical', 0)}")
    print(f"  Warning: {summary['severity_counts'].get('warning', 0)}")
    print(f"  Info: {summary['severity_counts'].get('info', 0)}")