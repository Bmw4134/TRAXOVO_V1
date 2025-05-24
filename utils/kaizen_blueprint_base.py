"""
TRAXORA Fleet Management System - Kaizen Blueprint Base

This module provides the base class for all Kaizen-managed blueprints,
ensuring proper registration and synchronization between routes and UI components.
"""

import os
import json
import inspect
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from flask import Blueprint, current_app
from bs4 import BeautifulSoup

from utils.kaizen_template_generator import extract_template_from_route, generate_template_for_route

logger = logging.getLogger(__name__)

class KaizenBlueprint(Blueprint):
    """
    Extended Blueprint class with built-in sync monitoring and auto-patching capabilities.
    """
    
    def __init__(self, name, import_name, **kwargs):
        """Initialize a Kaizen-managed blueprint with sync capabilities."""
        super().__init__(name, import_name, **kwargs)
        self.sync_registry_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kaizen_registry.json')
        self.register_with_kaizen()
        
    def register_with_kaizen(self):
        """Register this blueprint with the Kaizen monitoring system."""
        try:
            os.makedirs(os.path.dirname(self.sync_registry_path), exist_ok=True)
            
            if os.path.exists(self.sync_registry_path):
                with open(self.sync_registry_path, 'r') as f:
                    registry = json.load(f)
            else:
                registry = {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'blueprints': []
                }
                
            # Check if blueprint already registered
            for bp in registry['blueprints']:
                if bp['name'] == self.name:
                    # Blueprint already registered, update last_updated
                    bp['last_updated'] = datetime.now().isoformat()
                    break
            else:
                # Blueprint not registered, add it
                registry['blueprints'].append({
                    'name': self.name,
                    'import_name': self.import_name,
                    'registered': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'url_prefix': self.url_prefix,
                    'routes': []
                })
                
            # Update registry
            registry['last_updated'] = datetime.now().isoformat()
            with open(self.sync_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
                
            logger.info(f"Registered blueprint {self.name} with Kaizen sync system")
        except Exception as e:
            logger.error(f"Failed to register blueprint with Kaizen sync system: {str(e)}")
            
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
            # Register route with Kaizen sync system
            endpoint = options.pop('endpoint', None)
            if endpoint is None:
                endpoint = f.__name__
                
            self._update_registry_with_route(rule, endpoint, options)
            
            # Register route with Flask
            route_decorator = self.route(rule, **options)
            return route_decorator(f)
        return decorator
    
    def _update_registry_with_route(self, rule, function_name, options):
        """
        Update the Kaizen registry with a new route.
        
        Args:
            rule (str): The URL rule for the route
            function_name (str): The name of the route function
            options (dict): Additional options for the route
        """
        try:
            if os.path.exists(self.sync_registry_path):
                with open(self.sync_registry_path, 'r') as f:
                    registry = json.load(f)
                    
                # Find the blueprint
                for bp in registry['blueprints']:
                    if bp['name'] == self.name:
                        # Check if route already registered
                        for route in bp['routes']:
                            if route['rule'] == rule and route['function'] == function_name:
                                # Update existing entry
                                route['last_updated'] = datetime.now().isoformat()
                                route['methods'] = options.get('methods', ['GET'])
                                break
                        else:
                            # Add new entry
                            template = extract_template_from_route(getattr(self, function_name, None))
                            bp['routes'].append({
                                'rule': rule,
                                'function': function_name,
                                'registered': datetime.now().isoformat(),
                                'last_updated': datetime.now().isoformat(),
                                'methods': options.get('methods', ['GET']),
                                'template': template
                            })
                        break
                        
                # Update registry
                registry['last_updated'] = datetime.now().isoformat()
                with open(self.sync_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)
                    
                logger.debug(f"Updated registry with route {rule} -> {function_name}")
        except Exception as e:
            logger.error(f"Failed to update registry with route {rule} -> {function_name}: {str(e)}")
    
    def check_sync_status(self):
        """
        Check if all routes have corresponding templates and vice versa.
        
        Returns:
            dict: Sync status report
        """
        issues = []
        templates = []
        routes = []
        
        try:
            # Load registry
            if os.path.exists(self.sync_registry_path):
                with open(self.sync_registry_path, 'r') as f:
                    registry = json.load(f)
                    
                # Find the blueprint
                for bp in registry['blueprints']:
                    if bp['name'] == self.name:
                        # Check routes and templates
                        for route in bp['routes']:
                            routes.append(route)
                            
                            # Check if template exists
                            if route.get('template'):
                                template_path = os.path.join(current_app.template_folder, route['template'])
                                if not os.path.exists(template_path):
                                    issues.append({
                                        'type': 'missing_template',
                                        'route': route['rule'],
                                        'endpoint': route['function'],
                                        'template': route['template'],
                                        'severity': 'error'
                                    })
                            else:
                                # No template specified
                                issues.append({
                                    'type': 'no_template_specified',
                                    'route': route['rule'],
                                    'endpoint': route['function'],
                                    'severity': 'warning'
                                })
                        break
                        
                # Get all templates for this blueprint
                blueprint_template_dir = os.path.join(current_app.template_folder, self.name)
                if os.path.exists(blueprint_template_dir):
                    for root, _, files in os.walk(blueprint_template_dir):
                        for file in files:
                            if file.endswith('.html'):
                                rel_path = os.path.join(os.path.relpath(root, current_app.template_folder), file)
                                templates.append(rel_path)
                                
                                # Check if template is used by any route
                                template_used = False
                                for route in routes:
                                    if route.get('template') == rel_path:
                                        template_used = True
                                        break
                                        
                                if not template_used:
                                    issues.append({
                                        'type': 'unused_template',
                                        'template': rel_path,
                                        'severity': 'info'
                                    })
                
                # Check for template reference issues
                template_ref_issues = self._check_template_references()
                issues.extend(template_ref_issues)
                
            return {
                'blueprint': self.name,
                'routes_count': len(routes),
                'templates_count': len(templates),
                'issues_count': len(issues),
                'issues': issues,
                'status': 'ok' if len(issues) == 0 else 'issues_found'
            }
        except Exception as e:
            logger.error(f"Failed to check sync status: {str(e)}")
            return {
                'blueprint': self.name,
                'status': 'error',
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
            # Get all templates for this blueprint
            blueprint_template_dir = os.path.join(current_app.template_folder, self.name)
            if os.path.exists(blueprint_template_dir):
                for root, _, files in os.walk(blueprint_template_dir):
                    for file in files:
                        if file.endswith('.html'):
                            template_path = os.path.join(root, file)
                            
                            # Parse template
                            with open(template_path, 'r') as f:
                                template_content = f.read()
                                
                            # Check for url_for references
                            soup = BeautifulSoup(template_content, 'html.parser')
                            for a_tag in soup.find_all('a'):
                                href = a_tag.get('href', '')
                                if 'url_for' in href:
                                    # Extract endpoint
                                    import re
                                    endpoint_match = re.search(r"url_for\s*\(\s*['\"]([^'\"]+)['\"]", href)
                                    if endpoint_match:
                                        endpoint = endpoint_match.group(1)
                                        if endpoint.startswith(f"{self.name}."):
                                            # Check if endpoint exists
                                            function_name = endpoint.split('.')[-1]
                                            if not hasattr(self, function_name):
                                                issues.append({
                                                    'type': 'invalid_endpoint_reference',
                                                    'template': os.path.relpath(template_path, current_app.template_folder),
                                                    'endpoint': endpoint,
                                                    'severity': 'error'
                                                })
                            
                            # Check for invalid template includes
                            for include_tag in soup.find_all('include'):
                                src = include_tag.get('src', '')
                                if src.startswith(self.name + '/'):
                                    # Check if template exists
                                    include_path = os.path.join(current_app.template_folder, src)
                                    if not os.path.exists(include_path):
                                        issues.append({
                                            'type': 'invalid_include_reference',
                                            'template': os.path.relpath(template_path, current_app.template_folder),
                                            'include': src,
                                            'severity': 'error'
                                        })
        except Exception as e:
            logger.error(f"Failed to check template references: {str(e)}")
            
        return issues
        
    def auto_patch(self):
        """
        Attempt to automatically fix sync issues.
        
        Returns:
            dict: Auto-patch report
        """
        patched_issues = []
        
        # Get sync issues
        issues = self.check_sync_status()
        
        for issue in issues.get('issues', []):
            # Handle missing template issue
            if issue['type'] == 'missing_template':
                try:
                    # Create template using the generator
                    template_path = issue['template']
                    success = generate_template_for_route(
                        self.name, 
                        issue['route'], 
                        issue['endpoint'],
                        template_path
                    )
                    
                    if success:
                        patched_issues.append({
                            'type': 'missing_template',
                            'template': issue['template'],
                            'action': 'created',
                            'success': True
                        })
                    else:
                        patched_issues.append({
                            'type': 'missing_template',
                            'template': issue['template'],
                            'action': 'failed',
                            'error': 'Failed to generate template',
                            'success': False
                        })
                except Exception as e:
                    patched_issues.append({
                        'type': 'missing_template',
                        'template': issue['template'],
                        'action': 'failed',
                        'error': str(e),
                        'success': False
                    })
                    
            # Handle no template specified issue
            elif issue['type'] == 'no_template_specified':
                try:
                    # Update registry with template
                    if os.path.exists(self.sync_registry_path):
                        with open(self.sync_registry_path, 'r') as f:
                            registry = json.load(f)
                            
                        # Find the blueprint
                        for bp in registry['blueprints']:
                            if bp['name'] == self.name:
                                # Find the route
                                for route in bp['routes']:
                                    if route['rule'] == issue['route'] and route['function'] == issue['endpoint']:
                                        # Generate a template path
                                        template_path = f"{self.name}/{issue['endpoint']}.html"
                                        route['template'] = template_path
                                        
                                        # Create the template
                                        success = generate_template_for_route(
                                            self.name, 
                                            issue['route'], 
                                            issue['endpoint'],
                                            template_path
                                        )
                                        
                                        if success:
                                            # Update registry
                                            registry['last_updated'] = datetime.now().isoformat()
                                            with open(self.sync_registry_path, 'w') as f:
                                                json.dump(registry, f, indent=2)
                                                
                                            patched_issues.append({
                                                'type': 'no_template_specified',
                                                'route': issue['route'],
                                                'endpoint': issue['endpoint'],
                                                'template': template_path,
                                                'action': 'created',
                                                'success': True
                                            })
                                        else:
                                            patched_issues.append({
                                                'type': 'no_template_specified',
                                                'route': issue['route'],
                                                'endpoint': issue['endpoint'],
                                                'action': 'failed',
                                                'error': 'Failed to generate template',
                                                'success': False
                                            })
                                        break
                                break
                except Exception as e:
                    patched_issues.append({
                        'type': 'no_template_specified',
                        'route': issue['route'],
                        'endpoint': issue['endpoint'],
                        'action': 'failed',
                        'error': str(e),
                        'success': False
                    })
                    
        return {
            'blueprint': self.name,
            'patched_issues_count': len(patched_issues),
            'patched_issues': patched_issues,
            'status': 'ok' if len(patched_issues) > 0 else 'nothing_to_patch'
        }