"""
Mobile-Optimized Map for TRAXOVO

This module provides a mobile-friendly GPS map interface that works perfectly 
on phones for field crews, using authentic Gauge API data.
"""
import logging
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

mobile_map_bp = Blueprint('mobile_map', __name__, url_prefix='/mobile-map')

@mobile_map_bp.route('/')
@login_required
def mobile_map():
    """Mobile-optimized map view for field crews"""
    return render_template('mobile_map.html')

@mobile_map_bp.route('/api/gauge-assets')
@login_required
def api_gauge_assets():
    """API endpoint to get authentic GPS assets for mobile map"""
    try:
        # Get authentic data from Gauge API
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        if assets:
            # Format assets for mobile map display
            mobile_assets = []
            for asset in assets:
                if asset.get('latitude') and asset.get('longitude'):
                    mobile_assets.append({
                        'id': asset.get('id'),
                        'name': asset.get('name') or asset.get('description', f"Asset {asset.get('id')}"),
                        'latitude': float(asset.get('latitude')),
                        'longitude': float(asset.get('longitude')),
                        'description': asset.get('description', ''),
                        'last_update': asset.get('last_update'),
                        'speed': asset.get('speed', 0),
                        'status': asset.get('status', 'unknown')
                    })
            
            logger.info(f"Mobile map: Serving {len(mobile_assets)} authentic GPS assets")
            
            return jsonify({
                'success': True,
                'assets': mobile_assets,
                'total_count': len(mobile_assets),
                'source': 'Authentic Gauge API'
            })
        else:
            logger.warning("Mobile map: No assets returned from Gauge API")
            return jsonify({
                'success': False,
                'error': 'No assets available from authentic data source',
                'assets': []
            })
            
    except Exception as e:
        logger.error(f"Mobile map error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading authentic GPS data: {str(e)}',
            'assets': []
        }), 500

@mobile_map_bp.route('/mobile-attendance')
@login_required
def mobile_attendance():
    """Clean mobile attendance view for field crews"""
    return render_template('mobile_attendance.html')

@mobile_map_bp.route('/api/mobile-attendance')
@login_required
def api_mobile_attendance():
    """API endpoint to get clean attendance data for mobile view"""
    try:
        # Import name formatter utilities
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.name_formatter import clean_driver_name
        
        # Connect to attendance database to get authentic MTD data
        import sqlite3
        db_path = 'attendance_data.db'
        
        if not os.path.exists(db_path):
            logger.warning("Attendance database not found")
            return jsonify({
                'success': False,
                'error': 'Attendance database not available',
                'attendance': {}
            })
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get attendance data from authentic MTD processing
        cursor.execute("""
            SELECT driver_name, asset_assignment, date, status, 
                   start_time, end_time, job_site
            FROM attendance_records 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC, driver_name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Organize by day of week for clean mobile display
        attendance_by_day = {
            'monday': [],
            'tuesday': [],
            'wednesday': [], 
            'thursday': [],
            'friday': []
        }
        
        from datetime import datetime
        
        for row in rows:
            driver_name, asset_assignment, date_str, status, start_time, end_time, job_site = row
            
            # Parse date and get day of week
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A').lower()
                
                if day_name in attendance_by_day:
                    # Clean up the data for mobile display
                    clean_record = {
                        'driver_name': clean_driver_name(driver_name),
                        'asset_assignment': asset_assignment,
                        'status': status,
                        'start_time': start_time,
                        'end_time': end_time,
                        'job_site': job_site,
                        'date': date_str
                    }
                    attendance_by_day[day_name].append(clean_record)
            except:
                continue
        
        logger.info(f"Mobile attendance: Serving authentic MTD data for {len(rows)} records")
        
        return jsonify({
            'success': True,
            'attendance': attendance_by_day,
            'source': 'Authentic MTD Processing'
        })
        
    except Exception as e:
        logger.error(f"Mobile attendance error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading authentic attendance data: {str(e)}',
            'attendance': {}
        }), 500