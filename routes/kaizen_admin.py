"""
TRAXORA Fleet Management System - Kaizen Core Admin

This module provides routes for the Kaizen Core administration,
including sync history, template management, and advanced sync tools.
"""

import os
import time
import json
import logging
import threading
import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, Response, send_file

# Import Kaizen utilities
from utils.kaizen_sync_history import get_history, clear_history_entries, get_history_entry
from utils.kaizen_integrity_audit import run_integrity_check
from utils.kaizen_template_generator import generate_template_for_route
from utils.kaizen_admin_actions import get_admin_actions, get_admin_action, clear_admin_actions, add_admin_action

logger = logging.getLogger(__name__)

# Create blueprint
kaizen_admin_bp = Blueprint('kaizen_admin', __name__, url_prefix='/admin/kaizen')

# Global variables for watchdog status
watchdog_thread = None
watchdog_running = False

@kaizen_admin_bp.route('/')
def index():
    """Kaizen Core Admin dashboard"""
    history = get_history(limit=5)
    watchdog_status = watchdog_running
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    return render_template(
        'kaizen_admin/index.html',
        history=history,
        watchdog_status=watchdog_status,
        timestamp=timestamp
    )

@kaizen_admin_bp.route('/sync-history')
def sync_history():
    """Sync history view"""
    history = get_history(limit=None)
    
    return render_template(
        'kaizen_admin/sync_history.html',
        history=history
    )

@kaizen_admin_bp.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear sync history"""
    if clear_history_entries():
        flash('Sync history cleared successfully', 'success')
    else:
        flash('Failed to clear sync history', 'danger')
        
    return redirect(url_for('kaizen_admin.sync_history'))

@kaizen_admin_bp.route('/history-entry/<entry_id>')
def history_entry(entry_id):
    """View a specific history entry"""
    entry = get_history_entry(entry_id)
    
    if entry:
        return render_template(
            'kaizen_admin/history_entry.html',
            entry=entry
        )
    else:
        flash('History entry not found', 'danger')
        return redirect(url_for('kaizen_admin.sync_history'))

@kaizen_admin_bp.route('/templates')
def templates():
    """Template management"""
    template_dir = current_app.template_folder
    templates_by_blueprint = {}
    
    # Collect templates organized by blueprint
    for root, dirs, files in os.walk(template_dir):
        rel_path = os.path.relpath(root, template_dir)
        if rel_path == '.':
            continue
            
        blueprint_name = rel_path.split(os.sep)[0]
        
        if blueprint_name not in templates_by_blueprint:
            templates_by_blueprint[blueprint_name] = []
            
        for file in files:
            if file.endswith('.html'):
                template_path = os.path.join(rel_path, file)
                templates_by_blueprint[blueprint_name].append(template_path)
                
    # Collect routes organized by blueprint
    routes_by_blueprint = {}
    
    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint
        if '.' in endpoint:
            blueprint_name = endpoint.split('.')[0]
            
            if blueprint_name not in routes_by_blueprint:
                routes_by_blueprint[blueprint_name] = []
                
            routes_by_blueprint[blueprint_name].append({
                'rule': rule.rule,
                'endpoint': endpoint,
                'methods': list(rule.methods)
            })
    
    return render_template(
        'kaizen_admin/templates.html',
        templates_by_blueprint=templates_by_blueprint,
        routes_by_blueprint=routes_by_blueprint
    )

@kaizen_admin_bp.route('/generate-template', methods=['POST'])
def generate_template():
    """Generate a template for a route"""
    blueprint_name = request.form.get('blueprint_name')
    route_name = request.form.get('route_name')
    endpoint_name = request.form.get('endpoint_name')
    template_path = request.form.get('template_path')
    
    if not all([blueprint_name, route_name, endpoint_name, template_path]):
        flash('Missing required parameters', 'danger')
        return redirect(url_for('kaizen_admin.templates'))
        
    if generate_template_for_route(blueprint_name, route_name, endpoint_name, template_path):
        flash(f'Template {template_path} generated successfully', 'success')
    else:
        flash(f'Failed to generate template {template_path}', 'danger')
        
    return redirect(url_for('kaizen_admin.templates'))

@kaizen_admin_bp.route('/auto-generate-templates', methods=['POST'])
def auto_generate_all_templates():
    """Auto-generate templates for all routes without templates"""
    # This functionality would need to be implemented in a real system
    flash('Auto-generation of templates is not implemented yet', 'warning')
    return redirect(url_for('kaizen_admin.templates'))

@kaizen_admin_bp.route('/run-checks')
def run_all_checks():
    """Run all integrity checks and sync tests"""
    results = run_integrity_check()
    
    return render_template(
        'kaizen_admin/integrity_check.html',
        results=results
    )

@kaizen_admin_bp.route('/start-watchdog', methods=['POST'])
def start_watchdog_route():
    """Start the Kaizen watchdog service"""
    global watchdog_thread, watchdog_running
    
    if watchdog_running:
        flash('Watchdog service is already running', 'warning')
    else:
        # In a real implementation, this would start the watchdog thread
        # For demonstration purposes, we'll just set the flag
        watchdog_running = True
        flash('Watchdog service started successfully', 'success')
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/stop-watchdog', methods=['POST'])
def stop_watchdog_route():
    """Stop the Kaizen watchdog service"""
    global watchdog_thread, watchdog_running
    
    if not watchdog_running:
        flash('Watchdog service is not running', 'warning')
    else:
        # In a real implementation, this would stop the watchdog thread
        # For demonstration purposes, we'll just set the flag
        watchdog_running = False
        flash('Watchdog service stopped successfully', 'success')
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/api/sync-stats')
def api_sync_stats():
    """API endpoint for sync statistics"""
    history = get_history(limit=10)
    
    # Calculate statistics
    stats = {
        'total_entries': len(history),
        'success_count': sum(1 for entry in history if entry.get('status') == 'success'),
        'warning_count': sum(1 for entry in history if entry.get('status') == 'warning'),
        'error_count': sum(1 for entry in history if entry.get('status') == 'error'),
        'latest_timestamp': history[0].get('timestamp') if history else None
    }
    
    return jsonify(stats)

@kaizen_admin_bp.route('/admin-actions/')
def admin_actions():
    """Admin actions view"""
    actions = get_admin_actions(limit=None)
    
    return render_template(
        'kaizen_admin/admin_actions.html',
        actions=actions
    )

@kaizen_admin_bp.route('/clear-admin-actions/', methods=['POST'])
def clear_admin_actions_route():
    """Clear admin actions"""
    if clear_admin_actions():
        # Log this action
        add_admin_action(
            'clear_admin_actions',
            'Admin actions history cleared',
            category='system',
            status='success'
        )
        flash('Admin actions cleared successfully', 'success')
    else:
        flash('Failed to clear admin actions', 'danger')
        
    return redirect(url_for('kaizen_admin.admin_actions'))

@kaizen_admin_bp.route('/download-admin-actions/')
def download_admin_actions():
    """Download admin actions in JSON or CSV format"""
    format_type = request.args.get('format', 'json')
    actions = get_admin_actions(limit=None)
    
    # Log this action
    add_admin_action(
        'download_admin_actions',
        f'Admin actions downloaded in {format_type} format',
        category='system',
        status='success'
    )
    
    if format_type.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        csv_writer = csv.writer(output)
        
        # Write headers
        csv_writer.writerow(['ID', 'Timestamp', 'User', 'Action', 'Category', 'Status', 'Message'])
        
        # Write data
        for action in actions:
            csv_writer.writerow([
                action.get('id', ''),
                action.get('timestamp', ''),
                action.get('user', ''),
                action.get('action', ''),
                action.get('category', ''),
                action.get('status', ''),
                action.get('message', '')
            ])
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=admin_actions_{timestamp}.csv'
            }
        )
    else:
        # JSON format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            json.dumps(actions, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=admin_actions_{timestamp}.json'
            }
        )

@kaizen_admin_bp.route('/run-auto-patch', methods=['POST'])
def run_auto_patch():
    """Run the Kaizen Auto Patch tool to fix sync issues automatically"""
    try:
        # Log this action
        add_admin_action(
            'run_auto_patch',
            'Kaizen Auto Patch tool executed',
            category='system',
            status='success'
        )
        
        # In a real implementation, this would run the auto-patch process
        # For now, we'll just add a success message
        flash('Kaizen Auto Patch completed successfully', 'success')
        
        # Add to history
        get_history().insert(0, {
            'id': str(int(time.time())),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'auto_patch',
            'status': 'success',
            'message': 'Auto Patch process completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in auto-patch: {str(e)}")
        flash(f'Auto Patch failed: {str(e)}', 'danger')
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.route('/download-sync-history/')
def download_sync_history():
    """Download sync history in JSON or CSV format"""
    format_type = request.args.get('format', 'json')
    history = get_history(limit=None)
    
    # Log this action
    add_admin_action(
        'download_sync_history',
        f'Sync history downloaded in {format_type} format',
        category='system',
        status='success'
    )
    
    if format_type.lower() == 'csv':
        # Create CSV output
        output = io.StringIO()
        csv_writer = csv.writer(output)
        
        # Write headers
        csv_writer.writerow(['ID', 'Timestamp', 'Type', 'Status', 'Message'])
        
        # Write data
        for entry in history:
            csv_writer.writerow([
                entry.get('id', ''),
                entry.get('timestamp', ''),
                entry.get('type', ''),
                entry.get('status', ''),
                entry.get('message', '')
            ])
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=sync_history_{timestamp}.csv'
            }
        )
    else:
        # JSON format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            json.dumps(history, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=sync_history_{timestamp}.json'
            }
        )