"""
TRAXOVO Job Security Monitoring Routes
Implements PE zone-based equipment monitoring and theft detection
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user

from gauge_api import GaugeAPI
from modules.security.theft_detection import TheftDetectionEngine

logger = logging.getLogger(__name__)

job_security_bp = Blueprint('job_security', __name__, url_prefix='/job-security-monitoring')

@job_security_bp.route('/')
@login_required
def dashboard():
    """Main job security monitoring dashboard - Admin and PE access only"""
    try:
        # TODO: Implement proper role checking
        # For now, allow all logged-in users
        
        # Initialize theft detection engine
        theft_engine = TheftDetectionEngine()
        
        # Get asset data from Gauge API
        gauge_api = GaugeAPI()
        all_assets = gauge_api.get_assets()
        
        if not all_assets:
            all_assets = []
        
        # Filter assets based on user's PE zones (or show all if admin)
        user_email = getattr(current_user, 'email', 'admin@traxovo.com')
        filtered_assets = theft_engine.filter_assets_by_pe_zones(all_assets, user_email)
        
        # Run theft detection scan
        security_alerts = theft_engine.run_full_theft_scan(filtered_assets)
        
        # Get user's assigned zones
        user_zones = theft_engine.get_pe_zones(user_email)
        is_admin = theft_engine.is_admin_user(user_email)
        
        return render_template('job_security_monitoring/dashboard.html',
                             assets=filtered_assets,
                             security_alerts=security_alerts,
                             user_zones=user_zones,
                             is_admin=is_admin,
                             total_assets=len(filtered_assets),
                             total_alerts=security_alerts['summary']['total_alerts'])
                             
    except Exception as e:
        logger.error(f"Error loading job security dashboard: {e}")
        flash('Error loading security monitoring data', 'error')
        return redirect(url_for('dashboard'))

@job_security_bp.route('/api/alerts')
@login_required
def get_alerts():
    """Get current security alerts for API calls"""
    try:
        theft_engine = TheftDetectionEngine()
        gauge_api = GaugeAPI()
        all_assets = gauge_api.get_assets()
        
        if not all_assets:
            return jsonify({"error": "No asset data available"})
        
        # Filter assets by user zones
        user_email = getattr(current_user, 'email', 'admin@traxovo.com')
        filtered_assets = theft_engine.filter_assets_by_pe_zones(all_assets, user_email)
        
        # Run security scan
        alerts = theft_engine.run_full_theft_scan(filtered_assets)
        
        return jsonify(alerts)
        
    except Exception as e:
        logger.error(f"Error getting security alerts: {e}")
        return jsonify({"error": "Failed to retrieve alerts"})

@job_security_bp.route('/generate-theft-report/<zone_id>')
@login_required
def generate_theft_report(zone_id):
    """Generate theft detection report for specific zone"""
    try:
        theft_engine = TheftDetectionEngine()
        
        # Verify user has access to this zone
        user_email = getattr(current_user, 'email', 'admin@traxovo.com')
        user_zones = theft_engine.get_pe_zones(user_email)
        is_admin = theft_engine.is_admin_user(user_email)
        
        if not is_admin and zone_id not in user_zones:
            flash('Access denied: You do not have permission for this zone', 'error')
            return redirect(url_for('job_security.dashboard'))
        
        # Get assets for specific zone
        gauge_api = GaugeAPI()
        all_assets = gauge_api.get_assets()
        
        if not all_assets:
            all_assets = []
        
        # Filter to zone-specific assets
        zone_assets = []
        for asset in all_assets:
            asset_zone = theft_engine.determine_asset_zone(asset)
            if asset_zone == zone_id:
                zone_assets.append(asset)
        
        # Run security scan on zone assets
        zone_alerts = theft_engine.run_full_theft_scan(zone_assets)
        
        # Format as report
        report = {
            "zone_id": zone_id,
            "zone_name": f"Zone {zone_id}",
            "generated_at": datetime.now().isoformat(),
            "generated_by": user_email,
            "asset_count": len(zone_assets),
            "alerts": zone_alerts,
            "summary": {
                "high_priority": len([a for alerts in zone_alerts.values() 
                                    if isinstance(alerts, list) 
                                    for a in alerts 
                                    if isinstance(a, dict) and a.get('severity') == 'HIGH']),
                "medium_priority": len([a for alerts in zone_alerts.values() 
                                      if isinstance(alerts, list) 
                                      for a in alerts 
                                      if isinstance(a, dict) and a.get('severity') == 'MEDIUM']),
                "low_priority": len([a for alerts in zone_alerts.values() 
                                   if isinstance(alerts, list) 
                                   for a in alerts 
                                   if isinstance(a, dict) and a.get('severity') == 'LOW'])
            }
        }
        
        # Return JSON format or render HTML based on request
        if request.args.get('format') == 'json':
            return jsonify(report)
        else:
            return render_template('job_security_monitoring/theft_report.html', 
                                 report=report, zone_id=zone_id)
                                 
    except Exception as e:
        logger.error(f"Error generating theft report for zone {zone_id}: {e}")
        flash('Error generating theft report', 'error')
        return redirect(url_for('job_security.dashboard'))

@job_security_bp.route('/zones')
@login_required
def zones():
    """View zone assignments and boundaries"""
    try:
        theft_engine = TheftDetectionEngine()
        
        user_email = getattr(current_user, 'email', 'admin@traxovo.com')
        user_zones = theft_engine.get_pe_zones(user_email)
        is_admin = theft_engine.is_admin_user(user_email)
        
        # Get zone definitions
        zone_config = theft_engine.config.get('zone_definitions', {})
        
        if is_admin:
            available_zones = zone_config
        else:
            available_zones = {k: v for k, v in zone_config.items() if k in user_zones}
        
        return render_template('job_security_monitoring/zones.html',
                             zones=available_zones,
                             user_zones=user_zones,
                             is_admin=is_admin)
                             
    except Exception as e:
        logger.error(f"Error loading zones: {e}")
        flash('Error loading zone information', 'error')
        return redirect(url_for('job_security.dashboard'))