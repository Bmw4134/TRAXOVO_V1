"""
TRAXORA Fleet Management System - Kaizen Blueprint Base

This module provides the base class for all Kaizen-managed blueprints,
ensuring proper registration and synchronization between routes and UI components.
"""

import os
import logging
import inspect
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KaizenBlueprint(Blueprint):
    """
    Extended Blueprint class with built-in sync monitoring and auto-patching capabilities.
    """
    
    def __init__(self, name, import_name, **kwargs):
        """Initialize a Kaizen-managed blueprint with sync capabilities."""
        super().__init__(name, import_name, **kwargs)
        self.kaizen_routes = []
        self.kaizen_templates = []
        self.sync_status = True
        self.auto_patch_enabled = True
        self.last_sync_time = datetime.now()
        
        # Register with the Kaizen system
        self.register_with_kaizen()
        
    def register_with_kaizen(self):
        """Register this blueprint with the Kaizen monitoring system."""
        try:
            # Create entry in Kaizen registry
            kaizen_registry_path = os.path.join('config', 'kaizen_registry.json')
            import json
            
            try:
                os.makedirs(os.path.dirname(kaizen_registry_path), exist_ok=True)
                
                if os.path.exists(kaizen_registry_path):
                    with open(kaizen_registry_path, 'r') as f:
                        registry = json.load(f)
                else:
                    registry = {'blueprints': []}
                    
                # Check if blueprint is already registered
                for bp in registry['blueprints']:
                    if bp['name'] == self.name:
                        # Update existing entry
                        bp['import_name'] = self.import_name
                        bp['last_updated'] = datetime.now().isoformat()
                        break
                else:
                    # Add new entry
                    registry['blueprints'].append({
                        'name': self.name,
                        'import_name': self.import_name,
                        'registered': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat(),
                        'url_prefix': self.url_prefix,
                        'routes': []
                    })
                    
                # Save registry
                with open(kaizen_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)
                    
                logger.info(f"Registered blueprint '{self.name}' with Kaizen system")
            except Exception as e:
                logger.error(f"Error registering blueprint '{self.name}' with Kaizen: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to register blueprint '{self.name}' with Kaizen: {str(e)}")
            
    def kaizen_route(self, rule, **options):
        """
        Decorator that registers a route with Kaizen sync monitoring.
        
        Args:
            rule (str): The URL rule for the route
            **options: Additional options to pass to the route decorator
            
        Returns:
            function: The decorated function
        """
        def decorator(f):
            # Register the route with Kaizen
            self.kaizen_routes.append({
                'rule': rule,
                'endpoint': options.get('endpoint', f.__name__),
                'function': f.__name__,
                'methods': options.get('methods', ['GET']),
                'template': self._extract_template_from_route(f)
            })
            
            # Register with the Kaizen registry
            self._update_registry_with_route(rule, f.__name__, options)
            
            # Apply the standard route decorator
            route_decorator = self.route(rule, **options)
            return route_decorator(f)
        return decorator
    
    def _extract_template_from_route(self, func):
        """
        Extract the template name from a route function by analyzing its source code.
        
        Args:
            func (function): The route function to analyze
            
        Returns:
            str: The template name or None if not found
        """
        try:
            source = inspect.getsource(func)
            import re
            
            # Look for render_template calls
            template_match = re.search(r"render_template\s*\(\s*['\"]([^'\"]+)['\"]", source)
            if template_match:
                return template_match.group(1)
                
            return None
        except Exception as e:
            logger.error(f"Error extracting template from route function: {str(e)}")
            return None
            
    def _update_registry_with_route(self, rule, function_name, options):
        """
        Update the Kaizen registry with a new route.
        
        Args:
            rule (str): The URL rule for the route
            function_name (str): The name of the route function
            options (dict): Additional options for the route
        """
        try:
            # Update the Kaizen registry
            kaizen_registry_path = os.path.join('config', 'kaizen_registry.json')
            import json
            
            if os.path.exists(kaizen_registry_path):
                with open(kaizen_registry_path, 'r') as f:
                    registry = json.load(f)
                    
                # Find the blueprint entry
                for bp in registry['blueprints']:
                    if bp['name'] == self.name:
                        # Check if route is already registered
                        for route in bp['routes']:
                            if route['rule'] == rule and route['function'] == function_name:
                                # Update existing entry
                                route['last_updated'] = datetime.now().isoformat()
                                route['methods'] = options.get('methods', ['GET'])
                                break
                        else:
                            # Add new entry
                            bp['routes'].append({
                                'rule': rule,
                                'function': function_name,
                                'registered': datetime.now().isoformat(),
                                'last_updated': datetime.now().isoformat(),
                                'methods': options.get('methods', ['GET']),
                                'template': self._extract_template_from_route(
                                    getattr(self, function_name, None) if hasattr(self, function_name) else None
                                )
                            })
                            
                        # Update blueprint entry
                        bp['last_updated'] = datetime.now().isoformat()
                        break
                        
                # Save registry
                with open(kaizen_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating registry with route: {str(e)}")
            
    def check_sync_status(self):
        """
        Check if all routes have corresponding templates and vice versa.
        
        Returns:
            dict: Sync status report
        """
        try:
            issues = []
            
            # Check all routes for corresponding templates
            for route in self.kaizen_routes:
                template = route.get('template')
                if template:
                    # Check if template file exists
                    template_path = os.path.join(current_app.template_folder, template)
                    if not os.path.exists(template_path):
                        issues.append({
                            'type': 'missing_template',
                            'route': route['rule'],
                            'template': template,
                            'severity': 'high'
                        })
                else:
                    # If no template is specified, check if the route function returns render_template
                    if hasattr(self, route['function']):
                        func = getattr(self, route['function'])
                        source = inspect.getsource(func)
                        if 'render_template' in source and not template:
                            issues.append({
                                'type': 'unregistered_template',
                                'route': route['rule'],
                                'function': route['function'],
                                'severity': 'medium'
                            })
                            
            # Check for invalid template references in the template folder
            template_issues = self._check_template_references()
            issues.extend(template_issues)
            
            # Update sync status
            self.sync_status = len(issues) == 0
            self.last_sync_time = datetime.now()
            
            return {
                'status': 'synced' if self.sync_status else 'issues',
                'blueprint': self.name,
                'timestamp': self.last_sync_time.isoformat(),
                'issues': issues,
                'routes_count': len(self.kaizen_routes),
                'templates_count': len(self.kaizen_templates)
            }
        except Exception as e:
            logger.error(f"Error checking sync status: {str(e)}")
            return {
                'status': 'error',
                'blueprint': self.name,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            
    def _check_template_references(self):
        """
        Check for invalid template references in template files.
        
        Returns:
            list: List of template reference issues
        """
        issues = []
        
        try:
            import re
            from bs4 import BeautifulSoup
            
            # Scan template folder for this blueprint
            blueprint_template_folder = os.path.join(current_app.template_folder, self.name)
            if os.path.exists(blueprint_template_folder):
                for root, dirs, files in os.walk(blueprint_template_folder):
                    for file in files:
                        if file.endswith('.html'):
                            template_path = os.path.join(root, file)
                            self.kaizen_templates.append(template_path)
                            
                            # Parse template file
                            with open(template_path, 'r') as f:
                                content = f.read()
                                
                            # Check for url_for references
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Look for Jinja2 expressions with url_for
                            url_for_matches = re.findall(r"url_for\s*\(\s*['\"]([^'\"]+)['\"]", content)
                            for match in url_for_matches:
                                # Check if the endpoint exists
                                if match.startswith(self.name + '.'):
                                    # Extract the endpoint name
                                    endpoint = match.split('.')[1]
                                    
                                    # Check if the endpoint is registered
                                    endpoint_exists = False
                                    for route in self.kaizen_routes:
                                        if route['endpoint'] == endpoint:
                                            endpoint_exists = True
                                            break
                                            
                                    if not endpoint_exists:
                                        issues.append({
                                            'type': 'invalid_endpoint_reference',
                                            'template': os.path.relpath(template_path, current_app.template_folder),
                                            'endpoint': match,
                                            'severity': 'high'
                                        })
        except Exception as e:
            logger.error(f"Error checking template references: {str(e)}")
            
        return issues
        
    def auto_patch(self):
        """
        Attempt to automatically fix sync issues.
        
        Returns:
            dict: Auto-patch report
        """
        if not self.auto_patch_enabled:
            return {
                'status': 'disabled',
                'blueprint': self.name,
                'timestamp': datetime.now().isoformat()
            }
            
        # Check sync status
        sync_status = self.check_sync_status()
        
        # If there are no issues, return success
        if sync_status['status'] == 'synced':
            return {
                'status': 'success',
                'blueprint': self.name,
                'timestamp': datetime.now().isoformat(),
                'message': 'No issues to patch'
            }
            
        # Auto-patch issues
        patched_issues = []
        
        for issue in sync_status['issues']:
            # Handle missing template issue
            if issue['type'] == 'missing_template':
                try:
                    # Create a basic template
                    template_path = os.path.join(current_app.template_folder, issue['template'])
                    os.makedirs(os.path.dirname(template_path), exist_ok=True)
                    
                    with open(template_path, 'w') as f:
                        f.write(f"""{% extends "base.html" %}

{% block title %}{self.name.capitalize()} - {issue['route'].capitalize()}{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>{issue['route'].capitalize()}</h1>
    <p>This page was auto-generated by Kaizen.</p>
</div>
{% endblock %}""")
                        
                    patched_issues.append({
                        'type': 'missing_template',
                        'template': issue['template'],
                        'action': 'created',
                        'success': True
                    })
                except Exception as e:
                    patched_issues.append({
                        'type': 'missing_template',
                        'template': issue['template'],
                        'action': 'failed',
                        'error': str(e),
                        'success': False
                    })
                    
            # Handle invalid endpoint reference
            elif issue['type'] == 'invalid_endpoint_reference':
                try:
                    # Find similar endpoints
                    similar_endpoints = []
                    endpoint = issue['endpoint'].split('.')[1] if '.' in issue['endpoint'] else issue['endpoint']
                    
                    for route in self.kaizen_routes:
                        # Calculate similarity score
                        from difflib import SequenceMatcher
                        similarity = SequenceMatcher(None, endpoint, route['endpoint']).ratio()
                        
                        if similarity > 0.7:
                            similar_endpoints.append({
                                'endpoint': f"{self.name}.{route['endpoint']}",
                                'similarity': similarity
                            })
                            
                    # Sort by similarity
                    similar_endpoints.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    if similar_endpoints:
                        # Update the template with the most similar endpoint
                        template_path = os.path.join(current_app.template_folder, issue['template'])
                        
                        with open(template_path, 'r') as f:
                            content = f.read()
                            
                        # Replace the invalid endpoint
                        import re
                        new_content = re.sub(
                            r"url_for\s*\(\s*['\"]" + re.escape(issue['endpoint']) + r"['\"]",
                            f"url_for('{similar_endpoints[0]['endpoint']}')",
                            content
                        )
                        
                        with open(template_path, 'w') as f:
                            f.write(new_content)
                            
                        patched_issues.append({
                            'type': 'invalid_endpoint_reference',
                            'template': issue['template'],
                            'old_endpoint': issue['endpoint'],
                            'new_endpoint': similar_endpoints[0]['endpoint'],
                            'action': 'updated',
                            'success': True
                        })
                    else:
                        patched_issues.append({
                            'type': 'invalid_endpoint_reference',
                            'template': issue['template'],
                            'endpoint': issue['endpoint'],
                            'action': 'skipped',
                            'reason': 'No similar endpoints found',
                            'success': False
                        })
                except Exception as e:
                    patched_issues.append({
                        'type': 'invalid_endpoint_reference',
                        'template': issue['template'],
                        'endpoint': issue['endpoint'],
                        'action': 'failed',
                        'error': str(e),
                        'success': False
                    })
                    
        # Check sync status again
        new_sync_status = self.check_sync_status()
        
        # Generate report
        return {
            'status': 'success' if new_sync_status['status'] == 'synced' else 'partial',
            'blueprint': self.name,
            'timestamp': datetime.now().isoformat(),
            'patched_issues': patched_issues,
            'remaining_issues': new_sync_status['issues'],
            'success_count': sum(1 for issue in patched_issues if issue['success']),
            'failure_count': sum(1 for issue in patched_issues if not issue['success'])
        }