"""
TRAXORA Kaizen Integrity Audit

This module performs comprehensive integrity audits on the full application stack,
ensuring route/template consistency and identifying any disconnects between
frontend and backend elements.
"""

import os
import re
import logging
import importlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KaizenIntegrityAudit:
    """
    Performs comprehensive integrity audits on the TRAXORA application
    to ensure frontend/backend synchronization.
    """
    
    def __init__(self, app_root='.'):
        """
        Initialize the integrity audit with the application root directory.
        
        Args:
            app_root (str): Root directory of the application
        """
        self.app_root = Path(app_root)
        self.routes_dir = self.app_root / 'routes'
        self.templates_dir = self.app_root / 'templates'
        self.main_app_file = self.app_root / 'main.py'
        self.app_file = self.app_root / 'app.py'
        
        # Tracking containers
        self.routes = []
        self.blueprints = []
        self.templates = []
        self.template_references = []
        self.orphaned_routes = []
        self.orphaned_templates = []
        self.conditional_elements = []
        self.integrity_issues = []
        
    def scan_routes(self):
        """
        Scan all Python files in routes directory and main app files for route definitions.
        """
        logger.info("Scanning route definitions...")
        
        # Process route files
        if self.routes_dir.exists():
            for file_path in self.routes_dir.glob('**/*.py'):
                self._process_route_file(file_path)
                
        # Process main app files
        for app_file in [self.main_app_file, self.app_file]:
            if app_file.exists():
                self._process_route_file(app_file)
                
        logger.info(f"Found {len(self.routes)} routes and {len(self.blueprints)} blueprints")
        
    def _process_route_file(self, file_path):
        """
        Process a Python file to extract route and blueprint definitions.
        
        Args:
            file_path (Path): Path to the Python file
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract blueprint definitions
            blueprint_pattern = r'(\w+)\s*=\s*Blueprint\([\'"](\w+)[\'"],\s*[\'"]([^\'"]*)[\'"]'
            for match in re.finditer(blueprint_pattern, content):
                var_name = match.group(1)
                blueprint_name = match.group(2)
                url_prefix = match.group(3)
                
                self.blueprints.append({
                    'var_name': var_name,
                    'name': blueprint_name,
                    'url_prefix': url_prefix,
                    'file': str(file_path)
                })
                
            # Extract route definitions
            route_patterns = [
                # Blueprint routes: @blueprint.route('/path')
                r'@(\w+)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[(.*?)\])?\)',
                # App routes: @app.route('/path')
                r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[(.*?)\])?\)'
            ]
            
            for pattern in route_patterns:
                for match in re.finditer(pattern, content):
                    if pattern.startswith('@app'):
                        # App route
                        path = match.group(1)
                        methods = match.group(2) if match.group(2) else 'GET'
                        blueprint = None
                        
                        # Get the function name
                        func_match = re.search(rf'{re.escape(match.group(0))}\s*\ndef\s+(\w+)', content)
                        function_name = func_match.group(1) if func_match else None
                        
                        self.routes.append({
                            'path': path,
                            'methods': methods,
                            'blueprint': None,
                            'function': function_name,
                            'file': str(file_path)
                        })
                    else:
                        # Blueprint route
                        blueprint_var = match.group(1)
                        path = match.group(2)
                        methods = match.group(3) if match.group(3) else 'GET'
                        
                        # Get the function name
                        func_match = re.search(rf'{re.escape(match.group(0))}\s*\ndef\s+(\w+)', content)
                        function_name = func_match.group(1) if func_match else None
                        
                        # Find the blueprint name
                        blueprint_name = None
                        for bp in self.blueprints:
                            if bp['var_name'] == blueprint_var:
                                blueprint_name = bp['name']
                                break
                                
                        self.routes.append({
                            'path': path,
                            'methods': methods,
                            'blueprint': blueprint_name,
                            'blueprint_var': blueprint_var,
                            'function': function_name,
                            'file': str(file_path)
                        })
                        
        except Exception as e:
            logger.error(f"Error processing route file {file_path}: {str(e)}")
            
    def scan_templates(self):
        """
        Scan all template files for URL references and conditional elements.
        """
        logger.info("Scanning template files...")
        
        if self.templates_dir.exists():
            for file_path in self.templates_dir.glob('**/*.html'):
                self._process_template_file(file_path)
                
        logger.info(f"Found {len(self.template_references)} template references and {len(self.conditional_elements)} conditional elements")
        
    def _process_template_file(self, file_path):
        """
        Process a template file to extract URL references and conditional elements.
        
        Args:
            file_path (Path): Path to the template file
        """
        try:
            self.templates.append(str(file_path))
            
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract url_for references
            url_for_pattern = r'{{\s*url_for\([\'"]([^\'"]+)[\'"]'
            for match in re.finditer(url_for_pattern, content):
                endpoint = match.group(1)
                
                self.template_references.append({
                    'type': 'url_for',
                    'endpoint': endpoint,
                    'file': str(file_path)
                })
                
            # Extract direct href references
            soup = BeautifulSoup(content, 'html.parser')
            
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if href and not href.startswith(('http', 'https', 'mailto', '#', 'javascript')):
                    if not href.startswith('{{'):  # Skip template variables
                        self.template_references.append({
                            'type': 'href',
                            'endpoint': href,
                            'text': a_tag.text.strip(),
                            'file': str(file_path)
                        })
                        
            # Extract form actions
            for form in soup.find_all('form'):
                action = form.get('action')
                if action and not action.startswith(('http', 'https', '#', 'javascript')):
                    if not action.startswith('{{'):  # Skip template variables
                        self.template_references.append({
                            'type': 'form',
                            'endpoint': action,
                            'method': form.get('method', 'GET'),
                            'file': str(file_path)
                        })
                        
            # Find conditional elements
            if_blocks = re.finditer(r'{%\s*if\s+(.*?)\s*%}(.*?){%\s*endif\s*%}', content, re.DOTALL)
            for block in if_blocks:
                condition = block.group(1)
                block_content = block.group(2)
                
                # Check if the conditional block contains links or UI elements
                if ('href' in block_content or 'url_for' in block_content or 
                    'button' in block_content or 'form' in block_content):
                    self.conditional_elements.append({
                        'condition': condition,
                        'preview': block_content[:100] + ('...' if len(block_content) > 100 else ''),
                        'file': str(file_path)
                    })
                    
        except Exception as e:
            logger.error(f"Error processing template file {file_path}: {str(e)}")
            
    def analyze_integrity(self):
        """
        Analyze the collected data to identify integrity issues.
        """
        logger.info("Analyzing application integrity...")
        
        # Find orphaned routes (routes without UI references)
        for route in self.routes:
            path = route['path']
            blueprint = route['blueprint']
            function = route['function']
            
            # Skip static files, health checks, and API routes
            if any(skip in path.lower() for skip in ['/static', '/health', '/api']):
                continue
                
            # Construct possible endpoint references
            possible_refs = []
            
            # Direct path reference
            possible_refs.append(path)
            
            # Function name reference
            if function:
                possible_refs.append(function)
                
            # Blueprint function reference
            if blueprint and function:
                possible_refs.append(f"{blueprint}.{function}")
                
            # Check if any reference exists in templates
            found = False
            for ref in self.template_references:
                if ref['endpoint'] in possible_refs:
                    found = True
                    break
                    
            if not found:
                self.orphaned_routes.append(route)
                
        # Find orphaned template references (references without routes)
        for ref in self.template_references:
            endpoint = ref['endpoint']
            
            # Skip external links, static files
            if endpoint.startswith(('/', 'http', 'https', 'static')):
                continue
                
            # Check if it's a blueprint.function reference
            if '.' in endpoint:
                parts = endpoint.split('.')
                blueprint_name = parts[0]
                function_name = parts[1]
                
                # Find matching route
                found = False
                for route in self.routes:
                    if route['blueprint'] == blueprint_name and route['function'] == function_name:
                        found = True
                        break
                        
                if not found:
                    self.orphaned_templates.append(ref)
            else:
                # Check if it's a direct function name reference
                found = False
                for route in self.routes:
                    if route['function'] == endpoint:
                        found = True
                        break
                        
                if not found:
                    self.orphaned_templates.append(ref)
                    
        # Check for other integrity issues
        self._check_blueprint_registration()
        self._check_database_relationships()
                    
        logger.info(f"Found {len(self.orphaned_routes)} orphaned routes and {len(self.orphaned_templates)} orphaned template references")
        
    def _check_blueprint_registration(self):
        """
        Check if all blueprints are properly registered in the main application.
        """
        try:
            if not self.main_app_file.exists():
                return
                
            with open(self.main_app_file, 'r') as f:
                content = f.read()
                
            for blueprint in self.blueprints:
                bp_name = blueprint['name']
                bp_var = blueprint['var_name']
                
                # Check if the blueprint is registered
                register_pattern = rf'app\.register_blueprint\({bp_var}|.*{bp_name}.*register'
                if not re.search(register_pattern, content):
                    self.integrity_issues.append({
                        'type': 'blueprint_not_registered',
                        'message': f"Blueprint '{bp_name}' ({bp_var}) defined in {blueprint['file']} is not registered in main.py",
                        'severity': 'error'
                    })
                    
        except Exception as e:
            logger.error(f"Error checking blueprint registration: {str(e)}")
            
    def _check_database_relationships(self):
        """
        Check database relationships for integrity issues.
        """
        # Find all model files
        model_files = list(self.app_root.glob('**/models.py'))
        if not model_files:
            return
            
        try:
            for model_file in model_files:
                with open(model_file, 'r') as f:
                    content = f.read()
                    
                # Find relationship definitions
                rel_pattern = r'(\w+)\s*=\s*(?:db\.relationship|relationship)\([\'"](\w+)[\'"]'
                rel_matches = re.finditer(rel_pattern, content)
                
                for match in rel_matches:
                    rel_name = match.group(1)
                    related_class = match.group(2)
                    
                    # Look for foreign key definition
                    fk_pattern = r'(\w+)\s*=\s*(?:db\.Column|Column)\(.*?ForeignKey\([\'"].*?' + re.escape(related_class.lower()) + r'.*?[\'"]\)'
                    if not re.search(fk_pattern, content, re.IGNORECASE):
                        self.integrity_issues.append({
                            'type': 'relationship_no_foreign_key',
                            'message': f"Relationship '{rel_name}' to '{related_class}' in {model_file} might be missing a properly defined foreign key",
                            'severity': 'warning'
                        })
                        
        except Exception as e:
            logger.error(f"Error checking database relationships: {str(e)}")
            
    def generate_report(self):
        """
        Generate a comprehensive report of the integrity audit.
        
        Returns:
            dict: Audit report
        """
        # Run all scans and analysis
        self.scan_routes()
        self.scan_templates()
        self.analyze_integrity()
        
        # Generate report
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_routes': len(self.routes),
                'total_blueprints': len(self.blueprints),
                'total_templates': len(self.templates),
                'total_template_references': len(self.template_references),
                'orphaned_routes': len(self.orphaned_routes),
                'orphaned_templates': len(self.orphaned_templates),
                'conditional_elements': len(self.conditional_elements),
                'integrity_issues': len(self.integrity_issues)
            },
            'routes': self.routes,
            'blueprints': self.blueprints,
            'orphaned_routes': self.orphaned_routes,
            'orphaned_templates': self.orphaned_templates,
            'conditional_elements': self.conditional_elements,
            'integrity_issues': self.integrity_issues
        }
        
        # Determine overall integrity status
        if (len(self.orphaned_routes) == 0 and 
            len(self.orphaned_templates) == 0 and 
            not any(issue['severity'] == 'error' for issue in self.integrity_issues)):
            report['status'] = 'PASS'
        else:
            report['status'] = 'FAIL'
            
        return report

def run_integrity_audit(app_root='.'):
    """
    Run a complete integrity audit and return the report.
    
    Args:
        app_root (str): Root directory of the application
        
    Returns:
        dict: Audit report
    """
    logger.info("Starting Kaizen Integrity Audit...")
    audit = KaizenIntegrityAudit(app_root)
    report = audit.generate_report()
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"integrity_audit_{timestamp}.json"
    
    import json
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Audit report saved to {report_file}")
    except Exception as e:
        logger.error(f"Error saving audit report: {str(e)}")
        
    return report

if __name__ == '__main__':
    run_integrity_audit()