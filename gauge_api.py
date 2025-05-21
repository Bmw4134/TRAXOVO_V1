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
        base_url = os.environ.get('GAUGE_API_URL', '')
        # Clean up the URL to ensure it doesn't have trailing components
        if '/AssetList/' in base_url:
            # Extract just the base URL without the AssetList part
            base_parts = base_url.split('/AssetList/')
            self.api_url = base_parts[0]
            self.asset_list_id = base_parts[1] if len(base_parts) > 1 else None
        else:
            self.api_url = base_url
            self.asset_list_id = None
        
        self.username = os.environ.get('GAUGE_API_USERNAME')
        self.password = os.environ.get('GAUGE_API_PASSWORD')
        self.token = None
        self.token_expiry = None
        
        logger.info(f"Gauge API initialized with URL: {self.api_url} (Asset List ID: {self.asset_list_id})")
    
    def check_connection(self):
        """Check if connection to the Gauge API is available"""
        try:
            self.authenticate()
            return self.token is not None
        except Exception as e:
            logger.error(f"Failed to connect to Gauge API: {str(e)}")
            return False
    
    def connection_status(self):
        """Get a detailed connection status, useful for UI display"""
        if not self.api_url:
            return {
                'status': 'not_configured',
                'message': 'API URL not configured'
            }
        
        if not self.username or not self.password:
            return {
                'status': 'missing_credentials',
                'message': 'API credentials not fully configured'
            }
        
        try:
            self.authenticate()
            if self.token:
                return {
                    'status': 'connected',
                    'message': 'Successfully connected to Gauge API'
                }
            else:
                return {
                    'status': 'authentication_failed',
                    'message': 'Failed to authenticate with Gauge API'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error connecting to Gauge API: {str(e)}'
            }
    
    def authenticate(self):
        """Authenticate with the Gauge API and get an access token"""
        # Check if we have a valid token already
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return
        
        if not self.api_url or not self.username or not self.password:
            logger.error("Gauge API credentials are not fully configured")
            self.token = None
            self.token_expiry = None
            return
        
        try:
            # Suppress just the InsecureRequestWarning specifically
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Log more details for debugging
            logger.info(f"Attempting to authenticate with Gauge API at {self.api_url}")
            
            # Try the correct endpoint first
            auth_url = f"{self.api_url}/api/v1/auth/token"
            
            response = requests.post(
                auth_url,
                json={
                    "username": self.username,
                    "password": self.password
                },
                timeout=10,
                verify=False  # SSL verification disabled with warning suppression
            )
            
            # If first attempt fails, try alternative endpoint format
            if response.status_code == 404:
                logger.info("First auth attempt returned 404, trying alternative endpoint")
                auth_url = f"{self.api_url}/auth/token"
                response = requests.post(
                    auth_url,
                    json={
                        "username": self.username,
                        "password": self.password
                    },
                    timeout=10,
                    verify=False
                )
            
            # Check for non-200 status code specifically to provide better error handling
            if response.status_code != 200:
                logger.error(f"Authentication failed with status code {response.status_code} at {auth_url}: {response.text[:200]}...")
                self.token = None
                self.token_expiry = None
                return
                
            # Try to parse JSON response 
            try:
                data = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response from API: {response.text[:100]}...")
                self.token = None
                self.token_expiry = None
                return
                
            if 'token' in data:
                self.token = data['token']
                # Token typically expires in 24 hours
                self.token_expiry = datetime.now() + timedelta(hours=23)
                logger.info("Successfully authenticated with Gauge API")
            else:
                logger.error("Failed to get token from API response")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Gauge API: {str(e)}")
            self.token = None
            self.token_expiry = None
    
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
                timeout=30,
                verify=False  # Disable SSL verification for development environments
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
                timeout=30,
                verify=False  # Disable SSL verification for development environments
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
                timeout=30,
                verify=False  # Disable SSL verification for development environments
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
                timeout=60,  # Longer timeout for reports
                verify=False  # Disable SSL verification for development environments
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
                timeout=60,  # Longer timeout for reports
                verify=False  # Disable SSL verification for development environments
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
                timeout=60,  # Longer timeout for reports
                verify=False  # Disable SSL verification for development environments
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get asset time on site from Gauge API: {str(e)}")
            raise