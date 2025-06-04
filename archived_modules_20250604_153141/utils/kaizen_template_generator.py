"""
TRAXORA Fleet Management System - Kaizen Template Generator

This module provides utilities for automatically generating templates for routes
that don't have corresponding templates.
"""

import os
import re
import inspect
import logging
from typing import Dict, List, Optional, Any, Union

from flask import Blueprint, current_app

from utils.kaizen_sync_history import add_history_entry

logger = logging.getLogger(__name__)

def generate_template_for_route(blueprint_name, route_name, endpoint_name, template_path):
    """
    Generate a template for a route that doesn't have a corresponding template.
    
    Args:
        blueprint_name (str): Name of the blueprint
        route_name (str): Name of the route
        endpoint_name (str): Name of the endpoint function
        template_path (str): Path to the template
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure template directory exists
        template_dir = os.path.dirname(os.path.join(current_app.template_folder, template_path))
        os.makedirs(template_dir, exist_ok=True)
        
        # Get the blueprint object
        blueprint = current_app.blueprints.get(blueprint_name)
        
        if not blueprint:
            logger.error(f"Blueprint {blueprint_name} not found")
            return False
            
        # Get the endpoint function
        endpoint_func = getattr(blueprint, endpoint_name, None)
        
        if not endpoint_func:
            logger.error(f"Endpoint {endpoint_name} not found in blueprint {blueprint_name}")
            return False
            
        # Get the function source code to extract title
        try:
            source = inspect.getsource(endpoint_func)
            title_match = re.search(r'"""(.+?)"""', source, re.DOTALL)
            title = title_match.group(1).strip() if title_match else f"{endpoint_name.replace('_', ' ').title()}"
        except Exception:
            title = f"{endpoint_name.replace('_', ' ').title()}"
            
        # Generate template content
        content = generate_admin_template(template_path, title)
        
        # Write template to file
        with open(os.path.join(current_app.template_folder, template_path), 'w') as f:
            f.write(content)
            
        # Log success
        logger.info(f"Generated template {template_path} for route {route_name}")
        
        # Add to history
        add_history_entry(
            'template_generation',
            'success',
            f"Generated template {template_path} for route {route_name}",
            {
                'blueprint': blueprint_name,
                'route': route_name,
                'endpoint': endpoint_name,
                'template': template_path
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to generate template: {str(e)}")
        
        # Add to history
        add_history_entry(
            'template_generation',
            'error',
            f"Failed to generate template {template_path} for route {route_name}",
            {
                'blueprint': blueprint_name,
                'route': route_name,
                'endpoint': endpoint_name,
                'template': template_path,
                'error': str(e)
            }
        )
        
        return False

def generate_admin_template(template_path, title, content_blocks=None):
    """
    Generate an admin template with the Kaizen theme.
    
    Args:
        template_path (str): Path to the template
        title (str): Title of the page
        content_blocks (list): List of content blocks to include
        
    Returns:
        str: The generated template content
    """
    # Determine if this is a blueprint template
    blueprint_name = os.path.dirname(template_path).split(os.path.sep)[0] if os.path.sep in template_path else ''
    
    # Build template content
    content = "{% extends \"base.html\" %}\n\n"
    content += f"{{% block title %}}{title}{{%  endblock %}}\n\n"
    content += "{% block content %}\n"
    content += "<div class=\"container-fluid mt-4\">\n"
    content += "    <div class=\"row\">\n"
    
    # Add sidebar if this is a blueprint template
    if blueprint_name:
        content += "        <div class=\"col-md-3\">\n"
        content += "            <!-- Sidebar -->\n"
        content += "            <div class=\"card mb-4\">\n"
        content += f"                <div class=\"card-header\">\n"
        content += f"                    <h5 class=\"mb-0\">{blueprint_name.replace('_', ' ').title()}</h5>\n"
        content += "                </div>\n"
        content += "                <div class=\"card-body p-0\">\n"
        content += "                    <div class=\"list-group list-group-flush\">\n"
        
        # Try to add sidebar links based on the blueprint routes
        try:
            blueprint = current_app.blueprints.get(blueprint_name)
            if blueprint:
                for rule in current_app.url_map.iter_rules():
                    if rule.endpoint.startswith(f"{blueprint_name}."):
                        endpoint = rule.endpoint.split('.')[-1]
                        endpoint_title = endpoint.replace('_', ' ').title()
                        
                        if endpoint == 'index':
                            endpoint_title = 'Dashboard'
                            
                        is_active = f"{blueprint_name}/{endpoint}" in template_path
                        active_class = ' active' if is_active else ''
                        
                        content += f"                        <a href=\"{{{{ url_for('{rule.endpoint}') }}}}\" class=\"list-group-item list-group-item-action{active_class}\">\n"
                        content += f"                            <i class=\"bi bi-{get_icon_for_endpoint(endpoint)} me-2\"></i> {endpoint_title}\n"
                        content += "                        </a>\n"
        except Exception:
            # Fallback to basic sidebar
            content += f"                        <a href=\"{{{{ url_for('{blueprint_name}.index') }}}}\" class=\"list-group-item list-group-item-action active\">\n"
            content += f"                            <i class=\"bi bi-speedometer2 me-2\"></i> Dashboard\n"
            content += "                        </a>\n"
            
        content += "                    </div>\n"
        content += "                </div>\n"
        content += "            </div>\n"
        content += "        </div>\n"
        
        content += "        <div class=\"col-md-9\">\n"
    else:
        content += "        <div class=\"col-md-12\">\n"
        
    # Add main content
    content += "            <!-- Main Content -->\n"
    content += "            <div class=\"card mb-4\">\n"
    content += "                <div class=\"card-header\">\n"
    content += f"                    <h5 class=\"mb-0\">{title}</h5>\n"
    content += "                </div>\n"
    content += "                <div class=\"card-body\">\n"
    
    # Add content blocks
    if content_blocks:
        for block in content_blocks:
            content += f"                    {block}\n"
    else:
        content += "                    <!-- Page content goes here -->\n"
        content += "                    <p>This is an auto-generated template. Customize it as needed.</p>\n"
        
    content += "                </div>\n"
    content += "            </div>\n"
    content += "        </div>\n"
    content += "    </div>\n"
    content += "</div>\n"
    content += "{% endblock %}"
    
    return content

def extract_template_from_route(func):
    """
    Extract the template name from a route function by analyzing its source code.
    
    Args:
        func (function): The route function to analyze
        
    Returns:
        str: The template name or None if not found
    """
    try:
        source = inspect.getsource(func)
        
        # Check for render_template calls
        template_match = re.search(r"render_template\s*\(\s*['\"]([^'\"]+)['\"]", source)
        if template_match:
            return template_match.group(1)
            
        return None
    except Exception:
        return None

def get_icon_for_endpoint(endpoint):
    """
    Get an appropriate Bootstrap icon for an endpoint.
    
    Args:
        endpoint (str): Name of the endpoint
        
    Returns:
        str: Name of the Bootstrap icon
    """
    # Map common endpoint names to icons
    icon_map = {
        'index': 'speedometer2',
        'dashboard': 'speedometer2',
        'list': 'list-ul',
        'create': 'plus-circle',
        'edit': 'pencil-square',
        'delete': 'trash',
        'view': 'eye',
        'detail': 'file-text',
        'report': 'bar-chart',
        'upload': 'upload',
        'download': 'download',
        'settings': 'gear',
        'profile': 'person',
        'users': 'people',
        'search': 'search',
        'login': 'box-arrow-in-right',
        'logout': 'box-arrow-right',
        'admin': 'shield',
        'history': 'clock-history',
        'sync': 'arrow-repeat',
        'templates': 'file-earmark-code',
        'run_checks': 'shield-check',
        'integrity_check': 'shield-check',
        'auto_generate': 'magic',
        'generate': 'magic',
        'start': 'play-circle',
        'stop': 'stop-circle',
        'api': 'code-slash'
    }
    
    # Check for direct matches
    if endpoint in icon_map:
        return icon_map[endpoint]
        
    # Check for partial matches
    for key, icon in icon_map.items():
        if key in endpoint:
            return icon
            
    # Return a default icon
    return 'circle'