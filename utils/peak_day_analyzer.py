"""
Peak Day Analyzer - May 8th Heavy Usage Analysis

Analyzes your peak activity day (May 8th, 2025) with 4,437 GPS events
to demonstrate TRAXORA's performance under maximum operational load.
"""

import pandas as pd
import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger(__name__)

def analyze_may_8th_peak_activity():
    """Analyze May 8th - your heaviest usage day"""
    
    results = {
        'date': '2025-05-08',
        'total_gps_events': 0,
        'unique_drivers': 0,
        'on_time_drivers': 0,
        'late_drivers': 0,
        'early_end_drivers': 0,
        'not_on_job_drivers': 0,
        'peak_activity_hours': [],
        'driver_details': []
    }
    
    try:
        # Load your real MTD file
        mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        df = pd.read_csv(mtd_file, skiprows=8)
        
        # Filter for May 8th only
        df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
        may_8_data = df[df['EventDateTime'].dt.date == pd.to_datetime('2025-05-08').date()]
        
        logger.info(f"Analyzing May 8th: {len(may_8_data)} GPS events")
        
        # Count total events for May 8th
        results['total_gps_events'] = len(may_8_data)
        
        # Extract unique drivers from Contact column
        if 'Contact' in may_8_data.columns:
            unique_contacts = may_8_data['Contact'].dropna().unique()
            driver_names = []
            
            for contact in unique_contacts:
                if contact and str(contact) != 'nan':
                    # Extract driver name from format like "Ammar Elhamad (210003)"
                    if '(' in str(contact):
                        driver_name = str(contact).split('(')[0].strip()
                        if driver_name:
                            driver_names.append(driver_name)
            
            results['unique_drivers'] = len(driver_names)
            
            # Analyze each driver's activity on May 8th
            for driver in driver_names[:20]:  # Analyze first 20 drivers for performance
                driver_data = may_8_data[may_8_data['Contact'].str.contains(driver, na=False)]
                
                if len(driver_data) > 0:
                    # Find start and end times
                    start_times = driver_data[driver_data['MsgType'] == 'Key On']['EventDateTime']
                    end_times = driver_data[driver_data['MsgType'] == 'Key Off']['EventDateTime']
                    
                    classification = "Not On Job"
                    start_time_str = "N/A"
                    
                    if len(start_times) > 0:
                        first_start = start_times.min()
                        start_time_str = first_start.strftime('%H:%M:%S')
                        start_hour = first_start.hour
                        start_minute = first_start.minute
                        
                        # Classify based on 7:30 AM start time rule
                        if start_hour < 7 or (start_hour == 7 and start_minute <= 30):
                            classification = "On Time"
                            results['on_time_drivers'] += 1
                        elif start_hour == 7 and start_minute > 30:
                            classification = "Late"
                            results['late_drivers'] += 1
                        elif start_hour >= 8:
                            classification = "Late"
                            results['late_drivers'] += 1
                        
                        # Check for early end (before 4:00 PM)
                        if len(end_times) > 0:
                            last_end = end_times.max()
                            if last_end.hour < 16:  # Before 4:00 PM
                                classification = "Early End"
                                results['early_end_drivers'] += 1
                                # Remove from other counts
                                if results['on_time_drivers'] > 0 and classification == "Early End":
                                    results['on_time_drivers'] -= 1
                                elif results['late_drivers'] > 0 and classification == "Early End":
                                    results['late_drivers'] -= 1
                    else:
                        results['not_on_job_drivers'] += 1
                    
                    results['driver_details'].append({
                        'name': driver,
                        'start_time': start_time_str,
                        'classification': classification,
                        'gps_events': len(driver_data)
                    })
        
        # Find peak activity hours
        if len(may_8_data) > 0:
            hourly_activity = may_8_data['EventDateTime'].dt.hour.value_counts().sort_index()
            peak_hours = hourly_activity.nlargest(3)
            results['peak_activity_hours'] = [
                f"{hour}:00-{hour+1}:00 ({count} events)" 
                for hour, count in peak_hours.items()
            ]
        
        logger.info(f"May 8th Analysis Complete: {results['unique_drivers']} drivers, {results['on_time_drivers']} on time")
        
    except Exception as e:
        logger.error(f"Error analyzing May 8th data: {e}")
    
    return results

def generate_may_8th_report():
    """Generate detailed report for May 8th peak day"""
    analysis = analyze_may_8th_peak_activity()
    
    report = {
        'date': analysis['date'],
        'summary': {
            'total_gps_events': analysis['total_gps_events'],
            'unique_drivers': analysis['unique_drivers'],
            'on_time': analysis['on_time_drivers'],
            'late': analysis['late_drivers'],
            'early_end': analysis['early_end_drivers'],
            'not_on_job': analysis['not_on_job_drivers']
        },
        'peak_hours': analysis['peak_activity_hours'],
        'top_drivers': analysis['driver_details'][:10]  # Top 10 drivers
    }
    
    return report