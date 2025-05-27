"""
Job Security Monitoring - TRAXOVO Live Field Test Module

Detects theft, orphaned GPS, off-hours activity using authentic Gauge API data.
Minimal scaffold - safe for live-edit deployment.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

logger = logging.getLogger(__name__)

job_security_monitoring_bp = Blueprint('job_security_monitoring', __name__, url_prefix='/job-security')

@job_security_monitoring_bp.route('/')
@login_required
def security_dashboard():
    """Job Security Monitoring Dashboard"""
    try:
        security_alerts = get_security_alerts()
        
        return render_template('job_security_monitoring/dashboard.html',
                             alerts=security_alerts,
                             total_alerts=len(security_alerts))
    except Exception as e:
        logger.error(f"Security monitoring error: {e}")
        return render_template('job_security_monitoring/dashboard.html',
                             alerts=[], total_alerts=0)

@job_security_monitoring_bp.route('/api/security-alerts')
@login_required
def api_security_alerts():
    """API endpoint for security alerts using authentic GPS data"""
    try:
        alerts = get_security_alerts()
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'source': 'Authentic Gauge API GPS Data'
        })
    except Exception as e:
        logger.error(f"Security alerts API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@job_security_monitoring_bp.route('/generate-theft-report')
@login_required
def generate_theft_report():
    """Generate theft report - JSON/HTML export stub"""
    try:
        theft_incidents = detect_theft_patterns()
        
        report_data = {
            'report_date': datetime.now().isoformat(),
            'theft_incidents': theft_incidents,
            'total_incidents': len(theft_incidents),
            'report_type': 'Security Theft Analysis'
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Theft report generation error: {e}")
        return jsonify({'error': str(e)}), 500

def get_security_alerts():
    """Get security alerts from authentic Gauge API data"""
    alerts = []
    
    try:
        from gauge_api import GaugeAPI
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        current_time = datetime.now()
        off_hours_start = current_time.replace(hour=19, minute=0, second=0)  # 7 PM
        off_hours_end = current_time.replace(hour=6, minute=0, second=0)     # 6 AM
        
        for asset in assets:
            asset_id = asset.get('id')
            last_update = asset.get('last_update')
            speed = asset.get('speed', 0)
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            
            if not last_update:
                continue
                
            try:
                last_seen = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                
                # Detect orphaned GPS (no movement for 24+ hours)
                if (current_time - last_seen).total_seconds() > 86400:  # 24 hours
                    alerts.append({
                        'type': 'ORPHANED_GPS',
                        'asset_id': asset_id,
                        'severity': 'HIGH',
                        'message': f'Asset {asset_id} has not moved for over 24 hours',
                        'last_seen': last_update,
                        'coordinates': {'lat': lat, 'lon': lon}
                    })
                
                # Detect off-hours activity
                if speed and float(speed) > 5:  # Moving faster than 5 mph
                    current_hour = current_time.hour
                    if current_hour >= 19 or current_hour <= 6:  # Off hours
                        alerts.append({
                            'type': 'OFF_HOURS_ACTIVITY',
                            'asset_id': asset_id,
                            'severity': 'MEDIUM',
                            'message': f'Asset {asset_id} moving during off-hours (Speed: {speed} mph)',
                            'timestamp': current_time.isoformat(),
                            'speed': speed,
                            'coordinates': {'lat': lat, 'lon': lon}
                        })
                
            except Exception as parse_error:
                logger.warning(f"Date parsing error for asset {asset_id}: {parse_error}")
                
    except Exception as e:
        logger.error(f"Security alert detection error: {e}")
    
    return alerts

def detect_theft_patterns():
    """Detect potential theft patterns from authentic GPS data"""
    theft_incidents = []
    
    try:
        from gauge_api import GaugeAPI
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        for asset in assets:
            asset_id = asset.get('id')
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            last_update = asset.get('last_update')
            
            # Basic theft detection: asset moved outside expected work zones
            if lat and lon:
                # Check if coordinates are outside North Texas work area
                if not is_in_work_area(float(lat), float(lon)):
                    theft_incidents.append({
                        'incident_type': 'LOCATION_ANOMALY',
                        'asset_id': asset_id,
                        'description': f'Asset {asset_id} detected outside normal work area',
                        'coordinates': {'lat': lat, 'lon': lon},
                        'detected_at': last_update,
                        'risk_level': 'HIGH'
                    })
                    
    except Exception as e:
        logger.error(f"Theft pattern detection error: {e}")
    
    return theft_incidents

def is_in_work_area(lat, lon):
    """Check if coordinates are within North Texas work area"""
    # North Texas bounding box (approximate)
    north_texas_bounds = {
        'min_lat': 32.0,   # Southern boundary
        'max_lat': 33.5,   # Northern boundary  
        'min_lon': -97.5,  # Western boundary
        'max_lon': -96.0   # Eastern boundary
    }
    
    return (north_texas_bounds['min_lat'] <= lat <= north_texas_bounds['max_lat'] and
            north_texas_bounds['min_lon'] <= lon <= north_texas_bounds['max_lon'])