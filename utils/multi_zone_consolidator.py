"""
Multi-Zone Job Consolidation for TRAXOVO Live Field Test

Consolidates jobs with multiple subzones into single parent zones.
Structure: Parent Zone ID, Subzone ID, Description, Address, Lat, Lon
Use parent zone for rules + summary, subzones for map + alerts.
"""
import logging
import pandas as pd
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MultiZoneConsolidator:
    def __init__(self):
        self.zones_file = "consolidated_zones.json"
        
    def process_multi_zone_csv(self, csv_file_path):
        """
        Process CSV with multi-zone structure.
        
        Expected columns:
        Parent Zone ID, Subzone ID, Description, Address, Lat, Lon
        """
        try:
            logger.info(f"Processing multi-zone CSV: {csv_file_path}")
            
            df = pd.read_csv(csv_file_path)
            
            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            consolidated_zones = {}
            
            for _, row in df.iterrows():
                parent_id = str(row.get('parent_zone_id', '')).strip()
                subzone_id = str(row.get('subzone_id', '')).strip()
                description = str(row.get('description', '')).strip()
                address = str(row.get('address', '')).strip()
                lat = float(row.get('lat', 0)) if pd.notna(row.get('lat')) else None
                lon = float(row.get('lon', 0)) if pd.notna(row.get('lon')) else None
                
                if not parent_id:
                    continue
                    
                # Initialize parent zone if not exists
                if parent_id not in consolidated_zones:
                    consolidated_zones[parent_id] = {
                        'parent_zone_id': parent_id,
                        'parent_zone_name': description.split('-')[0].strip() if description else parent_id,
                        'subzones': [],
                        'total_subzones': 0,
                        'center_lat': None,
                        'center_lon': None,
                        'bounding_box': {'min_lat': None, 'max_lat': None, 'min_lon': None, 'max_lon': None}
                    }
                
                # Add subzone
                if subzone_id:
                    subzone = {
                        'subzone_id': subzone_id,
                        'description': description,
                        'address': address,
                        'lat': lat,
                        'lon': lon,
                        'parent_zone_id': parent_id
                    }
                    
                    consolidated_zones[parent_id]['subzones'].append(subzone)
                    consolidated_zones[parent_id]['total_subzones'] += 1
                    
                    # Update bounding box and center calculation
                    if lat and lon:
                        self._update_zone_bounds(consolidated_zones[parent_id], lat, lon)
            
            # Calculate center points for parent zones
            for zone_id, zone_data in consolidated_zones.items():
                self._calculate_zone_center(zone_data)
                
            logger.info(f"✅ Consolidated {len(consolidated_zones)} parent zones with {sum(z['total_subzones'] for z in consolidated_zones.values())} subzones")
            
            return consolidated_zones
            
        except Exception as e:
            logger.error(f"Failed to process multi-zone CSV: {e}")
            return {}
    
    def _update_zone_bounds(self, zone_data, lat, lon):
        """Update bounding box for a zone"""
        bounds = zone_data['bounding_box']
        
        if bounds['min_lat'] is None or lat < bounds['min_lat']:
            bounds['min_lat'] = lat
        if bounds['max_lat'] is None or lat > bounds['max_lat']:
            bounds['max_lat'] = lat
        if bounds['min_lon'] is None or lon < bounds['min_lon']:
            bounds['min_lon'] = lon
        if bounds['max_lon'] is None or lon > bounds['max_lon']:
            bounds['max_lon'] = lon
    
    def _calculate_zone_center(self, zone_data):
        """Calculate center point for parent zone"""
        valid_coords = [(s['lat'], s['lon']) for s in zone_data['subzones'] if s['lat'] and s['lon']]
        
        if valid_coords:
            avg_lat = sum(coord[0] for coord in valid_coords) / len(valid_coords)
            avg_lon = sum(coord[1] for coord in valid_coords) / len(valid_coords)
            zone_data['center_lat'] = avg_lat
            zone_data['center_lon'] = avg_lon
    
    def get_parent_zone_for_rules(self, zone_id):
        """
        Get parent zone data for rules application.
        Used by attendance validation logic.
        """
        zones = self.load_consolidated_zones()
        
        # Check if it's already a parent zone
        if zone_id in zones:
            return zones[zone_id]
        
        # Search subzones to find parent
        for parent_id, zone_data in zones.items():
            for subzone in zone_data['subzones']:
                if subzone['subzone_id'] == zone_id:
                    return zone_data
        
        return None
    
    def get_subzones_for_map(self, parent_zone_id):
        """
        Get subzone details for map display and alerts.
        """
        zones = self.load_consolidated_zones()
        parent_zone = zones.get(parent_zone_id)
        
        if not parent_zone:
            return []
        
        return parent_zone['subzones']
    
    def get_zone_hierarchy_summary(self):
        """
        Get complete zone hierarchy for dashboard display.
        """
        zones = self.load_consolidated_zones()
        summary = []
        
        for parent_id, zone_data in zones.items():
            parent_summary = {
                'parent_zone_id': parent_id,
                'parent_zone_name': zone_data['parent_zone_name'],
                'total_subzones': zone_data['total_subzones'],
                'center_coordinates': {
                    'lat': zone_data['center_lat'],
                    'lon': zone_data['center_lon']
                },
                'subzones': []
            }
            
            for subzone in zone_data['subzones']:
                parent_summary['subzones'].append({
                    'subzone_id': subzone['subzone_id'],
                    'description': subzone['description'],
                    'coordinates': {
                        'lat': subzone['lat'],
                        'lon': subzone['lon']
                    }
                })
            
            summary.append(parent_summary)
        
        return summary
    
    def find_zone_by_coordinates(self, lat, lon, radius_km=1.0):
        """
        Find which zone (parent/subzone) contains given coordinates.
        Used for GPS alert mapping.
        """
        zones = self.load_consolidated_zones()
        matches = []
        
        for parent_id, zone_data in zones.items():
            # Check subzones first (more specific)
            for subzone in zone_data['subzones']:
                if subzone['lat'] and subzone['lon']:
                    distance = self._calculate_distance(lat, lon, subzone['lat'], subzone['lon'])
                    if distance <= radius_km:
                        matches.append({
                            'type': 'subzone',
                            'parent_zone_id': parent_id,
                            'subzone_id': subzone['subzone_id'],
                            'description': subzone['description'],
                            'distance_km': distance
                        })
            
            # Check parent zone center
            if zone_data['center_lat'] and zone_data['center_lon']:
                distance = self._calculate_distance(lat, lon, zone_data['center_lat'], zone_data['center_lon'])
                if distance <= radius_km * 2:  # Larger radius for parent zones
                    matches.append({
                        'type': 'parent_zone',
                        'parent_zone_id': parent_id,
                        'parent_zone_name': zone_data['parent_zone_name'],
                        'distance_km': distance
                    })
        
        # Sort by distance, closest first
        matches.sort(key=lambda x: x['distance_km'])
        return matches
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in km"""
        import math
        
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def save_consolidated_zones(self, zones):
        """Save consolidated zones to JSON file"""
        try:
            with open(self.zones_file, 'w') as f:
                json.dump(zones, f, indent=2)
            logger.info(f"✅ Consolidated zones saved to {self.zones_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save consolidated zones: {e}")
            return False
    
    def load_consolidated_zones(self):
        """Load consolidated zones from JSON file"""
        try:
            if Path(self.zones_file).exists():
                with open(self.zones_file, 'r') as f:
                    zones = json.load(f)
                logger.info(f"✅ Consolidated zones loaded from {self.zones_file}")
                return zones
            else:
                logger.info("No consolidated zones file found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load consolidated zones: {e}")
            return {}