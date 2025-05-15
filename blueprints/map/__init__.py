"""
Map Blueprint

This module provides routes and functionality for the map view, including:
- Asset location visualization
- Geofence creation and management
- Real-time tracking of assets within job sites
- Location-based analytics
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

from app import db
from models import Asset, AssetHistory
from gauge_api import get_asset_data

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
map_bp = Blueprint('map', __name__, url_prefix='/map')

@map_bp.route('/')
@login_required
def index():
    """Render the main map view."""
    return render_template('map/index.html')

@map_bp.route('/assets.json')
@login_required
def asset_locations():
    """Return asset location data as GeoJSON."""
    
    # Get assets from database or API
    try:
        assets = Asset.query.filter(
            Asset.latitude.isnot(None),
            Asset.longitude.isnot(None),
            Asset.active == True
        ).all()
        
        # If no assets in database, try to get from API
        if not assets:
            asset_data = get_asset_data()
            assets = []
            for data in asset_data:
                if data.get('latitude') and data.get('longitude'):
                    assets.append(data)
    except Exception as e:
        logger.error(f"Error fetching asset locations: {e}")
        return jsonify({"error": str(e)}), 500
    
    # Transform to GeoJSON format
    features = []
    for asset in assets:
        # Handle both ORM and dictionary objects
        if isinstance(asset, dict):
            asset_id = asset.get('id')
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            label = asset.get('label') or asset.get('asset_identifier', 'Unknown')
            asset_class = asset.get('asset_class', 'Unknown')
            asset_category = asset.get('asset_category', 'Unknown')
            active = asset.get('active', False)
            ignition = asset.get('ignition', False)
            location = asset.get('location', 'Unknown')
            site = asset.get('site', 'Unknown')
            district = asset.get('district', 'Unknown')
            event_date_time = asset.get('event_date_time')
            if event_date_time and isinstance(event_date_time, str):
                event_date_time = datetime.fromisoformat(event_date_time.replace('Z', '+00:00'))
            speed = asset.get('speed', 0)
        else:
            asset_id = asset.id
            lat = asset.latitude
            lon = asset.longitude
            label = asset.label or asset.asset_identifier
            asset_class = asset.asset_class
            asset_category = asset.asset_category
            active = asset.active
            ignition = asset.ignition
            location = asset.location
            site = asset.site
            district = asset.district
            event_date_time = asset.event_date_time
            speed = asset.speed
        
        # Only include assets with valid coordinates
        if lat and lon:
            # Calculate time since last update
            time_since_update = None
            if event_date_time:
                time_since_update = (datetime.utcnow() - event_date_time).total_seconds() / 3600  # hours
            
            # Define asset status
            status = "unknown"
            label_lower = label.lower() if label else ""
            
            # Check for retired/scrapped/sold assets in the label
            if any(keyword in label_lower for keyword in ["retired", "sold", "scrap", "stolen", "total out"]):
                status = "retired"
            # Otherwise use active/ignition status
            elif active:
                if ignition:
                    status = "active"
                else:
                    status = "idle"
            else:
                status = "inactive"
            
            # Create GeoJSON feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": asset_id,
                    "label": label,
                    "asset_class": asset_class,
                    "asset_category": asset_category,
                    "status": status,
                    "speed": speed,
                    "location": location,
                    "site": site,
                    "district": district,
                    "time_since_update": time_since_update,
                    "popup_content": f"<strong>{label}</strong><br>Status: {status}<br>Site: {site}"
                }
            }
            features.append(feature)
    
    # Create GeoJSON object
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return jsonify(geojson)

@map_bp.route('/geofences.json')
@login_required
def geofences():
    """Generate and return geofences as GeoJSON based on asset clusters."""
    
    # Get clustering parameters from request
    eps = request.args.get('eps', 0.005, type=float)  # cluster radius in degrees
    min_samples = request.args.get('min_samples', 3, type=int)  # min points for a cluster
    
    # Get assets from database or API
    try:
        assets = Asset.query.filter(
            Asset.latitude.isnot(None),
            Asset.longitude.isnot(None)
        ).all()
        
        # If no assets in database, try to get from API
        if not assets:
            asset_data = get_asset_data()
            assets = []
            for data in asset_data:
                if data.get('latitude') and data.get('longitude'):
                    assets.append(data)
    except Exception as e:
        logger.error(f"Error fetching assets for geofence generation: {e}")
        return jsonify({"error": str(e)}), 500
    
    # Extract coordinates and location/site info
    coordinates = []
    location_info = []
    
    for asset in assets:
        # Handle both ORM and dictionary objects
        if isinstance(asset, dict):
            lat = asset.get('latitude')
            lon = asset.get('longitude')
            location = asset.get('location', 'Unknown')
            site = asset.get('site', 'Unknown')
        else:
            lat = asset.latitude
            lon = asset.longitude
            location = asset.location
            site = asset.site
        
        if lat and lon:
            coordinates.append([lon, lat])
            location_info.append({
                'location': location,
                'site': site
            })
    
    # If no valid coordinates, return empty GeoJSON
    if not coordinates:
        return jsonify({
            "type": "FeatureCollection",
            "features": []
        })
    
    # Convert to numpy array for DBSCAN
    X = np.array(coordinates)
    
    # Perform clustering with DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = db.labels_
    
    # Number of clusters (excluding noise points with label -1)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    # Generate geofences for each cluster
    features = []
    for i in range(n_clusters):
        # Get points in cluster
        cluster_points = X[labels == i]
        
        # Need at least 3 points for a convex hull
        if len(cluster_points) < 3:
            continue
        
        # Calculate convex hull
        hull = ConvexHull(cluster_points)
        hull_points = cluster_points[hull.vertices]
        
        # Convert hull to GeoJSON polygon
        polygon = [[p.tolist() for p in hull_points]]
        
        # Add first point to close the polygon
        polygon[0].append(polygon[0][0])
        
        # Determine most common location/site name for this cluster
        cluster_locations = [location_info[j] for j, label in enumerate(labels) if label == i]
        location_counts = {}
        site_counts = {}
        
        for info in cluster_locations:
            location = info['location']
            site = info['site']
            
            if location not in location_counts:
                location_counts[location] = 0
            location_counts[location] += 1
            
            if site not in site_counts:
                site_counts[site] = 0
            site_counts[site] += 1
        
        # Get most common location and site
        most_common_location = max(location_counts.items(), key=lambda x: x[1])[0] if location_counts else 'Unknown'
        most_common_site = max(site_counts.items(), key=lambda x: x[1])[0] if site_counts else 'Unknown'
        
        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": polygon
            },
            "properties": {
                "id": f"geofence-{i}",
                "name": most_common_site if most_common_site != 'Unknown' else most_common_location,
                "point_count": len(cluster_points),
                "location": most_common_location,
                "site": most_common_site
            }
        }
        
        features.append(feature)
    
    # Create GeoJSON object
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return jsonify(geojson)

@map_bp.route('/asset-status')
@login_required
def asset_status():
    """Get summary of asset status for the map dashboard."""
    try:
        # Get assets from database
        assets = Asset.query.all()
        
        # If no assets in database, try to get from API
        if not assets:
            asset_data = get_asset_data()
            
            # Create count summaries
            total = len(asset_data)
            active = sum(1 for a in asset_data if a.get('active'))
            inactive = total - active
            ignition_on = sum(1 for a in asset_data if a.get('ignition'))
            
            # Count by asset class
            class_counts = {}
            for asset in asset_data:
                asset_class = asset.get('asset_class', 'Unknown')
                if asset_class not in class_counts:
                    class_counts[asset_class] = 0
                class_counts[asset_class] += 1
            
            # Count by location
            location_counts = {}
            for asset in asset_data:
                location = asset.get('location', 'Unknown')
                if location not in location_counts:
                    location_counts[location] = 0
                location_counts[location] += 1
        else:
            # Create count summaries from database
            total = len(assets)
            active = Asset.query.filter_by(active=True).count()
            inactive = total - active
            ignition_on = Asset.query.filter_by(ignition=True).count()
            
            # Count by asset class
            class_counts = {}
            for asset in assets:
                asset_class = asset.asset_class or 'Unknown'
                if asset_class not in class_counts:
                    class_counts[asset_class] = 0
                class_counts[asset_class] += 1
            
            # Count by location
            location_counts = {}
            for asset in assets:
                location = asset.location or 'Unknown'
                if location not in location_counts:
                    location_counts[location] = 0
                location_counts[location] += 1
        
        # Sort and format results
        class_data = [{"name": k, "count": v} for k, v in sorted(class_counts.items(), key=lambda x: x[1], reverse=True) if k != 'Unknown']
        location_data = [{"name": k, "count": v} for k, v in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10] if k != 'Unknown']
        
        return jsonify({
            "total": total,
            "active": active,
            "inactive": inactive,
            "ignition_on": ignition_on,
            "by_class": class_data,
            "by_location": location_data
        })
        
    except Exception as e:
        logger.error(f"Error generating asset status: {e}")
        return jsonify({"error": str(e)}), 500

@map_bp.route('/job-sites')
@login_required
def job_sites():
    """Get list of job sites for filtering."""
    try:
        # Get unique sites from assets
        sites = db.session.query(Asset.site).filter(
            Asset.site.isnot(None),
            Asset.site != ''
        ).distinct().all()
        
        # Format sites
        site_list = [site[0] for site in sites if site[0]]
        
        # If no sites in database, try to get from API
        if not site_list:
            asset_data = get_asset_data()
            site_set = set()
            for asset in asset_data:
                site = asset.get('site')
                if site and site != 'Unknown':
                    site_set.add(site)
            site_list = list(site_set)
        
        return jsonify({
            "sites": sorted(site_list)
        })
        
    except Exception as e:
        logger.error(f"Error fetching job sites: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the map blueprint with the app."""
    app.register_blueprint(map_bp)
    
    # Add to navbar
    if hasattr(app, 'navbar_items'):
        app.navbar_items.append({
            'name': 'Map',
            'url': '/map/',
            'icon': 'map',
            'order': 2
        })