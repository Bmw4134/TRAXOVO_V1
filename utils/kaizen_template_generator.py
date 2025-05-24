"""
TRAXORA Fleet Management System - Kaizen Template Generator

This module provides automated template generation for new routes,
ensuring UI consistency and reducing manual template creation.
"""

import os
import logging
import re
from datetime import datetime
import inspect
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TemplateGenerator:
    """Template generator for Kaizen blueprints"""
    
    @staticmethod
    def generate_template(blueprint_name, route_name, route_function=None):
        """
        Generate a template for a route
        
        Args:
            blueprint_name (str): Name of the blueprint
            route_name (str): Name of the route (endpoint)
            route_function (function, optional): The route function
            
        Returns:
            str: Path to the generated template
        """
        try:
            # Determine template directory
            template_dir = os.path.join(current_app.template_folder, blueprint_name)
            os.makedirs(template_dir, exist_ok=True)
            
            # Determine template name
            template_name = f"{route_name}.html"
            template_path = os.path.join(template_dir, template_name)
            
            # Check if template already exists
            if os.path.exists(template_path):
                logger.info(f"Template already exists: {template_path}")
                return template_path
                
            # Generate template content
            content = TemplateGenerator._generate_template_content(blueprint_name, route_name, route_function)
            
            # Write template file
            with open(template_path, 'w') as f:
                f.write(content)
                
            logger.info(f"Template generated: {template_path}")
            
            # Log the template generation
            TemplateGenerator._log_template_generation(blueprint_name, route_name, template_path)
            
            return template_path
        except Exception as e:
            logger.error(f"Error generating template for {blueprint_name}.{route_name}: {str(e)}")
            return None
            
    @staticmethod
    def _generate_template_content(blueprint_name, route_name, route_function=None):
        """
        Generate the content for a template
        
        Args:
            blueprint_name (str): Name of the blueprint
            route_name (str): Name of the route (endpoint)
            route_function (function, optional): The route function
            
        Returns:
            str: Template content
        """
        # Extract docstring from route function
        title = route_name.replace('_', ' ').title()
        description = ""
        
        if route_function:
            docstring = inspect.getdoc(route_function)
            if docstring:
                # Use the first line of the docstring as title if available
                lines = docstring.strip().split('\n')
                if lines:
                    title = lines[0].strip()
                    if len(lines) > 1:
                        description = '\n'.join(lines[1:]).strip()
        
        # Format the template title for display
        display_title = title
        if display_title.endswith("dashboard"):
            display_title = display_title.replace("dashboard", "").strip() + " Dashboard"
            
        # Generate sidebar content for this blueprint
        sidebar_content = TemplateGenerator._generate_sidebar_content(blueprint_name)
                
        # Generate template content
        return f"""{% extends "base.html" %}

{% block title %}{display_title} - TRAXORA{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-3 col-lg-2 d-md-block bg-dark sidebar collapse" id="sidebarMenu">
            <div class="position-sticky pt-3">
                <ul class="nav flex-column">
                    {sidebar_content}
                </ul>
            </div>
        </div>
        
        <!-- Main content -->
        <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">{display_title}</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <div class="btn-group me-2">
                        <button type="button" class="btn btn-sm btn-outline-secondary">Share</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary">Export</button>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle">
                        <span data-feather="calendar"></span>
                        This week
                    </button>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Overview</h5>
                        </div>
                        <div class="card-body">
                            <p class="card-text">{description if description else "Welcome to the " + display_title + " page."}</p>
                            <p class="card-text text-muted">Auto-generated by Kaizen on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="list-group">
                                <a href="#" class="list-group-item list-group-item-action">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">Action 1</h5>
                                        <small class="text-muted">Now</small>
                                    </div>
                                    <p class="mb-1">Example action button with description.</p>
                                </a>
                                <a href="#" class="list-group-item list-group-item-action">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">Action 2</h5>
                                        <small class="text-muted">Today</small>
                                    </div>
                                    <p class="mb-1">Another example action button.</p>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Status</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <h6>System Health</h6>
                                <div class="progress mb-2">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">100%</div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <h6>Database Status</h6>
                                <div class="progress mb-2">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">100%</div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <h6>API Health</h6>
                                <div class="progress mb-2">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">100%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Page loaded: {blueprint_name}.{route_name}');
    });
</script>
{% endblock %}"""
    
    @staticmethod
    def _generate_sidebar_content(blueprint_name):
        """
        Generate sidebar content for a blueprint
        
        Args:
            blueprint_name (str): Name of the blueprint
            
        Returns:
            str: Sidebar content
        """
        # Get all routes for this blueprint
        blueprint_routes = []
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint.startswith(f"{blueprint_name}."):
                endpoint = rule.endpoint.split('.')[1]
                if endpoint != 'static':  # Skip static routes
                    blueprint_routes.append({
                        'endpoint': endpoint,
                        'url': rule.rule
                    })
                
        # Generate sidebar items
        sidebar_items = []
        for route in blueprint_routes:
            display_name = route['endpoint'].replace('_', ' ').title()
            endpoint = f"{blueprint_name}.{route['endpoint']}"
            sidebar_items.append(f"""<li class="nav-item">
                        <a class="nav-link{% if request.endpoint == '{endpoint}' %} active{% endif %}" href="{{ url_for('{endpoint}') }}">
                            <i class="bi bi-circle"></i>
                            {display_name}
                        </a>
                    </li>""")
                
        return '\n                    '.join(sidebar_items)
    
    @staticmethod
    def _log_template_generation(blueprint_name, route_name, template_path):
        """
        Log template generation to the Kaizen history
        
        Args:
            blueprint_name (str): Name of the blueprint
            route_name (str): Name of the route (endpoint)
            template_path (str): Path to the generated template
        """
        try:
            from utils.kaizen_sync_history import SyncHistory
            
            # Create history entry
            SyncHistory.add_entry(
                event_type='template_generation',
                blueprint=blueprint_name,
                endpoint=route_name,
                details={
                    'template_path': template_path,
                    'generated_at': datetime.now().isoformat(),
                    'auto_generated': True
                }
            )
        except Exception as e:
            logger.error(f"Error logging template generation: {str(e)}")