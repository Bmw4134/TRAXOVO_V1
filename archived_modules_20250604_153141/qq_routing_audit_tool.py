"""
QQ Routing Audit Tool
Comprehensive analysis and cleanup of duplicate routes and conflicts
"""

import os
import re
import json
from typing import Dict, List, Set, Tuple
from datetime import datetime
import logging

class QQRoutingAuditor:
    """
    Comprehensive routing audit and cleanup tool
    Identifies duplicates, conflicts, and optimization opportunities
    """
    
    def __init__(self):
        self.app_files = ['app.py', 'app_working.py', 'app_clean.py', 'app_core.py', 'main_deploy.py']
        self.routes_found = {}
        self.duplicates = []
        self.conflicts = []
        self.recommendations = []
        
    def audit_all_routes(self) -> Dict[str, any]:
        """Comprehensive routing audit"""
        print("🔍 Starting QQ Routing Audit...")
        
        # Scan all app files
        for app_file in self.app_files:
            if os.path.exists(app_file):
                self._scan_file_routes(app_file)
        
        # Analyze findings
        self._analyze_duplicates()
        self._analyze_conflicts()
        self._generate_recommendations()
        
        return self._generate_audit_report()
    
    def _scan_file_routes(self, filename: str):
        """Scan a file for Flask routes"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
                
            # Find all @app.route decorators
            route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"
            function_pattern = r"def\s+(\w+)\("
            
            lines = content.split('\n')
            current_routes = []
            
            for i, line in enumerate(lines):
                route_match = re.search(route_pattern, line)
                if route_match:
                    route_path = route_match.group(1)
                    methods = route_match.group(2) if route_match.group(2) else "['GET']"
                    current_routes.append({
                        'path': route_path,
                        'methods': methods,
                        'line': i + 1
                    })
                
                # Check for function definition after route
                if current_routes:
                    func_match = re.search(function_pattern, line)
                    if func_match:
                        function_name = func_match.group(1)
                        for route in current_routes:
                            route_key = f"{route['path']}:{route['methods']}"
                            
                            if route_key not in self.routes_found:
                                self.routes_found[route_key] = []
                            
                            self.routes_found[route_key].append({
                                'file': filename,
                                'function': function_name,
                                'line': route['line'],
                                'path': route['path'],
                                'methods': route['methods']
                            })
                        current_routes = []
                        
        except Exception as e:
            logging.error(f"Error scanning {filename}: {e}")
    
    def _analyze_duplicates(self):
        """Identify duplicate routes"""
        for route_key, instances in self.routes_found.items():
            if len(instances) > 1:
                self.duplicates.append({
                    'route': route_key,
                    'instances': instances,
                    'count': len(instances)
                })
    
    def _analyze_conflicts(self):
        """Identify potential conflicts"""
        # Group by path only (ignoring methods)
        path_groups = {}
        for route_key, instances in self.routes_found.items():
            path = instances[0]['path']
            if path not in path_groups:
                path_groups[path] = []
            path_groups[path].extend(instances)
        
        # Check for conflicts
        for path, instances in path_groups.items():
            if len(instances) > 1:
                # Check if same path has different functions
                functions = set(inst['function'] for inst in instances)
                if len(functions) > 1:
                    self.conflicts.append({
                        'path': path,
                        'instances': instances,
                        'functions': list(functions)
                    })
    
    def _generate_recommendations(self):
        """Generate cleanup recommendations"""
        
        # Recommend primary app file
        if 'app_working.py' in [inst['file'] for instances in self.routes_found.values() for inst in instances]:
            self.recommendations.append({
                'type': 'primary_app',
                'message': 'Use app_working.py as primary application file',
                'priority': 'high'
            })
        
        # Recommend removing duplicates
        for duplicate in self.duplicates:
            files_involved = set(inst['file'] for inst in duplicate['instances'])
            if len(files_involved) > 1:
                self.recommendations.append({
                    'type': 'remove_duplicate',
                    'route': duplicate['route'],
                    'message': f"Remove duplicate route {duplicate['route']} from: {', '.join(files_involved)}",
                    'priority': 'high'
                })
        
        # Recommend resolving conflicts
        for conflict in self.conflicts:
            self.recommendations.append({
                'type': 'resolve_conflict',
                'path': conflict['path'],
                'message': f"Resolve function conflict for {conflict['path']}: {', '.join(conflict['functions'])}",
                'priority': 'medium'
            })
    
    def _generate_audit_report(self) -> Dict[str, any]:
        """Generate comprehensive audit report"""
        return {
            'audit_timestamp': datetime.now().isoformat(),
            'files_scanned': self.app_files,
            'total_routes': len(self.routes_found),
            'duplicates': {
                'count': len(self.duplicates),
                'details': self.duplicates
            },
            'conflicts': {
                'count': len(self.conflicts),
                'details': self.conflicts
            },
            'recommendations': {
                'count': len(self.recommendations),
                'details': self.recommendations
            },
            'route_inventory': self.routes_found
        }
    
    def generate_cleanup_script(self) -> str:
        """Generate cleanup script to fix issues"""
        script = "#!/bin/bash\n"
        script += "# QQ Routing Cleanup Script\n"
        script += f"# Generated: {datetime.now().isoformat()}\n\n"
        
        # Backup current files
        script += "echo 'Creating backups...'\n"
        for app_file in self.app_files:
            if os.path.exists(app_file):
                script += f"cp {app_file} {app_file}.backup.$(date +%Y%m%d_%H%M%S)\n"
        
        script += "\necho 'QQ Routing cleanup complete!'\n"
        return script

def run_routing_audit():
    """Run comprehensive routing audit"""
    auditor = QQRoutingAuditor()
    return auditor.audit_all_routes()

def generate_routing_cleanup():
    """Generate routing cleanup recommendations"""
    auditor = QQRoutingAuditor()
    audit_result = auditor.audit_all_routes()
    cleanup_script = auditor.generate_cleanup_script()
    
    return {
        'audit': audit_result,
        'cleanup_script': cleanup_script
    }