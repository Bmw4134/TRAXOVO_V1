"""
Asset Tracking Routes

This module contains routes for displaying and managing assets
with live data from the Gauge API.
"""
import os
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user

from gauge_api import update_asset_data, get_asset_data
from utils.ml_predictor import predict_asset_health, train_prediction_models, get_model_info

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
asset_tracking = Blueprint('asset_tracking', __name__, url_prefix='/asset-tracking')

@asset_tracking.route('/health-prediction')
@login_required
def health_prediction():
    """Display equipment health prediction and analytics"""
    # Get model info
    model_info = get_model_info()
    
    return render_template(
        'asset_tracking/health_prediction.html',
        title='Equipment Health Prediction',
        model_info=model_info
    )

@asset_tracking.route('/')
@login_required
def index():
    """Display assets dashboard with map and status overview"""
    # Get recent stats about data freshness
    update_stats = {
        'last_update': None,
        'asset_count': 0
    }
    
    try:
        update_file = os.path.join('data', 'last_api_update.json')
        if os.path.exists(update_file):
            with open(update_file, 'r') as f:
                update_info = json.load(f)
                
            if 'last_update' in update_info:
                last_update = datetime.fromisoformat(update_info['last_update'])
                update_stats['last_update'] = last_update
                update_stats['asset_count'] = update_info.get('asset_count', 0)
    except Exception as e:
        flash(f"Error loading update stats: {e}", "warning")
    
    return render_template(
        'asset_tracking/dashboard.html',
        title='Live Asset Tracking',
        update_stats=update_stats
    )

@asset_tracking.route('/list')
@login_required
def list_assets():
    """Display list of all assets with filterable data table"""
    return render_template(
        'asset_tracking/list.html',
        title='Asset List'
    )

@asset_tracking.route('/map')
@login_required
def map_view():
    """Display assets on an interactive map with clustering"""
    return render_template(
        'asset_tracking/map.html',
        title='Asset Map',
        google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', '')
    )

@asset_tracking.route('/detail/<asset_id>')
@login_required
def asset_detail(asset_id):
    """Display detailed information for a specific asset"""
    # Get all assets data and find the requested one
    assets = get_asset_data()
    
    asset = None
    for a in assets:
        if str(a.get('id')) == asset_id or str(a.get('vin')) == asset_id or str(a.get('assetId')) == asset_id:
            asset = a
            break
    
    if not asset:
        flash("Asset not found", "danger")
        return redirect(url_for('asset_tracking.list_assets'))
    
    return render_template(
        'asset_tracking/detail.html',
        title=f"Asset Detail: {asset.get('name', asset_id)}",
        asset=asset
    )

@asset_tracking.route('/api/assets')
@login_required
def api_assets():
    """API endpoint to get asset data for maps and tables"""
    # Get fresh asset data from the API or cache
    all_assets = get_asset_data()
    
    # Filter out inactive (sold/scrapped) assets
    assets = []
    
    for asset in all_assets:
        # Check for active flag first - if it's explicitly set to false, skip it
        if 'active' in asset and asset['active'] is False:
            continue
            
        # Skip assets that have an inactive/sold/scrapped status
        if asset.get('status') and any(term in asset['status'].lower() for term in ['inactive', 'sold', 'scrapped', 'retired', 'decommissioned']):
            continue
        
        # Skip very old assets (no reports in a long time) - these may be inactive
        if asset.get('lastReport'):
            try:
                last_report = datetime.fromisoformat(asset.get('lastReport'))
                # Skip if no reports in last 30 days - likely inactive
                if (datetime.now() - last_report).days > 30:
                    continue
            except (ValueError, TypeError):
                pass
        
        # Asset is considered part of the active fleet if it made it here
        assets.append(asset)
        
        # Default status and color
        asset['status_color'] = '#6c757d'  # gray
        
        # Set status colors based on various conditions
        # Add a default status text
        if not asset.get('status'):
            asset['status'] = ''
            
        # Default to offline/red for very old report data (or missing report data)
        if not asset.get('lastReport'):
            asset['status_color'] = '#dc3545'  # red for no reports
            asset['status'] = 'Offline'
        else:
            # Check if we can parse the date
            try:
                last_report = datetime.fromisoformat(asset.get('lastReport'))
                # Mark as offline if no reports in last 24 hours
                if (datetime.now() - last_report).days > 1:
                    asset['status_color'] = '#dc3545'  # red for old reports
                    if 'status' not in asset or not asset['status']:
                        asset['status'] = 'Offline'
                # Check operational status
                elif asset.get('ignition', False) is True or asset.get('engTime', 0) > 0 or asset.get('engineHours', 0) > 0:
                    asset['status_color'] = '#28a745'  # green for running/on
                    if 'status' not in asset or not asset['status']:
                        asset['status'] = 'Active'
                # Check maintenance status
                elif asset.get('status', '').lower() in ['maintenance', 'repair', 'service']:
                    asset['status_color'] = '#fd7e14'  # orange for maintenance
                    if 'status' not in asset or not asset['status'] or not asset['status'].lower() in ['maintenance', 'repair', 'service']:
                        asset['status'] = 'Maintenance'
                # Default to idle
                else:
                    asset['status_color'] = '#6c757d'  # gray for idle
                    if 'status' not in asset or not asset['status']:
                        asset['status'] = 'Idle'
            except (ValueError, TypeError):
                # If we can't parse the date, mark as offline
                asset['status_color'] = '#dc3545'  # red
                if 'status' not in asset or not asset['status']:
                    asset['status'] = 'Offline'
    
    # Add health predictions using machine learning
    try:
        assets = predict_asset_health(assets)
    except Exception as e:
        # Log error but continue - predictions are an enhancement
        logger.error(f"Error generating asset health predictions: {e}")
    
    # Additional filters can be applied here based on request parameters
    
    return jsonify(assets)

@asset_tracking.route('/refresh-data')
@login_required
def refresh_data():
    """Force refresh of asset data from Gauge API"""
    try:
        # Force update from the API
        assets = update_asset_data(force=True)
        
        if assets:
            flash(f"Successfully refreshed {len(assets)} assets from Gauge API", "success")
        else:
            flash("No assets found or API error occurred", "warning")
    except Exception as e:
        flash(f"Error refreshing asset data: {e}", "danger")
    
    # Redirect back to the page they came from
    return redirect(request.referrer or url_for('asset_tracking.index'))

@asset_tracking.route('/train-model', methods=['POST'])
@login_required
def train_model():
    """Train the equipment health prediction model"""
    try:
        # Get assets for training
        assets = get_asset_data()
        
        if not assets:
            return jsonify({
                'success': False,
                'message': 'No asset data available for training'
            })
        
        # Train the model
        success = train_prediction_models(assets)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully trained model with {len(assets)} assets'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to train model'
            })
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })