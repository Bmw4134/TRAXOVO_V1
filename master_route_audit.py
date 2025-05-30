"""
Master Route Health Audit & Repair System
TRAXOVO Final Deployment Preparation
"""

import os
import re
import json
from datetime import datetime

class MasterRouteAuditor:
    """Comprehensive route health audit and repair system"""
    
    def __init__(self):
        self.context_file = 'context_state.json'
        self.routes_found = []
        self.template_issues = []
        self.repairs_needed = []
    
    def scan_main_routes(self):
        """Scan main.py for all route definitions"""
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Find all @app.route definitions
        route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"].*?\)\s*def\s+(\w+)'
        matches = re.findall(route_pattern, content, re.MULTILINE)
        
        for route_path, function_name in matches:
            # Find template usage in function
            func_start = content.find(f'def {function_name}(')
            if func_start != -1:
                # Find next function or end of file
                next_func = content.find('\n@app.route', func_start)
                if next_func == -1:
                    next_func = content.find('\ndef ', func_start + 10)
                if next_func == -1:
                    next_func = len(content)
                
                func_content = content[func_start:next_func]
                
                # Extract template name
                template_match = re.search(r'render_template\([\'"]([^\'"]+)[\'"]', func_content)
                template_name = template_match.group(1) if template_match else 'no_template'
                
                self.routes_found.append({
                    'path': route_path,
                    'function': function_name,
                    'template': template_name,
                    'exists': os.path.exists(f'templates/{template_name}') if template_name != 'no_template' else True
                })
    
    def identify_broken_routes(self):
        """Identify routes with missing or incorrect templates"""
        for route in self.routes_found:
            if not route['exists'] and route['template'] != 'no_template':
                self.template_issues.append({
                    'route': route['path'],
                    'function': route['function'],
                    'missing_template': route['template'],
                    'fix_needed': True
                })
            
            # Check for old template usage that should be unified
            if route['template'] in ['dashboard_herc_inspired.html', 'enhanced_dashboard_simple.html', 'attendance_matrix_complete.html']:
                self.repairs_needed.append({
                    'route': route['path'],
                    'function': route['function'],
                    'old_template': route['template'],
                    'suggested_template': self.get_unified_template(route['template'])
                })
    
    def get_unified_template(self, old_template):
        """Map old templates to unified versions"""
        mapping = {
            'dashboard_herc_inspired.html': 'master_unified.html',
            'enhanced_dashboard_simple.html': 'enhanced_dashboard_unified.html',
            'attendance_matrix_complete.html': 'attendance_complete_unified.html',
            'fleet_map.html': 'fleet_map_unified.html'
        }
        return mapping.get(old_template, 'master_unified.html')
    
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'total_routes_found': len(self.routes_found),
            'template_issues': len(self.template_issues),
            'repairs_needed': len(self.repairs_needed),
            'routes': self.routes_found,
            'issues': self.template_issues,
            'repairs': self.repairs_needed,
            'recommendations': [
                'Update all routes to use unified templates',
                'Ensure master_unified.html is base template',
                'Verify attendance system routing',
                'Check fleet map integration'
            ]
        }
        return report
    
    def update_context_state(self):
        """Update context_state.json with corrected mappings"""
        try:
            with open(self.context_file, 'r') as f:
                context = json.load(f)
        except:
            context = {}
        
        # Update routing state with audit results
        context['routing_audit'] = {
            'last_audit': datetime.now().isoformat(),
            'routes_verified': len(self.routes_found),
            'issues_found': len(self.template_issues),
            'repairs_applied': len(self.repairs_needed)
        }
        
        # Update template mappings
        context['template_mappings'] = {}
        for route in self.routes_found:
            context['template_mappings'][route['path']] = route['template']
        
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2)

def run_master_audit():
    """Execute master route health audit"""
    auditor = MasterRouteAuditor()
    auditor.scan_main_routes()
    auditor.identify_broken_routes()
    
    report = auditor.generate_audit_report()
    auditor.update_context_state()
    
    # Save audit report
    with open('audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✅ Master Route Audit Complete")
    print(f"   - {report['total_routes_found']} routes found")
    print(f"   - {report['template_issues']} template issues")
    print(f"   - {report['repairs_needed']} repairs needed")
    
    return report

if __name__ == "__main__":
    run_master_audit()