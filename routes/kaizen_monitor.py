"""
TRAXORA Fleet Management System - Kaizen Monitor

This module provides routes for the Kaizen monitoring system, which enforces
real-time synchronization between backend routes and UI components.
"""

import os
import logging
from datetime import datetime
import json
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from utils.kaizen_integrity_audit import run_integrity_audit
import kaizen_sync_tester

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
kaizen_monitor_bp = Blueprint('kaizen_monitor', __name__, url_prefix='/admin/kaizen')

@kaizen_monitor_bp.route('/')
def index():
    """Kaizen Monitor dashboard"""
    return render_template('kaizen_monitor/index.html', 
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@kaizen_monitor_bp.route('/run-integrity-audit')
def run_audit():
    """Run a full integrity audit"""
    try:
        # Run the integrity audit
        report = run_integrity_audit()
        
        # Save report to a static file for access via web
        static_dir = os.path.join('static', 'reports')
        os.makedirs(static_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"integrity_audit_{timestamp}.json"
        static_path = os.path.join(static_dir, report_file)
        
        with open(static_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Save report to the session for the result page
        from flask import session
        session['audit_report'] = report
        session['audit_report_path'] = f"/static/reports/{report_file}"
        
        # Redirect to the results page
        return redirect(url_for('kaizen_monitor.audit_results'))
    except Exception as e:
        logger.error(f"Error running integrity audit: {str(e)}")
        flash(f"Error running integrity audit: {str(e)}", "danger")
        return redirect(url_for('kaizen_monitor.index'))

@kaizen_monitor_bp.route('/audit-results')
def audit_results():
    """Display integrity audit results"""
    from flask import session
    
    report = session.get('audit_report')
    report_path = session.get('audit_report_path')
    
    if not report:
        flash("No audit report found. Please run an audit first.", "warning")
        return redirect(url_for('kaizen_monitor.index'))
        
    return render_template('kaizen_monitor/audit_results.html',
                          report=report,
                          report_path=report_path,
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@kaizen_monitor_bp.route('/run-sync-test')
def run_sync_test():
    """Run the Kaizen sync test"""
    try:
        # Run the sync test
        kaizen_sync_tester.run_tests()
        flash("Sync test completed successfully.", "success")
    except Exception as e:
        logger.error(f"Error running sync test: {str(e)}")
        flash(f"Error running sync test: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_monitor.index'))

@kaizen_monitor_bp.route('/run-auto-patch')
def run_auto_patch():
    """Run the Kaizen auto-patch script"""
    try:
        # Rename the original run_tests function to preserve it
        original_run_tests = kaizen_sync_tester.run_tests
        
        # Override with a function that captures the output
        results = []
        def capture_output():
            import io
            import sys
            original_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            # Run the tests with auto-patching
            kaizen_sync_tester.run_tests()
            
            sys.stdout = original_stdout
            output = captured_output.getvalue()
            results.append(output)
            
            return output
            
        # Run the capture function
        output = capture_output()
        
        # Restore the original function
        kaizen_sync_tester.run_tests = original_run_tests
        
        # Check for success in the output
        if "All systems in sync" in output:
            flash("Auto-patch completed successfully. All systems in sync!", "success")
        else:
            flash("Auto-patch completed with issues. Please check the logs.", "warning")
            
        # Save the output to a log file
        log_dir = os.path.join('logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"auto_patch_{timestamp}.log")
        
        with open(log_file, 'w') as f:
            f.write(output)
            
        return redirect(url_for('kaizen_monitor.index'))
    except Exception as e:
        logger.error(f"Error running auto-patch: {str(e)}")
        flash(f"Error running auto-patch: {str(e)}", "danger")
        return redirect(url_for('kaizen_monitor.index'))

@kaizen_monitor_bp.route('/api/status')
def api_status():
    """API endpoint for Kaizen system status"""
    try:
        # Get the most recent audit report
        audit_reports = []
        report_dir = os.path.join('static', 'reports')
        if os.path.exists(report_dir):
            for file in os.listdir(report_dir):
                if file.startswith('integrity_audit_') and file.endswith('.json'):
                    audit_reports.append(file)
                    
        latest_report = None
        if audit_reports:
            # Sort by timestamp (part of filename)
            audit_reports.sort(reverse=True)
            latest_report_path = os.path.join(report_dir, audit_reports[0])
            
            with open(latest_report_path, 'r') as f:
                latest_report = json.load(f)
                
        return jsonify({
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'last_audit': latest_report['timestamp'] if latest_report else None,
            'audit_status': latest_report['status'] if latest_report else None,
            'issues': {
                'orphaned_routes': len(latest_report['orphaned_routes']) if latest_report else 0,
                'orphaned_templates': len(latest_report['orphaned_templates']) if latest_report else 0,
                'integrity_issues': len(latest_report['integrity_issues']) if latest_report else 0
            }
        })
    except Exception as e:
        logger.error(f"Error getting Kaizen status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500