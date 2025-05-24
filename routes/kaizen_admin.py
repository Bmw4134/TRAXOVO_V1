"""
TRAXORA Fleet Management System - Kaizen Core Admin

This module provides routes for the Kaizen Core administration,
including sync history, template management, and advanced sync tools.
"""

import os
import logging
from datetime import datetime
import json
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app

from utils.kaizen_blueprint_base import KaizenBlueprint
from utils.kaizen_sync_history import SyncHistory
from utils.kaizen_template_generator import TemplateGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
kaizen_admin_bp = KaizenBlueprint('kaizen_admin', __name__, url_prefix='/admin/kaizen-core')

@kaizen_admin_bp.kaizen_route('/')
def index():
    """Kaizen Core Admin dashboard"""
    try:
        # Get sync history stats
        sync_stats = SyncHistory.get_stats()
        
        # Get recent history entries
        recent_history = SyncHistory.get_history(limit=5)
        
        # Get all registered blueprints
        blueprints = []
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                if blueprint_name not in [bp.get('name') for bp in blueprints]:
                    # Check if it's a Kaizen blueprint
                    bp = current_app.blueprints.get(blueprint_name)
                    is_kaizen = bp and hasattr(bp, 'check_sync_status')
                    
                    blueprints.append({
                        'name': blueprint_name,
                        'is_kaizen': is_kaizen
                    })
        
        return render_template('kaizen_admin/index.html',
                               sync_stats=sync_stats,
                               recent_history=recent_history,
                               blueprints=blueprints,
                               timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error loading Kaizen Core Admin: {str(e)}")
        flash(f"Error loading Kaizen Core Admin: {str(e)}", "danger")
        return redirect(url_for('admin.index'))

@kaizen_admin_bp.kaizen_route('/sync-history')
def sync_history():
    """Sync history view"""
    try:
        # Get filter parameters
        event_type = request.args.get('event_type')
        blueprint = request.args.get('blueprint')
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        # Get history entries
        history = SyncHistory.get_history(
            limit=limit,
            event_type=event_type,
            blueprint=blueprint,
            status=status
        )
        
        # Get stats for summary
        sync_stats = SyncHistory.get_stats()
        
        # Get unique filter options
        filter_options = {
            'event_types': list(sync_stats.get('event_types', {}).keys()),
            'blueprints': list(sync_stats.get('blueprints', {}).keys()),
            'statuses': list(sync_stats.get('statuses', {}).keys())
        }
        
        return render_template('kaizen_admin/sync_history.html',
                             history=history,
                             sync_stats=sync_stats,
                             filter_options=filter_options,
                             current_filters={
                                 'event_type': event_type,
                                 'blueprint': blueprint,
                                 'status': status,
                                 'limit': limit
                             },
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error loading sync history: {str(e)}")
        flash(f"Error loading sync history: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.kaizen_route('/clear-history')
def clear_history():
    """Clear sync history"""
    try:
        SyncHistory.clear_history()
        flash("Sync history cleared successfully", "success")
        return redirect(url_for('kaizen_admin.sync_history'))
    except Exception as e:
        logger.error(f"Error clearing sync history: {str(e)}")
        flash(f"Error clearing sync history: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.sync_history'))

@kaizen_admin_bp.kaizen_route('/history-entry/<entry_id>')
def history_entry(entry_id):
    """View a specific history entry"""
    try:
        entry = SyncHistory.get_entry(entry_id)
        
        if not entry:
            flash(f"History entry not found: {entry_id}", "warning")
            return redirect(url_for('kaizen_admin.sync_history'))
            
        return render_template('kaizen_admin/history_entry.html',
                             entry=entry,
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error loading history entry: {str(e)}")
        flash(f"Error loading history entry: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.sync_history'))

@kaizen_admin_bp.kaizen_route('/templates')
def templates():
    """Template management"""
    try:
        # Get all registered blueprints
        blueprints = []
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                route_name = endpoint.split('.')[1]
                
                if blueprint_name not in [bp.get('name') for bp in blueprints]:
                    blueprints.append({
                        'name': blueprint_name,
                        'routes': []
                    })
                    
                # Add route to blueprint
                for bp in blueprints:
                    if bp.get('name') == blueprint_name:
                        bp['routes'].append({
                            'name': route_name,
                            'endpoint': endpoint,
                            'url': rule.rule
                        })
                        break
        
        # Get template generation history
        template_history = SyncHistory.get_history(
            limit=10,
            event_type='template_generation'
        )
        
        return render_template('kaizen_admin/templates.html',
                             blueprints=blueprints,
                             template_history=template_history,
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error loading template management: {str(e)}")
        flash(f"Error loading template management: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.kaizen_route('/generate-template', methods=['POST'])
def generate_template():
    """Generate a template for a route"""
    try:
        # Get form data
        blueprint_name = request.form.get('blueprint')
        route_name = request.form.get('route')
        
        if not blueprint_name or not route_name:
            flash("Blueprint name and route name are required", "warning")
            return redirect(url_for('kaizen_admin.templates'))
            
        # Get route function
        endpoint = f"{blueprint_name}.{route_name}"
        route_function = None
        
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint == endpoint:
                view_func = current_app.view_functions.get(endpoint)
                if view_func:
                    route_function = view_func
                break
                
        # Generate template
        template_path = TemplateGenerator.generate_template(
            blueprint_name=blueprint_name,
            route_name=route_name,
            route_function=route_function
        )
        
        if template_path:
            flash(f"Template generated successfully: {template_path}", "success")
            
            # Log to sync history
            SyncHistory.add_entry(
                event_type='template_generation',
                blueprint=blueprint_name,
                endpoint=route_name,
                details={
                    'template_path': template_path,
                    'generated_at': datetime.now().isoformat(),
                    'auto_generated': False
                }
            )
        else:
            flash(f"Error generating template for {blueprint_name}.{route_name}", "danger")
            
        return redirect(url_for('kaizen_admin.templates'))
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        flash(f"Error generating template: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.templates'))

@kaizen_admin_bp.kaizen_route('/auto-generate-all-templates')
def auto_generate_all_templates():
    """Auto-generate templates for all routes without templates"""
    try:
        # Get all registered routes
        routes = []
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                route_name = endpoint.split('.')[1]
                
                if route_name != 'static':  # Skip static routes
                    routes.append({
                        'blueprint': blueprint_name,
                        'route': route_name,
                        'endpoint': endpoint,
                        'url': rule.rule
                    })
        
        # Generate templates for all routes
        generated_count = 0
        skipped_count = 0
        
        for route in routes:
            # Check if template already exists
            blueprint_name = route['blueprint']
            route_name = route['route']
            
            template_path = os.path.join(current_app.template_folder, blueprint_name, f"{route_name}.html")
            
            if os.path.exists(template_path):
                skipped_count += 1
                continue
                
            # Get route function
            route_function = current_app.view_functions.get(route['endpoint'])
            
            # Generate template
            result = TemplateGenerator.generate_template(
                blueprint_name=blueprint_name,
                route_name=route_name,
                route_function=route_function
            )
            
            if result:
                generated_count += 1
                
        flash(f"Auto-generated {generated_count} templates, skipped {skipped_count} existing templates", "success")
        return redirect(url_for('kaizen_admin.templates'))
    except Exception as e:
        logger.error(f"Error auto-generating templates: {str(e)}")
        flash(f"Error auto-generating templates: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.templates'))

@kaizen_admin_bp.kaizen_route('/run-all-checks')
def run_all_checks():
    """Run all integrity checks and sync tests"""
    try:
        # Run integrity audit
        from utils.kaizen_integrity_audit import run_integrity_audit
        audit_report = run_integrity_audit()
        
        # Run sync tests
        import kaizen_sync_tester
        kaizen_sync_tester.run_tests()
        
        # Log to sync history
        SyncHistory.add_entry(
            event_type='system_check',
            details={
                'audit_report': audit_report,
                'ran_at': datetime.now().isoformat()
            }
        )
        
        flash("All system checks completed successfully", "success")
        return redirect(url_for('kaizen_admin.index'))
    except Exception as e:
        logger.error(f"Error running system checks: {str(e)}")
        flash(f"Error running system checks: {str(e)}", "danger")
        return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.kaizen_route('/start-watchdog')
def start_watchdog():
    """Start the Kaizen watchdog service"""
    try:
        # Import the watchdog module
        try:
            from utils.kaizen_watchdog import start_watchdog
            
            # Start the watchdog
            start_watchdog()
            
            # Log to sync history
            SyncHistory.add_entry(
                event_type='watchdog_start',
                details={
                    'started_at': datetime.now().isoformat()
                }
            )
            
            flash("Kaizen watchdog service started successfully", "success")
        except ImportError:
            logger.error("Error starting watchdog: kaizen_watchdog module not found")
            flash("Error starting watchdog: kaizen_watchdog module not found", "danger")
    except Exception as e:
        logger.error(f"Error starting watchdog: {str(e)}")
        flash(f"Error starting watchdog: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.kaizen_route('/stop-watchdog')
def stop_watchdog():
    """Stop the Kaizen watchdog service"""
    try:
        # Import the watchdog module
        try:
            from utils.kaizen_watchdog import stop_watchdog
            
            # Stop the watchdog
            stop_watchdog()
            
            # Log to sync history
            SyncHistory.add_entry(
                event_type='watchdog_stop',
                details={
                    'stopped_at': datetime.now().isoformat()
                }
            )
            
            flash("Kaizen watchdog service stopped successfully", "success")
        except ImportError:
            logger.error("Error stopping watchdog: kaizen_watchdog module not found")
            flash("Error stopping watchdog: kaizen_watchdog module not found", "danger")
    except Exception as e:
        logger.error(f"Error stopping watchdog: {str(e)}")
        flash(f"Error stopping watchdog: {str(e)}", "danger")
        
    return redirect(url_for('kaizen_admin.index'))

@kaizen_admin_bp.kaizen_route('/api/sync-stats')
def api_sync_stats():
    """API endpoint for sync statistics"""
    try:
        # Get sync history stats
        sync_stats = SyncHistory.get_stats()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'stats': sync_stats
        })
    except Exception as e:
        logger.error(f"Error getting sync stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500