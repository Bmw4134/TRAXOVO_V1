"""
TRAXORA Daily Driver Report - Fixed Version

Working implementation using your real MTD data files
"""

from flask import Blueprint, render_template, jsonify
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from utils.live_mtd_processor import process_todays_mtd_files
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

daily_driver_fixed_bp = Blueprint('daily_driver_fixed', __name__, url_prefix='/daily-reports')

@daily_driver_fixed_bp.route('/')
def dashboard():
    """Fixed daily driver dashboard using your real data"""
    
    try:
        # Get real metrics from your MTD files
        metrics = process_todays_mtd_files()
        
        # Get complete driver list
        all_drivers = extract_all_drivers_from_mtd()
        
        # Load your actual driving history for detailed analysis
        driving_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        driver_details = []
        if os.path.exists(driving_file):
            df = pd.read_csv(driving_file, skiprows=8, nrows=1000, low_memory=False)
            
            # Process real driver data from your MTD file
            for driver_info in all_drivers[:10]:  # Show top 10 drivers
                driver_name = driver_info['driver_name']
                asset_id = driver_info['asset_id']
                
                # Get events for this driver
                driver_events = df[df['Textbox53'] == driver_info['asset_assignment']]
                
                if not driver_events.empty:
                    # Count events
                    event_count = len(driver_events)
                    
                    # Determine status based on activity level
                    if event_count >= 10:
                        status = 'Active'
                        status_class = 'success'
                    elif event_count >= 5:
                        status = 'Moderate'
                        status_class = 'warning'
                    else:
                        status = 'Low Activity'
                        status_class = 'danger'
                    
                    driver_details.append({
                        'name': driver_name,
                        'asset_id': asset_id,
                        'event_count': event_count,
                        'status': status,
                        'status_class': status_class,
                        'vehicle': driver_info.get('vehicle_type', 'Unknown')
                    })
        
        return render_template('daily_driver_fixed/dashboard.html',
                             metrics=metrics,
                             driver_details=driver_details,
                             total_drivers=len(all_drivers))
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('daily_driver_fixed/dashboard.html',
                             metrics={'error': str(e)},
                             driver_details=[],
                             total_drivers=0)

@daily_driver_fixed_bp.route('/api/metrics')
def api_metrics():
    """API endpoint for current metrics"""
    
    try:
        metrics = process_todays_mtd_files()
        all_drivers = extract_all_drivers_from_mtd()
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'total_drivers': len(all_drivers),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@daily_driver_fixed_bp.route('/generate-report/<date>')
def generate_report(date):
    """Generate report for specific date"""
    
    try:
        # Use your real MTD data to generate reports
        all_drivers = extract_all_drivers_from_mtd()
        
        report_data = {
            'date': date,
            'total_drivers': len(all_drivers),
            'drivers': all_drivers[:20],  # First 20 drivers
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'report': report_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })