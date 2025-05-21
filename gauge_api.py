"""
Gauge API Integration Module

This module provides integration with the Gauge API for telematic data retrieval.
"""
import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GaugeAPI:
    """Gauge API client for interacting with the Gauge telematics system"""
    
    def __init__(self):
        """Initialize the Gauge API client"""
        self.api_url = os.environ.get('GAUGE_API_URL')
        self.username = os.environ.get('GAUGE_API_USERNAME')
        self.password = os.environ.get('GAUGE_API_PASSWORD')
        self.token = None
        self.token_expiry = None
    
    def check_connection(self):
        """Check if connection to the Gauge API is available"""
        try:
            self.authenticate()
            return self.token is not None
        except Exception as e:
            logger.error(f"Failed to connect to Gauge API: {str(e)}")
            return False
    
    def authenticate(self):
        """Authenticate with the Gauge API and get an access token"""
        # Check if we have a valid token already
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return
        
        if not self.api_url or not self.username or not self.password:
            raise ValueError("Gauge API credentials are not configured")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/token",
                json={
                    "username": self.username,
                    "password": self.password
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'token' in data:
                self.token = data['token']
                # Token typically expires in 24 hours
                self.token_expiry = datetime.now() + timedelta(hours=23)
                logger.info("Successfully authenticated with Gauge API")
            else:
                logger.error("Failed to get token from Gauge API")
                raise ValueError("Authentication failed - no token in response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Gauge API: {str(e)}")
            self.token = None
            self.token_expiry = None
            raise
    
    def get_headers(self):
        """Get the API request headers with authentication token"""
        self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_assets(self):
        """Get a list of all assets from the Gauge API"""
        try:
            response = requests.get(
                f"{self.api_url}/assets",
                headers=self.get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get assets from Gauge API: {str(e)}")
            raise
    
    def get_asset_location(self, asset_id):
        """Get the current location of an asset"""
        try:
            response = requests.get(
                f"{self.api_url}/assets/{asset_id}/location",
                headers=self.get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get asset location from Gauge API: {str(e)}")
            raise
    
    def get_asset_locations(self, asset_id, start_date, end_date):
        """Get location history for an asset in a date range"""
        try:
            response = requests.get(
                f"{self.api_url}/assets/{asset_id}/locations",
                headers=self.get_headers(),
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get asset locations from Gauge API: {str(e)}")
            raise
    
    def get_driving_history(self, start_date, end_date):
        """Get driving history for all assets in a date range"""
        try:
            response = requests.get(
                f"{self.api_url}/reports/driving-history",
                headers=self.get_headers(),
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=60  # Longer timeout for reports
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get driving history from Gauge API: {str(e)}")
            raise
    
    def get_activity_detail(self, start_date, end_date):
        """Get activity detail for all assets in a date range"""
        try:
            response = requests.get(
                f"{self.api_url}/reports/activity-detail",
                headers=self.get_headers(),
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=60  # Longer timeout for reports
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get activity detail from Gauge API: {str(e)}")
            raise
    
    def get_asset_time_on_site(self, start_date, end_date):
        """Get asset time on site report for all assets in a date range"""
        try:
            response = requests.get(
                f"{self.api_url}/reports/asset-time-on-site",
                headers=self.get_headers(),
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=60  # Longer timeout for reports
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get asset time on site from Gauge API: {str(e)}")
            raise