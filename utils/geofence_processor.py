"""
Geofence Processor Module

This module handles processing and management of geofence data, including:
- Static geofences from provided location files
- Dynamic geofences generated from asset clusters
- Combined geofence logic for site identification
"""

import os
import pandas as pd
import json
import logging
from datetime import datetime
import numpy as np
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models import Geofence

# Initialize logger
logger = logging.getLogger(__name__)

def import_static_geofences(filepath=None):
    """
    Import static geofences from an Excel file with site location data.
    
    Args:
        filepath (str): Path to the Excel file with geofence data
        
    Returns:
        int: Number of geofences imported
    """
    if not filepath:
        # Check for file in extracted_data directory
        filepath = 'extracted_data/expansion_assets_and_sites/Ragle_Site_Locations.xlsx'
        
        if not os.path.exists(filepath):
            # Try other potential locations
            potential_paths = [
                'attached_assets/Ragle_Site_Locations.xlsx',
                'data/Ragle_Site_Locations.xlsx'
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    filepath = path
                    break
            else:
                logger.error("Static geofence file not found")
                return 0
    
    try:
        # Read Excel file
        df = pd.read_excel(filepath)
        
        # Ensure required columns exist
        required_columns = ['Site Name', 'Latitude', 'Longitude', 'Radius']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns in geofence file: {missing_columns}")
            return 0
        
        # Process geofences
        count = 0
        for _, row in df.iterrows():
            try:
                # Check if geofence with same name already exists
                existing = Geofence.query.filter_by(name=row['Site Name']).first()
                
                if existing:
                    # Update existing geofence
                    existing.latitude = row['Latitude']
                    existing.longitude = row['Longitude']
                    existing.radius = row['Radius']
                    existing.type = 'static'
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new geofence
                    geofence = Geofence(
                        name=row['Site Name'],
                        latitude=row['Latitude'],
                        longitude=row['Longitude'],
                        radius=row['Radius'],
                        type='static'
                    )
                    db.session.add(geofence)
                
                count += 1
            
            except Exception as e:
                logger.error(f"Error processing geofence '{row.get('Site Name', 'Unknown')}': {e}")
                continue
        
        # Commit changes
        db.session.commit()
        logger.info(f"Successfully imported {count} static geofences")
        return count
    
    except Exception as e:
        logger.error(f"Error importing static geofences: {e}")
        db.session.rollback()
        return 0

def update_dynamic_geofences(assets):
    """
    Update dynamic geofences based on clustered asset locations.
    
    This is called after DBSCAN clustering is used to identify natural clusters
    of assets that likely represent job sites.
    
    Args:
        assets (list): List of processed assets with assigned clusters
        
    Returns:
        int: Number of dynamic geofences created or updated
    """
    try:
        # Group assets by cluster
        clusters = {}
        for asset in assets:
            cluster_id = asset.get('cluster_id')
            if cluster_id is not None and cluster_id >= 0:  # Ignore noise points (-1)
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(asset)
        
        # Process each cluster
        count = 0
        for cluster_id, cluster_assets in clusters.items():
            if len(cluster_assets) < 3:
                # Skip small clusters (require at least 3 assets to form meaningful site)
                continue
            
            # Calculate center point (average of coordinates)
            latitudes = [a.get('latitude') for a in cluster_assets if a.get('latitude')]
            longitudes = [a.get('longitude') for a in cluster_assets if a.get('longitude')]
            
            if not latitudes or not longitudes:
                continue
                
            center_lat = sum(latitudes) / len(latitudes)
            center_lon = sum(longitudes) / len(longitudes)
            
            # Calculate radius (maximum distance from center to any point in cluster)
            from math import radians, cos, sin, asin, sqrt
            
            def haversine(lat1, lon1, lat2, lon2):
                """Calculate distance between two points in km"""
                # Convert decimal degrees to radians
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                
                # Haversine formula
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                # Radius of earth in kilometers
                r = 6371
                return c * r
            
            distances = [haversine(center_lat, center_lon, a.get('latitude'), a.get('longitude')) 
                         for a in cluster_assets]
            radius = max(distances) * 1000  # Convert to meters
            
            # Ensure minimum radius of 100 meters
            radius = max(radius, 100)
            
            # Determine site name from most common location or site
            locations = {}
            sites = {}
            for asset in cluster_assets:
                location = asset.get('location')
                site = asset.get('site')
                
                if location:
                    locations[location] = locations.get(location, 0) + 1
                if site:
                    sites[site] = sites.get(site, 0) + 1
            
            # Use most common site name, fallback to location, or generate cluster name
            if sites:
                name = max(sites.items(), key=lambda x: x[1])[0]
            elif locations:
                name = max(locations.items(), key=lambda x: x[1])[0]
            else:
                name = f"Cluster {cluster_id}"
            
            # Check if dynamic geofence with similar center already exists
            similar_fence = None
            dynamic_fences = Geofence.query.filter_by(type='dynamic').all()
            
            for fence in dynamic_fences:
                distance = haversine(center_lat, center_lon, fence.latitude, fence.longitude)
                # If within 100 meters, consider it the same site
                if distance < 0.1:  
                    similar_fence = fence
                    break
            
            if similar_fence:
                # Update existing fence
                similar_fence.latitude = center_lat
                similar_fence.longitude = center_lon
                similar_fence.radius = radius
                similar_fence.updated_at = datetime.utcnow()
                # Update name if the new one is more specific (not just "Cluster X")
                if not similar_fence.name.startswith("Cluster ") or name.startswith("Cluster "):
                    similar_fence.name = name
            else:
                # Create new dynamic geofence
                geofence = Geofence(
                    name=name,
                    latitude=center_lat,
                    longitude=center_lon,
                    radius=radius,
                    type='dynamic'
                )
                db.session.add(geofence)
            
            count += 1
        
        # Commit changes
        db.session.commit()
        logger.info(f"Successfully updated {count} dynamic geofences")
        return count
        
    except Exception as e:
        logger.error(f"Error updating dynamic geofences: {e}")
        db.session.rollback()
        return 0

def get_all_geofences():
    """
    Get all geofences from the database.
    
    Returns:
        list: List of geofence dictionaries
    """
    try:
        geofences = Geofence.query.all()
        result = []
        
        for fence in geofences:
            result.append({
                'id': fence.id,
                'name': fence.name,
                'latitude': fence.latitude,
                'longitude': fence.longitude,
                'radius': fence.radius,
                'type': fence.type,
                'created_at': fence.created_at.isoformat() if fence.created_at else None,
                'updated_at': fence.updated_at.isoformat() if fence.updated_at else None
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving geofences: {e}")
        return []

def export_geofences_as_geojson():
    """
    Export all geofences as GeoJSON format.
    
    Returns:
        dict: GeoJSON object with all geofences
    """
    try:
        geofences = Geofence.query.all()
        features = []
        
        for fence in geofences:
            # Create circular polygon approximation (20 points)
            import math
            
            points = []
            for i in range(20):
                angle = math.radians(i * 18)  # 360 degrees / 20 points
                # Convert radius from meters to degrees (approximate)
                # 111,320 meters = 1 degree of latitude
                # cos(lat) * 111,320 meters = 1 degree of longitude
                lat_offset = (fence.radius / 111320) * math.sin(angle)
                lon_offset = (fence.radius / (111320 * math.cos(math.radians(fence.latitude)))) * math.cos(angle)
                
                points.append([fence.longitude + lon_offset, fence.latitude + lat_offset])
            
            # Close the polygon
            points.append(points[0])
            
            # Create GeoJSON feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [points]
                },
                "properties": {
                    "id": fence.id,
                    "name": fence.name,
                    "type": fence.type,
                    "radius": fence.radius,
                    "center": [fence.longitude, fence.latitude]
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
        logger.error(f"Error exporting geofences as GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}