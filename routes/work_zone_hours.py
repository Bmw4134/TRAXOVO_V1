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
        for record in driver_records:
            # Calculate work hours
            start_time = record.get('start_time', '07:00')
            end_time = record.get('end_time', '16:00')
            
            if start_time and end_time:
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                work_hours = max(0, end_hour - start_hour)
                
                efficiency_data['total_hours'] += work_hours
                
                # Consider productive hours based on status
                if record.get('status') == 'On Time':
                    efficiency_data['productive_hours'] += work_hours
                elif record.get('status') == 'Late Start':
                    efficiency_data['productive_hours'] += max(0, work_hours - 1)
                elif record.get('status') == 'Early End':
                    efficiency_data['productive_hours'] += max(0, work_hours - 2)
                
                # Track site utilization
                job_site = record.get('job_site', 'Unknown')
                if job_site not in efficiency_data['site_utilization']:
                    efficiency_data['site_utilization'][job_site] = {
                        'total_hours': 0,
                        'driver_count': 0,
                        'efficiency': 0
                    }
                
                efficiency_data['site_utilization'][job_site]['total_hours'] += work_hours
                efficiency_data['site_utilization'][job_site]['driver_count'] += 1
        
        # Calculate overall efficiency rate
        if efficiency_data['total_hours'] > 0:
            efficiency_data['efficiency_rate'] = round(
                (efficiency_data['productive_hours'] / efficiency_data['total_hours']) * 100, 2
            )
        
        # Calculate site-specific efficiency
        for site_data in efficiency_data['site_utilization'].values():
            if site_data['total_hours'] > 0:
                site_data['efficiency'] = round(
                    (site_data['total_hours'] / max(1, site_data['driver_count'] * 8)) * 100, 2
                )
    
    except Exception as e:
        logger.error(f"Error calculating work zone efficiency: {e}")
    
    return efficiency_data

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
        
        # Calculate efficiency metrics
        job_site_boundaries = {}  # This would be populated from your GPS data
        efficiency_data = calculate_work_zone_efficiency(weekly_records, job_site_boundaries)
        
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