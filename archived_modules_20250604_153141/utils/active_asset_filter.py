"""
Active Asset Filter

This module filters assets to show only active, GPS-enabled equipment,
excluding sold, disposed, stolen, or inactive assets.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ActiveAssetFilter:
    """
    Filter assets to show only active, GPS-enabled equipment
    """
    
    def __init__(self):
        # Define keywords that indicate inactive assets
        self.inactive_keywords = [
            'sold', 'disposed', 'stolen', 'inactive', 'retired', 'scrapped',
            'out of service', 'decommissioned', 'transferred', 'salvage'
        ]
        
        # Define asset types that should be excluded
        self.excluded_types = [
            'trailer without gps', 'non-powered equipment', 'static equipment'
        ]
    
    def filter_active_assets(self, assets):
        """
        Filter assets to return only active, GPS-enabled equipment
        
        Args:
            assets: List of asset dictionaries from API or database
            
        Returns:
            List of filtered active assets
        """
        if not assets:
            return []
        
        active_assets = []
        now = datetime.now()
        cutoff_date = now - timedelta(days=30)  # Consider assets with activity in last 30 days
        
        for asset in assets:
            if self._is_asset_active(asset, cutoff_date):
                active_assets.append(asset)
        
        logger.info(f"Filtered {len(assets)} total assets to {len(active_assets)} active assets")
        return active_assets
    
    def _is_asset_active(self, asset, cutoff_date):
        """
        Determine if an asset is active based on multiple criteria
        
        Args:
            asset: Asset dictionary
            cutoff_date: Cutoff date for recent activity
            
        Returns:
            Boolean indicating if asset is active
        """
        # Check asset name/description for inactive keywords
        name = asset.get('name', '').lower()
        description = asset.get('description', '').lower()
        
        for keyword in self.inactive_keywords:
            if keyword in name or keyword in description:
                return False
        
        # Check asset type
        asset_type = asset.get('type', '').lower()
        for excluded_type in self.excluded_types:
            if excluded_type in asset_type:
                return False
        
        # Check if asset has GPS coordinates
        lat = asset.get('last_latitude') or asset.get('latitude')
        lng = asset.get('last_longitude') or asset.get('longitude')
        
        if not lat or not lng:
            return False
        
        # Check for recent location updates
        last_update = asset.get('last_location_update')
        if last_update:
            try:
                if isinstance(last_update, str):
                    last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                
                if last_update < cutoff_date:
                    return False
            except:
                # If we can't parse the date, assume it's old
                return False
        
        # Check asset status
        status = asset.get('status', '').lower()
        if status in ['inactive', 'sold', 'disposed', 'stolen', 'retired']:
            return False
        
        # If all checks pass, asset is considered active
        return True
    
    def get_asset_summary(self, all_assets, active_assets):
        """
        Get summary of asset filtering results
        
        Args:
            all_assets: Original list of all assets
            active_assets: Filtered list of active assets
            
        Returns:
            Dictionary with filtering summary
        """
        total_count = len(all_assets)
        active_count = len(active_assets)
        filtered_count = total_count - active_count
        
        return {
            'total_assets': total_count,
            'active_assets': active_count,
            'filtered_out': filtered_count,
            'active_percentage': round((active_count / total_count * 100), 1) if total_count > 0 else 0
        }