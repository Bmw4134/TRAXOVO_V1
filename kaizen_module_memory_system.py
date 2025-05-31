"""
TRAXOVO Kaizen Module Memory System
Self-learning internal logic for remembering and applying module/routing fixes
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

class KaizenModuleMemory:
    def __init__(self):
        self.memory_file = 'kaizen_memory/module_fixes.json'
        self.patterns_file = 'kaizen_memory/routing_patterns.json'
        self.ensure_memory_directories()
        self.fix_patterns = self.load_fix_patterns()
        self.routing_solutions = self.load_routing_solutions()
    
    def ensure_memory_directories(self):
        """Create memory storage directories"""
        os.makedirs('kaizen_memory', exist_ok=True)
    
    def remember_fix(self, module_name: str, error_type: str, solution: str, success: bool = True):
        """Remember a successful module fix for future reference"""
        
        fix_record = {
            'timestamp': datetime.now().isoformat(),
            'module_name': module_name,
            'error_type': error_type,
            'solution': solution,
            'success': success,
            'applied_count': 1
        }
        
        # Load existing fixes
        fixes = self.load_module_fixes()
        
        # Check if similar fix exists
        existing_fix = self.find_similar_fix(fixes, module_name, error_type)
        
        if existing_fix:
            # Update existing fix
            existing_fix['applied_count'] += 1
            existing_fix['last_applied'] = datetime.now().isoformat()
            if success:
                existing_fix['success_rate'] = (existing_fix.get('success_rate', 0.5) + 1.0) / 2
        else:
            # Add new fix
            fixes.append(fix_record)
        
        # Save updated fixes
        self.save_module_fixes(fixes)
        
        logging.info(f"Kaizen Memory: Remembered fix for {module_name} - {error_type}")
    
    def get_suggested_fix(self, module_name: str, error_type: str) -> str:
        """Get suggested fix based on previous successful solutions"""
        
        fixes = self.load_module_fixes()
        
        # Find exact match first
        for fix in fixes:
            if fix['module_name'] == module_name and fix['error_type'] == error_type:
                if fix.get('success_rate', 0) > 0.7:  # 70% success rate threshold
                    return fix['solution']
        
        # Find similar module fixes
        for fix in fixes:
            if error_type in fix['error_type'] or fix['error_type'] in error_type:
                if fix.get('success_rate', 0) > 0.6:
                    return f"Similar fix applied to {fix['module_name']}: {fix['solution']}"
        
        return self.get_generic_fix_pattern(error_type)
    
    def remember_routing_solution(self, route_pattern: str, issue: str, solution: str):
        """Remember routing solutions for white screen/404 errors"""
        
        solution_record = {
            'timestamp': datetime.now().isoformat(),
            'route_pattern': route_pattern,
            'issue': issue,
            'solution': solution,
            'effectiveness': 1.0
        }
        
        solutions = self.load_routing_solutions()
        solutions.append(solution_record)
        self.save_routing_solutions(solutions)
        
        logging.info(f"Kaizen Memory: Remembered routing solution for {route_pattern}")
    
    def auto_apply_known_fixes(self, error_log: str) -> List[str]:
        """Automatically suggest fixes based on error patterns"""
        
        suggestions = []
        
        # Common routing fix patterns
        if "Blueprint" in error_log and "cannot be assigned" in error_log:
            suggestions.append("Fix blueprint registration - ensure proper import and registration order")
        
        if "Template not found" in error_log:
            suggestions.append("Create missing template file or check template path")
        
        if "404" in error_log or "Not Found" in error_log:
            suggestions.append("Add missing route handler or check URL patterns")
        
        if "ImportError" in error_log:
            suggestions.append("Check module imports and ensure all dependencies are available")
        
        if "500" in error_log or "Internal Server Error" in error_log:
            suggestions.append("Check for syntax errors and database connectivity")
        
        # Load learned patterns
        fixes = self.load_module_fixes()
        for fix in fixes:
            if any(keyword in error_log.lower() for keyword in fix['error_type'].lower().split()):
                suggestions.append(f"Learned fix: {fix['solution']}")
        
        return suggestions
    
    def get_generic_fix_pattern(self, error_type: str) -> str:
        """Get generic fix patterns for common errors"""
        
        patterns = {
            'blueprint': "Ensure blueprint is properly imported and registered with app.register_blueprint()",
            'template': "Create missing template file in templates/ directory",
            'route': "Add @app.route() decorator or @blueprint.route() for blueprint routes",
            'import': "Check import statements and ensure modules exist",
            'database': "Verify database connection and model imports",
            'authentication': "Check login_required decorators and session configuration"
        }
        
        for pattern_key, fix in patterns.items():
            if pattern_key in error_type.lower():
                return fix
        
        return "Review error logs and apply standard debugging procedures"
    
    def load_module_fixes(self) -> List[Dict]:
        """Load remembered module fixes"""
        
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_module_fixes(self, fixes: List[Dict]):
        """Save module fixes to memory"""
        
        with open(self.memory_file, 'w') as f:
            json.dump(fixes, f, indent=2)
    
    def load_routing_solutions(self) -> List[Dict]:
        """Load routing solutions"""
        
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_routing_solutions(self, solutions: List[Dict]):
        """Save routing solutions"""
        
        with open(self.patterns_file, 'w') as f:
            json.dump(solutions, f, indent=2)
    
    def load_fix_patterns(self) -> Dict:
        """Load common fix patterns"""
        
        return {
            'blueprint_registration': {
                'pattern': 'Expression of type "Blueprint" cannot be assigned',
                'solution': 'Fix blueprint import and registration order',
                'code_template': '''
# Correct blueprint registration pattern:
from routes.module_name import blueprint_name
app.register_blueprint(blueprint_name)
                '''
            },
            'template_missing': {
                'pattern': 'TemplateNotFound',
                'solution': 'Create missing template file',
                'code_template': '''
# Create template in templates/ directory
# Ensure correct template path in render_template()
                '''
            },
            'route_missing': {
                'pattern': '404 Not Found',
                'solution': 'Add missing route handler',
                'code_template': '''
@app.route('/route-path')
def route_handler():
    return render_template('template.html')
                '''
            }
        }
    
    def find_similar_fix(self, fixes: List[Dict], module_name: str, error_type: str) -> Dict:
        """Find similar fix in memory"""
        
        for fix in fixes:
            if (fix['module_name'] == module_name and 
                any(keyword in fix['error_type'] for keyword in error_type.split())):
                return fix
        return None
    
    def generate_fix_report(self) -> Dict:
        """Generate report of all remembered fixes"""
        
        fixes = self.load_module_fixes()
        solutions = self.load_routing_solutions()
        
        return {
            'total_fixes_remembered': len(fixes),
            'total_routing_solutions': len(solutions),
            'most_common_errors': self.get_most_common_errors(fixes),
            'success_rate': self.calculate_overall_success_rate(fixes),
            'recent_fixes': fixes[-10:] if fixes else [],
            'generated_at': datetime.now().isoformat()
        }
    
    def get_most_common_errors(self, fixes: List[Dict]) -> List[Dict]:
        """Get most common error types"""
        
        error_counts = {}
        for fix in fixes:
            error_type = fix['error_type']
            if error_type in error_counts:
                error_counts[error_type] += 1
            else:
                error_counts[error_type] = 1
        
        return [
            {'error_type': error, 'count': count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ][:5]
    
    def calculate_overall_success_rate(self, fixes: List[Dict]) -> float:
        """Calculate overall success rate of remembered fixes"""
        
        if not fixes:
            return 0.0
        
        successful_fixes = sum(1 for fix in fixes if fix.get('success', False))
        return successful_fixes / len(fixes)

# Global instance for easy access
kaizen_memory = KaizenModuleMemory()

# Common fixes to remember initially
def initialize_common_fixes():
    """Initialize with common fix patterns"""
    
    # Blueprint registration fixes
    kaizen_memory.remember_fix(
        'blueprint_registration',
        'Expression of type "Blueprint" cannot be assigned',
        'Ensure blueprint imports are correct and registration follows proper order',
        True
    )
    
    # Template fixes
    kaizen_memory.remember_fix(
        'template_system',
        'TemplateNotFound error',
        'Create missing template file in templates/ directory with correct name',
        True
    )
    
    # Routing fixes
    kaizen_memory.remember_fix(
        'routing_system',
        '404 Not Found errors',
        'Add missing route handlers and check URL patterns',
        True
    )
    
    # Import fixes
    kaizen_memory.remember_fix(
        'import_system',
        'ImportError or ModuleNotFoundError',
        'Check import paths and ensure modules exist in correct directories',
        True
    )

# Initialize common fixes on import
initialize_common_fixes()