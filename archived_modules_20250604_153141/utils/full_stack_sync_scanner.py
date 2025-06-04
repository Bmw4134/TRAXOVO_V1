"""
TRAXORA Full-Stack Sync Scanner

This tool scans the entire application to ensure proper synchronization between
backend routes and frontend UI elements, identifying any disconnects or issues.
"""

import os
import re
import logging
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullStackSyncScanner:
    """
    Scanner to ensure synchronization between backend routes and frontend templates
    """
    
    def __init__(self, app_root='.'):
        """
        Initialize the scanner with the application root directory
        
        Args:
            app_root (str): Root directory of the application
        """
        self.app_root = Path(app_root)
        self.routes_dir = self.app_root / 'routes'
        self.templates_dir = self.app_root / 'templates'
        
        # Track discovered routes and template references
        self.route_definitions = []
        self.template_references = defaultdict(list)
        self.conditional_blocks = []
        self.orphaned_routes = []
        self.orphaned_templates = []
        self.blueprint_registrations = []
        
    def extract_routes_from_file(self, file_path):
        """
        Extract route definitions from a Python file
        
        Args:
            file_path (Path): Path to the Python file
            
        Returns:
            list: List of route definitions
        """
        routes = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract route decorators
            route_pattern = r'@(?:\w+\.)?route\([\'"]([^\'"]+)[\'"](,\s*methods=\[.*?\])?\)'
            matches = re.finditer(route_pattern, content)
            
            blueprint_name = None
            blueprint_pattern = r'(\w+)\s*=\s*Blueprint\([\'"](\w+)[\'"]'
            blueprint_match = re.search(blueprint_pattern, content)
            if blueprint_match:
                blueprint_var = blueprint_match.group(1)
                blueprint_name = blueprint_match.group(2)
            
            for match in matches:
                route_path = match.group(1)
                methods = match.group(2) if match.group(2) else ", methods=['GET']"
                
                # Get the function name associated with this route
                function_name = None
                function_pattern = r'@(?:\w+\.)?route\([\'"]' + re.escape(route_path) + r'[\'"](,\s*methods=\[.*?\])?\)\s*\n\s*def\s+(\w+)'
                function_match = re.search(function_pattern, content)
                if function_match:
                    function_name = function_match.group(1)
                
                routes.append({
                    'path': route_path,
                    'methods': methods,
                    'function': function_name,
                    'blueprint': blueprint_name,
                    'file': str(file_path)
                })
                
            # Extract blueprint registrations
            if blueprint_name:
                self.blueprint_registrations.append({
                    'blueprint_var': blueprint_var,
                    'blueprint_name': blueprint_name,
                    'file': str(file_path)
                })
                
        except Exception as e:
            logger.error(f"Error extracting routes from {file_path}: {str(e)}")
            
        return routes
    
    def scan_backend_routes(self):
        """
        Scan all Python files in routes directory and main app file for route definitions
        """
        logger.info("Scanning backend routes...")
        
        # Check routes directory
        if self.routes_dir.exists():
            for file_path in self.routes_dir.glob('**/*.py'):
                routes = self.extract_routes_from_file(file_path)
                self.route_definitions.extend(routes)
                
        # Check app.py and main.py for routes
        for main_file in ['app.py', 'main.py']:
            main_path = self.app_root / main_file
            if main_path.exists():
                routes = self.extract_routes_from_file(main_path)
                self.route_definitions.extend(routes)
                
        logger.info(f"Found {len(self.route_definitions)} route definitions")
        
    def extract_url_references_from_template(self, file_path):
        """
        Extract URL references from a template file
        
        Args:
            file_path (Path): Path to the template file
            
        Returns:
            list: List of URL references
        """
        references = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all url_for references
            url_for_pattern = r'{{\s*url_for\([\'"]([^\'"]+)[\'"](,\s*.*?)?\)\s*}}'
            matches = re.finditer(url_for_pattern, content)
            
            for match in matches:
                endpoint = match.group(1)
                args = match.group(2) if match.group(2) else ""
                references.append({
                    'type': 'url_for',
                    'endpoint': endpoint,
                    'args': args.strip(', '),
                    'file': str(file_path)
                })
            
            # Find all href references to routes
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if href and not href.startswith(('http', 'https', 'mailto', '#', 'javascript', '{{')):
                    references.append({
                        'type': 'href',
                        'endpoint': href,
                        'text': a_tag.text.strip(),
                        'file': str(file_path)
                    })
            
            # Find all form actions
            for form in soup.find_all('form'):
                action = form.get('action')
                if action and not action.startswith(('http', 'https', '#', 'javascript', '{{')):
                    references.append({
                        'type': 'form',
                        'endpoint': action,
                        'method': form.get('method', 'GET'),
                        'file': str(file_path)
                    })
                    
            # Find conditional blocks that might hide UI elements
            if_blocks = re.finditer(r'{%\s*if\s+(.*?)\s*%}(.*?){%\s*endif\s*%}', content, re.DOTALL)
            for block in if_blocks:
                condition = block.group(1)
                block_content = block.group(2)
                if 'href' in block_content or 'url_for' in block_content:
                    self.conditional_blocks.append({
                        'condition': condition,
                        'file': str(file_path),
                        'content_preview': block_content[:100] + ('...' if len(block_content) > 100 else '')
                    })
                
        except Exception as e:
            logger.error(f"Error extracting URL references from {file_path}: {str(e)}")
            
        return references
    
    def scan_frontend_templates(self):
        """
        Scan all template files for URL references
        """
        logger.info("Scanning frontend templates...")
        
        if self.templates_dir.exists():
            for file_path in self.templates_dir.glob('**/*.html'):
                references = self.extract_url_references_from_template(file_path)
                for ref in references:
                    self.template_references[ref['endpoint']].append(ref)
                
        logger.info(f"Found references to {len(self.template_references)} distinct endpoints in templates")
        
    def analyze_sync_issues(self):
        """
        Analyze synchronization issues between backend routes and frontend templates
        """
        logger.info("Analyzing synchronization issues...")
        
        # Find orphaned routes (routes without UI references)
        for route in self.route_definitions:
            route_path = route['path']
            blueprint = route['blueprint']
            function = route['function']
            
            # Construct possible endpoint names
            possible_endpoints = [
                route_path,
                function,
                f"{blueprint}.{function}" if blueprint else function
            ]
            
            found = False
            for endpoint in possible_endpoints:
                if endpoint in self.template_references:
                    found = True
                    break
                    
            if not found:
                # Exclude common API routes that don't need UI references
                if not (route_path.startswith('/api/') or 
                        route_path.endswith('.json') or 
                        route_path.endswith('.xml') or
                        'health' in route_path.lower() or
                        'favicon.ico' in route_path):
                    self.orphaned_routes.append(route)
        
        # Find orphaned template references (UI references without routes)
        for endpoint, references in self.template_references.items():
            # Skip if it's not a direct route reference
            if endpoint.startswith(('static', 'http', 'https', '#', 'javascript')):
                continue
                
            found = False
            
            # Check if it's a direct route path match
            for route in self.route_definitions:
                if route['path'] == endpoint:
                    found = True
                    break
                    
            # Check if it's a blueprint.function_name reference
            if not found and '.' in endpoint:
                blueprint_name, function_name = endpoint.split('.', 1)
                for route in self.route_definitions:
                    if route['blueprint'] == blueprint_name and route['function'] == function_name:
                        found = True
                        break
            
            # Check if it's just a function name
            if not found:
                for route in self.route_definitions:
                    if route['function'] == endpoint:
                        found = True
                        break
                        
            if not found:
                self.orphaned_templates.append({
                    'endpoint': endpoint,
                    'references': references
                })
                
        logger.info(f"Found {len(self.orphaned_routes)} orphaned routes")
        logger.info(f"Found {len(self.orphaned_templates)} orphaned template references")
        logger.info(f"Found {len(self.conditional_blocks)} conditional blocks that might hide UI elements")
        
    def check_database_integrity(self):
        """
        Check for common database integrity issues
        """
        issues = []
        
        try:
            models_path = self.app_root / 'models.py'
            if not models_path.exists():
                # Try to find models in different locations
                possible_models = list(self.app_root.glob('**/models.py'))
                if possible_models:
                    models_path = possible_models[0]
                else:
                    return ["Models file not found. Unable to check database integrity."]
            
            with open(models_path, 'r') as f:
                content = f.read()
            
            # Check for relationship definitions without properly defined foreign keys
            rel_pattern = r'(\w+)\s*=\s*relationship\([\'"](\w+)[\'"]'
            rel_matches = re.finditer(rel_pattern, content)
            
            for match in rel_matches:
                rel_name = match.group(1)
                related_class = match.group(2)
                
                # Look for corresponding foreign key
                fk_pattern = r'(\w+)\s*=\s*Column\(.*?ForeignKey\([\'"].*?' + re.escape(related_class.lower()) + r'.*?[\'"]\)'
                if not re.search(fk_pattern, content, re.IGNORECASE):
                    issues.append(f"Relationship '{rel_name}' to '{related_class}' might be missing a properly defined foreign key.")
            
            # Check for db.Table declarations for many-to-many relationships
            table_pattern = r'(\w+)\s*=\s*Table\([\'"](\w+)[\'"]'
            table_matches = re.finditer(table_pattern, content)
            
            for match in rel_matches:
                table_var = match.group(1)
                table_name = match.group(2)
                
                # Check if the table has foreign keys defined
                fk_pattern = r'{}.*?ForeignKey\('.format(re.escape(table_var))
                if not re.search(fk_pattern, content, re.DOTALL):
                    issues.append(f"Association table '{table_name}' might be missing foreign key definitions.")
                    
        except Exception as e:
            issues.append(f"Error checking database integrity: {str(e)}")
            
        return issues
                
    def generate_report(self):
        """
        Generate a comprehensive report of synchronization issues
        
        Returns:
            dict: Report of synchronization issues
        """
        # Run all scans
        self.scan_backend_routes()
        self.scan_frontend_templates()
        self.analyze_sync_issues()
        
        # Check database integrity
        db_issues = self.check_database_integrity()
        
        return {
            'summary': {
                'total_routes': len(self.route_definitions),
                'total_endpoints_referenced': len(self.template_references),
                'orphaned_routes': len(self.orphaned_routes),
                'orphaned_templates': len(self.orphaned_templates),
                'conditional_blocks': len(self.conditional_blocks),
                'database_issues': len(db_issues)
            },
            'orphaned_routes': self.orphaned_routes,
            'orphaned_templates': self.orphaned_templates,
            'conditional_blocks': self.conditional_blocks,
            'blueprint_registrations': self.blueprint_registrations,
            'database_issues': db_issues
        }

def generate_html_report(report, output_file='sync_report.html'):
    """
    Generate an HTML report from the scanner results
    
    Args:
        report (dict): Scanner report
        output_file (str): Output HTML file path
        
    Returns:
        str: Path to the generated HTML report
    """
    # Determine card color based on issues
    has_issues = (report['summary']['orphaned_routes'] > 0 or 
                 report['summary']['orphaned_templates'] > 0 or 
                 report['summary']['database_issues'] > 0 or 
                 report['summary']['conditional_blocks'] > 0)
    issues_card_color = "bg-danger" if has_issues else "bg-success"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TRAXORA Full-Stack Sync Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .section {{ margin-bottom: 30px; }}
            .issue-card {{ margin-bottom: 15px; }}
            .code {{ font-family: monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1 class="mb-4">TRAXORA Full-Stack Sync Report</h1>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <h5 class="card-title">Total Routes</h5>
                            <p class="card-text display-4">{report['summary']['total_routes']}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white bg-success">
                        <div class="card-body">
                            <h5 class="card-title">Referenced Endpoints</h5>
                            <p class="card-text display-4">{report['summary']['total_endpoints_referenced']}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white {issues_card_color}">
                        <div class="card-body">
                            <h5 class="card-title">Sync Issues</h5>
                            <p class="card-text display-4">{report['summary']['orphaned_routes'] + report['summary']['orphaned_templates'] + report['summary']['database_issues'] + report['summary']['conditional_blocks']}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Orphaned Routes <span class="badge bg-warning">{report['summary']['orphaned_routes']}</span></h2>
                <p class="text-muted">These backend routes don't have matching UI elements. They may be API endpoints or need UI components.</p>
                
                <div class="accordion" id="orphanedRoutesAccordion">
    """
    
    for i, route in enumerate(report['orphaned_routes']):
        html += f"""
                    <div class="accordion-item issue-card">
                        <h2 class="accordion-header" id="orphanedRoute{i}Heading">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#orphanedRoute{i}Collapse" aria-expanded="false" aria-controls="orphanedRoute{i}Collapse">
                                <strong>{route['path']}</strong> <span class="ms-2 badge bg-secondary">{route['methods']}</span>
                            </button>
                        </h2>
                        <div id="orphanedRoute{i}Collapse" class="accordion-collapse collapse" aria-labelledby="orphanedRoute{i}Heading" data-bs-parent="#orphanedRoutesAccordion">
                            <div class="accordion-body">
                                <p><strong>Function:</strong> {route['function']}</p>
                                <p><strong>Blueprint:</strong> {route['blueprint'] or 'None'}</p>
                                <p><strong>File:</strong> {route['file']}</p>
                                <div class="alert alert-info">
                                    <strong>Solution:</strong> Add a UI element in a template file that references this route using url_for('{route['blueprint'] + "." + route['function'] if route['blueprint'] else route['function']}')
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2>Orphaned Template References <span class="badge bg-warning">{}</span></h2>
                <p class="text-muted">These UI elements reference endpoints that don't exist in the backend. They may be mistyped or need routes to be created.</p>
                
                <div class="accordion" id="orphanedTemplatesAccordion">
    """.format(report['summary']['orphaned_templates'])
    
    for i, template in enumerate(report['orphaned_templates']):
        html += f"""
                    <div class="accordion-item issue-card">
                        <h2 class="accordion-header" id="orphanedTemplate{i}Heading">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#orphanedTemplate{i}Collapse" aria-expanded="false" aria-controls="orphanedTemplate{i}Collapse">
                                <strong>{template['endpoint']}</strong> <span class="ms-2 badge bg-secondary">{len(template['references'])} references</span>
                            </button>
                        </h2>
                        <div id="orphanedTemplate{i}Collapse" class="accordion-collapse collapse" aria-labelledby="orphanedTemplate{i}Heading" data-bs-parent="#orphanedTemplatesAccordion">
                            <div class="accordion-body">
                                <h5>References:</h5>
                                <ul class="list-group mb-3">
        """
        
        for ref in template['references']:
            html += f"""
                                    <li class="list-group-item">
                                        <strong>Type:</strong> {ref['type']}
                                        <br><strong>File:</strong> {ref['file']}
                                        {f"<br><strong>Text:</strong> {ref['text']}" if 'text' in ref else ""}
                                    </li>
            """
            
        html += f"""
                                </ul>
                                <div class="alert alert-info">
                                    <strong>Solution:</strong> {'Create a route that handles this endpoint or correct the template reference if mistyped.' if '.' not in template['endpoint'] else f"Make sure the blueprint '{template['endpoint'].split('.')[0]}' is properly registered and has a function named '{template['endpoint'].split('.')[1]}'."}
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2>Conditional UI Elements <span class="badge bg-warning">{}</span></h2>
                <p class="text-muted">These UI elements are conditionally rendered and might be hidden under certain conditions.</p>
                
                <div class="accordion" id="conditionalBlocksAccordion">
    """.format(report['summary']['conditional_blocks'])
    
    for i, block in enumerate(report['conditional_blocks']):
        html += f"""
                    <div class="accordion-item issue-card">
                        <h2 class="accordion-header" id="conditionalBlock{i}Heading">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#conditionalBlock{i}Collapse" aria-expanded="false" aria-controls="conditionalBlock{i}Collapse">
                                <strong>Condition:</strong> {block['condition']}
                            </button>
                        </h2>
                        <div id="conditionalBlock{i}Collapse" class="accordion-collapse collapse" aria-labelledby="conditionalBlock{i}Heading" data-bs-parent="#conditionalBlocksAccordion">
                            <div class="accordion-body">
                                <p><strong>File:</strong> {block['file']}</p>
                                <div class="code">{block['content_preview']}</div>
                                <div class="alert alert-info mt-3">
                                    <strong>Recommendation:</strong> Ensure this conditional block is properly tested and users understand when this UI element is available.
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2>Database Integrity Issues <span class="badge bg-warning">{}</span></h2>
                <p class="text-muted">These issues might affect database relationships and proper model mapping.</p>
                
                <div class="accordion" id="databaseIssuesAccordion">
    """.format(report['summary']['database_issues'])
    
    for i, issue in enumerate(report['database_issues']):
        html += f"""
                    <div class="accordion-item issue-card">
                        <h2 class="accordion-header" id="databaseIssue{i}Heading">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#databaseIssue{i}Collapse" aria-expanded="false" aria-controls="databaseIssue{i}Collapse">
                                <strong>Issue #{i+1}</strong>
                            </button>
                        </h2>
                        <div id="databaseIssue{i}Collapse" class="accordion-collapse collapse" aria-labelledby="databaseIssue{i}Heading" data-bs-parent="#databaseIssuesAccordion">
                            <div class="accordion-body">
                                <div class="alert alert-warning">
                                    {issue}
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Write the HTML to a file
    static_dir = Path('static/reports')
    static_dir.mkdir(parents=True, exist_ok=True)
    
    static_path = static_dir / output_file
    with open(static_path, 'w') as f:
        f.write(html)
        
    report_path = Path(output_file)
    with open(report_path, 'w') as f:
        f.write(html)
        
    return {
        'file_path': str(report_path),
        'static_path': str(static_path),
        'url': f'/static/reports/{output_file}'
    }

def run_scan():
    """
    Run a full scan of the application
    
    Returns:
        dict: Report and file paths
    """
    scanner = FullStackSyncScanner()
    report = scanner.generate_report()
    html_report = generate_html_report(report)
    
    return {
        'report': report,
        'html_report': html_report
    }

if __name__ == '__main__':
    print("Running TRAXORA Full-Stack Sync Scanner...")
    results = run_scan()
    print(f"Scan complete. HTML report generated at {results['html_report']['file_path']}")
    print(f"Static report available at {results['html_report']['url']}")