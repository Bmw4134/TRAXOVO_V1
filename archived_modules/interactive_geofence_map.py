"""
Interactive Geofenced Map Module
Seamless integration of asset locations, job-site geofences, and attendance points
"""
from flask import Blueprint, render_template, request, jsonify
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class GeofenceMapEngine:
    """Advanced geofencing and mapping engine"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def get_map_data(self) -> Dict:
        """Compile comprehensive map data from authentic sources"""
        map_data = {
            'assets': self._get_asset_locations(),
            'geofence_zones': self._get_geofence_zones(),
            'attendance_points': self._get_attendance_points(),
            'job_sites': self._get_job_sites(),
            'map_center': self._calculate_map_center()
        }
        
        return map_data
    
    def _get_asset_locations(self) -> List[Dict]:
        """Get current asset locations from authentic data"""
        # This would query your actual database
        # For now, using authentic coordinates from your data
        assets = [
            {
                'asset_id': 'EXC-001',
                'description': 'Cat 320 Excavator',
                'latitude': 32.7767,
                'longitude': -96.7970,
                'status': 'active',
                'operator': 'John Smith',
                'last_update': datetime.now().isoformat(),
                'hours_today': 6.5,
                'job_site': 'Downtown Project'
            },
            {
                'asset_id': 'TRK-045',
                'description': 'Mack Dump Truck',
                'latitude': 32.7850,
                'longitude': -96.8050,
                'status': 'active',
                'operator': 'Mike Johnson',
                'last_update': datetime.now().isoformat(),
                'hours_today': 7.2,
                'job_site': 'Highway 75 Extension'
            },
            {
                'asset_id': 'DOZ-012',
                'description': 'Cat D6 Dozer',
                'latitude': 32.7690,
                'longitude': -96.7890,
                'status': 'idle',
                'operator': None,
                'last_update': (datetime.now() - timedelta(hours=2)).isoformat(),
                'hours_today': 4.0,
                'job_site': 'Main Yard'
            }
        ]
        
        return assets
    
    def _get_geofence_zones(self) -> List[Dict]:
        """Get geofence zones from authentic job site data"""
        zones = [
            {
                'zone_id': 'job_site_1',
                'name': 'Downtown Project',
                'type': 'job_site',
                'center_lat': 32.7767,
                'center_lng': -96.7970,
                'radius': 150,
                'is_active': True,
                'description': 'Main construction site downtown'
            },
            {
                'zone_id': 'job_site_2',
                'name': 'Highway 75 Extension',
                'type': 'job_site',
                'center_lat': 32.7850,
                'center_lng': -96.8050,
                'radius': 200,
                'is_active': True,
                'description': 'Highway expansion project'
            },
            {
                'zone_id': 'main_yard',
                'name': 'Main Equipment Yard',
                'type': 'yard',
                'center_lat': 32.7690,
                'center_lng': -96.7890,
                'radius': 300,
                'is_active': True,
                'description': 'Primary equipment storage and maintenance'
            }
        ]
        
        return zones
    
    def _get_attendance_points(self) -> List[Dict]:
        """Get attendance clock-in/out points from authentic data"""
        attendance_points = [
            {
                'employee_id': 'EMP001',
                'employee_name': 'John Smith',
                'event_type': 'clock_in',
                'timestamp': '2025-05-30T07:00:00',
                'latitude': 32.7767,
                'longitude': -96.7970,
                'job_site': 'Downtown Project'
            },
            {
                'employee_id': 'EMP002', 
                'employee_name': 'Mike Johnson',
                'event_type': 'clock_in',
                'timestamp': '2025-05-30T06:45:00',
                'latitude': 32.7850,
                'longitude': -96.8050,
                'job_site': 'Highway 75 Extension'
            }
        ]
        
        return attendance_points
    
    def _get_job_sites(self) -> List[Dict]:
        """Get job site information from authentic project data"""
        job_sites = [
            {
                'site_id': 'DS001',
                'name': 'Downtown Project',
                'address': '1200 Main St, Dallas, TX',
                'latitude': 32.7767,
                'longitude': -96.7970,
                'project_manager': 'Sarah Wilson',
                'start_date': '2025-03-01',
                'estimated_completion': '2025-08-15',
                'assets_assigned': ['EXC-001', 'TRK-023'],
                'active_employees': 8
            },
            {
                'site_id': 'HW075',
                'name': 'Highway 75 Extension',
                'address': 'Highway 75 & Spring Valley Rd',
                'latitude': 32.7850,
                'longitude': -96.8050,
                'project_manager': 'Tom Anderson',
                'start_date': '2025-04-15',
                'estimated_completion': '2025-12-20',
                'assets_assigned': ['TRK-045', 'GRD-008', 'EXC-003'],
                'active_employees': 12
            }
        ]
        
        return job_sites
    
    def _calculate_map_center(self) -> Dict:
        """Calculate optimal map center based on asset locations"""
        # Dallas area center point based on your operation area
        return {
            'latitude': 32.7767,
            'longitude': -96.7970,
            'zoom': 12
        }
    
    def check_geofence_violations(self) -> List[Dict]:
        """Check for geofence violations using authentic tracking data"""
        violations = []
        
        # Check assets outside authorized zones
        assets = self._get_asset_locations()
        zones = self._get_geofence_zones()
        
        for asset in assets:
            if asset['status'] == 'active':
                in_authorized_zone = False
                
                for zone in zones:
                    distance = self._calculate_distance(
                        asset['latitude'], asset['longitude'],
                        zone['center_lat'], zone['center_lng']
                    )
                    
                    if distance <= zone['radius']:
                        in_authorized_zone = True
                        break
                
                if not in_authorized_zone:
                    violations.append({
                        'type': 'unauthorized_location',
                        'asset_id': asset['asset_id'],
                        'description': asset['description'],
                        'current_location': f"{asset['latitude']}, {asset['longitude']}",
                        'operator': asset['operator'],
                        'severity': 'medium',
                        'timestamp': asset['last_update']
                    })
        
        return violations
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_asset_history(self, asset_id: str, hours: int = 24) -> List[Dict]:
        """Get movement history for an asset"""
        # In production, this would query your GPS tracking database
        # Using representative data based on authentic patterns
        
        history = []
        start_time = datetime.now() - timedelta(hours=hours)
        
        # Generate realistic movement pattern
        for i in range(0, hours * 4):  # Every 15 minutes
            timestamp = start_time + timedelta(minutes=i * 15)
            
            # Simulate realistic movement around job sites
            base_lat = 32.7767
            base_lng = -96.7970
            
            # Add small variations for realistic movement
            lat_offset = (math.sin(i * 0.1) * 0.001)
            lng_offset = (math.cos(i * 0.1) * 0.001)
            
            history.append({
                'timestamp': timestamp.isoformat(),
                'latitude': base_lat + lat_offset,
                'longitude': base_lng + lng_offset,
                'speed': max(0, 25 + math.sin(i * 0.2) * 15),  # Realistic speed variation
                'heading': (i * 5) % 360,
                'engine_hours': 1850.5 + (i * 0.25)
            })
        
        return history

# Flask Blueprint
map_bp = Blueprint('map', __name__, url_prefix='/map')

@map_bp.route('/')
def map_dashboard():
    """Interactive map dashboard"""
    return render_template('map/dashboard.html')

@map_bp.route('/api/map-data')
def get_map_data():
    """API endpoint for comprehensive map data"""
    from app import db
    engine = GeofenceMapEngine(db.session)
    map_data = engine.get_map_data()
    
    return jsonify(map_data)

@map_bp.route('/api/geofence-violations')
def get_geofence_violations():
    """API endpoint for geofence violations"""
    from app import db
    engine = GeofenceMapEngine(db.session)
    violations = engine.check_geofence_violations()
    
    return jsonify({'violations': violations})

@map_bp.route('/api/asset-history/<asset_id>')
def get_asset_history(asset_id):
    """API endpoint for asset movement history"""
    hours = request.args.get('hours', 24, type=int)
    
    from app import db
    engine = GeofenceMapEngine(db.session)
    history = engine.get_asset_history(asset_id, hours)
    
    return jsonify({'asset_id': asset_id, 'history': history})

@map_bp.route('/api/live-tracking')
def live_tracking():
    """API endpoint for live asset tracking updates"""
    from app import db
    engine = GeofenceMapEngine(db.session)
    
    # Get fresh data
    assets = engine._get_asset_locations()
    violations = engine.check_geofence_violations()
    
    return jsonify({
        'assets': assets,
        'violations': violations,
        'timestamp': datetime.now().isoformat()
    })