"""
TRAXORA Fleet Management System - Gauge API Module

This module provides utilities for connecting to and retrieving data from the Gauge API.
"""

import os
import requests
import logging
import json
from datetime import datetime
import base64

# Configure logging
logger = logging.getLogger(__name__)

# API configuration from environment variables
GAUGE_API_URL = os.environ.get('GAUGE_API_URL', 'https://api.gaugesmart.com')
GAUGE_API_KEY = os.environ.get('GAUGE_API_KEY')
GAUGE_API_USERNAME = os.environ.get('GAUGE_API_USERNAME')
GAUGE_API_PASSWORD = os.environ.get('GAUGE_API_PASSWORD')
GAUGE_ASSET_LIST_ID = os.environ.get('GAUGE_ASSET_LIST_ID', '28dcba94c01e453fa8e9215a068f30e4')

def test_gauge_api_connection():
    """
    Test connection to the Gauge API
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        logger.info(f"Testing Gauge API connection to: {GAUGE_API_URL}")
        
        # Try with API key first
        if GAUGE_API_KEY:
            headers = {
                'Authorization': f'Bearer {GAUGE_API_KEY}',
                'Content-Type': 'application/json'
            }
            endpoint = f"{GAUGE_API_URL}/assets"
            
            response = requests.get(endpoint, headers=headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                logger.info("Gauge API connection successful with API key")
                return True
            else:
                logger.warning(f"API key failed with status: {response.status_code}")
        
        # Try with username/password
        if GAUGE_API_USERNAME and GAUGE_API_PASSWORD:
            auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
            endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"
            
            response = requests.get(endpoint, auth=auth, timeout=30, verify=False)
            
            if response.status_code == 200:
                logger.info("Gauge API connection successful with basic auth")
                return True
            else:
                logger.warning(f"Basic auth failed with status: {response.status_code}")
                
        logger.error("All Gauge API authentication methods failed")
        return False
        
    except Exception as e:
        logger.error(f"Error testing Gauge API connection: {str(e)}")
        return False

def get_assets():
    """
    Get list of assets from the Gauge API
    
    Returns:
        list: List of assets, or empty list if failed
    """
    try:
        # Try with API key first
        if GAUGE_API_KEY:
            headers = {
                'Authorization': f'Bearer {GAUGE_API_KEY}',
                'Content-Type': 'application/json'
            }
            endpoint = f"{GAUGE_API_URL}/assets"
            
            response = requests.get(endpoint, headers=headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"Retrieved {len(assets)} assets from Gauge API (API key)")
                return assets
        
        # Try with username/password
        if GAUGE_API_USERNAME and GAUGE_API_PASSWORD:
            auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
            endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"
            
            response = requests.get(endpoint, auth=auth, timeout=30, verify=False)
            
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"Retrieved {len(assets)} assets from Gauge API (basic auth)")
                return assets
        
        logger.error("Failed to get assets from Gauge API")
        return []
        
    except Exception as e:
        logger.error(f"Error getting assets from Gauge API: {str(e)}")
        return []

def get_asset_locations(asset_id, start_date=None, end_date=None):
    """
    Get location history for a specific asset
    
    Args:
        asset_id (str): Asset ID
        start_date (datetime): Start date for history
        end_date (datetime): End date for history
        
    Returns:
        list: List of location records
    """
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=1)
        if not end_date:
            end_date = datetime.now()
            
        # Try with API key first
        if GAUGE_API_KEY:
            headers = {
                'Authorization': f'Bearer {GAUGE_API_KEY}',
                'Content-Type': 'application/json'
            }
            endpoint = f"{GAUGE_API_URL}/assets/{asset_id}/locations"
            params = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                locations = response.json()
                logger.info(f"Retrieved {len(locations)} location records for asset {asset_id}")
                return locations
        
        # Try with username/password
        if GAUGE_API_USERNAME and GAUGE_API_PASSWORD:
            auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
            endpoint = f"{GAUGE_API_URL}/assets/{asset_id}/history"
            
            response = requests.get(endpoint, auth=auth, timeout=30, verify=False)
            
            if response.status_code == 200:
                locations = response.json()
                logger.info(f"Retrieved {len(locations)} location records for asset {asset_id}")
                return locations
        
        logger.error(f"Failed to get location data for asset {asset_id}")
        return []
        
    except Exception as e:
        logger.error(f"Error getting asset locations: {str(e)}")
        return []

def get_driver_data():
    """
    Get driver/operator data from Gauge API
    
    Returns:
        list: List of driver records
    """
    try:
        # Try with API key first
        if GAUGE_API_KEY:
            headers = {
                'Authorization': f'Bearer {GAUGE_API_KEY}',
                'Content-Type': 'application/json'
            }
            endpoint = f"{GAUGE_API_URL}/drivers"
            
            response = requests.get(endpoint, headers=headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                drivers = response.json()
                logger.info(f"Retrieved {len(drivers)} driver records from Gauge API")
                return drivers
        
        logger.warning("Driver data endpoint not available or configured")
        return []
        
    except Exception as e:
        logger.error(f"Error getting driver data: {str(e)}")
        return []