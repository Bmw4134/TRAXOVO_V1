"""
TRAXORA Fleet Management System - Gauge API Module

This module handles communication with the Gauge Telematics API.
"""
import os
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GaugeAPI:
    """
    GaugeAPI class for interacting with the Gauge Telematics API.
    This class handles authentication, data retrieval, and error handling.
    """
    
    def __init__(self):
        """Initialize the GaugeAPI with configuration from environment variables"""
        self.api_url = os.environ.get('GAUGE_API_URL')
        self.username = os.environ.get('GAUGE_API_USERNAME')
        self.password = os.environ.get('GAUGE_API_PASSWORD')
        self.token = None
        self.token_expiry = None
    
    def check_connection(self):
        """
        Check if the connection to the Gauge API is working.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if not all([self.api_url, self.username, self.password]):
                logger.error("Gauge API credentials are not properly configured")
                return False
                
            # Try to authenticate
            self._authenticate()
            return self.token is not None
        except Exception as e:
            logger.error(f"Error connecting to Gauge API: {str(e)}")
            return False
    
    def _authenticate(self):
        """
        Authenticate with the Gauge API and obtain a token.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return True
            
        try:
            auth_url = f"{self.api_url}/auth"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('token')
            
            # Set token expiry (typically 24 hours, but we'll use the expiry if provided)
            expires_in = data.get('expiresIn', 86400)  # Default to 24 hours
            self.token_expiry = datetime.now().timestamp() + expires_in
            
            logger.info("Successfully authenticated with Gauge API")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Gauge API: {str(e)}")
            self.token = None
            self.token_expiry = None
            return False
    
    def get_asset_locations(self):
        """
        Get the locations of all assets.
        
        Returns:
            list: A list of asset location dictionaries
        """
        if not self._authenticate():
            return []
            
        try:
            url = f"{self.api_url}/assets/locations"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get asset locations: {str(e)}")
            return []
    
    def get_asset_details(self, asset_id):
        """
        Get details for a specific asset.
        
        Args:
            asset_id (str): The ID of the asset
            
        Returns:
            dict: Asset details or None if not found
        """
        if not self._authenticate():
            return None
            
        try:
            url = f"{self.api_url}/assets/{asset_id}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get asset details for {asset_id}: {str(e)}")
            return None
    
    def get_driving_history(self, start_date, end_date=None, asset_ids=None):
        """
        Get driving history for specified assets and date range.
        
        Args:
            start_date (str): Start date in format YYYY-MM-DD
            end_date (str, optional): End date in format YYYY-MM-DD. Default is start_date.
            asset_ids (list, optional): List of asset IDs to get history for. Default is all assets.
            
        Returns:
            dict: Driving history data or empty dict if error
        """
        if not self._authenticate():
            return {}
            
        try:
            end_date = end_date or start_date
            url = f"{self.api_url}/driving-history"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "startDate": start_date,
                "endDate": end_date
            }
            
            if asset_ids:
                payload["assetIds"] = asset_ids
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Save to cache file for offline access
            cache_dir = os.path.join("data", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"driving_history_{start_date}_{end_date}.json")
            
            with open(cache_file, 'w') as f:
                json.dump(response.json(), f)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get driving history: {str(e)}")
            return {}
    
    def get_assets(self):
        """
        Get a list of all assets.
        
        Returns:
            list: A list of asset dictionaries
        """
        if not self._authenticate():
            return []
            
        try:
            url = f"{self.api_url}/assets"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get assets: {str(e)}")
            return []