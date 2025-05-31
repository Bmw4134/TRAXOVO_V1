"""
Complete Attendance Workflow with Gauge API Integration
Daily → Weekly → Monthly reporting pipeline for morning reviews
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import logging
from datetime import datetime, timedelta, date
import os
import json
from pathlib import Path
import pandas as pd
from gauge_api_legacy import GaugeAPI

attendance_workflow_bp = Blueprint('attendance_workflow', __name__)
logger = logging.getLogger(__name__)

# Initialize Gauge API
get_unified_data("assets")
        
        if not assets_data:
            return jsonify({
                'success': False,
                'message': 'No data received from Gauge API. Please check your API credentials.'
            })
        
        # Process asset data for attendance tracking
        attendance_records = process_gauge_data_for_attendance(assets_data)
        
        # Save to attendance tracking system
        save_attendance_records(attendance_records)
        
        return jsonify({
            'success': True,
            'message': f'Successfully synced {len(attendance_records)} attendance records from Gauge',
            'records_processed': len(attendance_records),
            'sync_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing from Gauge API: {e}")
        return jsonify({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        }), 500

@attendance_workflow_bp.route('/attendance-workflow/daily-report/<date_str>')
def generate_daily_report(date_str):
    """Generate daily attendance report"""
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get attendance data for the specific date
        daily_data = get_daily_attendance_data(report_date)
        
        # Generate report summary
        report = {
            'date': date_str,
            'total_drivers': len(daily_data),
            'on_time': len([d for d in daily_data if d.get('status') == 'on_time']),
            'late_arrivals': len([d for d in daily_data if d.get('status') == 'late']),
            'early_departures': len([d for d in daily_data if d.get('status') == 'early_end']),
            'absent': len([d for d in daily_data if d.get('status') == 'absent']),
            'drivers': daily_data,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save daily report
        save_daily_report(report_date, report)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return jsonify({'error': str(e)}), 500

@attendance_workflow_bp.route('/attendance-workflow/weekly-report')
def generate_weekly_report():
    """Generate weekly attendance summary"""
    try:
        # Get current week dates
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        
        weekly_data = []
        total_metrics = {
            'total_drivers': 0,
            'total_on_time': 0,
            'total_late': 0,
            'total_early_end': 0,
            'total_absent': 0
        }
        
        for date_obj in week_dates:
            daily_data = get_daily_attendance_data(date_obj)
            daily_summary = {
                'date': date_obj.strftime('%Y-%m-%d'),
                'day_name': date_obj.strftime('%A'),
                'total_drivers': len(daily_data),
                'on_time': len([d for d in daily_data if d.get('status') == 'on_time']),
                'late': len([d for d in daily_data if d.get('status') == 'late']),
                'early_end': len([d for d in daily_data if d.get('status') == 'early_end']),
                'absent': len([d for d in daily_data if d.get('status') == 'absent'])
            }
            weekly_data.append(daily_summary)
            
            # Update totals
            total_metrics['total_drivers'] += daily_summary['total_drivers']
            total_metrics['total_on_time'] += daily_summary['on_time']
            total_metrics['total_late'] += daily_summary['late']
            total_metrics['total_early_end'] += daily_summary['early_end']
            total_metrics['total_absent'] += daily_summary['absent']
        
        week_report = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
            'daily_summaries': weekly_data,
            'week_totals': total_metrics,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'report': week_report
        })
        
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        return jsonify({'error': str(e)}), 500

@attendance_workflow_bp.route('/attendance-workflow/monthly-report')
def generate_monthly_report():
    """Generate monthly attendance summary"""
    try:
        today = date.today()
        month_start = today.replace(day=1)
        
        # Get all days in current month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        
        monthly_data = []
        month_metrics = {
            'total_work_days': 0,
            'average_attendance': 0,
            'total_late_incidents': 0,
            'total_early_departures': 0,
            'total_absences': 0
        }
        
        current_date = month_start
        while current_date <= min(month_end, today):
            # Skip weekends for work day calculation
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_data = get_daily_attendance_data(current_date)
                daily_summary = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total_drivers': len(daily_data),
                    'on_time': len([d for d in daily_data if d.get('status') == 'on_time']),
                    'late': len([d for d in daily_data if d.get('status') == 'late']),
                    'early_end': len([d for d in daily_data if d.get('status') == 'early_end']),
                    'absent': len([d for d in daily_data if d.get('status') == 'absent'])
                }
                monthly_data.append(daily_summary)
                
                month_metrics['total_work_days'] += 1
                month_metrics['total_late_incidents'] += daily_summary['late']
                month_metrics['total_early_departures'] += daily_summary['early_end']
                month_metrics['total_absences'] += daily_summary['absent']
            
            current_date += timedelta(days=1)
        
        # Calculate average attendance
        if month_metrics['total_work_days'] > 0:
            total_present_days = sum(day['total_drivers'] - day['absent'] for day in monthly_data)
            month_metrics['average_attendance'] = round(
                total_present_days / month_metrics['total_work_days'], 2
            )
        
        month_report = {
            'month': today.strftime('%B %Y'),
            'month_start': month_start.strftime('%Y-%m-%d'),
            'month_end': month_end.strftime('%Y-%m-%d'),
            'daily_summaries': monthly_data,
            'month_metrics': month_metrics,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'report': month_report
        })
        
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        return jsonify({'error': str(e)}), 500

def process_gauge_data_for_attendance(assets_data):
    """Process Gauge API data to extract attendance information"""
    attendance_records = []
    
    for asset in assets_data:
        # Extract driver information from asset data
        driver_name = asset.get('assigned_driver', '')
        if not driver_name:
            continue
            
        # Create attendance record based on asset activity
        record = {
            'driver_name': driver_name,
            'asset_id': asset.get('id', ''),
            'date': date.today().strftime('%Y-%m-%d'),
            'last_activity': asset.get('last_activity_time', ''),
            'location': asset.get('last_known_location', ''),
            'status': determine_attendance_status(asset),
            'source': 'gauge_api'
        }
        attendance_records.append(record)
    
    return attendance_records

def determine_attendance_status(asset_data):
    """Determine attendance status based on asset activity"""
    last_activity = asset_data.get('last_activity_time', '')
    if not last_activity:
        return 'absent'
    
    try:
        activity_time = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        now = datetime.now()
        
        # If activity within last 4 hours, consider present
        if (now - activity_time).total_seconds() < 14400:  # 4 hours
            return 'on_time'
        else:
            return 'absent'
    except:
        return 'unknown'

def get_daily_attendance_summary(report_date):
    """Get daily attendance summary"""
    daily_data = get_daily_attendance_data(report_date)
    
    return {
        'date': report_date.strftime('%Y-%m-%d'),
        'total_drivers': len(daily_data),
        'on_time': len([d for d in daily_data if d.get('status') == 'on_time']),
        'issues': len([d for d in daily_data if d.get('status') in ['late', 'early_end', 'absent']])
    }

def get_weekly_attendance_summary(current_date):
    """Get weekly attendance summary"""
    week_start = current_date - timedelta(days=current_date.weekday())
    week_data = []
    
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        daily_summary = get_daily_attendance_summary(day_date)
        week_data.append(daily_summary)
    
    return {
        'week_start': week_start.strftime('%Y-%m-%d'),
        'daily_data': week_data
    }

def get_monthly_attendance_summary(current_date):
    """Get monthly attendance summary"""
    month_start = current_date.replace(day=1)
    
    return {
        'month': current_date.strftime('%B %Y'),
        'work_days_processed': 0,  # Will be calculated from actual data
        'average_attendance': 0    # Will be calculated from actual data
    }

def get_daily_attendance_data(report_date):
    """Get attendance data for a specific date"""
    # Check for saved attendance data
    attendance_dir = Path('./attendance_data')
    date_file = attendance_dir / f'attendance_{report_date.strftime("%Y-%m-%d")}.json'
    
    if date_file.exists():
        with open(date_file, 'r') as f:
            return json.load(f)
    
    return []

def save_attendance_records(records):
    """Save attendance records to the system"""
    attendance_dir = Path('./attendance_data')
    attendance_dir.mkdir(exist_ok=True)
    
    # Group records by date
    records_by_date = {}
    for record in records:
        record_date = record['date']
        if record_date not in records_by_date:
            records_by_date[record_date] = []
        records_by_date[record_date].append(record)
    
    # Save each date group
    for date_str, date_records in records_by_date.items():
        date_file = attendance_dir / f'attendance_{date_str}.json'
        
        # Load existing records if file exists
        existing_records = []
        if date_file.exists():
            with open(date_file, 'r') as f:
                existing_records = json.load(f)
        
        # Merge records (avoid duplicates)
        existing_drivers = {r['driver_name'] for r in existing_records}
        new_records = [r for r in date_records if r['driver_name'] not in existing_drivers]
        
        # Save updated records
        all_records = existing_records + new_records
        with open(date_file, 'w') as f:
            json.dump(all_records, f, indent=2)

def save_daily_report(report_date, report_data):
    """Save daily report to file system"""
    reports_dir = Path('./reports/daily')
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f'daily_report_{report_date.strftime("%Y-%m-%d")}.json'
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)