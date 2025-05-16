"""
Main routes for the application
"""
import os
import logging
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.security import check_password_hash

from models import User, Asset, APIConfig, db
from utils import load_data, filter_assets, get_asset_by_id, get_asset_categories, get_asset_locations, get_asset_status

# Configure logging
logger = logging.getLogger(__name__)

def register_routes(app):
    """
    Register routes with the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Render the main dashboard page"""
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')
                
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Handle user logout"""
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/assets')
    @login_required
    def assets():
        """Render the assets page with advanced filtering"""
        # Load initial assets data
        try:
            from gauge_api import get_asset_data
            assets_data = get_asset_data()
            
            # Get unique categories, locations for filter dropdowns
            categories = get_asset_categories(assets_data)
            locations = get_asset_locations(assets_data)
            statuses = ["Available", "In Use", "Maintenance", "Out of Service"]
            
            return render_template('assets.html', 
                                 assets=assets_data,
                                 categories=categories,
                                 locations=locations,
                                 statuses=statuses,
                                 asset_count=len(assets_data))
        except Exception as e:
            logger.error(f"Error loading assets: {e}")
            flash("There was an error loading asset data. Please try again.", "danger")
            return render_template('assets.html', assets=[])
    
    @app.route('/asset/<asset_id>')
    @login_required
    def asset_detail(asset_id):
        """Render the asset detail page"""
        asset = Asset.query.filter_by(asset_identifier=asset_id).first_or_404()
        return render_template('asset_detail.html', asset=asset)
    
    @app.route('/reports')
    @login_required
    def reports():
        """Render the reports page"""
        return render_template('reports.html')
    
    @app.route('/api/assets')
    @login_required
    def api_assets():
        """API endpoint to get asset data in JSON format with advanced filtering"""
        try:
            # Get query parameters for filtering
            query = request.args.get('query', '').lower()
            category = request.args.get('category', 'all')
            status = request.args.get('status', 'all')
            location = request.args.get('location', 'all')
            sort_by = request.args.get('sort_by', 'id')
            
            # Load asset data from source
            from gauge_api import get_asset_data
            data = get_asset_data()
            
            if not data:
                logger.warning("No asset data returned from API")
                return jsonify([])
            
            # Apply server-side filtering if requested parameters are provided
            # Otherwise, we'll let the client handle filtering for better UX
            if category != 'all' or status != 'all' or location != 'all' or query:
                # Filter assets using the utility function
                filtered_data = filter_assets(data, status, category, location)
                
                # Additional query search
                if query:
                    filtered_data = [asset for asset in filtered_data if (
                        (asset.get('asset_identifier') and query in asset.get('asset_identifier', '').lower()) or
                        (asset.get('label') and query in asset.get('label', '').lower()) or
                        (asset.get('asset_category') and query in asset.get('asset_category', '').lower()) or
                        (asset.get('location') and query in asset.get('location', '').lower()) or
                        (asset.get('serial_number') and query in asset.get('serial_number', '').lower())
                    )]
            else:
                filtered_data = data
            
            # Log success and return filtered data
            logger.info(f"API assets request: returning {len(filtered_data)} assets")
            return jsonify(filtered_data)
            
        except Exception as e:
            logger.error(f"Error in API assets endpoint: {e}")
            return jsonify({"error": "Error retrieving asset data"}), 500
    
    @app.route('/api/asset/<asset_id>')
    @login_required
    def api_asset_detail(asset_id):
        """API endpoint to get a specific asset by ID"""
        data = get_asset_by_id(asset_id)
        if data:
            return jsonify(data)
        return jsonify({"error": "Asset not found"}), 404
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        return render_template('500.html'), 500