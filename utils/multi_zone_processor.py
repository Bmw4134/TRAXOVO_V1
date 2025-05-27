"""
Multi-Zone Job Logic Processor for TRAXOVO Construction Ops

This module processes authentic job site data from CSV/Excel files and creates
consolidated parent zone + subzone structures for real construction projects.
Uses authentic Ragle, Select, or Unified job data - no placeholder zones.
"""
import json
import os
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class MultiZoneProcessor:
    """Process authentic construction job data into consolidated zone structures"""
    
    def __init__(self):
        self.config_path = 'config/consolidated_zones.json'
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs('config', exist_ok=True)
    
    def process_construction_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Process authentic construction job CSV data
        
        Expected format: Parent Zone ID | Subzone ID | Project Description | Site Address | Latitude | Longitude
        
        Args:
            csv_file_path (str): Path to authentic job site CSV file
            
        Returns:
            Dict: Consolidated zone structure with parent/subzone relationships
        """
        try:
            # Read authentic construction data
            df = pd.read_csv(csv_file_path)
            logger.info(f"Processing authentic construction data from {csv_file_path}")
            
            # Process the authentic job data
            zone_structure = self._extract_construction_zones(df)
            
            # Save consolidated structure
            self._save_zone_structure(zone_structure)
            
            return zone_structure
            
        except Exception as e:
            logger.error(f"Error processing construction CSV: {e}")
            return self._get_error_structure(str(e))
    
    def process_pm_excel_zones(self, excel_file_path: str, sheet_name: str = 'PM') -> Dict[str, Any]:
        """
        Process PM sheet from Daily Driver Excel for zone working rules
        
        Args:
            excel_file_path (str): Path to authentic Daily Driver Excel
            sheet_name (str): PM sheet name
            
        Returns:
            Dict: Zone working rules extracted from authentic PM data
        """
        try:
            # Read authentic PM data
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            logger.info(f"Processing authentic PM data from {excel_file_path}")
            
            # Extract working rules from authentic PM data
            working_rules = self._extract_pm_working_rules(df)
            
            return working_rules
            
        except Exception as e:
            logger.error(f"Error processing PM Excel: {e}")
            return {}
    
    def _extract_construction_zones(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract zone structure from authentic construction data"""
        zone_structure = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "source": "Authentic Construction Job Data",
            "parent_zones": {},
            "subzone_index": {},
            "validation_rules": {}
        }
        
        # Expected columns in authentic construction data
        expected_cols = ['parent_zone_id', 'subzone_id', 'project_description', 'site_address', 'latitude', 'longitude']
        
        # Map common column variations
        col_mapping = {
            'parent zone id': 'parent_zone_id',
            'parent_zone_id': 'parent_zone_id',
            'zone_id': 'parent_zone_id',
            'subzone id': 'subzone_id',
            'subzone_id': 'subzone_id',
            'sub_zone_id': 'subzone_id',
            'project description': 'project_description',
            'project_description': 'project_description',
            'description': 'project_description',
            'site address': 'site_address',
            'site_address': 'site_address',
            'address': 'site_address',
            'latitude': 'latitude',
            'lat': 'latitude',
            'longitude': 'longitude',
            'lng': 'longitude',
            'lon': 'longitude'
        }
        
        # Normalize column names
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        
        # Apply column mapping
        df = df.rename(columns=col_mapping)
        
        for _, row in df.iterrows():
            try:
                parent_zone_id = self._safe_get_value(row, 'parent_zone_id')
                subzone_id = self._safe_get_value(row, 'subzone_id') 
                project_desc = self._safe_get_value(row, 'project_description')
                site_address = self._safe_get_value(row, 'site_address')
                latitude = self._safe_get_numeric(row, 'latitude')
                longitude = self._safe_get_numeric(row, 'longitude')
                
                if not parent_zone_id:
                    continue
                
                # Initialize parent zone if not exists
                if parent_zone_id not in zone_structure["parent_zones"]:
                    zone_structure["parent_zones"][parent_zone_id] = {
                        "zone_id": parent_zone_id,
                        "zone_name": project_desc or f"Zone {parent_zone_id}",
                        "primary_address": site_address,
                        "center_coordinates": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "subzones": {},
                        "total_subzones": 0,
                        "coverage_area": {
                            "min_lat": latitude,
                            "max_lat": latitude,
                            "min_lng": longitude,
                            "max_lng": longitude
                        }
                    }
                
                parent_zone = zone_structure["parent_zones"][parent_zone_id]
                
                # Add subzone to parent zone
                if subzone_id:
                    subzone_key = f"{parent_zone_id}_{subzone_id}"
                    
                    parent_zone["subzones"][subzone_key] = {
                        "subzone_id": subzone_id,
                        "parent_zone_id": parent_zone_id,
                        "description": project_desc,
                        "address": site_address,
                        "coordinates": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "gps_fence_radius": 100,  # 100 meter default
                        "active": True
                    }
                    
                    # Update subzone index for quick lookups
                    zone_structure["subzone_index"][subzone_key] = parent_zone_id
                    
                    # Update parent zone coverage area
                    if latitude and longitude:
                        coverage = parent_zone["coverage_area"]
                        coverage["min_lat"] = min(coverage["min_lat"], latitude)
                        coverage["max_lat"] = max(coverage["max_lat"], latitude)
                        coverage["min_lng"] = min(coverage["min_lng"], longitude)
                        coverage["max_lng"] = max(coverage["max_lng"], longitude)
                
                parent_zone["total_subzones"] = len(parent_zone["subzones"])
                
            except Exception as e:
                logger.warning(f"Error processing construction data row: {e}")
                continue
        
        # Create validation rules for parent zones
        for zone_id, zone_data in zone_structure["parent_zones"].items():
            zone_structure["validation_rules"][zone_id] = {
                "require_gps_validation": True,
                "gps_tolerance_meters": 150,
                "allow_subzone_switching": True,
                "working_hours": {
                    "start_time": "06:00",
                    "end_time": "19:00",
                    "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "attendance_rules": {
                    "late_threshold_minutes": 15,
                    "early_departure_threshold": 30,
                    "minimum_hours": 8.0
                }
            }
        
        logger.info(f"Processed {len(zone_structure['parent_zones'])} parent zones with {len(zone_structure['subzone_index'])} total subzones")
        
        return zone_structure
    
    def _extract_pm_working_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract working rules from authentic PM data"""
        working_rules = {}
        
        # Common PM sheet column variations
        pm_cols = {
            'zone_id': ['zone_id', 'zone', 'job_zone', 'zone_code'],
            'zone_name': ['zone_name', 'zone_description', 'job_name', 'project_name'],
            'sr_pm': ['sr_pm', 'project_manager', 'pm', 'supervisor'],
            'start_time': ['start_time', 'work_start', 'shift_start', 'begin_time'],
            'end_time': ['end_time', 'work_end', 'shift_end', 'finish_time'],
            'late_threshold': ['late_threshold', 'late_minutes', 'grace_period']
        }
        
        # Normalize column names
        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
        
        for _, row in df.iterrows():
            try:
                zone_id = self._find_column_value(row, pm_cols['zone_id'])
                zone_name = self._find_column_value(row, pm_cols['zone_name'])
                sr_pm = self._find_column_value(row, pm_cols['sr_pm'])
                start_time = self._find_column_value(row, pm_cols['start_time'])
                end_time = self._find_column_value(row, pm_cols['end_time'])
                late_threshold = self._find_column_value(row, pm_cols['late_threshold'])
                
                if zone_id:
                    working_rules[zone_id] = {
                        "zone_id": zone_id,
                        "zone_name": zone_name or f"Zone {zone_id}",
                        "sr_pm": sr_pm or "Unassigned",
                        "working_hours": {
                            "start_time": self._parse_time(start_time) or "06:00",
                            "end_time": self._parse_time(end_time) or "19:00",
                            "late_threshold_minutes": self._parse_minutes(late_threshold) or 15
                        }
                    }
                    
            except Exception as e:
                logger.warning(f"Error processing PM rule row: {e}")
                continue
        
        return working_rules
    
    def _safe_get_value(self, row, column_name):
        """Safely get value from row"""
        if column_name in row.index and pd.notna(row[column_name]):
            return str(row[column_name]).strip()
        return None
    
    def _safe_get_numeric(self, row, column_name):
        """Safely get numeric value from row"""
        if column_name in row.index and pd.notna(row[column_name]):
            try:
                return float(row[column_name])
            except (ValueError, TypeError):
                pass
        return None
    
    def _find_column_value(self, row, possible_columns):
        """Find value using multiple possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                return str(row[col]).strip()
        return None
    
    def _parse_time(self, time_value):
        """Parse time value to HH:MM format"""
        if not time_value or pd.isna(time_value):
            return None
        
        time_str = str(time_value).strip()
        if ':' in time_str:
            return time_str[:5]  # Take HH:MM part
        elif len(time_str) == 4 and time_str.isdigit():
            return f"{time_str[:2]}:{time_str[2:]}"
        
        return None
    
    def _parse_minutes(self, minute_value):
        """Parse minute value to integer"""
        if not minute_value or pd.isna(minute_value):
            return None
        
        try:
            return int(float(minute_value))
        except (ValueError, TypeError):
            return None
    
    def _get_error_structure(self, error_msg: str) -> Dict[str, Any]:
        """Return error structure when processing fails"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "source": "Error - No Authentic Data Processed",
            "error": error_msg,
            "parent_zones": {},
            "subzone_index": {},
            "validation_rules": {}
        }
    
    def _save_zone_structure(self, zone_structure: Dict[str, Any]):
        """Save consolidated zone structure to JSON"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(zone_structure, f, indent=2)
            logger.info(f"Consolidated zone structure saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving zone structure: {e}")
    
    def load_zone_structure(self) -> Dict[str, Any]:
        """Load consolidated zone structure"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Zone structure file not found at {self.config_path}")
                return self._get_error_structure("No authentic zone data found")
        except Exception as e:
            logger.error(f"Error loading zone structure: {e}")
            return self._get_error_structure(str(e))
    
    def get_parent_zone(self, zone_id: str) -> Dict[str, Any]:
        """Get parent zone data"""
        structure = self.load_zone_structure()
        return structure.get("parent_zones", {}).get(zone_id, {})
    
    def get_subzone(self, subzone_key: str) -> Tuple[str, Dict[str, Any]]:
        """Get subzone data and parent zone ID"""
        structure = self.load_zone_structure()
        parent_zone_id = structure.get("subzone_index", {}).get(subzone_key)
        
        if parent_zone_id:
            parent_zone = structure.get("parent_zones", {}).get(parent_zone_id, {})
            subzone_data = parent_zone.get("subzones", {}).get(subzone_key, {})
            return parent_zone_id, subzone_data
        
        return None, {}
    
    def validate_gps_in_zone(self, zone_id: str, latitude: float, longitude: float, subzone_id: str = None) -> Dict[str, Any]:
        """
        Validate GPS coordinates against authentic zone boundaries
        
        Args:
            zone_id (str): Parent zone ID
            latitude (float): GPS latitude
            longitude (float): GPS longitude  
            subzone_id (str): Optional specific subzone to check
            
        Returns:
            Dict: Validation result with zone match details
        """
        structure = self.load_zone_structure()
        parent_zone = structure.get("parent_zones", {}).get(zone_id, {})
        
        if not parent_zone:
            return {
                "valid": False,
                "reason": f"Zone {zone_id} not found in authentic data",
                "zone_id": zone_id
            }
        
        # Check specific subzone if requested
        if subzone_id:
            subzone_key = f"{zone_id}_{subzone_id}"
            subzone_data = parent_zone.get("subzones", {}).get(subzone_key, {})
            
            if subzone_data:
                subzone_coords = subzone_data.get("coordinates", {})
                subzone_lat = subzone_coords.get("latitude")
                subzone_lng = subzone_coords.get("longitude")
                radius = subzone_data.get("gps_fence_radius", 100)
                
                if subzone_lat and subzone_lng:
                    distance = self._calculate_distance(latitude, longitude, subzone_lat, subzone_lng)
                    
                    if distance <= radius:
                        return {
                            "valid": True,
                            "zone_id": zone_id,
                            "subzone_id": subzone_id,
                            "match_type": "subzone",
                            "distance_meters": distance,
                            "address": subzone_data.get("address")
                        }
        
        # Check parent zone coverage area
        coverage = parent_zone.get("coverage_area", {})
        if (coverage.get("min_lat") <= latitude <= coverage.get("max_lat") and
            coverage.get("min_lng") <= longitude <= coverage.get("max_lng")):
            
            return {
                "valid": True,
                "zone_id": zone_id,
                "match_type": "parent_zone",
                "address": parent_zone.get("primary_address")
            }
        
        return {
            "valid": False,
            "reason": "GPS coordinates outside authentic zone boundaries",
            "zone_id": zone_id,
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS points in meters"""
        import math
        
        # Haversine formula for distance calculation
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c