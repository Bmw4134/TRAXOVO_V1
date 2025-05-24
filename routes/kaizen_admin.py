"""
TRAXORA Kaizen Admin Module

This module provides administrative controls for the Kaizen sync system,
allowing for configuration, monitoring, and manual triggering of sync tests.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, current_app

# Import Kaizen utilities
import kaizen_sync_tester
from utils.kaizen_integrity_audit import run_integrity_audit
from utils.kaizen_watchdog import start_watchdog_service

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
kaizen_admin_bp = Blueprint('kaizen_admin', __name__, url_prefix='/admin/kaizen-core')

# Global watchdog service
watchdog_thread = None
config = {
    'auto_sync': True,
    'auto_patch': True,
    'notify_on_issues': True,
    'strict_mode': False,
    'last_updated': datetime.now().isoformat()
}

@kaizen_admin_bp.route('/')
def index():
    """Kaizen Admin dashboard"""
    global config
    return render_template('kaizen_admin/index.html', 
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          config=config,
                          watchdog_active=watchdog_thread is not None and watchdog_thread.is_alive())

@kaizen_admin_bp.route('/start-watchdog')
def start_watchdog():
    """Start the Kaizen Watchdog service"""
    global watchdog_thread
    
    try:
        if watchdog_thread is None or not watchdog_thread.is_alive():
            watchdog_thread = start_watchdog_service()
            flash("Kaizen Watchdog service started successfully.", "success")
        else:
            flash("Kaizen Watchdog service is already running.", "info")
    except Exception as e:
        logger.error(f"Error starting Kaizen Watchdog service: {str(e)}")
        flash(f"Error starting Kaizen Watchdog service: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/run-sync-test')
def run_sync_test():
    """Run a manual sync test"""
    try:
        logger.info("Running sync test...")
        kaizen_sync_tester.run_tests()
        flash("Sync test completed successfully.", "success")
    except Exception as e:
        logger.error(f"Error running sync test: {str(e)}")
        flash(f"Error running sync test: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/run-integrity-audit')
def run_audit():
    """Run a manual integrity audit"""
    try:
        logger.info("Running integrity audit...")
        report = run_integrity_audit()
        
        # Save report to a static file for access via web
        static_dir = os.path.join('static', 'reports')
        os.makedirs(static_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"integrity_audit_{timestamp}.json"
        static_path = os.path.join(static_dir, report_file)
        
        with open(static_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        flash(f"Integrity audit completed with status: {report['status']}.", 
              "success" if report['status'] == 'PASS' else "warning")
    except Exception as e:
        logger.error(f"Error running integrity audit: {str(e)}")
        flash(f"Error running integrity audit: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/update-config', methods=['POST'])
def update_config():
    """Update Kaizen configuration"""
    global config
    
    try:
        # Update configuration
        config['auto_sync'] = 'auto_sync' in request.form
        config['auto_patch'] = 'auto_patch' in request.form
        config['notify_on_issues'] = 'notify_on_issues' in request.form
        config['strict_mode'] = 'strict_mode' in request.form
        config['last_updated'] = datetime.now().isoformat()
        
        flash("Configuration updated successfully.", "success")
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        flash(f"Error updating configuration: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/api/status')
def api_status():
    """API endpoint for Kaizen Admin status"""
    global config, watchdog_thread
    
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'config': config,
        'watchdog_active': watchdog_thread is not None and watchdog_thread.is_alive()
    })