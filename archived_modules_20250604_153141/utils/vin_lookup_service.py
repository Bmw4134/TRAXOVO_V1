"""
VIN Lookup Service

This module provides VIN (Vehicle Identification Number) lookup capabilities
to retrieve vehicle details and check for active recalls via the NHTSA API.
"""

import logging
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class VINLookupService:
    """
    Service for looking up vehicle information and recalls by VIN.
    Uses the NHTSA (National Highway Traffic Safety Administration) API.
    """
    
    def __init__(self):
        """Initialize the VIN lookup service"""
        self.nhtsa_base_url = "https://vpic.nhtsa.dot.gov/api/vehicles"
        self.last_request_time = None
        self.cache = {}  # Simple cache to avoid repeated API calls
    
    def lookup_vin(self, vin):
        """
        Look up vehicle information by VIN
        
        Args:
            vin (str): Vehicle Identification Number
            
        Returns:
            dict: Vehicle information including year, make, model
        """
        if not vin or len(vin) < 17:
            logger.warning(f"Invalid VIN: {vin}")
            return {
                "success": False,
                "error": "Invalid VIN format. VIN should be 17 characters.",
                "data": None
            }
        
        # Check cache first
        if vin in self.cache and 'vehicle_info' in self.cache[vin]:
            logger.info(f"Using cached vehicle info for VIN: {vin}")
            return self.cache[vin]['vehicle_info']
        
        # Construct API URL
        url = f"{self.nhtsa_base_url}/DecodeVinValues/{vin}?format=json"
        
        try:
            response = requests.get(url, timeout=10)
            self.last_request_time = datetime.now()
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'Results' in data and len(data['Results']) > 0:
                        result = data['Results'][0]
                        
                        # Extract relevant vehicle information
                        vehicle_info = {
                            "success": True,
                            "error": None,
                            "data": {
                                "vin": vin,
                                "year": result.get('ModelYear'),
                                "make": result.get('Make'),
                                "model": result.get('Model'),
                                "trim": result.get('Trim'),
                                "vehicle_type": result.get('VehicleType'),
                                "body_class": result.get('BodyClass'),
                                "engine": result.get('EngineCylinders'),
                                "fuel_type": result.get('FuelTypePrimary'),
                                "gvwr": result.get('GVWR'),
                                "plant": result.get('PlantCity'),
                                "manufacturer": result.get('Manufacturer')
                            }
                        }
                        
                        # Cache the result
                        if vin not in self.cache:
                            self.cache[vin] = {}
                        self.cache[vin]['vehicle_info'] = vehicle_info
                        
                        logger.info(f"Successfully retrieved vehicle info for VIN: {vin}")
                        return vehicle_info
                    else:
                        logger.warning(f"No vehicle information found for VIN: {vin}")
                        return {
                            "success": False,
                            "error": "No vehicle information found for this VIN.",
                            "data": None
                        }
                except Exception as e:
                    logger.error(f"Error parsing VIN response: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Error parsing response: {str(e)}",
                        "data": None
                    }
            else:
                logger.error(f"API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "data": None
                }
        except Exception as e:
            logger.error(f"Error looking up VIN: {str(e)}")
            return {
                "success": False,
                "error": f"Error looking up VIN: {str(e)}",
                "data": None
            }
    
    def check_recalls(self, vin):
        """
        Check for active recalls by VIN
        
        Args:
            vin (str): Vehicle Identification Number
            
        Returns:
            dict: Recall information if available
        """
        if not vin or len(vin) < 17:
            logger.warning(f"Invalid VIN for recall check: {vin}")
            return {
                "success": False,
                "error": "Invalid VIN format. VIN should be 17 characters.",
                "data": None
            }
        
        # Check cache first
        if vin in self.cache and 'recalls' in self.cache[vin]:
            logger.info(f"Using cached recall info for VIN: {vin}")
            return self.cache[vin]['recalls']
        
        # Construct API URL
        url = f"{self.nhtsa_base_url}/GetRecallsByVIN/{vin}?format=json"
        
        try:
            response = requests.get(url, timeout=10)
            self.last_request_time = datetime.now()
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'Results' in data:
                        recalls = data['Results']
                        
                        # Process recalls
                        recall_info = {
                            "success": True,
                            "error": None,
                            "data": {
                                "vin": vin,
                                "recall_count": len(recalls),
                                "recalls": recalls
                            }
                        }
                        
                        # Add severity assessment
                        recall_info["data"]["has_critical_recalls"] = any(
                            recall.get('Conequence', '').lower().find('crash') >= 0 or
                            recall.get('Conequence', '').lower().find('fire') >= 0 or
                            recall.get('Conequence', '').lower().find('injury') >= 0
                            for recall in recalls
                        )
                        
                        # Cache the result
                        if vin not in self.cache:
                            self.cache[vin] = {}
                        self.cache[vin]['recalls'] = recall_info
                        
                        logger.info(f"Successfully retrieved recall info for VIN: {vin}")
                        return recall_info
                    else:
                        logger.warning(f"No recall information format for VIN: {vin}")
                        return {
                            "success": False,
                            "error": "Invalid response format.",
                            "data": None
                        }
                except Exception as e:
                    logger.error(f"Error parsing recall response: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Error parsing response: {str(e)}",
                        "data": None
                    }
            else:
                logger.error(f"API error in recall check: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "data": None
                }
        except Exception as e:
            logger.error(f"Error checking recalls: {str(e)}")
            return {
                "success": False,
                "error": f"Error checking recalls: {str(e)}",
                "data": None
            }
    
    def get_vehicle_info_with_recalls(self, vin):
        """
        Comprehensive lookup that returns both vehicle info and recall status
        
        Args:
            vin (str): Vehicle Identification Number
            
        Returns:
            dict: Combined vehicle and recall information
        """
        # Get vehicle information
        vehicle_info = self.lookup_vin(vin)
        
        # Get recall information
        recall_info = self.check_recalls(vin)
        
        # Combine the results
        combined_info = {
            "success": vehicle_info.get("success") or recall_info.get("success"),
            "vehicle_info": vehicle_info.get("data"),
            "recalls": recall_info.get("data"),
            "has_recalls": recall_info.get("data", {}).get("recall_count", 0) > 0 if recall_info.get("success") else None,
            "has_critical_recalls": recall_info.get("data", {}).get("has_critical_recalls", False) if recall_info.get("success") else None,
            "errors": []
        }
        
        # Add any errors
        if not vehicle_info.get("success"):
            combined_info["errors"].append(f"Vehicle info: {vehicle_info.get('error')}")
        
        if not recall_info.get("success"):
            combined_info["errors"].append(f"Recall info: {recall_info.get('error')}")
        
        return combined_info


# Factory function to get a singleton instance
_instance = None
def get_vin_service():
    """Get a singleton instance of the VIN lookup service"""
    global _instance
    if _instance is None:
        _instance = VINLookupService()
    return _instance