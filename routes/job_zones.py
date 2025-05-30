"""
Job Zones Module - GENOPS Step 3.1
Geofence management with dual shift support
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging

job_zones_bp = Blueprint('job_zones', __name__, url_prefix='/job-zones')

# GENOPS Step 3.1: Add dual_shift support to job zones
def get_job_zones():
    """Get all job zones with dual shift configuration"""
    try:
        # Mock data structure for job zones - replace with Supabase integration
        job_zones = [
            {
                'id': 1,
                'name': 'Downtown Construction Site',
                'latitude': 30.2672,
                'longitude': -97.7431,
                'radius': 0.5,  # miles
                'dual_shift': True,
                'morning_start': '06:00',
                'morning_end': '14:30',
                'evening_start': '15:00',
                'evening_end': '23:30',
                'active': True
            },
            {
                'id': 2,
                'name': 'Highway 290 Project',
                'latitude': 30.2849,
                'longitude': -97.7341,
                'radius': 0.3,
                'dual_shift': False,
                'morning_start': '07:00',
                'morning_end': '17:00',
                'evening_start': None,
                'evening_end': None,
                'active': True
            },
            {
                'id': 3,
                'name': 'Airport Expansion',
                'latitude': 30.1945,
                'longitude': -97.6699,
                'radius': 0.8,
                'dual_shift': True,
                'morning_start': '05:30',
                'morning_end': '14:00',
                'evening_start': '14:30',
                'evening_end': '23:00',
                'active': True
            }
        ]
        
        return job_zones
        
    except Exception as e:
        logging.error(f"Error loading job zones: {e}")
        return []

def check_zone_coverage(latitude, longitude):
    """Check which job zone(s) cover a given GPS coordinate"""
    from routes.attendance import haversine
    
    covering_zones = []
    zones = get_job_zones()
    
    for zone in zones:
        if not zone['active']:
            continue
            
        distance = haversine(
            longitude, latitude,
            zone['longitude'], zone['latitude']
        )
        
        if distance <= zone['radius']:
            covering_zones.append(zone)
    
    return covering_zones

def is_valid_shift_time(check_time, zone, shift_type='auto'):
    """
    Check if check-in/out time is valid for the zone's shift schedule
    
    Args:
        check_time: datetime object
        zone: job zone dictionary
        shift_type: 'morning', 'evening', or 'auto' to detect
    """
    try:
        time_str = check_time.strftime('%H:%M')
        
        # Single shift zone
        if not zone['dual_shift']:
            return (zone['morning_start'] <= time_str <= zone['morning_end'])
        
        # Dual shift zone
        morning_valid = (zone['morning_start'] <= time_str <= zone['morning_end'])
        evening_valid = (zone['evening_start'] <= time_str <= zone['evening_end'])
        
        if shift_type == 'morning':
            return morning_valid
        elif shift_type == 'evening':
            return evening_valid
        else:  # auto-detect
            return morning_valid or evening_valid
            
    except Exception as e:
        logging.error(f"Shift time validation error: {e}")
        return False

@job_zones_bp.route('/')
def job_zones_list():
    """Job zones management dashboard"""
    zones = get_job_zones()
    
    context = {
        'page_title': 'Job Zones',
        'page_subtitle': 'Geofence and shift management',
        'zones': zones,
        'total_zones': len(zones),
        'active_zones': len([z for z in zones if z['active']]),
        'dual_shift_zones': len([z for z in zones if z['dual_shift']])
    }
    
    return render_template('job_zones.html', **context)

@job_zones_bp.route('/api/coverage')
def api_zone_coverage():
    """API endpoint to check zone coverage for GPS coordinates"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        
        covering_zones = check_zone_coverage(lat, lon)
        
        return jsonify({
            'status': 'success',
            'latitude': lat,
            'longitude': lon,
            'zones': covering_zones,
            'covered': len(covering_zones) > 0
        })
        
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid latitude or longitude'
        }), 400
    except Exception as e:
        logging.error(f"Zone coverage API error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@job_zones_bp.route('/validate-shift')
def validate_shift_time():
    """Validate if a time falls within valid shift hours"""
    try:
        zone_id = int(request.args.get('zone_id'))
        check_time = datetime.fromisoformat(request.args.get('time'))
        shift_type = request.args.get('shift', 'auto')
        
        zones = get_job_zones()
        zone = next((z for z in zones if z['id'] == zone_id), None)
        
        if not zone:
            return jsonify({
                'status': 'error',
                'message': 'Zone not found'
            }), 404
        
        is_valid = is_valid_shift_time(check_time, zone, shift_type)
        
        return jsonify({
            'status': 'success',
            'valid': is_valid,
            'zone': zone['name'],
            'shift_type': shift_type,
            'dual_shift': zone['dual_shift']
        })
        
    except Exception as e:
        logging.error(f"Shift validation error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500