"""
TRAXORA GENIUS CORE | Samsara Bridge

This module provides a conditional bridge to the Samsara API,
only activating for specific company contexts.
"""
import os
import logging
import requests
from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SamsaraBridge:
    """Bridge to the Samsara API with conditional activation based on company context"""
    
    def __init__(self, company_name: str = None):
        """
        Initialize the Samsara bridge
        
        Args:
            company_name (str): Name of the company context
        """
        self.company_name = company_name
        self.api_key = None
        self.api_base_url = "https://api.samsara.com/v1"
        self.enabled = False
        self._initialize()
    
    def _initialize(self):
        """Initialize the bridge based on company context"""
        # Only activate for specific companies
        if self.company_name == "Unified Specialties":
            logger.info(f"Samsara Bridge activating for {self.company_name}")
            
            # Get the API key from environment
            self.api_key = os.environ.get("UNIFIED_SAMSARA_API_KEY")
            
            if not self.api_key:
                logger.warning("Samsara API key not found in environment variables")
                return
            
            self.enabled = True
            logger.info("Samsara Bridge successfully initialized")
        else:
            logger.info(f"Samsara Bridge not configured for {self.company_name}")
    
    def is_enabled(self) -> bool:
        """
        Check if the Samsara bridge is enabled
        
        Returns:
            bool: True if the bridge is enabled, False otherwise
        """
        return self.enabled
    
    def get_vehicles(self) -> List[Dict]:
        """
        Get all vehicles from Samsara fleet
        
        Returns:
            list: List of vehicle data dictionaries
        """
        if not self.enabled:
            logger.warning("Samsara Bridge not enabled, cannot get vehicles")
            return []
        
        try:
            response = requests.get(
                f"{self.api_base_url}/fleet/vehicles",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("vehicles", [])
            else:
                logger.error(f"Failed to get vehicles: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting vehicles from Samsara: {str(e)}")
            return []
    
    def get_locations(self, start_time: Optional[datetime] = None, 
                      end_time: Optional[datetime] = None) -> List[Dict]:
        """
        Get location history for all vehicles
        
        Args:
            start_time (datetime): Start time for location history
            end_time (datetime): End time for location history
            
        Returns:
            list: List of location data dictionaries
        """
        if not self.enabled:
            logger.warning("Samsara Bridge not enabled, cannot get locations")
            return []
        
        # Default to last 24 hours if not specified
        if not start_time:
            start_time = datetime.now() - timedelta(days=1)
        if not end_time:
            end_time = datetime.now()
        
        # Convert to Unix timestamps (milliseconds)
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        try:
            response = requests.get(
                f"{self.api_base_url}/fleet/locations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "startMs": start_ms,
                    "endMs": end_ms
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("locations", [])
            else:
                logger.error(f"Failed to get locations: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting locations from Samsara: {str(e)}")
            return []
    
    def get_drivers(self) -> List[Dict]:
        """
        Get all drivers from Samsara fleet
        
        Returns:
            list: List of driver data dictionaries
        """
        if not self.enabled:
            logger.warning("Samsara Bridge not enabled, cannot get drivers")
            return []
        
        try:
            response = requests.get(
                f"{self.api_base_url}/fleet/drivers",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("drivers", [])
            else:
                logger.error(f"Failed to get drivers: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting drivers from Samsara: {str(e)}")
            return []
    
    def get_driver_locations(self, driver_id: str) -> Dict:
        """
        Get current location for a specific driver
        
        Args:
            driver_id (str): ID of the driver
            
        Returns:
            dict: Driver location data
        """
        if not self.enabled:
            logger.warning("Samsara Bridge not enabled, cannot get driver location")
            return {}
        
        try:
            response = requests.get(
                f"{self.api_base_url}/fleet/drivers/{driver_id}/locations",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get driver location: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting driver location from Samsara: {str(e)}")
            return {}

def get_bridge(company_name: str = None) -> SamsaraBridge:
    """
    Factory function to get a Samsara bridge instance
    
    Args:
        company_name (str): Name of the company context
        
    Returns:
        SamsaraBridge: Initialized bridge instance
    """
    return SamsaraBridge(company_name)