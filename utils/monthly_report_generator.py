"""
TRAXORA Monthly Report Generator - Complete Fleet Analysis

This module generates comprehensive monthly reports from your MTD files,
extracting all 133 asset-driver assignments and providing detailed metrics
for your complete fleet operations.
"""

import pandas as pd
import os
import logging
from datetime import datetime, timedelta
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

def extract_all_drivers_from_mtd():
    """Extract all drivers from your complete MTD file"""
    
    driving_history_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
    
    if not os.path.exists(driving_history_file):
        logger.error(f"MTD file not found: {driving_history_file}")
        return []
    
    try:
        # Read complete MTD file
        df = pd.read_csv(driving_history_file, skiprows=8, low_memory=False)
        
        # Extract all asset-driver assignments from Textbox53
        asset_assignments = df['Textbox53'].dropna().unique()
        
        drivers = []
        for assignment in asset_assignments:
            if assignment and str(assignment) != 'nan':
                assignment_str = str(assignment)
                
                driver_info = {
                    'asset_assignment': assignment_str,
                    'driver_name': None,
                    'asset_id': None,
                    'vehicle_type': None
                }
                
                # Format 1: "#210003 - AMMAR I. ELHAMAD FORD F150 2024"
                if ' - ' in assignment_str and assignment_str.startswith('#'):
                    parts = assignment_str.split(' - ', 1)
                    if len(parts) > 1:
                        driver_info['asset_id'] = parts[0]
                        name_and_vehicle = parts[1]
                        # Extract driver name (first few words before vehicle info)
                        words = name_and_vehicle.split()
                        name_words = []
                        for word in words:
                            if word.isupper() or (len(word) > 1 and word[0].isupper() and word[1:].islower()):
                                name_words.append(word)
                            else:
                                break
                        if name_words:
                            driver_info['driver_name'] = ' '.join(name_words[:4])  # Max 4 words for name
                        
                        # Extract vehicle info
                        vehicle_words = []
                        for i, word in enumerate(words):
                            if word in ['FORD', 'RAM', 'CHEVROLET', 'JEEP', 'TOYOTA']:
                                vehicle_words = words[i:]
                                break
                        if vehicle_words:
                            driver_info['vehicle_type'] = ' '.join(vehicle_words[:3])
                
                # Format 2: "ET-01 (SAUL MARTINEZ ALVAREZ) RAM 1500 2022"
                elif '(' in assignment_str and ')' in assignment_str:
                    # Extract asset ID
                    driver_info['asset_id'] = assignment_str.split('(')[0].strip()
                    
                    # Extract driver name from parentheses
                    start = assignment_str.find('(') + 1
                    end = assignment_str.find(')')
                    if start > 0 and end > start:
                        driver_name = assignment_str[start:end].strip()
                        if driver_name and 'OPEN' not in driver_name.upper():
                            driver_info['driver_name'] = driver_name
                    
                    # Extract vehicle info (after parentheses)
                    after_parentheses = assignment_str[end+1:].strip()
                    if after_parentheses:
                        driver_info['vehicle_type'] = after_parentheses
                
                # Only include if we found a driver name
                if driver_info['driver_name']:
                    drivers.append(driver_info)
        
        logger.info(f"Extracted {len(drivers)} drivers from MTD file")
        return drivers
        
    except Exception as e:
        logger.error(f"Error extracting drivers: {e}")
        return []

def generate_monthly_attendance_report(drivers_list):
    """Generate comprehensive monthly attendance report"""
    
    try:
        # Read activity data for attendance analysis
        driving_history_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        df = pd.read_csv(driving_history_file, skiprows=8, low_memory=False)
        
        # Convert EventDateTime to datetime
        df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
        
        # Group by driver and analyze attendance patterns
        attendance_data = []
        
        for driver_info in drivers_list:
            driver_name = driver_info['driver_name']
            asset_id = driver_info['asset_id']
            
            # Filter data for this driver's asset
            driver_data = df[df['Textbox53'] == driver_info['asset_assignment']]
            
            if not driver_data.empty:
                # Analyze Key On/Off events for attendance
                key_events = driver_data[driver_data['MsgType'].isin(['Key On', 'Key Off'])]
                
                if not key_events.empty:
                    # Get unique dates this driver worked
                    work_dates = key_events['EventDateTime'].dt.date.unique()
                    
                    daily_stats = []
                    for date in work_dates:
                        date_events = key_events[key_events['EventDateTime'].dt.date == date]
                        key_on_events = date_events[date_events['MsgType'] == 'Key On']
                        key_off_events = date_events[date_events['MsgType'] == 'Key Off']
                        
                        if not key_on_events.empty and not key_off_events.empty:
                            first_on = key_on_events['EventDateTime'].min()
                            last_off = key_off_events['EventDateTime'].max()
                            
                            # Classification based on start time
                            start_hour = first_on.hour
                            end_hour = last_off.hour
                            
                            if start_hour <= 7:  # On time (7 AM or earlier)
                                status = 'On Time'
                            elif start_hour <= 8:  # Late but acceptable
                                status = 'Late'
                            else:  # Very late
                                status = 'Very Late'
                            
                            # Check for early end (before 4 PM)
                            if end_hour < 16:
                                status += ' / Early End'
                            
                            daily_stats.append({
                                'date': date,
                                'start_time': first_on,
                                'end_time': last_off,
                                'status': status,
                                'hours_worked': (last_off - first_on).total_seconds() / 3600
                            })
                    
                    # Calculate summary statistics
                    total_days = len(daily_stats)
                    on_time_days = len([d for d in daily_stats if 'On Time' in d['status']])
                    late_days = len([d for d in daily_stats if 'Late' in d['status']])
                    early_end_days = len([d for d in daily_stats if 'Early End' in d['status']])
                    
                    attendance_data.append({
                        'driver_name': driver_name,
                        'asset_id': asset_id,
                        'vehicle_type': driver_info['vehicle_type'],
                        'total_days_worked': total_days,
                        'on_time_days': on_time_days,
                        'late_days': late_days,
                        'early_end_days': early_end_days,
                        'attendance_rate': round((on_time_days / total_days * 100), 1) if total_days > 0 else 0,
                        'daily_details': daily_stats
                    })
        
        return attendance_data
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {e}")
        return []

def create_monthly_summary():
    """Create complete monthly summary report"""
    
    # Extract all drivers
    drivers = extract_all_drivers_from_mtd()
    
    if not drivers:
        return {
            'error': 'No drivers found in MTD file',
            'total_drivers': 0
        }
    
    # Generate attendance report
    attendance_data = generate_monthly_attendance_report(drivers)
    
    # Calculate fleet-wide metrics
    total_drivers = len(drivers)
    drivers_with_activity = len(attendance_data)
    
    if attendance_data:
        total_on_time = sum(d['on_time_days'] for d in attendance_data)
        total_late = sum(d['late_days'] for d in attendance_data)
        total_early_end = sum(d['early_end_days'] for d in attendance_data)
        total_days = sum(d['total_days_worked'] for d in attendance_data)
        
        fleet_metrics = {
            'total_assigned_drivers': total_drivers,
            'active_drivers': drivers_with_activity,
            'total_work_days': total_days,
            'on_time_percentage': round((total_on_time / total_days * 100), 1) if total_days > 0 else 0,
            'late_percentage': round((total_late / total_days * 100), 1) if total_days > 0 else 0,
            'early_end_percentage': round((total_early_end / total_days * 100), 1) if total_days > 0 else 0
        }
    else:
        fleet_metrics = {
            'total_assigned_drivers': total_drivers,
            'active_drivers': 0,
            'total_work_days': 0,
            'on_time_percentage': 0,
            'late_percentage': 0,
            'early_end_percentage': 0
        }
    
    return {
        'fleet_metrics': fleet_metrics,
        'driver_details': attendance_data,
        'all_drivers': drivers,
        'report_generated': datetime.now().isoformat()
    }

def save_monthly_report():
    """Save monthly report to file"""
    
    report_data = create_monthly_summary()
    
    # Ensure exports directory exists
    os.makedirs('exports', exist_ok=True)
    
    # Save JSON report
    json_file = f"exports/monthly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    # Save Excel report
    if report_data.get('driver_details'):
        excel_file = f"exports/monthly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Create summary sheet
        summary_df = pd.DataFrame([report_data['fleet_metrics']])
        
        # Create driver details sheet
        details_df = pd.DataFrame(report_data['driver_details'])
        
        # Create all drivers sheet
        all_drivers_df = pd.DataFrame(report_data['all_drivers'])
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Fleet Summary', index=False)
            details_df.to_excel(writer, sheet_name='Driver Details', index=False)
            all_drivers_df.to_excel(writer, sheet_name='All Drivers', index=False)
        
        logger.info(f"Monthly report saved to {excel_file}")
        return excel_file
    
    logger.info(f"Monthly report saved to {json_file}")
    return json_file

if __name__ == "__main__":
    # Generate and save monthly report
    report_file = save_monthly_report()
    print(f"Monthly report generated: {report_file}")