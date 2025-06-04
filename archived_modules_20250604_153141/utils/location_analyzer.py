"""
Location Analyzer Module

This module provides utilities for analyzing asset location data, creating job
site geofences, and determining if assets are within job sites.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull, Delaunay
import json

# Configure logging
logger = logging.getLogger(__name__)

class LocationAnalyzer:
    """
    Analyze asset location data to determine job sites and asset assignments.
    """
    
    def __init__(self, 
                eps: float = 0.005, 
                min_samples: int = 3, 
                min_cluster_size: int = 3,
                max_travel_speed: float = 65.0):
        """
        Initialize the location analyzer.
        
        Args:
            eps (float): The maximum distance between two samples for them to be 
                         considered as in the same neighborhood (in degrees)
            min_samples (int): The minimum number of samples in a neighborhood for a 
                             point to be considered a core point
            min_cluster_size (int): Minimum number of points to form a valid cluster
            max_travel_speed (float): Maximum expected travel speed in mph
        """
        self.eps = eps
        self.min_samples = min_samples
        self.min_cluster_size = min_cluster_size
        self.max_travel_speed = max_travel_speed
        self.site_map = {}  # Map site names to geofence polygons
        self.clusters = {}  # Map cluster IDs to sets of points
        
    def identify_job_sites(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify job sites from asset location data.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries with lat/long
            
        Returns:
            Dict[str, Any]: Job site information including geofences
        """
        try:
            # Extract valid coordinates and site info
            coordinates = []
            site_names = []
            location_names = []
            asset_ids = []
            
            for asset in assets:
                lat = asset.get('latitude')
                lon = asset.get('longitude')
                site = asset.get('site')
                location = asset.get('location')
                asset_id = asset.get('id') or asset.get('asset_identifier')
                
                if lat and lon:
                    coordinates.append([lon, lat])
                    site_names.append(site)
                    location_names.append(location)
                    asset_ids.append(asset_id)
            
            # If no valid coordinates, return empty result
            if not coordinates:
                return {
                    'success': False,
                    'message': 'No valid coordinates found',
                    'job_sites': []
                }
            
            # Convert to numpy array for clustering
            X = np.array(coordinates)
            
            # Perform clustering with DBSCAN
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X)
            labels = db.labels_
            
            # Number of clusters (excluding noise points with label -1)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            # Create job site information
            job_sites = []
            
            for i in range(n_clusters):
                # Get points in this cluster
                cluster_points = X[labels == i]
                
                # Skip small clusters
                if len(cluster_points) < self.min_cluster_size:
                    continue
                
                # Get site and location names for this cluster
                cluster_sites = [site_names[j] for j, label in enumerate(labels) if label == i]
                cluster_locations = [location_names[j] for j, label in enumerate(labels) if label == i]
                cluster_assets = [asset_ids[j] for j, label in enumerate(labels) if label == i]
                
                # Count occurrences of each site and location
                site_counts = {}
                location_counts = {}
                
                for site in cluster_sites:
                    if site:
                        if site not in site_counts:
                            site_counts[site] = 0
                        site_counts[site] += 1
                
                for location in cluster_locations:
                    if location:
                        if location not in location_counts:
                            location_counts[location] = 0
                        location_counts[location] += 1
                
                # Get most common site and location
                most_common_site = max(site_counts.items(), key=lambda x: x[1])[0] if site_counts else None
                most_common_location = max(location_counts.items(), key=lambda x: x[1])[0] if location_counts else None
                
                # Try to create convex hull for the cluster
                try:
                    if len(cluster_points) >= 3:
                        hull = ConvexHull(cluster_points)
                        hull_points = cluster_points[hull.vertices]
                        
                        # Convert hull to polygon
                        polygon = [[point[0], point[1]] for point in hull_points]
                        
                        # Add first point at the end to close the polygon
                        polygon.append(polygon[0])
                    else:
                        # Not enough points for a convex hull, create a simple circle
                        center = np.mean(cluster_points, axis=0)
                        radius = self.eps * 1.5  # slightly larger than clustering radius
                        polygon = []
                        
                        # Create circle approximation with 8 points
                        for angle in range(0, 360, 45):
                            rad = np.radians(angle)
                            x = center[0] + radius * np.cos(rad)
                            y = center[1] + radius * np.sin(rad)
                            polygon.append([x, y])
                        
                        # Close the polygon
                        polygon.append(polygon[0])
                except Exception as e:
                    logger.error(f"Error creating convex hull: {e}")
                    polygon = []
                
                # Create job site info
                site_name = most_common_site or most_common_location or f"Cluster-{i}"
                
                job_site = {
                    'id': f"site-{i}",
                    'name': site_name,
                    'center': [
                        float(np.mean(cluster_points[:, 0])),
                        float(np.mean(cluster_points[:, 1]))
                    ],
                    'polygon': polygon,
                    'point_count': len(cluster_points),
                    'asset_count': len(set(cluster_assets)),
                    'assets': list(set(cluster_assets)),
                    'most_common_site': most_common_site,
                    'most_common_location': most_common_location
                }
                
                job_sites.append(job_site)
                
                # Store in site map for later use
                self.site_map[site_name] = polygon
                self.clusters[i] = set(cluster_assets)
            
            return {
                'success': True,
                'message': f'Found {len(job_sites)} job sites',
                'job_sites': job_sites
            }
            
        except Exception as e:
            logger.exception(f"Error identifying job sites: {e}")
            return {
                'success': False,
                'message': f'Error identifying job sites: {str(e)}',
                'job_sites': []
            }
    
    def generate_geofences(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate GeoJSON geofences from asset location data.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries with lat/long
            
        Returns:
            Dict[str, Any]: GeoJSON object with geofences
        """
        try:
            # Identify job sites
            result = self.identify_job_sites(assets)
            
            if not result['success']:
                return {
                    "type": "FeatureCollection",
                    "features": []
                }
            
            # Create GeoJSON features for each job site
            features = []
            
            for site in result['job_sites']:
                polygon = site['polygon']
                
                if not polygon:
                    continue
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon]
                    },
                    "properties": {
                        "id": site['id'],
                        "name": site['name'],
                        "point_count": site['point_count'],
                        "asset_count": site['asset_count'],
                        "location": site['most_common_location'] or "Unknown",
                        "site": site['most_common_site'] or "Unknown"
                    }
                }
                
                features.append(feature)
            
            # Create GeoJSON object
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            return geojson
            
        except Exception as e:
            logger.exception(f"Error generating geofences: {e}")
            return {
                "type": "FeatureCollection",
                "features": []
            }
    
    def point_in_polygon(self, point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """
        Check if a point is inside a polygon.
        
        Args:
            point (Tuple[float, float]): Coordinate (lon, lat)
            polygon (List[List[float]]): List of polygon vertices as [lon, lat]
            
        Returns:
            bool: True if point is inside polygon, False otherwise
        """
        try:
            # Extract x, y coordinates from point and polygon
            x, y = point
            
            # Convert polygon to numpy array for Delaunay
            points = np.array(polygon)
            
            # Create Delaunay triangulation
            tri = Delaunay(points)
            
            # Check if point is inside any triangle
            return tri.find_simplex([x, y]) >= 0
            
        except Exception as e:
            logger.error(f"Error checking point in polygon: {e}")
            return False
    
    def is_asset_on_site(self, asset: Dict[str, Any], site_name: str = None) -> bool:
        """
        Check if an asset is currently on a job site.
        
        Args:
            asset (Dict[str, Any]): Asset dictionary with lat/long
            site_name (str, optional): Name of site to check, or None to check all sites
            
        Returns:
            bool: True if asset is on site, False otherwise
        """
        try:
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            
            if not lat or not lon:
                return False
            
            point = (lon, lat)
            
            # If site name is provided, check only that site
            if site_name and site_name in self.site_map:
                return self.point_in_polygon(point, self.site_map[site_name])
            
            # Otherwise check all sites
            for site, polygon in self.site_map.items():
                if self.point_in_polygon(point, polygon):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if asset is on site: {e}")
            return False
    
    def get_assets_on_site(self, assets: List[Dict[str, Any]], site_name: str = None) -> List[Dict[str, Any]]:
        """
        Get all assets currently on a specific job site.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries
            site_name (str, optional): Name of site to check, or None to get assets on any site
            
        Returns:
            List[Dict[str, Any]]: List of assets on the specified site
        """
        try:
            result = []
            
            for asset in assets:
                if self.is_asset_on_site(asset, site_name):
                    result.append(asset)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting assets on site: {e}")
            return []
    
    def get_assets_off_site(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get all assets that are not on any job site.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries
            
        Returns:
            List[Dict[str, Any]]: List of assets not on any job site
        """
        try:
            result = []
            
            for asset in assets:
                if not self.is_asset_on_site(asset):
                    result.append(asset)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting assets off site: {e}")
            return []
    
    def calculate_distances(self, assets: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate distances between all assets.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries
            
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping asset ID to 
                                        dictionary of other asset IDs and distances
        """
        try:
            result = {}
            
            for i, asset1 in enumerate(assets):
                asset1_id = asset1.get('id') or asset1.get('asset_identifier')
                lat1 = asset1.get('latitude')
                lon1 = asset1.get('longitude')
                
                if not asset1_id or not lat1 or not lon1:
                    continue
                
                result[asset1_id] = {}
                
                for j, asset2 in enumerate(assets):
                    if i == j:
                        continue
                        
                    asset2_id = asset2.get('id') or asset2.get('asset_identifier')
                    lat2 = asset2.get('latitude')
                    lon2 = asset2.get('longitude')
                    
                    if not asset2_id or not lat2 or not lon2:
                        continue
                    
                    # Calculate Haversine distance
                    distance = self._haversine(lat1, lon1, lat2, lon2)
                    result[asset1_id][asset2_id] = distance
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating distances: {e}")
            return {}
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees).
        
        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
            
        Returns:
            float: Distance in miles
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 3956  # Radius of earth in miles
        return c * r
    
    def check_geofence_violations(self, asset: Dict[str, Any], allowed_sites: List[str] = None) -> Dict[str, Any]:
        """
        Check if an asset is outside of allowed geofences.
        
        Args:
            asset (Dict[str, Any]): Asset dictionary
            allowed_sites (List[str], optional): List of sites where the asset is allowed
            
        Returns:
            Dict[str, Any]: Violation information
        """
        try:
            asset_id = asset.get('id') or asset.get('asset_identifier')
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            
            if not asset_id or not lat or not lon:
                return {
                    'has_violation': False,
                    'message': 'Invalid asset data'
                }
            
            # If no allowed sites specified, check if asset is on any site
            if not allowed_sites:
                if not self.is_asset_on_site(asset):
                    return {
                        'has_violation': True,
                        'type': 'not_on_site',
                        'asset_id': asset_id,
                        'message': f'Asset {asset_id} is not on any known job site'
                    }
                return {
                    'has_violation': False,
                    'asset_id': asset_id,
                    'message': f'Asset {asset_id} is on a job site'
                }
            
            # Check if asset is on any of the allowed sites
            for site in allowed_sites:
                if site in self.site_map and self.point_in_polygon((lon, lat), self.site_map[site]):
                    return {
                        'has_violation': False,
                        'asset_id': asset_id,
                        'current_site': site,
                        'message': f'Asset {asset_id} is on allowed site {site}'
                    }
            
            # If we get here, asset is not on any allowed site
            current_site = None
            for site, polygon in self.site_map.items():
                if self.point_in_polygon((lon, lat), polygon):
                    current_site = site
                    break
            
            return {
                'has_violation': True,
                'type': 'wrong_site',
                'asset_id': asset_id,
                'current_site': current_site,
                'allowed_sites': allowed_sites,
                'message': f'Asset {asset_id} is not on any allowed site'
            }
            
        except Exception as e:
            logger.error(f"Error checking geofence violations: {e}")
            return {
                'has_violation': False,
                'message': f'Error checking violations: {str(e)}'
            }
    
    def calculate_efficiency_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for assets based on location data.
        
        Args:
            assets (List[Dict[str, Any]]): List of asset dictionaries
            
        Returns:
            Dict[str, Any]: Efficiency metrics
        """
        try:
            # Count assets by status
            total = len(assets)
            active_count = sum(1 for a in assets if a.get('active'))
            ignition_on = sum(1 for a in assets if a.get('ignition'))
            on_site_count = sum(1 for a in assets if self.is_asset_on_site(a))
            
            # Calculate percentages
            active_pct = (active_count / total) * 100 if total > 0 else 0
            ignition_pct = (ignition_on / total) * 100 if total > 0 else 0
            on_site_pct = (on_site_count / total) * 100 if total > 0 else 0
            
            # Count assets by site
            site_counts = {}
            for asset in assets:
                for site, polygon in self.site_map.items():
                    lat = asset.get('latitude')
                    lon = asset.get('longitude')
                    
                    if lat and lon and self.point_in_polygon((lon, lat), polygon):
                        if site not in site_counts:
                            site_counts[site] = {
                                'total': 0,
                                'active': 0,
                                'ignition_on': 0
                            }
                        
                        site_counts[site]['total'] += 1
                        if asset.get('active'):
                            site_counts[site]['active'] += 1
                        if asset.get('ignition'):
                            site_counts[site]['ignition_on'] += 1
            
            return {
                'total_assets': total,
                'active': active_count,
                'active_percentage': active_pct,
                'ignition_on': ignition_on,
                'ignition_percentage': ignition_pct,
                'on_site': on_site_count,
                'on_site_percentage': on_site_pct,
                'off_site': total - on_site_count,
                'off_site_percentage': 100 - on_site_pct,
                'by_site': site_counts
            }
            
        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")
            return {
                'error': str(e)
            }