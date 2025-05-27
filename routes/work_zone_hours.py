"""
TRAXORA Work Zone Hours Module

Integrated with the attendance system to track and analyze work zone efficiency,
GPS boundaries, and productivity metrics for field operations.
"""

from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Initialize blueprint
work_zone_hours_bp = Blueprint('work_zone_hours', __name__)

logger = logging.getLogger(__name__)

def calculate_work_zone_validation(driver_records, timecard_data=None, payroll_data=None):
    """
    Calculate work zone hours validation against timecards and payroll
    Core function for validating company vehicle time-on-site vs logged time vs paid time
    """
    validation_data = {
        'gps_total_hours': 0,
        'timecard_total_hours': 0,
        'payroll_total_hours': 0,
        'variance_gps_timecard': 0,
        'variance_timecard_payroll': 0,
        'discrepancy_count': 0,
        'validation_rate': 0,
        'site_utilization': {},
        'driver_discrepancies': []
    }
    
    try:
        # Process each driver record for validation
        driver_hours_summary = defaultdict(lambda: {
            'gps_hours': 0, 'timecard_hours': 0, 'payroll_hours': 0,
            'dates': set(), 'discrepancies': []
        })
        
        for record in driver_records:
            driver_name = record.get('name', 'Unknown')
            work_date = record.get('date', '')
            
            # Calculate GPS-tracked hours (company vehicle time on site)
            start_time = record.get('start_time', '07:00')
            end_time = record.get('end_time', '16:00')
            
            if start_time and end_time and ':' in start_time and ':' in end_time:
                try:
                    start_hour = int(start_time.split(':')[0])
                    start_min = int(start_time.split(':')[1])
                    end_hour = int(end_time.split(':')[0])
                    end_min = int(end_time.split(':')[1])
                    
                    gps_hours = (end_hour + end_min/60) - (start_hour + start_min/60)
                    gps_hours = max(0, gps_hours)
                    
                    driver_hours_summary[driver_name]['gps_hours'] += gps_hours
                    driver_hours_summary[driver_name]['dates'].add(work_date)
                    validation_data['gps_total_hours'] += gps_hours
                    
                    # Simulate timecard hours (would be loaded from timecard system)
                    # Standard 8-hour day with variations based on status
                    if record.get('status') == 'On Time':
                        timecard_hours = 8.0
                    elif record.get('status') == 'Late Start':
                        timecard_hours = 7.0  # Logged 1 hour less
                    elif record.get('status') == 'Early End':
                        timecard_hours = 6.5  # Logged early departure
                    elif record.get('status') == 'Not On Job':
                        timecard_hours = 0.0  # No timecard entry
                    else:
                        timecard_hours = 8.0
                    
                    driver_hours_summary[driver_name]['timecard_hours'] += timecard_hours
                    validation_data['timecard_total_hours'] += timecard_hours
                    
                    # Simulate payroll hours (would be loaded from payroll system)
                    # Usually matches timecard but may have discrepancies
                    payroll_hours = timecard_hours
                    if abs(gps_hours - timecard_hours) > 1.5:  # Significant variance
                        payroll_hours = min(gps_hours, timecard_hours)  # Conservative approach
                    
                    driver_hours_summary[driver_name]['payroll_hours'] += payroll_hours
                    validation_data['payroll_total_hours'] += payroll_hours
                    
                    # Check for discrepancies
                    gps_timecard_variance = abs(gps_hours - timecard_hours)
                    timecard_payroll_variance = abs(timecard_hours - payroll_hours)
                    
                    if gps_timecard_variance > 0.5 or timecard_payroll_variance > 0.5:
                        validation_data['discrepancy_count'] += 1
                        driver_hours_summary[driver_name]['discrepancies'].append({
                            'date': work_date,
                            'gps_hours': round(gps_hours, 2),
                            'timecard_hours': round(timecard_hours, 2),
                            'payroll_hours': round(payroll_hours, 2),
                            'gps_timecard_variance': round(gps_timecard_variance, 2),
                            'timecard_payroll_variance': round(timecard_payroll_variance, 2),
                            'status': record.get('status', 'Unknown'),
                            'job_site': record.get('job_site', 'Unknown')
                        })
                    
                    # Track site utilization for validation
                    job_site = record.get('job_site', 'Unknown')
                    if job_site not in validation_data['site_utilization']:
                        validation_data['site_utilization'][job_site] = {
                            'gps_hours': 0,
                            'timecard_hours': 0,
                            'payroll_hours': 0,
                            'driver_count': 0,
                            'validation_rate': 0
                        }
                    
                    validation_data['site_utilization'][job_site]['gps_hours'] += gps_hours
                    validation_data['site_utilization'][job_site]['timecard_hours'] += timecard_hours
                    validation_data['site_utilization'][job_site]['payroll_hours'] += payroll_hours
                    validation_data['site_utilization'][job_site]['driver_count'] += 1
                    
                except ValueError as e:
                    logger.error(f"Error parsing time for {driver_name}: {e}")
                    continue
        
        # Calculate overall variances
        if validation_data['timecard_total_hours'] > 0:
            validation_data['variance_gps_timecard'] = round(
                abs(validation_data['gps_total_hours'] - validation_data['timecard_total_hours']), 2
            )
        
        if validation_data['payroll_total_hours'] > 0:
            validation_data['variance_timecard_payroll'] = round(
                abs(validation_data['timecard_total_hours'] - validation_data['payroll_total_hours']), 2
            )
        
        # Calculate validation rate (percentage of records without significant discrepancies)
        total_records = len(driver_records)
        if total_records > 0:
            validation_data['validation_rate'] = round(
                ((total_records - validation_data['discrepancy_count']) / total_records) * 100, 2
            )
        
        # Calculate site-specific validation rates
        for site_data in validation_data['site_utilization'].values():
            if site_data['timecard_hours'] > 0:
                variance = abs(site_data['gps_hours'] - site_data['timecard_hours'])
                site_data['validation_rate'] = round(
                    max(0, 100 - (variance / site_data['timecard_hours'] * 100)), 2
                )
        
        # Compile driver-specific discrepancy summary
        for driver_name, summary in driver_hours_summary.items():
            if summary['discrepancies']:
                validation_data['driver_discrepancies'].append({
                    'driver_name': driver_name,
                    'total_gps_hours': round(summary['gps_hours'], 2),
                    'total_timecard_hours': round(summary['timecard_hours'], 2),
                    'total_payroll_hours': round(summary['payroll_hours'], 2),
                    'days_worked': len(summary['dates']),
                    'discrepancy_count': len(summary['discrepancies']),
                    'discrepancies': summary['discrepancies']
                })
    
    except Exception as e:
        logger.error(f"Error calculating work zone validation: {e}")
    
    return validation_data

def get_gps_zone_data(job_site):
    """Get GPS zone boundaries and tracking data for a job site"""
    # Integration with your authentic job site data
    zone_data = {
        'coordinates': {
            'center': {'lat': 32.7555, 'lng': -97.3308},
            'radius': 400
        },
        'active_drivers': 0,
        'zone_violations': 0,
        'coverage_area': '400m radius'
    }
    
    # Customize based on authentic job sites
    if job_site == '2024-004 - City of Dallas Sidewalks':
        zone_data['coordinates'] = {
            'center': {'lat': 32.7555, 'lng': -97.3308},
            'radius': 400
        }
        zone_data['coverage_area'] = 'Dallas Sidewalks Project Area'
    elif job_site == 'TEXDIST':
        zone_data['coordinates'] = {
            'center': {'lat': 32.7767, 'lng': -96.7970},
            'radius': 500
        }
        zone_data['coverage_area'] = 'TEXDIST Operations Zone'
    elif 'HOU' in job_site:
        zone_data['coordinates'] = {
            'center': {'lat': 29.7604, 'lng': -95.3698},
            'radius': 600
        }
        zone_data['coverage_area'] = 'Houston Operations Area'
    
    return zone_data

@work_zone_hours_bp.route('/work-zone-dashboard')
def work_zone_dashboard():
    """Main work zone hours dashboard"""
    try:
        # Import the MTD data from the comprehensive reports module
        from routes.comprehensive_reports import load_mtd_data
        mtd_data = load_mtd_data()
        
        # Get recent date range for analysis
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Collect driver records for the week
        weekly_records = []
        for date in mtd_data['daily_records']:
            if start_date.strftime('%Y-%m-%d') <= date <= end_date.strftime('%Y-%m-%d'):
                weekly_records.extend(mtd_data['daily_records'][date])
        
        # Calculate validation metrics - GPS vs Timecard vs Payroll
        validation_data = calculate_work_zone_validation(weekly_records)
        
        # Get zone data for each active job site
        zone_data = {}
        for location in mtd_data['locations']:
            zone_data[location] = get_gps_zone_data(location)
        
        # Calculate productivity trends
        daily_productivity = defaultdict(dict)
        for date in mtd_data['daily_records']:
            if start_date.strftime('%Y-%m-%d') <= date <= end_date.strftime('%Y-%m-%d'):
                daily_records = mtd_data['daily_records'][date]
                total_hours = sum(8 for _ in daily_records)  # Standard 8-hour day
                productive_hours = sum(
                    8 if r['status'] == 'On Time' 
                    else 7 if r['status'] == 'Late Start'
                    else 6 if r['status'] == 'Early End'
                    else 0
                    for r in daily_records
                )
                
                daily_productivity[date] = {
                    'total_hours': total_hours,
                    'productive_hours': productive_hours,
                    'efficiency': round((productive_hours / max(1, total_hours)) * 100, 2),
                    'driver_count': len(daily_records)
                }
        
        return render_template('work_zone_dashboard.html',
                             efficiency_data=efficiency_data,
                             zone_data=zone_data,
                             daily_productivity=dict(daily_productivity),
                             weekly_records=weekly_records,
                             active_sites=len(mtd_data['locations']),
                             total_drivers=len(mtd_data['drivers']))
    
    except Exception as e:
        logger.error(f"Error in work zone dashboard: {e}")
        return f"Error loading work zone dashboard: {str(e)}"

@work_zone_hours_bp.route('/work-zone-site/<site_name>')
def work_zone_site_detail(site_name):
    """Detailed work zone analysis for a specific site"""
    try:
        from routes.comprehensive_reports import load_mtd_data
        mtd_data = load_mtd_data()
        
        # Filter records for this specific site
        site_records = []
        for date_records in mtd_data['daily_records'].values():
            site_records.extend([r for r in date_records if r['job_site'] == site_name])
        
        # Calculate site-specific metrics
        site_efficiency = calculate_work_zone_efficiency(site_records, {})
        zone_info = get_gps_zone_data(site_name)
        
        # Daily breakdown for this site
        daily_breakdown = defaultdict(list)
        for record in site_records:
            daily_breakdown[record['date']].append(record)
        
        return render_template('work_zone_site_detail.html',
                             site_name=site_name,
                             site_records=site_records,
                             site_efficiency=site_efficiency,
                             zone_info=zone_info,
                             daily_breakdown=dict(daily_breakdown))
    
    except Exception as e:
        logger.error(f"Error in site detail: {e}")
        return f"Error loading site detail: {str(e)}"

@work_zone_hours_bp.route('/api/work-zone/efficiency/<date>')
def api_work_zone_efficiency(date):
    """API endpoint for work zone efficiency data"""
    try:
        from routes.comprehensive_reports import load_mtd_data
        mtd_data = load_mtd_data()
        
        if date in mtd_data['daily_records']:
            daily_records = mtd_data['daily_records'][date]
            efficiency_data = calculate_work_zone_efficiency(daily_records, {})
            return jsonify(efficiency_data)
        
        return jsonify({'error': 'No data for specified date'})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@work_zone_hours_bp.route('/api/work-zone/gps/<site>')
def api_gps_zone_data(site):
    """API endpoint for GPS zone data"""
    try:
        zone_data = get_gps_zone_data(site)
        return jsonify(zone_data)
    
    except Exception as e:
        return jsonify({'error': str(e)})