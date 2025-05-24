"""
TRAXORA Fleet Management System - Kaizen Integrity Audit

This module provides utilities for checking the integrity of the application,
including verifying route and template synchronization.
"""

import os
import json
import inspect
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from flask import current_app
from bs4 import BeautifulSoup

from utils.kaizen_sync_history import add_history_entry

logger = logging.getLogger(__name__)

def run_integrity_check():
    """
    Run a comprehensive integrity check on the application.
    
    Returns:
        dict: Results of the integrity check
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': [],
        'issues_count': 0,
        'status': 'ok'
    }
    
    # Check route-template synchronization
    template_sync_results = check_template_sync()
    results['checks'].append(template_sync_results)
    
    # Check template references
    template_ref_results = check_template_references()
    results['checks'].append(template_ref_results)
    
    # Calculate issues count and status
    issues_count = 0
    status = 'ok'
    
    for check in results['checks']:
        issues_count += check.get('issues_count', 0)
        if check.get('status') == 'critical':
            status = 'critical'
        elif check.get('status') == 'warning' and status != 'critical':
            status = 'warning'
            
    results['issues_count'] = issues_count
    results['status'] = status
    
    # Log results
    if status == 'ok':
        logger.info(f"Integrity check passed with no issues")
    else:
        logger.warning(f"Integrity check found {issues_count} issues with status '{status}'")
        
    # Add to history
    add_history_entry(
        'integrity_check',
        'success' if status == 'ok' else 'warning',
        f"Integrity check completed with status '{status}' and found {issues_count} issues",
        {'results': results}
    )
    
    return results
    
def check_template_sync():
    """
    Check that all routes have corresponding templates and vice versa.
    
    Returns:
        dict: Results of the template sync check
    """
    issues = []
    
    try:
        # Get all blueprints
        blueprints = []
        routes_count = 0
        templates_count = 0
        
        for rule in current_app.url_map.iter_rules():
            endpoint = rule.endpoint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
                if blueprint_name not in [bp.get('name') for bp in blueprints]:
                    blueprint = current_app.blueprints.get(blueprint_name)
                    if blueprint:
                        # Check for sync status method
                        if hasattr(blueprint, 'check_sync_status'):
                            # Use built-in sync status check
                            sync_status = blueprint.check_sync_status()
                            
                            routes_count += sync_status.get('routes_count', 0)
                            templates_count += sync_status.get('templates_count', 0)
                            
                            for issue in sync_status.get('issues', []):
                                issues.append({
                                    'blueprint': blueprint_name,
                                    'type': issue.get('type'),
                                    'route': issue.get('route', ''),
                                    'template': issue.get('template', ''),
                                    'severity': issue.get('severity', 'warning')
                                })
                        else:
                            # Manual check for this blueprint
                            blueprint_routes = []
                            
                            # Get routes for this blueprint
                            for r in current_app.url_map.iter_rules():
                                if r.endpoint.startswith(f"{blueprint_name}."):
                                    function_name = r.endpoint.split('.')[-1]
                                    blueprint_routes.append({
                                        'rule': r.rule,
                                        'function': function_name,
                                        'methods': list(r.methods),
                                        'endpoint': r.endpoint
                                    })
                                    
                            routes_count += len(blueprint_routes)
                            
                            # Get templates for this blueprint
                            blueprint_templates = []
                            template_dir = os.path.join(current_app.template_folder, blueprint_name)
                            if os.path.exists(template_dir):
                                for root, _, files in os.walk(template_dir):
                                    for file in files:
                                        if file.endswith('.html'):
                                            rel_path = os.path.join(os.path.relpath(root, current_app.template_folder), file)
                                            blueprint_templates.append(rel_path)
                                            
                            templates_count += len(blueprint_templates)
                            
                            # Check for routes without templates
                            for route in blueprint_routes:
                                function_name = route['function']
                                view_func = getattr(blueprint, function_name, None)
                                
                                if view_func:
                                    source = inspect.getsource(view_func)
                                    
                                    # Check if function renders a template
                                    if 'render_template' in source:
                                        import re
                                        template_match = re.search(r"render_template\s*\(\s*['\"]([^'\"]+)['\"]", source)
                                        
                                        if template_match:
                                            template_path = template_match.group(1)
                                            
                                            # Check if template exists
                                            if not os.path.exists(os.path.join(current_app.template_folder, template_path)):
                                                issues.append({
                                                    'blueprint': blueprint_name,
                                                    'type': 'missing_template',
                                                    'route': route['rule'],
                                                    'template': template_path,
                                                    'severity': 'error'
                                                })
                                        else:
                                            # Render template call found but template path not found
                                            issues.append({
                                                'blueprint': blueprint_name,
                                                'type': 'template_not_found_in_route',
                                                'route': route['rule'],
                                                'template': '',
                                                'severity': 'warning'
                                            })
                                    else:
                                        # Function doesn't render a template
                                        issues.append({
                                            'blueprint': blueprint_name,
                                            'type': 'no_template_specified',
                                            'route': route['rule'],
                                            'template': '',
                                            'severity': 'info'
                                        })
                        
                        blueprints.append({
                            'name': blueprint_name,
                            'url_prefix': getattr(blueprint, 'url_prefix', ''),
                            'routes_count': len(blueprint_routes) if 'blueprint_routes' in locals() else sync_status.get('routes_count', 0),
                            'templates_count': len(blueprint_templates) if 'blueprint_templates' in locals() else sync_status.get('templates_count', 0)
                        })
        
        # Determine status
        status = 'ok'
        critical_issues = 0
        warning_issues = 0
        
        for issue in issues:
            if issue['severity'] == 'error':
                critical_issues += 1
            elif issue['severity'] == 'warning':
                warning_issues += 1
                
        if critical_issues > 0:
            status = 'critical'
        elif warning_issues > 0:
            status = 'warning'
            
        return {
            'name': 'template_sync',
            'description': 'Check route-template synchronization',
            'blueprints': blueprints,
            'routes_count': routes_count,
            'templates_count': templates_count,
            'issues': issues,
            'issues_count': len(issues),
            'status': status
        }
    except Exception as e:
        logger.error(f"Failed to check template sync: {str(e)}")
        return {
            'name': 'template_sync',
            'description': 'Check route-template synchronization',
            'error': str(e),
            'issues_count': 1,
            'status': 'critical'
        }
        
def check_template_references():
    """
    Check template references for invalid endpoints or templates.
    
    Returns:
        dict: Results of the template references check
    """
    issues = []
    
    try:
        # Get all templates
        templates_checked = 0
        
        for root, _, files in os.walk(current_app.template_folder):
            for file in files:
                if file.endswith('.html'):
                    template_path = os.path.join(root, file)
                    rel_path = os.path.relpath(template_path, current_app.template_folder)
                    
                    # Parse template
                    with open(template_path, 'r') as f:
                        template_content = f.read()
                        
                    templates_checked += 1
                    
                    # Check for url_for references
                    soup = BeautifulSoup(template_content, 'html.parser')
                    
                    # Check all tags with href attribute
                    for tag in soup.find_all(href=True):
                        href = tag['href']
                        if 'url_for' in href:
                            # Extract endpoint
                            import re
                            endpoint_match = re.search(r"url_for\s*\(\s*['\"]([^'\"]+)['\"]", href)
                            if endpoint_match:
                                endpoint = endpoint_match.group(1)
                                
                                # Check if endpoint exists
                                if '.' in endpoint:
                                    blueprint_name, function_name = endpoint.split('.')
                                    blueprint = current_app.blueprints.get(blueprint_name)
                                    
                                    if not blueprint:
                                        issues.append({
                                            'template': rel_path,
                                            'type': 'invalid_blueprint_reference',
                                            'endpoint': endpoint,
                                            'severity': 'error'
                                        })
                                    elif not hasattr(blueprint, function_name):
                                        issues.append({
                                            'template': rel_path,
                                            'type': 'invalid_endpoint_reference',
                                            'endpoint': endpoint,
                                            'severity': 'error'
                                        })
                                else:
                                    # Check for non-blueprint endpoints
                                    if endpoint not in current_app.view_functions:
                                        issues.append({
                                            'template': rel_path,
                                            'type': 'invalid_endpoint_reference',
                                            'endpoint': endpoint,
                                            'severity': 'error'
                                        })
                    
                    # Check for include/extends tags
                    for tag in soup.find_all(['include', 'extends']):
                        template_ref = tag.get('src', tag.get('file', ''))
                        if template_ref and not os.path.exists(os.path.join(current_app.template_folder, template_ref)):
                            issues.append({
                                'template': rel_path,
                                'type': 'invalid_template_reference',
                                'reference': template_ref,
                                'severity': 'error'
                            })
                            
                    # Check for Jinja extends
                    extends_match = re.search(r"{%\s*extends\s+['\"]([^'\"]+)['\"]", template_content)
                    if extends_match:
                        extends_template = extends_match.group(1)
                        if not os.path.exists(os.path.join(current_app.template_folder, extends_template)):
                            issues.append({
                                'template': rel_path,
                                'type': 'invalid_extends_reference',
                                'reference': extends_template,
                                'severity': 'error'
                            })
                            
                    # Check for Jinja includes
                    for include_match in re.finditer(r"{%\s*include\s+['\"]([^'\"]+)['\"]", template_content):
                        include_template = include_match.group(1)
                        if not os.path.exists(os.path.join(current_app.template_folder, include_template)):
                            issues.append({
                                'template': rel_path,
                                'type': 'invalid_include_reference',
                                'reference': include_template,
                                'severity': 'error'
                            })
        
        # Determine status
        status = 'ok'
        if len(issues) > 0:
            status = 'critical'
            
        return {
            'name': 'template_references',
            'description': 'Check template references',
            'templates_checked': templates_checked,
            'issues': issues,
            'issues_count': len(issues),
            'status': status
        }
    except Exception as e:
        logger.error(f"Failed to check template references: {str(e)}")
        return {
            'name': 'template_references',
            'description': 'Check template references',
            'error': str(e),
            'issues_count': 1,
            'status': 'critical'
        }