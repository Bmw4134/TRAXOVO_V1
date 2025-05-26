"""
TRAXORA Daily Driver Reports - Complete Working System

Full-featured daily driver reporting with date range cycling and real MTD data processing.
"""

from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from utils.live_mtd_processor import process_todays_mtd_files
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

daily_driver_complete_bp = Blueprint('daily_driver_complete', __name__, url_prefix='/driver-reports')

def get_date_range_data(start_date, end_date):
    """Get driver data for any date range from your MTD files"""
    
    try:
        # Load your MTD file with real driver data
        driving_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        if not os.path.exists(driving_file):
            return {"error": "MTD data file not found"}
        
        # Read the complete dataset
        df = pd.read_csv(driving_file, skiprows=8, low_memory=False)
        df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + timedelta(days=1)  # Include end date
        
        filtered_df = df[(df['EventDateTime'] >= start_dt) & (df['EventDateTime'] < end_dt)]
        
        # Extract all drivers for the period
        all_drivers = extract_all_drivers_from_mtd()
        
        # Analyze activity for each day in range
        daily_reports = []
        current_date = start_dt.date()
        end_date_obj = pd.to_datetime(end_date).date()
        
        while current_date <= end_date_obj:
            day_data = filtered_df[filtered_df['EventDateTime'].dt.date == current_date]
            
            # Count active drivers for this day
            active_assets = day_data['Textbox53'].nunique()
            total_events = len(day_data)
            
            # Classify driver activity
            key_events = day_data[day_data['MsgType'].isin(['Key On', 'Key Off'])]
            
            # Simple attendance calculation
            if not key_events.empty:
                morning_events = key_events[key_events['EventDateTime'].dt.hour <= 8]
                on_time_count = len(morning_events['Textbox53'].unique())
                late_count = max(0, active_assets - on_time_count)
            else:
                on_time_count = 0
                late_count = 0
            
            daily_reports.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'formatted_date': current_date.strftime('%a, %b %d'),
                'active_drivers': active_assets,
                'total_events': total_events,
                'on_time': on_time_count,
                'late': late_count,
                'not_on_job': max(0, len(all_drivers) - active_assets)
            })
            
            current_date += timedelta(days=1)
        
        return {
            'date_range': f"{start_date} to {end_date}",
            'total_drivers': len(all_drivers),
            'daily_reports': daily_reports,
            'summary': {
                'total_days': len(daily_reports),
                'avg_active_drivers': sum(r['active_drivers'] for r in daily_reports) / len(daily_reports) if daily_reports else 0,
                'total_events': sum(r['total_events'] for r in daily_reports)
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing date range {start_date} to {end_date}: {e}")
        return {"error": str(e)}

@daily_driver_complete_bp.route('/')
def dashboard():
    """Complete daily driver dashboard with date range controls"""
    
    # Default to last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    # Get date range from query parameters
    start_param = request.args.get('start_date')
    end_param = request.args.get('end_date')
    
    if start_param:
        try:
            start_date = datetime.strptime(start_param, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_param:
        try:
            end_date = datetime.strptime(end_param, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get data for the date range
    range_data = get_date_range_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    # Get current day metrics
    current_metrics = process_todays_mtd_files()
    
    # Get all drivers for driver list
    all_drivers = extract_all_drivers_from_mtd()
    
    return render_template('daily_driver_complete/dashboard.html',
                         range_data=range_data,
                         current_metrics=current_metrics,
                         all_drivers=all_drivers[:20],  # Show first 20
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'))

@daily_driver_complete_bp.route('/api/date-range')
def api_date_range():
    """API endpoint for date range data"""
    
    start_date = request.args.get('start_date', (datetime.now().date() - timedelta(days=6)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().date().strftime('%Y-%m-%d'))
    
    range_data = get_date_range_data(start_date, end_date)
    
    return jsonify({
        'status': 'success' if 'error' not in range_data else 'error',
        'data': range_data,
        'timestamp': datetime.now().isoformat()
    })

@daily_driver_complete_bp.route('/driver/<driver_name>')
def driver_detail(driver_name):
    """Individual driver detail view"""
    
    try:
        # Load MTD data for this specific driver
        driving_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        df = pd.read_csv(driving_file, skiprows=8, low_memory=False)
        
        # Find driver's asset assignments
        all_drivers = extract_all_drivers_from_mtd()
        driver_info = next((d for d in all_drivers if d['driver_name'] == driver_name), None)
        
        if not driver_info:
            return jsonify({'error': 'Driver not found'})
        
        # Get driver's activity data
        driver_data = df[df['Textbox53'] == driver_info['asset_assignment']]
        
        if not driver_data.empty:
            driver_data['EventDateTime'] = pd.to_datetime(driver_data['EventDateTime'], errors='coerce')
            
            # Analyze driver's activity patterns
            daily_activity = driver_data.groupby(driver_data['EventDateTime'].dt.date).agg({
                'MsgType': 'count',
                'EventDateTime': ['min', 'max']
            }).round(2)
            
            activity_summary = {
                'total_events': len(driver_data),
                'active_days': len(daily_activity),
                'avg_events_per_day': len(driver_data) / len(daily_activity) if len(daily_activity) > 0 else 0,
                'first_activity': driver_data['EventDateTime'].min().strftime('%Y-%m-%d %H:%M') if not driver_data.empty else 'N/A',
                'last_activity': driver_data['EventDateTime'].max().strftime('%Y-%m-%d %H:%M') if not driver_data.empty else 'N/A'
            }
        else:
            activity_summary = {
                'total_events': 0,
                'active_days': 0,
                'avg_events_per_day': 0,
                'first_activity': 'N/A',
                'last_activity': 'N/A'
            }
        
        return render_template('daily_driver_complete/driver_detail.html',
                             driver_info=driver_info,
                             activity_summary=activity_summary)
        
    except Exception as e:
        logger.error(f"Error getting driver detail for {driver_name}: {e}")
        return jsonify({'error': str(e)})

@daily_driver_complete_bp.route('/export/<date>')
def export_daily_report(date):
    """Export daily report for specific date"""
    
    try:
        # Get data for the specific date
        range_data = get_date_range_data(date, date)
        
        if 'error' in range_data:
            return jsonify({'error': range_data['error']})
        
        # Create export data
        export_data = {
            'date': date,
            'report_data': range_data,
            'exported_at': datetime.now().isoformat(),
            'total_drivers': range_data.get('total_drivers', 0)
        }
        
        return jsonify({
            'status': 'success',
            'export_data': export_data,
            'filename': f"daily_driver_report_{date.replace('-', '_')}.json"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})