#!/usr/bin/env python3
"""
Equipment Lifecycle Module

This module manages the complete lifecycle of equipment assets,
tracking acquisition, disposal, and current status.

Key functionality:
- Record equipment acquisition with driver and division assignment
- Record equipment disposal with reason tracking
- Query active assets for a specific date
- Check status of specific asset on a given date
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LIFECYCLE_DATA_FILE = 'data/asset_registry.json'
LIFECYCLE_BACKUP_DIR = 'backups/lifecycle'

# Create required directories
os.makedirs(os.path.dirname(LIFECYCLE_DATA_FILE), exist_ok=True)
os.makedirs(LIFECYCLE_BACKUP_DIR, exist_ok=True)

# Asset status constants
STATUS_ACTIVE = "active"
STATUS_DISPOSED = "disposed"
STATUS_UNKNOWN = "unknown"

# Disposal reasons
DISPOSAL_REASONS = [
    "sold", 
    "scrapped", 
    "transferred", 
    "stolen", 
    "damaged", 
    "maintenance",
    "end_of_lease",
    "other"
]


class AssetRegistry:
    """
    Manages the asset registry that tracks equipment lifecycle.
    """
    
    def __init__(self, data_file=LIFECYCLE_DATA_FILE):
        """Initialize the asset registry with the data file."""
        self.data_file = data_file
        self.assets = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load asset registry data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                return data
            except Exception as e:
                logger.error(f"Error loading asset registry data: {e}")
                # If file exists but is corrupted, create a backup
                self._create_backup('corrupted')
                return self._initialize_data()
        else:
            return self._initialize_data()
    
    def _initialize_data(self) -> Dict:
        """Initialize a new empty asset registry."""
        return {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "last_modified": datetime.now().isoformat()
            },
            "assets": {}
        }
    
    def _save_data(self) -> bool:
        """Save asset registry data to file."""
        try:
            # Update last modified timestamp
            self.assets["metadata"]["last_modified"] = datetime.now().isoformat()
            
            # Create a backup before saving
            self._create_backup('autosave')
            
            # Save the data
            with open(self.data_file, 'w') as f:
                json.dump(self.assets, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving asset registry data: {e}")
            return False
    
    def _create_backup(self, reason: str) -> None:
        """Create a backup of the current data file."""
        if os.path.exists(self.data_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                LIFECYCLE_BACKUP_DIR, 
                f"asset_registry_{timestamp}_{reason}.json"
            )
            try:
                import shutil
                shutil.copy2(self.data_file, backup_file)
                logger.info(f"Created backup of asset registry: {backup_file}")
            except Exception as e:
                logger.error(f"Error creating backup: {e}")
    
    def format_date(self, date_value: Union[str, datetime, date]) -> str:
        """Format a date value to ISO format string (YYYY-MM-DD)."""
        if isinstance(date_value, str):
            # Try parsing string to date
            try:
                date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
                return date_obj.isoformat()
            except ValueError:
                # If parsing fails, return the original string
                return date_value
        elif isinstance(date_value, datetime):
            return date_value.date().isoformat()
        elif isinstance(date_value, date):
            return date_value.isoformat()
        else:
            raise ValueError(f"Unsupported date format: {date_value}")
    
    def add_acquisition(self, asset_id: str, driver_id: str, division: str, 
                      date_in: Union[str, datetime, date]) -> bool:
        """
        Record an asset acquisition.
        
        Args:
            asset_id: Unique identifier for the asset
            driver_id: ID of the driver assigned to the asset
            division: Division or department where the asset is assigned
            date_in: Acquisition date
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize asset ID
            asset_id = str(asset_id).strip().upper()
            
            # Format date
            formatted_date = self.format_date(date_in)
            
            # Create asset entry if it doesn't exist
            if asset_id not in self.assets.get("assets", {}):
                self.assets.setdefault("assets", {})[asset_id] = {
                    "acquisitions": [],
                    "disposals": []
                }
            
            # Add acquisition record
            acquisition = {
                "date": formatted_date,
                "driver_id": driver_id,
                "division": division,
                "recorded_at": datetime.now().isoformat()
            }
            
            self.assets["assets"][asset_id]["acquisitions"].append(acquisition)
            
            # Save changes
            return self._save_data()
            
        except Exception as e:
            logger.error(f"Error recording acquisition for asset {asset_id}: {e}")
            return False
    
    def add_disposal(self, asset_id: str, date_out: Union[str, datetime, date], 
                   reason: str = "other", notes: str = None) -> bool:
        """
        Record an asset disposal.
        
        Args:
            asset_id: Unique identifier for the asset
            date_out: Disposal date
            reason: Reason for disposal (must be one of DISPOSAL_REASONS)
            notes: Additional notes about the disposal
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize asset ID
            asset_id = str(asset_id).strip().upper()
            
            # Format date
            formatted_date = self.format_date(date_out)
            
            # Validate reason
            if reason not in DISPOSAL_REASONS:
                logger.warning(f"Invalid disposal reason: {reason}. Using 'other' instead.")
                reason = "other"
            
            # Check if asset exists
            if asset_id not in self.assets.get("assets", {}):
                logger.warning(f"Asset {asset_id} not found in registry.")
                return False
            
            # Add disposal record
            disposal = {
                "date": formatted_date,
                "reason": reason,
                "notes": notes,
                "recorded_at": datetime.now().isoformat()
            }
            
            self.assets["assets"][asset_id]["disposals"].append(disposal)
            
            # Save changes
            return self._save_data()
            
        except Exception as e:
            logger.error(f"Error recording disposal for asset {asset_id}: {e}")
            return False
    
    def get_asset_status(self, asset_id: str, 
                       check_date: Union[str, datetime, date] = None) -> str:
        """
        Get the status of an asset on a specific date.
        
        Args:
            asset_id: Unique identifier for the asset
            check_date: Date to check status for (default: current date)
            
        Returns:
            str: Asset status (active, disposed, or unknown)
        """
        try:
            # Normalize asset ID
            asset_id = str(asset_id).strip().upper()
            
            # Default to current date if not provided
            if check_date is None:
                check_date = datetime.now().date()
            
            # Format date
            formatted_date = self.format_date(check_date)
            check_date_obj = datetime.strptime(formatted_date, "%Y-%m-%d").date()
            
            # Check if asset exists
            if asset_id not in self.assets.get("assets", {}):
                return STATUS_UNKNOWN
            
            asset_data = self.assets["assets"][asset_id]
            
            # Check disposals
            for disposal in sorted(asset_data.get("disposals", []), 
                                  key=lambda x: x["date"], reverse=True):
                disposal_date = datetime.strptime(disposal["date"], "%Y-%m-%d").date()
                if disposal_date <= check_date_obj:
                    return STATUS_DISPOSED
            
            # Check acquisitions
            for acquisition in sorted(asset_data.get("acquisitions", []), 
                                     key=lambda x: x["date"], reverse=True):
                acquisition_date = datetime.strptime(acquisition["date"], "%Y-%m-%d").date()
                if acquisition_date <= check_date_obj:
                    return STATUS_ACTIVE
            
            # If we have no acquisition records before the check date
            return STATUS_UNKNOWN
            
        except Exception as e:
            logger.error(f"Error checking status for asset {asset_id}: {e}")
            return STATUS_UNKNOWN
    
    def get_active_assets(self, check_date: Union[str, datetime, date] = None) -> List[str]:
        """
        Get a list of active assets on a specific date.
        
        Args:
            check_date: Date to check status for (default: current date)
            
        Returns:
            List[str]: List of active asset IDs
        """
        try:
            active_assets = []
            
            # Default to current date if not provided
            if check_date is None:
                check_date = datetime.now().date()
            
            # Format date
            formatted_date = self.format_date(check_date)
            
            # Check status of each asset
            for asset_id in self.assets.get("assets", {}):
                status = self.get_asset_status(asset_id, formatted_date)
                if status == STATUS_ACTIVE:
                    active_assets.append(asset_id)
            
            return active_assets
            
        except Exception as e:
            logger.error(f"Error getting active assets: {e}")
            return []
    
    def get_asset_details(self, asset_id: str) -> Dict:
        """
        Get detailed information about an asset.
        
        Args:
            asset_id: Unique identifier for the asset
            
        Returns:
            Dict: Asset details or empty dict if not found
        """
        # Normalize asset ID
        asset_id = str(asset_id).strip().upper()
        
        # Return asset data if it exists, otherwise empty dict
        return self.assets.get("assets", {}).get(asset_id, {})
    
    def get_current_driver(self, asset_id: str, 
                         check_date: Union[str, datetime, date] = None) -> Optional[str]:
        """
        Get the driver assigned to an asset on a specific date.
        
        Args:
            asset_id: Unique identifier for the asset
            check_date: Date to check assignment for (default: current date)
            
        Returns:
            Optional[str]: Driver ID or None if not assigned/found
        """
        try:
            # Normalize asset ID
            asset_id = str(asset_id).strip().upper()
            
            # Default to current date if not provided
            if check_date is None:
                check_date = datetime.now().date()
            
            # Format date
            formatted_date = self.format_date(check_date)
            check_date_obj = datetime.strptime(formatted_date, "%Y-%m-%d").date()
            
            # Check if asset exists and is active
            status = self.get_asset_status(asset_id, check_date)
            if status != STATUS_ACTIVE:
                return None
            
            # Get asset data
            asset_data = self.assets.get("assets", {}).get(asset_id, {})
            
            # Find most recent acquisition before check date
            for acquisition in sorted(asset_data.get("acquisitions", []), 
                                     key=lambda x: x["date"], reverse=True):
                acquisition_date = datetime.strptime(acquisition["date"], "%Y-%m-%d").date()
                if acquisition_date <= check_date_obj:
                    return acquisition.get("driver_id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current driver for asset {asset_id}: {e}")
            return None


# Global asset registry instance
_registry = None

def get_registry() -> AssetRegistry:
    """Get or create the global asset registry instance."""
    global _registry
    if _registry is None:
        _registry = AssetRegistry()
    return _registry


# Public API functions

def record_acquisition(asset_id: str, driver_id: str, division: str, 
                      date_in: Union[str, datetime, date]) -> bool:
    """Record an asset acquisition."""
    return get_registry().add_acquisition(asset_id, driver_id, division, date_in)

def record_disposal(asset_id: str, date_out: Union[str, datetime, date], 
                  reason: str = "other", notes: str = None) -> bool:
    """Record an asset disposal."""
    return get_registry().add_disposal(asset_id, date_out, reason, notes)

def get_asset_status(asset_id: str, date: Union[str, datetime, date] = None) -> str:
    """Get the status of an asset on a specific date."""
    return get_registry().get_asset_status(asset_id, date)

def get_active_assets(date: Union[str, datetime, date] = None) -> List[str]:
    """Get a list of active assets on a specific date."""
    return get_registry().get_active_assets(date)

def get_asset_details(asset_id: str) -> Dict:
    """Get detailed information about an asset."""
    return get_registry().get_asset_details(asset_id)

def get_current_driver(asset_id: str, date: Union[str, datetime, date] = None) -> Optional[str]:
    """Get the driver assigned to an asset on a specific date."""
    return get_registry().get_current_driver(asset_id, date)


# Utility functions
def validate_asset_driver_pairing(asset_id: str, driver_id: str, 
                                date: Union[str, datetime, date] = None) -> bool:
    """
    Validate if a driver is correctly assigned to an asset on a specific date.
    
    Returns:
        bool: True if the pairing is valid, False otherwise
    """
    registry = get_registry()
    
    # Check if asset is active
    status = registry.get_asset_status(asset_id, date)
    if status != STATUS_ACTIVE:
        return False
    
    # Check if driver is assigned to asset
    current_driver = registry.get_current_driver(asset_id, date)
    if current_driver != driver_id:
        return False
    
    return True


if __name__ == "__main__":
    # Test the module
    print("Testing Equipment Lifecycle Module")
    
    # Sample data
    asset_id = "ET-123"
    driver_id = "D12345"
    division = "Houston"
    date_in = "2025-01-01"
    
    # Record acquisition
    success = record_acquisition(asset_id, driver_id, division, date_in)
    print(f"Recorded acquisition: {success}")
    
    # Check status
    status = get_asset_status(asset_id)
    print(f"Asset status: {status}")
    
    # Record disposal
    date_out = "2025-04-30"
    success = record_disposal(asset_id, date_out, "sold", "Sold to XYZ Company")
    print(f"Recorded disposal: {success}")
    
    # Check status again
    status = get_asset_status(asset_id)
    print(f"Asset status after disposal: {status}")
    
    # Check status on a specific date
    date_check = "2025-02-15"
    status = get_asset_status(asset_id, date_check)
    print(f"Asset status on {date_check}: {status}")
    
    # Get active assets
    active_assets = get_active_assets()
    print(f"Active assets: {active_assets}")