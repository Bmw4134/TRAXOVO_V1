"""
Smart Driver-to-Job Assignment Module
Uses authentic geofence data and GPS tracking to intelligently assign drivers to their actual job sites
"""
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class SmartJobAssignment:
    def __init__(self):
        self.job_sites = self.load_authentic_job_sites()
        self.driver_assignments = {}
        self.geofence_history = {}
        
    def load_authentic_job_sites(self) -> Dict:
        """Load your actual job sites from Gauge API data"""
        try:
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                gauge_data = json.load(f)
            
            # Extract unique job sites from your authentic data
            job_sites = {}
            for asset in gauge_data:
                location = asset.get('Location', '')
                site = asset.get('Site', '')
                
                if location and location != 'Unknown' and 'yard' not in location.lower():
                    # This is likely a job site
                    job_key = location.replace(' ', '_').upper()
                    if job_key not in job_sites:
                        job_sites[job_key] = {
                            'name': location,
                            'site_code': site,
                            'center_lat': asset.get('Latitude', 0),
                            'center_lng': asset.get('Longitude', 0),
                            'radius': 200,  # 200 meter radius
                            'assets_present': [],
                            'type': 'job_site'
                        }
                    
                    # Add asset to this job site
                    if asset.get('AssetIdentifier'):
                        job_sites[job_key]['assets_present'].append(asset.get('AssetIdentifier'))
            
            return job_sites
            
        except Exception as e:
            # Fallback with known job sites from your data
            return {
                'RIVERFRONT_CADIZ_BRIDGE': {
                    'name': 'Riverfront & Cadiz Bridge Improvement',
                    'center_lat': 32.76591,
                    'center_lng': -96.80289,
                    'radius': 300,
                    'type': 'bridge_project'
                },
                'SH_345_BRIDGE': {
                    'name': 'SH 345 Bridge Rehabilitation',
                    'center_lat': 32.78671,
                    'center_lng': -96.79152,
                    'radius': 250,
                    'type': 'bridge_project'
                }
            }
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def is_within_geofence(self, driver_lat: float, driver_lng: float, job_site: Dict) -> bool:
        """Check if driver is within job site geofence"""
        distance = self.calculate_distance(
            driver_lat, driver_lng,
            job_site['center_lat'], job_site['center_lng']
        )
        return distance <= job_site['radius']
    
    def determine_actual_job_assignment(self, driver_id: str, gps_history: List[Dict]) -> Optional[str]:
        """
        Intelligently determine which job site a driver is actually working at
        Uses dwell time and geofence analysis to avoid false positives from drive-throughs
        """
        if not gps_history:
            return None
        
        job_site_visits = {}
        
        # Analyze GPS history for each job site
        for job_key, job_site in self.job_sites.items():
            time_in_geofence = 0
            consecutive_points = 0
            
            for gps_point in gps_history:
                lat = gps_point.get('latitude', 0)
                lng = gps_point.get('longitude', 0)
                timestamp = gps_point.get('timestamp', datetime.now())
                
                if self.is_within_geofence(lat, lng, job_site):
                    consecutive_points += 1
                    time_in_geofence += 5  # Assume 5-minute intervals
                else:
                    # Reset if they leave the geofence
                    if consecutive_points < 3:  # Less than 15 minutes = likely drive-through
                        consecutive_points = 0
                        time_in_geofence = 0
            
            # Only count as actual job assignment if they spent significant time there
            if time_in_geofence >= 30:  # At least 30 minutes
                job_site_visits[job_key] = {
                    'time_spent': time_in_geofence,
                    'confidence': min(100, time_in_geofence / 60 * 100),  # Higher time = higher confidence
                    'job_name': job_site['name']
                }
        
        # Return the job site where they spent the most time
        if job_site_visits:
            best_assignment = max(job_site_visits.items(), key=lambda x: x[1]['time_spent'])
            return best_assignment[0]
        
        return None
    
    def get_driver_current_assignment(self, driver_id: str, current_lat: float, current_lng: float) -> Dict:
        """Get current job assignment for a driver with confidence level"""
        current_assignment = None
        confidence = 0
        
        # Check which geofence they're currently in
        for job_key, job_site in self.job_sites.items():
            if self.is_within_geofence(current_lat, current_lng, job_site):
                # Check their history to determine if this is their actual job
                if driver_id in self.geofence_history:
                    actual_job = self.determine_actual_job_assignment(
                        driver_id, 
                        self.geofence_history[driver_id]
                    )
                    if actual_job == job_key:
                        confidence = 95  # High confidence - they've been here a while
                    else:
                        confidence = 30  # Low confidence - might be driving through
                else:
                    confidence = 50  # Medium confidence - first detection
                
                current_assignment = {
                    'job_site': job_key,
                    'job_name': job_site['name'],
                    'confidence': confidence,
                    'assignment_type': 'active' if confidence > 70 else 'potential'
                }
                break
        
        return current_assignment or {
            'job_site': None,
            'job_name': 'En Route / Between Jobs',
            'confidence': 0,
            'assignment_type': 'unassigned'
        }
    
    def update_driver_location(self, driver_id: str, lat: float, lng: float, timestamp: datetime = None):
        """Update driver location and maintain geofence history"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Initialize history if needed
        if driver_id not in self.geofence_history:
            self.geofence_history[driver_id] = []
        
        # Add current location to history
        self.geofence_history[driver_id].append({
            'latitude': lat,
            'longitude': lng,
            'timestamp': timestamp
        })
        
        # Keep only last 24 hours of data
        cutoff_time = timestamp - timedelta(hours=24)
        self.geofence_history[driver_id] = [
            point for point in self.geofence_history[driver_id]
            if point['timestamp'] > cutoff_time
        ]
    
    def get_job_site_summary(self) -> Dict:
        """Get summary of all job sites and current assignments"""
        summary = {}
        
        for job_key, job_site in self.job_sites.items():
            summary[job_key] = {
                'name': job_site['name'],
                'location': f"{job_site['center_lat']:.4f}, {job_site['center_lng']:.4f}",
                'radius_meters': job_site['radius'],
                'assets_present': len(job_site.get('assets_present', [])),
                'type': job_site.get('type', 'job_site')
            }
        
        return summary

# Global instance
smart_assignment = SmartJobAssignment()

def get_driver_job_assignment(driver_id: str, lat: float, lng: float) -> Dict:
    """Get smart job assignment for a driver"""
    smart_assignment.update_driver_location(driver_id, lat, lng)
    return smart_assignment.get_driver_current_assignment(driver_id, lat, lng)

def get_all_job_sites() -> Dict:
    """Get all available job sites"""
    return smart_assignment.get_job_site_summary()