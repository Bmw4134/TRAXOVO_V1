"""
Google Cloud Platform Integration for TRAXOVO
Geocoding API and fleet location intelligence
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime

class GoogleCloudGeocoding:
    """Google Cloud Geocoding API integration for fleet tracking"""
    
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        self.project_id = "geocoding-api-445715"  # From your GCP console URL
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    def geocode_address(self, address: str) -> Dict:
        """Convert address to coordinates"""
        if not self.api_key:
            return {
                "status": "error",
                "message": "Google Cloud API key required",
                "requires_setup": True
            }
        
        try:
            params = {
                "address": address,
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                location = result["geometry"]["location"]
                
                return {
                    "status": "success",
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "formatted_address": result["formatted_address"],
                    "place_id": result.get("place_id"),
                    "location_type": result["geometry"].get("location_type")
                }
            else:
                return {
                    "status": "error",
                    "message": f"Geocoding failed: {data.get('status')}",
                    "raw_response": data
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Geocoding request failed: {str(e)}"
            }
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """Convert coordinates to address"""
        if not self.api_key:
            return {
                "status": "error",
                "message": "Google Cloud API key required",
                "requires_setup": True
            }
        
        try:
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                
                return {
                    "status": "success",
                    "formatted_address": result["formatted_address"],
                    "place_id": result.get("place_id"),
                    "address_components": result.get("address_components", [])
                }
            else:
                return {
                    "status": "error",
                    "message": f"Reverse geocoding failed: {data.get('status')}",
                    "raw_response": data
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Reverse geocoding request failed: {str(e)}"
            }
    
    def geocode_fleet_locations(self, asset_locations: List[Dict]) -> List[Dict]:
        """Batch geocode fleet asset locations"""
        geocoded_assets = []
        
        for asset in asset_locations:
            asset_id = asset.get("asset_id", "unknown")
            location_description = asset.get("location", "")
            
            if location_description:
                geocode_result = self.geocode_address(location_description)
                
                enhanced_asset = {
                    "asset_id": asset_id,
                    "original_location": location_description,
                    "geocoding": geocode_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                if geocode_result.get("status") == "success":
                    enhanced_asset.update({
                        "latitude": geocode_result["latitude"],
                        "longitude": geocode_result["longitude"],
                        "formatted_address": geocode_result["formatted_address"]
                    })
                
                geocoded_assets.append(enhanced_asset)
        
        return geocoded_assets
    
    def get_route_optimization_data(self, origin: str, destinations: List[str]) -> Dict:
        """Get route optimization data for fleet dispatch"""
        # This would integrate with Google Maps Distance Matrix API
        # For now, return structured data for the optimization engine
        
        return {
            "origin": origin,
            "destinations": destinations,
            "optimization_available": True,
            "estimated_setup_time": "15_minutes",
            "requires_distance_matrix_api": True,
            "project_id": self.project_id
        }
    
    def validate_api_access(self) -> Dict:
        """Validate Google Cloud API access"""
        if not self.api_key:
            return {
                "status": "setup_required",
                "message": "Google Cloud API key not configured",
                "instructions": [
                    "Go to Google Cloud Console",
                    "Enable Geocoding API",
                    "Create API key",
                    "Add GOOGLE_CLOUD_API_KEY to environment"
                ]
            }
        
        # Test with a simple geocoding request
        test_result = self.geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")
        
        if test_result.get("status") == "success":
            return {
                "status": "connected",
                "message": "Google Cloud Geocoding API active",
                "project_id": self.project_id,
                "api_working": True
            }
        else:
            return {
                "status": "error",
                "message": "API key configured but requests failing",
                "test_result": test_result
            }

class FleetLocationIntelligence:
    """Enhanced fleet location tracking with Google Cloud integration"""
    
    def __init__(self):
        self.geocoding = GoogleCloudGeocoding()
        
    def enhance_asset_tracking(self, fleet_data: List[Dict]) -> Dict:
        """Enhance fleet data with geocoding intelligence"""
        
        # Extract location data from fleet assets
        asset_locations = []
        for asset in fleet_data:
            if "location" in asset or "site" in asset:
                asset_locations.append({
                    "asset_id": asset.get("asset_id", asset.get("id")),
                    "location": asset.get("location") or asset.get("site", "")
                })
        
        # Geocode locations
        geocoded_assets = self.geocoding.geocode_fleet_locations(asset_locations)
        
        return {
            "total_assets": len(fleet_data),
            "geocoded_assets": len(geocoded_assets),
            "geocoding_success_rate": self._calculate_success_rate(geocoded_assets),
            "enhanced_tracking": geocoded_assets,
            "google_cloud_integration": self.geocoding.validate_api_access(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_success_rate(self, geocoded_assets: List[Dict]) -> float:
        """Calculate geocoding success rate"""
        if not geocoded_assets:
            return 0.0
        
        successful = sum(1 for asset in geocoded_assets 
                        if asset.get("geocoding", {}).get("status") == "success")
        
        return round((successful / len(geocoded_assets)) * 100, 2)
    
    def get_fleet_map_data(self, enhanced_assets: List[Dict]) -> Dict:
        """Generate map visualization data for fleet tracking"""
        
        map_points = []
        for asset in enhanced_assets:
            if asset.get("latitude") and asset.get("longitude"):
                map_points.append({
                    "asset_id": asset["asset_id"],
                    "lat": asset["latitude"],
                    "lng": asset["longitude"],
                    "title": asset.get("formatted_address", asset.get("original_location")),
                    "status": "active"
                })
        
        # Calculate map center (simple average)
        if map_points:
            center_lat = sum(point["lat"] for point in map_points) / len(map_points)
            center_lng = sum(point["lng"] for point in map_points) / len(map_points)
        else:
            center_lat, center_lng = 39.8283, -98.5795  # Geographic center of US
        
        return {
            "center": {"lat": center_lat, "lng": center_lng},
            "zoom": 6,
            "markers": map_points,
            "total_tracked_assets": len(map_points),
            "map_ready": len(map_points) > 0
        }

def get_google_cloud_integration():
    """Get Google Cloud integration instance"""
    return GoogleCloudGeocoding()

def get_fleet_location_intelligence():
    """Get fleet location intelligence instance"""
    return FleetLocationIntelligence()

if __name__ == "__main__":
    # Test Google Cloud integration
    gcp = get_google_cloud_integration()
    status = gcp.validate_api_access()
    print(json.dumps(status, indent=2))