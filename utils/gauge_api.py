` tags.

```python
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
        logger.info(f"Gauge API initialized with URL: {GAUGE_API_URL} (Asset List ID: {GAUGE_ASSET_LIST_ID})")

        # Try basic authentication
        if GAUGE_API_USERNAME and GAUGE_API_PASSWORD:
            logger.info("Trying direct API access with basic authentication")

            auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
            endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"

            response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

            if response.status_code == 200:
                logger.info("Direct API access with basic authentication successful")
                return True
            else:
                logger.error(f"API access failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        else:
            logger.error("API credentials not configured")
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
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return []

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"

        response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

        if response.status_code == 200:
            assets = response.json()
            logger.info(f"Retrieved {len(assets)} assets from Gauge API")
            return assets
        else:
            logger.error(f"Failed to get assets. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error getting assets from Gauge API: {str(e)}")
        return []

def get_asset_details(asset_id):
    """
    Get details for a specific asset

    Args:
        asset_id (str): Asset ID

    Returns:
        dict: Asset details, or empty dict if failed
    """
    try:
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return {}

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/Asset/{asset_id}"

        response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

        if response.status_code == 200:
            asset = response.json()
            logger.info(f"Retrieved details for asset {asset_id}")
            return asset
        else:
            logger.error(f"Failed to get asset details. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {}

    except Exception as e:
        logger.error(f"Error getting asset details from Gauge API: {str(e)}")
        return {}

def get_asset_location_history(asset_id, start_date, end_date):
    """
    Get location history for a specific asset

    Args:
        asset_id (str): Asset ID
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD

    Returns:
        list: Location history, or empty list if failed
    """
    try:
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return []

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/AssetHistory/{asset_id}"

        params = {
            'startDate': start_date,
            'endDate': end_date
        }

        response = requests.get(endpoint, auth=auth, params=params, timeout=30, verify=True)

        if response.status_code == 200:
            history = response.json()
            logger.info(f"Retrieved location history for asset {asset_id}")
            return history
        else:
            logger.error(f"Failed to get asset location history. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error getting asset location history from Gauge API: {str(e)}")
        return []
```

```
The code has been modified to enable SSL verification by setting `verify=True` in the `requests.get` calls within the functions `test_gauge_api_connection`, `get_assets`, `get_asset_details`, and `get_asset_location_history`.
```

```
<replit_final_file>
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
        logger.info(f"Gauge API initialized with URL: {GAUGE_API_URL} (Asset List ID: {GAUGE_ASSET_LIST_ID})")

        # Try basic authentication
        if GAUGE_API_USERNAME and GAUGE_API_PASSWORD:
            logger.info("Trying direct API access with basic authentication")

            auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
            endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"

            response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

            if response.status_code == 200:
                logger.info("Direct API access with basic authentication successful")
                return True
            else:
                logger.error(f"API access failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        else:
            logger.error("API credentials not configured")
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
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return []

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/AssetList/{GAUGE_ASSET_LIST_ID}"

        response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

        if response.status_code == 200:
            assets = response.json()
            logger.info(f"Retrieved {len(assets)} assets from Gauge API")
            return assets
        else:
            logger.error(f"Failed to get assets. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error getting assets from Gauge API: {str(e)}")
        return []

def get_asset_details(asset_id):
    """
    Get details for a specific asset

    Args:
        asset_id (str): Asset ID

    Returns:
        dict: Asset details, or empty dict if failed
    """
    try:
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return {}

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/Asset/{asset_id}"

        response = requests.get(endpoint, auth=auth, timeout=10, verify=True)

        if response.status_code == 200:
            asset = response.json()
            logger.info(f"Retrieved details for asset {asset_id}")
            return asset
        else:
            logger.error(f"Failed to get asset details. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {}

    except Exception as e:
        logger.error(f"Error getting asset details from Gauge API: {str(e)}")
        return {}

def get_asset_location_history(asset_id, start_date, end_date):
    """
    Get location history for a specific asset

    Args:
        asset_id (str): Asset ID
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD

    Returns:
        list: Location history, or empty list if failed
    """
    try:
        if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
            logger.error("API credentials not configured")
            return []

        auth = (GAUGE_API_USERNAME, GAUGE_API_PASSWORD)
        endpoint = f"{GAUGE_API_URL}/AssetHistory/{asset_id}"

        params = {
            'startDate': start_date,
            'endDate': end_date
        }

        response = requests.get(endpoint, auth=auth, params=params, timeout=30, verify=True)

        if response.status_code == 200:
            history = response.json()
            logger.info(f"Retrieved location history for asset {asset_id}")
            return history
        else:
            logger.error(f"Failed to get asset location history. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error getting asset location history from Gauge API: {str(e)}")
        return []