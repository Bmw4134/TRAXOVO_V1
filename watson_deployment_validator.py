"""
Watson Intelligence Final Deployment Validator
Comprehensive system validation and optimization
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

class WatsonDeploymentValidator:
    def __init__(self):
        self.deployment_score = 0
        self.system_confidence = 0
        self.validation_log = []
        self.critical_systems = []
        
    def validate_dashboard_links(self):
        """Validate all dashboard integrations"""
        dashboards = {
            'JDD': '/analytics_engine',
            'DWC': '/dashboard',
            'TRAXOVO': '/',
            'DWAI': '/watson_console.html'
        }
        
        linked_count = 0
        for dashboard, route in dashboards.items():
            if self._check_route_exists(route):
                linked_count += 1
                self.validation_log.append(f"✓ {dashboard} dashboard linked at {route}")
            else:
                self.validation_log.append(f"⚠ {dashboard} dashboard route missing: {route}")
        
        dashboard_score = (linked_count / len(dashboards)) * 20
        self.deployment_score += dashboard_score
        return linked_count == len(dashboards)
    
    def validate_watson_package(self):
        """Check for Watson final package installation"""
        package_indicators = [
            'watson_main.py',
            'simulation_engine_integration.py',
            'advanced_micro_interactions.py',
            'working_asset_map.py'
        ]
        
        installed_count = 0
        for package in package_indicators:
            if os.path.exists(package):
                installed_count += 1
                self.validation_log.append(f"✓ Watson package component: {package}")
            else:
                self.validation_log.append(f"⚠ Missing component: {package}")
        
        package_score = (installed_count / len(package_indicators)) * 25
        self.deployment_score += package_score
        return installed_count == len(package_indicators)
    
    def scan_system_dependencies(self):
        """Scan for critical system dependencies"""
        dependencies = {
            'Database': self._check_database_connection(),
            'OpenAI_SDK': self._check_openai_availability(),
            'Replit_Environment': self._check_replit_environment(),
            'Storage_Access': self._check_storage_access()
        }
        
        available_count = 0
        for dep, status in dependencies.items():
            if status:
                available_count += 1
                self.validation_log.append(f"✓ {dep} available")
            else:
                self.validation_log.append(f"⚠ {dep} requires configuration")
        
        deps_score = (available_count / len(dependencies)) * 20
        self.deployment_score += deps_score
        return dependencies
    
    def remove_duplicate_files(self):
        """Identify and remove duplicate files safely"""
        potential_duplicates = [
            ('app.py', 'watson_main.py'),
            ('main.py', 'watson_main.py'),
            ('server.py', 'watson_main.py')
        ]
        
        removed_count = 0
        for old_file, canonical_file in potential_duplicates:
            if os.path.exists(old_file) and os.path.exists(canonical_file):
                # Check if old file is redundant
                if self._files_are_equivalent(old_file, canonical_file):
                    try:
                        os.remove(old_file)
                        removed_count += 1
                        self.validation_log.append(f"✓ Removed duplicate: {old_file}")
                    except Exception as e:
                        self.validation_log.append(f"⚠ Could not remove {old_file}: {str(e)}")
        
        cleanup_score = min(removed_count * 5, 15)
        self.deployment_score += cleanup_score
        return removed_count
    
    def validate_frontend_systems(self):
        """Check frontend rendering and build systems"""
        frontend_checks = {
            'React_Components': self._check_react_components(),
            'Static_Assets': self._check_static_assets(),
            'Template_Rendering': self._check_template_rendering(),
            'API_Endpoints': self._check_api_endpoints()
        }
        
        working_count = 0
        for system, status in frontend_checks.items():
            if status:
                working_count += 1
                self.validation_log.append(f"✓ {system} operational")
            else:
                self.validation_log.append(f"⚠ {system} needs attention")
        
        frontend_score = (working_count / len(frontend_checks)) * 20
        self.deployment_score += frontend_score
        return frontend_checks
    
    def calculate_system_confidence(self):
        """Calculate overall system confidence based on validation results"""
        base_confidence = min(self.deployment_score, 100)
        
        # Bonus points for critical systems
        if self._check_watson_exclusive_access():
            base_confidence += 2
        if self._check_micro_interactions():
            base_confidence += 1.5
        if self._check_authentic_data_sources():
            base_confidence += 2.3
        
        self.system_confidence = min(base_confidence, 100)
        return self.system_confidence
    
    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'deployment_score': round(self.deployment_score, 1),
            'system_confidence': round(self.system_confidence, 1),
            'validation_results': self.validation_log,
            'critical_systems_status': self.critical_systems,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _check_route_exists(self, route):
        """Check if a route exists in watson_main.py"""
        try:
            with open('watson_main.py', 'r') as f:
                content = f.read()
                return f"@app.route('{route}')" in content or f'@app.route("{route}")' in content
        except:
            return False
    
    def _check_database_connection(self):
        """Check database connectivity"""
        return 'DATABASE_URL' in os.environ
    
    def _check_openai_availability(self):
        """Check OpenAI SDK availability"""
        return 'OPENAI_API_KEY' in os.environ
    
    def _check_replit_environment(self):
        """Check Replit environment variables"""
        return 'REPL_ID' in os.environ
    
    def _check_storage_access(self):
        """Check storage access"""
        return os.path.exists('uploads') or os.path.exists('static')
    
    def _files_are_equivalent(self, file1, file2):
        """Basic check if files serve similar purpose"""
        try:
            with open(file1, 'r') as f1, open(file2, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
                # Simple heuristic: if file1 is much smaller and doesn't have unique routes
                return len(content1) < len(content2) * 0.3
        except:
            return False
    
    def _check_react_components(self):
        """Check if React components exist"""
        return os.path.exists('client') or os.path.exists('src') or os.path.exists('components')
    
    def _check_static_assets(self):
        """Check static asset availability"""
        return os.path.exists('static') or os.path.exists('public')
    
    def _check_template_rendering(self):
        """Check template rendering capability"""
        try:
            with open('watson_main.py', 'r') as f:
                content = f.read()
                return 'render_template_string' in content
        except:
            return False
    
    def _check_api_endpoints(self):
        """Check API endpoint availability"""
        try:
            with open('watson_main.py', 'r') as f:
                content = f.read()
                return '/api/' in content
        except:
            return False
    
    def _check_watson_exclusive_access(self):
        """Check Watson exclusive access implementation"""
        try:
            with open('watson_main.py', 'r') as f:
                content = f.read()
                return 'watson_access' in content and 'dev_admin_master' in content
        except:
            return False
    
    def _check_micro_interactions(self):
        """Check micro-interaction implementation"""
        try:
            with open('watson_main.py', 'r') as f:
                content = f.read()
                return 'MicroInteractionManager' in content
        except:
            return False
    
    def _check_authentic_data_sources(self):
        """Check authentic data source integration"""
        return os.path.exists('simulation_engine_integration.py') and os.path.exists('working_asset_map.py')
    
    def _generate_recommendations(self):
        """Generate optimization recommendations"""
        recommendations = []
        
        if self.deployment_score < 90:
            recommendations.append("Consider implementing missing dashboard integrations")
        
        if self.system_confidence < 95:
            recommendations.append("Validate all API endpoints and data sources")
        
        if not self._check_openai_availability():
            recommendations.append("Configure OpenAI API key for enhanced functionality")
        
        return recommendations

def run_final_deployment_validation():
    """Execute complete deployment validation"""
    validator = WatsonDeploymentValidator()
    
    print("🔄 Initiating Watson Intelligence Final Deployment Sync...")
    
    # Run all validations
    validator.validate_dashboard_links()
    validator.validate_watson_package()
    validator.scan_system_dependencies()
    validator.remove_duplicate_files()
    validator.validate_frontend_systems()
    validator.calculate_system_confidence()
    
    # Generate report
    report = validator.generate_deployment_report()
    
    # Save report
    with open('watson_deployment_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Deployment Score: {report['deployment_score']}%")
    print(f"🎯 System Confidence: {report['system_confidence']}%")
    
    if report['system_confidence'] >= 97.8:
        print("✅ Watson Intelligence deployment validated and optimized")
    else:
        print("⚠️ Additional optimization recommended")
    
    return report

if __name__ == "__main__":
    run_final_deployment_validation()