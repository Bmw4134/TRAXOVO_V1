"""
TRAXORA GENIUS CORE | Samsara Sync Agent

This agent module provides real-time data synchronization with the Samsara API,
fetching vehicle, location, and driver data to feed into the GENIUS CORE pipeline.
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# Import the Samsara bridge
from samsara_bridge import get_bridge

logger = logging.getLogger(__name__)

class SamsaraSyncAgent:
    """Agent for synchronizing Samsara data with GENIUS CORE pipeline"""
    
    def __init__(self, company_name: str = None, config: Dict = None):
        """
        Initialize the Samsara sync agent
        
        Args:
            company_name (str): Name of the company context
            config (dict): Configuration for the agent
        """
        self.company_name = company_name
        self.config = config or {}
        self.bridge = get_bridge(company_name)
        self.sync_frequency = self.config.get('sync_frequency_minutes', 15)
        self.last_sync = None
        
        # Initialize storage for data
        self.vehicles_data = []
        self.locations_data = []
        self.drivers_data = []
        
        # Load cached data if available
        self._load_cached_data()
    
    def _load_cached_data(self):
        """Load cached data from disk"""
        try:
            cache_dir = os.path.join('data', 'samsara_cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Load vehicles
            vehicles_path = os.path.join(cache_dir, 'vehicles.json')
            if os.path.exists(vehicles_path):
                with open(vehicles_path, 'r') as f:
                    self.vehicles_data = json.load(f)
            
            # Load locations
            locations_path = os.path.join(cache_dir, 'locations.json')
            if os.path.exists(locations_path):
                with open(locations_path, 'r') as f:
                    self.locations_data = json.load(f)
            
            # Load drivers
            drivers_path = os.path.join(cache_dir, 'drivers.json')
            if os.path.exists(drivers_path):
                with open(drivers_path, 'r') as f:
                    self.drivers_data = json.load(f)
            
            logger.info(f"Loaded cached Samsara data: {len(self.vehicles_data)} vehicles, "
                       f"{len(self.locations_data)} locations, {len(self.drivers_data)} drivers")
        except Exception as e:
            logger.error(f"Error loading cached Samsara data: {str(e)}")
    
    def _save_cached_data(self):
        """Save data to disk cache"""
        try:
            cache_dir = os.path.join('data', 'samsara_cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Save vehicles
            vehicles_path = os.path.join(cache_dir, 'vehicles.json')
            with open(vehicles_path, 'w') as f:
                json.dump(self.vehicles_data, f)
            
            # Save locations
            locations_path = os.path.join(cache_dir, 'locations.json')
            with open(locations_path, 'w') as f:
                json.dump(self.locations_data, f)
            
            # Save drivers
            drivers_path = os.path.join(cache_dir, 'drivers.json')
            with open(drivers_path, 'w') as f:
                json.dump(self.drivers_data, f)
            
            logger.info("Saved Samsara data to cache")
        except Exception as e:
            logger.error(f"Error saving Samsara data to cache: {str(e)}")
    
    def needs_sync(self) -> bool:
        """
        Check if synchronization is needed
        
        Returns:
            bool: True if sync is needed, False otherwise
        """
        # If bridge is not enabled, no sync needed
        if not self.bridge.is_enabled():
            return False
        
        # If never synced, sync is needed
        if self.last_sync is None:
            return True
        
        # Check if it's time for a new sync
        time_since_last_sync = datetime.now() - self.last_sync
        return time_since_last_sync.total_seconds() > (self.sync_frequency * 60)
    
    def sync(self) -> bool:
        """
        Synchronize data from Samsara API
        
        Returns:
            bool: True if sync was successful, False otherwise
        """
        if not self.bridge.is_enabled():
            logger.warning("Samsara Bridge not enabled, cannot sync")
            return False
        
        try:
            # Sync vehicles
            vehicles = self.bridge.get_vehicles()
            if vehicles:
                self.vehicles_data = vehicles
                logger.info(f"Synced {len(vehicles)} vehicles from Samsara")
            
            # Sync locations (last 24 hours)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            locations = self.bridge.get_locations(start_time, end_time)
            if locations:
                self.locations_data = locations
                logger.info(f"Synced {len(locations)} location records from Samsara")
            
            # Sync drivers
            drivers = self.bridge.get_drivers()
            if drivers:
                self.drivers_data = drivers
                logger.info(f"Synced {len(drivers)} drivers from Samsara")
            
            # Update last sync time
            self.last_sync = datetime.now()
            
            # Save to cache
            self._save_cached_data()
            
            return True
        except Exception as e:
            logger.error(f"Error syncing data from Samsara: {str(e)}")
            return False
    
    def get_vehicles(self) -> List[Dict]:
        """
        Get vehicles data, syncing if needed
        
        Returns:
            list: List of vehicle data dictionaries
        """
        if self.needs_sync():
            self.sync()
        return self.vehicles_data
    
    def get_locations(self) -> List[Dict]:
        """
        Get locations data, syncing if needed
        
        Returns:
            list: List of location data dictionaries
        """
        if self.needs_sync():
            self.sync()
        return self.locations_data
    
    def get_drivers(self) -> List[Dict]:
        """
        Get drivers data, syncing if needed
        
        Returns:
            list: List of driver data dictionaries
        """
        if self.needs_sync():
            self.sync()
        return self.drivers_data
    
    def transform_data_for_geo_validator(self) -> List[Dict]:
        """
        Transform Samsara data for the geo_validator_agent
        
        Returns:
            list: Locations data in geo_validator format
        """
        if self.needs_sync():
            self.sync()
        
        if not self.locations_data:
            return []
        
        # Transform data into geo_validator compatible format
        transformed_data = []
        
        for location in self.locations_data:
            # Skip entries without valid coordinates
            if not location.get('latitude') or not location.get('longitude'):
                continue
            
            # Find vehicle info
            vehicle_id = location.get('vehicleId')
            vehicle_info = next((v for v in self.vehicles_data if v.get('id') == vehicle_id), {})
            
            transformed_location = {
                'timestamp': location.get('time'),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'vehicle_id': vehicle_id,
                'vehicle_name': vehicle_info.get('name', 'Unknown'),
                'speed': location.get('speed', 0),
                'heading': location.get('heading', 0),
                'source': 'samsara',
                'company': self.company_name
            }
            
            transformed_data.append(transformed_location)
        
        return transformed_data
    
    def transform_data_for_driver_classifier(self) -> List[Dict]:
        """
        Transform Samsara data for the driver_classifier_agent
        
        Returns:
            list: Driver data in driver_classifier format
        """
        if self.needs_sync():
            self.sync()
        
        if not self.drivers_data:
            return []
        
        # Transform data into driver_classifier compatible format
        transformed_data = []
        
        for driver in self.drivers_data:
            # Find vehicle assignment
            vehicle_id = driver.get('vehicleId')
            vehicle_info = next((v for v in self.vehicles_data if v.get('id') == vehicle_id), {})
            
            # Find latest location
            driver_locations = [loc for loc in self.locations_data 
                                if loc.get('vehicleId') == vehicle_id]
            latest_location = max(driver_locations, key=lambda x: x.get('time', 0)) if driver_locations else {}
            
            transformed_driver = {
                'driver_id': driver.get('id'),
                'name': f"{driver.get('firstName', '')} {driver.get('lastName', '')}".strip(),
                'vehicle_id': vehicle_id,
                'vehicle_name': vehicle_info.get('name', 'Unknown'),
                'last_location': {
                    'latitude': latest_location.get('latitude'),
                    'longitude': latest_location.get('longitude'),
                    'timestamp': latest_location.get('time')
                } if latest_location else {},
                'source': 'samsara',
                'company': self.company_name
            }
            
            transformed_data.append(transformed_driver)
        
        return transformed_data

def get_agent(company_name: str = None, config: Dict = None) -> SamsaraSyncAgent:
    """
    Factory function to get a Samsara sync agent instance
    
    Args:
        company_name (str): Name of the company context
        config (dict): Configuration for the agent
        
    Returns:
        SamsaraSyncAgent: Initialized agent instance
    """
    return SamsaraSyncAgent(company_name, config)

def handle(command: str, data: Any = None, config: Dict = None) -> Dict:
    """
    Handle a command for the Samsara sync agent
    
    Args:
        command (str): Command to execute
        data (any): Data for the command
        config (dict): Configuration for the command
        
    Returns:
        dict: Command result
    """
    logger.info(f"Handling Samsara sync agent command: {command}")
    
    company_name = config.get('company_name') if config else None
    agent = get_agent(company_name, config)
    
    if command == 'sync':
        success = agent.sync()
        return {
            'success': success,
            'last_sync': agent.last_sync.isoformat() if agent.last_sync else None
        }
    
    elif command == 'get_vehicles':
        vehicles = agent.get_vehicles()
        return {
            'success': True,
            'vehicles': vehicles,
            'count': len(vehicles)
        }
    
    elif command == 'get_locations':
        locations = agent.get_locations()
        return {
            'success': True,
            'locations': locations,
            'count': len(locations)
        }
    
    elif command == 'get_drivers':
        drivers = agent.get_drivers()
        return {
            'success': True,
            'drivers': drivers,
            'count': len(drivers)
        }
    
    elif command == 'transform_for_geo_validator':
        transformed_data = agent.transform_data_for_geo_validator()
        return {
            'success': True,
            'data': transformed_data,
            'count': len(transformed_data)
        }
    
    elif command == 'transform_for_driver_classifier':
        transformed_data = agent.transform_data_for_driver_classifier()
        return {
            'success': True,
            'data': transformed_data,
            'count': len(transformed_data)
        }
    
    else:
        logger.error(f"Unknown Samsara sync agent command: {command}")
        return {
            'success': False,
            'error': f"Unknown command: {command}"
        }