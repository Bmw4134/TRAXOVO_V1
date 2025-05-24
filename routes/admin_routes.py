"""
TRAXORA Fleet Management System - Admin Routes

This module provides routes for the admin dashboard and system administration,
including Kaizen sync management and system health monitoring.
"""

import os
import logging
from datetime import datetime
import json
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, send_file

from utils.kaizen_blueprint_base import KaizenBlueprint

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = KaizenBlueprint('admin', __name__, url_prefix='/admin')

@admin_bp.kaizen_route('/')
def index():
    """Admin dashboard"""
    return render_template('admin/index.html', 
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@admin_bp.kaizen_route('/sync-dashboard')
def sync_dashboard():
    """Sync management dashboard"""
    return render_template('admin/sync_dashboard.html',
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@admin_bp.kaizen_route('/run-sync-test')
def run_sync_test():
    """Run Kaizen sync test"""
    try:
        import kaizen_sync_tester
        results = kaizen_sync_tester.run_tests()
        
        flash("Sync test completed successfully", "success")
        return redirect(url_for('admin.sync_dashboard'))
    except Exception as e:
        logger.error(f"Error running sync test: {str(e)}")
        flash(f"Error running sync test: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/run-integrity-audit')
def run_integrity_audit():
    """Run integrity audit"""
    try:
        from utils.kaizen_integrity_audit import run_integrity_audit
        
        # Run the audit
        report = run_integrity_audit()
        
        # Save report to a file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"integrity_audit_{timestamp}.json"
        report_path = os.path.join('logs', report_file)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Store report in session
        from flask import session
        session['audit_report'] = report
        session['audit_report_file'] = report_path
        
        flash("Integrity audit completed successfully", "success")
        return redirect(url_for('admin.audit_results'))
    except Exception as e:
        logger.error(f"Error running integrity audit: {str(e)}")
        flash(f"Error running integrity audit: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/audit-results')
def audit_results():
    """Display integrity audit results"""
    try:
        from flask import session
        
        report = session.get('audit_report')
        report_file = session.get('audit_report_file')
        
        if not report:
            flash("No audit report found. Please run an integrity audit first.", "warning")
            return redirect(url_for('admin.sync_dashboard'))
            
        return render_template('admin/audit_results.html',
                             report=report,
                             report_file=report_file,
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error displaying audit results: {str(e)}")
        flash(f"Error displaying audit results: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/download-audit/<filename>')
def download_audit(filename):
    """Download audit report file"""
    try:
        file_path = os.path.join('logs', filename)
        
        if not os.path.exists(file_path):
            flash(f"Audit file not found: {filename}", "danger")
            return redirect(url_for('admin.sync_dashboard'))
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading audit file: {str(e)}")
        flash(f"Error downloading audit file: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/run-auto-patch')
def run_auto_patch():
    """Run auto-patch to fix sync issues"""
    try:
        # Get all registered blueprints
        blueprints = []
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                if blueprint_name not in blueprints:
                    blueprints.append(blueprint_name)
                    
        # Run auto-patch for each blueprint
        results = []
        for bp_name in blueprints:
            try:
                bp = current_app.blueprints.get(bp_name)
                if bp and hasattr(bp, 'auto_patch'):
                    result = bp.auto_patch()
                    results.append({
                        'blueprint': bp_name,
                        'result': result
                    })
            except Exception as e:
                logger.error(f"Error auto-patching blueprint {bp_name}: {str(e)}")
                results.append({
                    'blueprint': bp_name,
                    'error': str(e)
                })
                
        # Store results in session
        from flask import session
        session['auto_patch_results'] = results
        
        flash("Auto-patch completed successfully", "success")
        return redirect(url_for('admin.auto_patch_results'))
    except Exception as e:
        logger.error(f"Error running auto-patch: {str(e)}")
        flash(f"Error running auto-patch: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/auto-patch-results')
def auto_patch_results():
    """Display auto-patch results"""
    try:
        from flask import session
        
        results = session.get('auto_patch_results')
        
        if not results:
            flash("No auto-patch results found. Please run auto-patch first.", "warning")
            return redirect(url_for('admin.sync_dashboard'))
            
        return render_template('admin/auto_patch_results.html',
                             results=results,
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error displaying auto-patch results: {str(e)}")
        flash(f"Error displaying auto-patch results: {str(e)}", "danger")
        return redirect(url_for('admin.sync_dashboard'))

@admin_bp.kaizen_route('/api/sync-status')
def api_sync_status():
    """API endpoint for sync status"""
    try:
        # Get all registered blueprints
        blueprints = []
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                if blueprint_name not in blueprints:
                    blueprints.append(blueprint_name)
                    
        # Get sync status for each blueprint
        status = []
        for bp_name in blueprints:
            try:
                bp = current_app.blueprints.get(bp_name)
                if bp and hasattr(bp, 'check_sync_status'):
                    result = bp.check_sync_status()
                    status.append({
                        'blueprint': bp_name,
                        'status': result
                    })
                else:
                    status.append({
                        'blueprint': bp_name,
                        'status': 'not_kaizen'
                    })
            except Exception as e:
                logger.error(f"Error checking sync status for blueprint {bp_name}: {str(e)}")
                status.append({
                    'blueprint': bp_name,
                    'status': 'error',
                    'error': str(e)
                })
                
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'blueprints': status
        })
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500