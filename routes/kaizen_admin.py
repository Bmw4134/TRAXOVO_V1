"""
TRAXORA Fleet Management System - Kaizen Admin Routes

This module provides routes for the Kaizen admin interface,
allowing administrators to manage the sync enforcement system.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
kaizen_admin_bp = Blueprint('kaizen_admin', __name__, url_prefix='/admin/kaizen-core')

@kaizen_admin_bp.route('/')
def index():
    """Kaizen admin dashboard"""
    return render_template('kaizen_admin/index.html', timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@kaizen_admin_bp.route('/sync-test')
def sync_test():
    """Run full stack sync test"""
    try:
        from utils.full_stack_sync_scanner import run_scan
        results = run_scan()
        return jsonify({
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error running sync test: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@kaizen_admin_bp.route('/toggle-auto-patch', methods=['POST'])
def toggle_auto_patch():
    """Toggle auto-patch mode"""
    try:
        auto_patch_enabled = request.json.get('enabled', False)
        
        # Store the setting in a file
        config_path = os.path.join(current_app.root_path, 'config', 'kaizen_config.json')
        import json
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
            
        config['auto_patch_enabled'] = auto_patch_enabled
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        return jsonify({
            'status': 'success',
            'auto_patch_enabled': auto_patch_enabled,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error toggling auto-patch mode: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@kaizen_admin_bp.route('/integrity-audit')
def integrity_audit():
    """Run integrity audit"""
    try:
        from utils.kaizen_integrity_audit import run_audit
        results = run_audit()
        return jsonify({
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error running integrity audit: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@kaizen_admin_bp.route('/start-watchdog')
def start_watchdog():
    """Start the Kaizen watchdog service"""
    try:
        from utils.kaizen_watchdog import start_watchdog as start_watchdog_service
        result = start_watchdog_service()
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error starting watchdog: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@kaizen_admin_bp.route('/stop-watchdog')
def stop_watchdog():
    """Stop the Kaizen watchdog service"""
    try:
        from utils.kaizen_watchdog import stop_watchdog as stop_watchdog_service
        result = stop_watchdog_service()
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error stopping watchdog: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500