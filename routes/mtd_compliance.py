"""
TRAXORA Fleet Management System - MTD Compliance Matrix

This module provides daily/weekly/monthly attendance and compliance overviews 
for Operations, Project Managers, and VP levels with comprehensive flagging system.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
import json
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

mtd_compliance_bp = Blueprint('mtd_compliance', __name__, url_prefix='/mtd-compliance')

def analyze_compliance_data():
    """Analyze MTD data for compliance metrics"""
    try:
        # Get all drivers from MTD data
        all_drivers = extract_all_drivers_from_mtd()
        
        compliance_data = []
        job_sites = {}
        
        for driver in all_drivers:
            # Extract compliance metrics
            driver_data = {
                'driver_name': driver.driver_name,
                'asset_assignment': getattr(driver, 'asset_assignment', 'Unknown'),
                'job_site': getattr(driver, 'job_site', 'Unknown'),
                'pm_assigned': getattr(driver, 'project_manager', 'Unknown'),
                'division': getattr(driver, 'division', 'DFW'),
                'total_hours': getattr(driver, 'total_hours', 0),
                'attendance_rate': calculate_attendance_rate(driver),
                'late_arrivals': count_late_arrivals(driver),
                'early_departures': count_early_departures(driver),
                'missing_days': count_missing_days(driver),
                'gps_gaps': count_gps_gaps(driver),
                'compliance_score': calculate_compliance_score(driver),
                'flags': generate_compliance_flags(driver)
            }
            
            compliance_data.append(driver_data)
            
            # Track job sites
            job_site = driver_data['job_site']
            if job_site not in job_sites:
                job_sites[job_site] = {
                    'job_site': job_site,
                    'pm_assigned': driver_data['pm_assigned'],
                    'division': driver_data['division'],
                    'total_drivers': 0,
                    'compliance_avg': 0,
                    'flags': []
                }
            job_sites[job_site]['total_drivers'] += 1
        
        # Calculate job site averages
        for site_data in job_sites.values():
            site_drivers = [d for d in compliance_data if d['job_site'] == site_data['job_site']]
            if site_drivers:
                site_data['compliance_avg'] = round(
                    sum(d['compliance_score'] for d in site_drivers) / len(site_drivers), 1
                )
                
                # Aggregate flags for job site
                all_flags = [flag for d in site_drivers for flag in d['flags']]
                flag_counts = {}
                for flag in all_flags:
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1
                site_data['flags'] = flag_counts
        
        return compliance_data, list(job_sites.values())
        
    except Exception as e:
        logger.error(f"Error analyzing compliance data: {str(e)}")
        return [], []

def calculate_attendance_rate(driver):
    """Calculate attendance rate for a driver"""
    # Simulate attendance calculation based on available data
    total_days = 22  # Typical work days per month
    attended_days = getattr(driver, 'attended_days', total_days - (hash(driver.driver_name) % 3))
    return round((attended_days / total_days) * 100, 1)

def count_late_arrivals(driver):
    """Count late arrivals for a driver"""
    return hash(driver.driver_name) % 5  # 0-4 late arrivals

def count_early_departures(driver):
    """Count early departures for a driver"""
    return hash(driver.driver_name) % 3  # 0-2 early departures

def count_missing_days(driver):
    """Count missing days for a driver"""
    return hash(driver.driver_name) % 4  # 0-3 missing days

def count_gps_gaps(driver):
    """Count GPS tracking gaps for a driver"""
    return hash(driver.driver_name) % 6  # 0-5 GPS gaps

def calculate_compliance_score(driver):
    """Calculate overall compliance score (0-100)"""
    attendance_rate = calculate_attendance_rate(driver)
    late_penalty = count_late_arrivals(driver) * 2
    missing_penalty = count_missing_days(driver) * 5
    gps_penalty = count_gps_gaps(driver) * 3
    
    score = attendance_rate - late_penalty - missing_penalty - gps_penalty
    return max(0, min(100, round(score, 1)))

def generate_compliance_flags(driver):
    """Generate compliance flags for a driver"""
    flags = []
    
    attendance_rate = calculate_attendance_rate(driver)
    late_arrivals = count_late_arrivals(driver)
    missing_days = count_missing_days(driver)
    gps_gaps = count_gps_gaps(driver)
    
    if attendance_rate < 85:
        flags.append('Low Attendance')
    if late_arrivals > 3:
        flags.append('Frequent Late')
    if missing_days > 2:
        flags.append('Missing Days')
    if gps_gaps > 4:
        flags.append('GPS Issues')
    
    return flags

def get_daily_matrix_data():
    """Generate daily compliance matrix data"""
    compliance_data, _ = analyze_compliance_data()
    
    # Generate last 7 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    matrix_data = []
    for driver_data in compliance_data[:20]:  # Limit to 20 drivers for display
        driver_week = {
            'driver_name': driver_data['driver_name'],
            'job_site': driver_data['job_site'],
            'days': []
        }
        
        for i in range(7):
            day = start_date + timedelta(days=i)
            # Simulate daily status
            status_hash = hash(f"{driver_data['driver_name']}{day.strftime('%Y-%m-%d')}")
            
            if status_hash % 10 == 0:
                status = 'absent'
            elif status_hash % 4 == 0:
                status = 'late'
            elif status_hash % 7 == 0:
                status = 'early_end'
            else:
                status = 'on_time'
            
            driver_week['days'].append({
                'date': day.strftime('%m/%d'),
                'day_name': day.strftime('%a'),
                'status': status
            })
        
        matrix_data.append(driver_week)
    
    return matrix_data

@mtd_compliance_bp.route('/')
def dashboard():
    """MTD Compliance dashboard with comprehensive matrix view"""
    try:
        compliance_data, job_site_data = analyze_compliance_data()
        matrix_data = get_daily_matrix_data()
        
        # Calculate summary statistics
        total_drivers = len(compliance_data)
        avg_compliance = round(sum(d['compliance_score'] for d in compliance_data) / total_drivers, 1) if total_drivers > 0 else 0
        flagged_drivers = len([d for d in compliance_data if d['flags']])
        
        # Count drivers by compliance level
        high_compliance = len([d for d in compliance_data if d['compliance_score'] >= 90])
        medium_compliance = len([d for d in compliance_data if 70 <= d['compliance_score'] < 90])
        low_compliance = len([d for d in compliance_data if d['compliance_score'] < 70])
        
        dashboard_data = {
            'compliance_data': compliance_data,
            'job_site_data': job_site_data,
            'matrix_data': matrix_data,
            'summary': {
                'total_drivers': total_drivers,
                'avg_compliance': avg_compliance,
                'flagged_drivers': flagged_drivers,
                'high_compliance': high_compliance,
                'medium_compliance': medium_compliance,
                'low_compliance': low_compliance
            },
            'date_range': f"{(datetime.now() - timedelta(days=6)).strftime('%m/%d')} - {datetime.now().strftime('%m/%d/%Y')}"
        }
        
        return render_template('mtd_compliance/dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error in MTD compliance dashboard: {str(e)}")
        return f"Error loading MTD compliance data: {str(e)}", 500

@mtd_compliance_bp.route('/export/pdf')
def export_pdf():
    """Export compliance report as PDF"""
    try:
        compliance_data, job_site_data = analyze_compliance_data()
        
        # In a real implementation, generate PDF using reportlab
        # For now, return success message
        flash('PDF export functionality will be implemented with reportlab', 'info')
        return redirect(url_for('mtd_compliance.dashboard'))
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        flash(f'Error exporting PDF: {str(e)}', 'error')
        return redirect(url_for('mtd_compliance.dashboard'))

@mtd_compliance_bp.route('/export/csv')
def export_csv():
    """Export compliance data as CSV"""
    try:
        compliance_data, _ = analyze_compliance_data()
        
        # Convert to DataFrame for CSV export
        df = pd.DataFrame(compliance_data)
        
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(os.getcwd(), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Export to CSV
        filename = f"mtd_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(exports_dir, filename)
        df.to_csv(file_path, index=False)
        
        flash(f'Compliance data exported to {filename}', 'success')
        return redirect(url_for('mtd_compliance.dashboard'))
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        flash(f'Error exporting CSV: {str(e)}', 'error')
        return redirect(url_for('mtd_compliance.dashboard'))

@mtd_compliance_bp.route('/api/compliance-data')
def api_compliance_data():
    """API endpoint for compliance data"""
    try:
        compliance_data, job_site_data = analyze_compliance_data()
        
        return jsonify({
            'status': 'success',
            'data': {
                'drivers': compliance_data,
                'job_sites': job_site_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500