"""
TRAXOVO Job Security Monitoring - Theft Detection Engine
Implements theft detection algorithms for equipment security
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import math

logger = logging.getLogger(__name__)

class TheftDetectionEngine:
    """Core theft detection logic for TRAXOVO security monitoring"""
    
    def __init__(self):
        self.load_zone_assignments()
    
    def load_zone_assignments(self):
        """Load PE zone assignments from configuration"""
        try:
            with open('modules/security/pe_zone_assignment.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.error("PE zone assignment file not found")
            self.config = {"pe_assignments": {}, "zone_definitions": {}}
    
    def get_pe_zones(self, user_id: str) -> List[str]:
        """Get zones assigned to a specific PE"""
        # TODO: Implement user_id to pe_id mapping
        for pe_id, pe_data in self.config.get("pe_assignments", {}).items():
            if pe_data.get("email") == user_id or pe_id == user_id:
                return pe_data.get("zones", [])
        return []
    
    def is_admin_user(self, user_id: str) -> bool:
        """Check if user has admin access to all zones"""
        # TODO: Implement proper admin role checking
        for pe_id, pe_data in self.config.get("pe_assignments", {}).items():
            if (pe_data.get("email") == user_id or pe_id == user_id) and \
               pe_data.get("security_level") == "ADMIN":
                return True
        return False
    
    def filter_assets_by_pe_zones(self, assets: List[Dict], user_id: str) -> List[Dict]:
        """Filter assets to only show those in PE's assigned zones"""
        if self.is_admin_user(user_id):
            return assets  # Admin sees all assets
        
        pe_zones = self.get_pe_zones(user_id)
        if not pe_zones:
            return []  # No zones assigned
        
        filtered_assets = []
        for asset in assets:
            asset_zone = self.determine_asset_zone(asset)
            if asset_zone in pe_zones:
                filtered_assets.append(asset)
        
        return filtered_assets
    
    def determine_asset_zone(self, asset: Dict) -> Optional[str]:
        """Determine which zone an asset belongs to based on GPS coordinates"""
        try:
            asset_lat = float(asset.get('latitude', 0))
            asset_lng = float(asset.get('longitude', 0))
            
            if asset_lat == 0 and asset_lng == 0:
                return None
            
            # Check each zone to see if asset falls within boundaries
            for zone_id, zone_data in self.config.get("zone_definitions", {}).items():
                boundary = zone_data.get("boundary", {})
                center = boundary.get("center", [0, 0])
                radius_miles = boundary.get("radius_miles", 0)
                
                distance = self.calculate_distance(
                    asset_lat, asset_lng, center[0], center[1]
                )
                
                if distance <= radius_miles:
                    return zone_id
            
            return "UNASSIGNED"
        
        except (ValueError, TypeError):
            return None
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS coordinates in miles"""
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def detect_geofence_violation(self, asset: Dict) -> Dict[str, Any]:
        """Detect if asset has left its assigned zone"""
        current_zone = self.determine_asset_zone(asset)
        # TODO: Compare with asset's assigned zone from database
        
        violation = {
            "type": "geofence_violation",
            "asset_id": asset.get("id"),
            "asset_name": asset.get("name"),
            "current_zone": current_zone,
            "expected_zone": "TODO: Get from asset assignment",
            "timestamp": datetime.now().isoformat(),
            "severity": "HIGH" if current_zone == "UNASSIGNED" else "MEDIUM",
            "coordinates": {
                "lat": asset.get("latitude"),
                "lng": asset.get("longitude")
            }
        }
        
        return violation
    
    def detect_off_hours_movement(self, asset: Dict) -> Optional[Dict[str, Any]]:
        """Detect movement during non-working hours"""
        current_zone = self.determine_asset_zone(asset)
        if not current_zone or current_zone == "UNASSIGNED":
            return None
        
        zone_config = self.config.get("zone_definitions", {}).get(current_zone, {})
        working_hours = zone_config.get("working_hours", {})
        
        # TODO: Implement actual movement detection and time checking
        # For now, return a stub structure
        
        now = datetime.now()
        if self.is_outside_working_hours(now, working_hours):
            return {
                "type": "off_hours_movement",
                "asset_id": asset.get("id"),
                "asset_name": asset.get("name"),
                "zone": current_zone,
                "timestamp": now.isoformat(),
                "severity": "MEDIUM",
                "details": "Movement detected outside working hours"
            }
        
        return None
    
    def detect_orphaned_equipment(self, asset: Dict) -> Optional[Dict[str, Any]]:
        """Detect equipment moved without associated worker"""
        # TODO: Cross-reference with timecard/worker assignment data
        
        return {
            "type": "orphaned_equipment",
            "asset_id": asset.get("id"),
            "asset_name": asset.get("name"),
            "timestamp": datetime.now().isoformat(),
            "severity": "HIGH",
            "details": "Equipment movement without associated worker check-in"
        }
    
    def detect_long_offline(self, asset: Dict) -> Optional[Dict[str, Any]]:
        """Detect assets offline for extended periods"""
        last_update = asset.get("last_update")
        if not last_update:
            return None
        
        try:
            # TODO: Parse last_update timestamp properly
            # For now, simulate 6+ hour offline detection
            
            return {
                "type": "long_offline",
                "asset_id": asset.get("id"),
                "asset_name": asset.get("name"),
                "timestamp": datetime.now().isoformat(),
                "severity": "LOW",
                "details": f"Asset offline for extended period. Last seen: {last_update}"
            }
        
        except Exception:
            return None
    
    def is_outside_working_hours(self, timestamp: datetime, working_hours: Dict) -> bool:
        """Check if timestamp is outside configured working hours"""
        try:
            day_name = timestamp.strftime("%A").lower()
            working_days = working_hours.get("days", [])
            
            if day_name not in working_days:
                return True  # Weekend or non-working day
            
            start_time = working_hours.get("start", "06:00")
            end_time = working_hours.get("end", "19:00")
            
            current_time = timestamp.strftime("%H:%M")
            
            return current_time < start_time or current_time > end_time
        
        except Exception:
            return False  # Default to working hours if parsing fails
    
    def run_full_theft_scan(self, assets: List[Dict]) -> Dict[str, List[Dict]]:
        """Run all theft detection algorithms on asset list"""
        alerts = {
            "geofence_violations": [],
            "off_hours_movement": [],
            "orphaned_equipment": [],
            "long_offline": [],
            "summary": {
                "total_assets_scanned": len(assets),
                "total_alerts": 0,
                "scan_timestamp": datetime.now().isoformat()
            }
        }
        
        for asset in assets:
            # Run each detection algorithm
            geofence_alert = self.detect_geofence_violation(asset)
            if geofence_alert:
                alerts["geofence_violations"].append(geofence_alert)
            
            offhours_alert = self.detect_off_hours_movement(asset)
            if offhours_alert:
                alerts["off_hours_movement"].append(offhours_alert)
            
            orphaned_alert = self.detect_orphaned_equipment(asset)
            if orphaned_alert:
                alerts["orphaned_equipment"].append(orphaned_alert)
            
            offline_alert = self.detect_long_offline(asset)
            if offline_alert:
                alerts["long_offline"].append(offline_alert)
        
        # Calculate summary
        total_alerts = sum(len(alerts[key]) for key in alerts if isinstance(alerts[key], list))
        alerts["summary"]["total_alerts"] = total_alerts
        
        return alerts