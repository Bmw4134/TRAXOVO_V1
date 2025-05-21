"""
Routes for equipment alerts management.

This module defines all routes related to equipment alerts, including 
the alerts dashboard, notifications, and alert management endpoints.
"""

import os
import json
import logging
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort
)
from flask_login import login_required, current_user

from main import User, Asset
from models.alerts import EquipmentAlert, AlertNotification
from utils.alerts_processor import (
    generate_equipment_alerts, get_alerts_summary,
    get_alerts_by_severity, get_alerts_by_type, get_alerts_by_location
)

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


@alerts_bp.route('/')
@login_required
def alerts_dashboard():
    """Equipment alerts dashboard"""
    # Generate alerts if requested
    if request.args.get('refresh') == 'true':
        # Only allow admin users to manually refresh alerts
        if current_user.is_admin:
            try:
                generated_alerts = generate_equipment_alerts()
                flash(f"Generated {len(generated_alerts)} equipment alerts", "success")
            except Exception as e:
                flash(f"Error generating alerts: {str(e)}", "danger")
                logger.error(f"Error generating alerts: {e}")
    
    # Get alerts from database
    try:
        # Get active alerts (unresolved)
        critical_alerts = EquipmentAlert.get_alerts_by_level('critical')
        warning_alerts = EquipmentAlert.get_alerts_by_level('warning')
        info_alerts = EquipmentAlert.get_alerts_by_level('info')
        
        # Get summary data
        summary = EquipmentAlert.get_alerts_summary()
        
        # Get alerts grouped by type
        alerts_by_type = {}
        for alert_type in summary.get('type_counts', {}):
            alerts_by_type[alert_type] = EquipmentAlert.get_alerts_by_type(alert_type)
        
    except Exception as e:
        flash(f"Error loading alerts: {str(e)}", "danger")
        logger.error(f"Error loading alerts: {e}")
        return render_template('alerts/dashboard.html')
    
    # Render the dashboard
    return render_template(
        'alerts/dashboard.html',
        critical_alerts=critical_alerts,
        warning_alerts=warning_alerts,
        info_alerts=info_alerts,
        alerts_by_type=alerts_by_type,
        summary=summary
    )


@alerts_bp.route('/asset/<asset_id>')
@login_required
def asset_alerts(asset_id):
    """View alerts for a specific asset"""
    # Get alerts for this asset
    try:
        # Include resolved alerts if requested
        include_resolved = request.args.get('include_resolved') == 'true'
        
        # Get alerts for this asset
        alerts = EquipmentAlert.get_alerts_by_asset(asset_id, include_resolved=include_resolved)
        
        # Get the asset
        from models import Asset
        asset = Asset.query.filter_by(asset_identifier=asset_id).first_or_404()
        
    except Exception as e:
        flash(f"Error loading asset alerts: {str(e)}", "danger")
        logger.error(f"Error loading asset alerts: {e}")
        return redirect(url_for('assets'))
    
    # Render the asset alerts page
    return render_template(
        'alerts/asset_alerts.html',
        asset=asset,
        alerts=alerts,
        include_resolved=include_resolved
    )


@alerts_bp.route('/acknowledge/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        # Get the alert
        alert = EquipmentAlert.query.get_or_404(alert_id)
        
        # Acknowledge the alert
        alert.acknowledge(current_user.id)
        
        flash(f"Alert acknowledged: {alert.description}", "success")
        
    except Exception as e:
        flash(f"Error acknowledging alert: {str(e)}", "danger")
        logger.error(f"Error acknowledging alert: {e}")
    
    # Redirect back to referrer or dashboard
    referrer = request.referrer or url_for('alerts.alerts_dashboard')
    return redirect(referrer)


@alerts_bp.route('/resolve/<int:alert_id>', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        # Get the alert
        alert = EquipmentAlert.query.get_or_404(alert_id)
        
        # Get resolution notes if provided
        notes = request.form.get('resolution_notes')
        
        # Resolve the alert
        alert.resolve(current_user.id, notes)
        
        flash(f"Alert resolved: {alert.description}", "success")
        
    except Exception as e:
        flash(f"Error resolving alert: {str(e)}", "danger")
        logger.error(f"Error resolving alert: {e}")
    
    # Redirect back to referrer or dashboard
    referrer = request.referrer or url_for('alerts.alerts_dashboard')
    return redirect(referrer)


@alerts_bp.route('/refresh', methods=['POST'])
@login_required
def refresh_alerts():
    """Manually refresh/generate alerts"""
    # Only allow admin users to manually refresh alerts
    if not current_user.is_admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('alerts.alerts_dashboard'))
    
    try:
        # Generate new alerts
        start_time = datetime.now()
        generated_alerts = generate_equipment_alerts()
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create database records for new alerts
        created_count = 0
        for alert in generated_alerts:
            # Check if alert already exists
            asset_id = alert.get('asset_id')
            alert_type = alert.get('type')
            
            # Skip if already exists for this asset and type and is still active
            existing = EquipmentAlert.query.filter_by(
                asset_id=asset_id,
                alert_type=alert_type,
                resolved=False
            ).first()
            
            if not existing:
                # Create new alert
                db_alert = EquipmentAlert.create_from_alert_dict(alert)
                from app import db
                db.session.add(db_alert)
                created_count += 1
        
        # Commit changes
        from app import db
        db.session.commit()
        
        flash(f"Generated {len(generated_alerts)} alerts ({created_count} new) in {processing_time:.2f} seconds", "success")
        
    except Exception as e:
        flash(f"Error refreshing alerts: {str(e)}", "danger")
        logger.error(f"Error refreshing alerts: {e}")
    
    # Redirect back to dashboard
    return redirect(url_for('alerts.alerts_dashboard'))


@alerts_bp.route('/api/alerts')
@login_required
def api_alerts():
    """API endpoint to get alerts data"""
    try:
        # Get filter parameters
        alert_level = request.args.get('level')
        alert_type = request.args.get('type')
        asset_id = request.args.get('asset_id')
        include_resolved = request.args.get('include_resolved') == 'true'
        
        # Base query
        query = EquipmentAlert.query
        
        # Apply filters
        if alert_level:
            query = query.filter_by(level=alert_level)
            
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
            
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
            
        if not include_resolved:
            query = query.filter_by(resolved=False)
            
        # Execute query
        alerts = query.order_by(
            EquipmentAlert.level.desc(),
            EquipmentAlert.created_at.desc()
        ).all()
        
        # Convert to dictionaries
        alerts_data = [alert.to_dict() for alert in alerts]
        
        return jsonify(alerts_data)
        
    except Exception as e:
        logger.error(f"Error in API alerts endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/settings')
@login_required
def alerts_settings():
    """Settings page for equipment alerts"""
    # Only allow admin users to view settings
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('alerts.alerts_dashboard'))
    
    return render_template('alerts/settings.html')


def register_alerts_routes(app):
    """Register alerts routes with the app"""
    app.register_blueprint(alerts_bp)
@alerts_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('alerts/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/asset/<asset_id>')
def asset_<asset_id>():
    """Handler for /asset/<asset_id>"""
    try:
        # Add your route handler logic here
        return render_template('alerts/asset_<asset_id>.html')
    except Exception as e:
        logger.error(f"Error in asset_<asset_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/acknowledge/<int:alert_id>')
def acknowledge_<int:alert_id>():
    """Handler for /acknowledge/<int:alert_id>"""
    try:
        # Add your route handler logic here
        return render_template('alerts/acknowledge_<int:alert_id>.html')
    except Exception as e:
        logger.error(f"Error in acknowledge_<int:alert_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/resolve/<int:alert_id>')
def resolve_<int:alert_id>():
    """Handler for /resolve/<int:alert_id>"""
    try:
        # Add your route handler logic here
        return render_template('alerts/resolve_<int:alert_id>.html')
    except Exception as e:
        logger.error(f"Error in resolve_<int:alert_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/refresh')
def refresh():
    """Handler for /refresh"""
    try:
        # Add your route handler logic here
        return render_template('alerts/refresh.html')
    except Exception as e:
        logger.error(f"Error in refresh: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/api/alerts')
def api_alerts():
    """Handler for /api/alerts"""
    try:
        # Add your route handler logic here
        return render_template('alerts/api_alerts.html')
    except Exception as e:
        logger.error(f"Error in api_alerts: {e}")
        return render_template('error.html', error=str(e)), 500

@alerts_bp.route('/settings')
def settings():
    """Handler for /settings"""
    try:
        # Add your route handler logic here
        return render_template('alerts/settings.html')
    except Exception as e:
        logger.error(f"Error in settings: {e}")
        return render_template('error.html', error=str(e)), 500
