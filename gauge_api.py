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
            
            # List of possible endpoint formats to try
            endpoint_formats = [
                "/api/v1/auth/token",
                "/auth/token",
                "/api/auth/token",
                "/api/v2/auth/token",
                "/v1/auth/token"
            ]
            
            # Try each endpoint format until one works
            for endpoint in endpoint_formats:
                auth_url = f"{self.api_url.rstrip('/')}{endpoint}"
                
                try:
                    logger.info(f"Trying authentication endpoint: {auth_url}")
                    response = requests.post(
                        auth_url,
                        json={
                            "username": self.username,
                            "password": self.password
                        },
                        timeout=15,  # Increased timeout for more reliability
                        verify=False  # SSL verification disabled with warning suppression
                    )
                    
                    # If we get a successful response, process it
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if 'token' in data:
                                self.token = data['token']
                                # Token typically expires in 24 hours
                                self.token_expiry = datetime.now() + timedelta(hours=23)
                                logger.info(f"Successfully authenticated with Gauge API using endpoint: {endpoint}")
                                return
                            else:
                                logger.warning(f"Response from {auth_url} does not contain a token")
                        except ValueError:
                            logger.warning(f"Invalid JSON response from {auth_url}: {response.text[:100]}...")
                    else:
                        logger.warning(f"Authentication attempt to {auth_url} failed with status code {response.status_code}")
                        
                except requests.exceptions.RequestException as req_err:
                    logger.warning(f"Request failed for {auth_url}: {str(req_err)}")
                    continue
            
            # If we get here, all authentication attempts failed
            logger.error("All authentication attempts failed. Please check API URL and credentials.")
            self.token = None
            self.token_expiry = None
                
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
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
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get assets")
                return []
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            "/assets",
            "/api/v1/assets",
            "/api/assets"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get assets from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30,
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get assets from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting assets from {endpoint}: {str(e)}")
                continue
        
        logger.error("All attempts to get assets failed")
        return []
    
    def get_asset_location(self, asset_id):
        """Get the current location of an asset"""
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get asset location")
                return {}
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            f"/assets/{asset_id}/location",
            f"/api/v1/assets/{asset_id}/location",
            f"/api/assets/{asset_id}/location"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get asset location from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30,
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get asset location from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting asset location from {endpoint}: {str(e)}")
                continue
        
        logger.error(f"All attempts to get location for asset {asset_id} failed")
        return {}
    
    def get_asset_locations(self, asset_id, start_date, end_date):
        """Get location history for an asset in a date range"""
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get asset location history")
                return []
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            f"/assets/{asset_id}/locations",
            f"/api/v1/assets/{asset_id}/locations",
            f"/api/assets/{asset_id}/locations",
            f"/assets/{asset_id}/location/history"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get asset location history from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    timeout=30,
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get asset location history from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting asset location history from {endpoint}: {str(e)}")
                continue
        
        logger.error(f"All attempts to get location history for asset {asset_id} failed")
        return []
    
    def get_driving_history(self, start_date, end_date):
        """Get driving history for all assets in a date range"""
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get driving history")
                return []
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            "/reports/driving-history",
            "/api/v1/reports/driving-history",
            "/api/reports/driving-history",
            "/api/v1/reports/driving_history",
            "/reports/driving_history"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get driving history from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    timeout=60,  # Longer timeout for reports
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get driving history from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting driving history from {endpoint}: {str(e)}")
                continue
        
        logger.error("All attempts to get driving history failed")
        return []
    
    def get_activity_detail(self, start_date, end_date):
        """Get activity detail for all assets in a date range"""
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get activity detail")
                return []
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            "/reports/activity-detail",
            "/api/v1/reports/activity-detail",
            "/api/reports/activity-detail",
            "/api/v1/reports/activity_detail",
            "/reports/activity_detail"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get activity detail from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    timeout=60,  # Longer timeout for reports
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get activity detail from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting activity detail from {endpoint}: {str(e)}")
                continue
        
        logger.error("All attempts to get activity detail failed")
        return []
    
    def get_asset_time_on_site(self, start_date, end_date):
        """Get asset time on site report for all assets in a date range"""
        if not self.token:
            self.authenticate()
            if not self.token:
                logger.error("Not authenticated with Gauge API, cannot get asset time on site report")
                return []
                
        # List of possible endpoint formats to try
        endpoint_formats = [
            "/reports/asset-time-on-site",
            "/api/v1/reports/asset-time-on-site",
            "/api/reports/asset-time-on-site",
            "/reports/assets/time-on-site",
            "/api/v1/reports/asset_time_on_site",
            "/reports/asset_time_on_site"
        ]
        
        for endpoint in endpoint_formats:
            try:
                url = f"{self.api_url.rstrip('/')}{endpoint}"
                logger.info(f"Trying to get asset time on site report from: {url}")
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    timeout=60,  # Longer timeout for reports
                    verify=False  # Disable SSL verification for development environments
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get asset time on site report from {url}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error getting asset time on site report from {endpoint}: {str(e)}")
                continue
        
        logger.error("All attempts to get asset time on site report failed")
        return []