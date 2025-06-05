"""
KAIZEN Final Unlock Test System
Initialize and validate unrestricted module access across all dashboards
Execute TRD: Validate unlocks across all dashboards
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KaizenUnlockValidator:
    """
    KAIZEN Final Push Test Bundle Validator
    Validates unrestricted module access, fingerprint matching, and UI readiness
    """
    
    def __init__(self):
        self.unlock_status = {}
        self.validation_results = {}
        self.fingerprint_matches = {}
        self.ui_readiness = {}
        self.module_access = {}
        
        logger.info("KAIZEN Unlock Validator initialized")
    
    def validate_all_dashboards(self) -> Dict[str, Any]:
        """
        TRD: Validate unlocks across all dashboards
        Execute comprehensive validation sequence
        """
        logger.info("Starting TRD validation sequence across all dashboards...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "validation_phase": "FINAL_UNLOCK_TEST",
            "dashboards_validated": [],
            "module_access_status": {},
            "fingerprint_validation": {},
            "ui_readiness_status": {},
            "unlock_summary": {}
        }
        
        # Step 1: Discover all dashboards
        dashboards = self._discover_dashboards()
        logger.info(f"Discovered {len(dashboards)} dashboards for validation")
        
        # Step 2: Validate each dashboard
        for dashboard in dashboards:
            dashboard_result = self._validate_single_dashboard(dashboard)
            validation_results["dashboards_validated"].append(dashboard_result)
        
        # Step 3: Validate unrestricted module access
        module_access = self._validate_unrestricted_module_access()
        validation_results["module_access_status"] = module_access
        
        # Step 4: Validate fingerprint matches
        fingerprint_validation = self._validate_fingerprint_matches()
        validation_results["fingerprint_validation"] = fingerprint_validation
        
        # Step 5: Validate UI readiness
        ui_readiness = self._validate_ui_readiness()
        validation_results["ui_readiness_status"] = ui_readiness
        
        # Step 6: Generate unlock summary
        unlock_summary = self._generate_unlock_summary(validation_results)
        validation_results["unlock_summary"] = unlock_summary
        
        logger.info("TRD validation sequence completed")
        return validation_results
    
    def _discover_dashboards(self) -> List[Dict[str, str]]:
        """Discover all available dashboards"""
        dashboards = []
        
        # Check templates directory for HTML dashboards
        templates_dir = Path('./templates')
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.html'):
                dashboard_name = template_file.stem
                dashboards.append({
                    "name": dashboard_name,
                    "type": "html_template",
                    "path": str(template_file),
                    "route": f"/{dashboard_name.replace('_', '-')}"
                })
        
        # Check for Flask routes in main app files
        app_files = ['app_qq_enhanced.py', 'app_production_ready.py', 'app.py']
        
        for app_file in app_files:
            if os.path.exists(app_file):
                routes = self._extract_routes_from_app(app_file)
                for route in routes:
                    dashboards.append({
                        "name": route["name"],
                        "type": "flask_route",
                        "path": app_file,
                        "route": route["path"]
                    })
        
        return dashboards
    
    def _extract_routes_from_app(self, app_file: str) -> List[Dict[str, str]]:
        """Extract Flask routes from app file"""
        routes = []
        
        try:
            with open(app_file, 'r') as f:
                content = f.read()
            
            import re
            # Find all route decorators
            route_pattern = r"@app\.route\('([^']+)'\)\s*\ndef\s+([^(]+)\("
            matches = re.findall(route_pattern, content)
            
            for path, function_name in matches:
                if not path.startswith('/api/') and path != '/':
                    routes.append({
                        "name": function_name,
                        "path": path
                    })
        
        except Exception as e:
            logger.warning(f"Failed to extract routes from {app_file}: {e}")
        
        return routes
    
    def _validate_single_dashboard(self, dashboard: Dict[str, str]) -> Dict[str, Any]:
        """Validate a single dashboard for unlock status"""
        dashboard_result = {
            "dashboard_name": dashboard["name"],
            "dashboard_type": dashboard["type"],
            "dashboard_route": dashboard["route"],
            "validation_timestamp": datetime.now().isoformat(),
            "unlock_status": "unknown",
            "module_dependencies": [],
            "access_restrictions": [],
            "fingerprint_status": "pending",
            "ui_components": [],
            "validation_errors": []
        }
        
        try:
            # Check if dashboard file exists and is accessible
            if os.path.exists(dashboard["path"]):
                dashboard_result["unlock_status"] = "accessible"
                
                # Analyze dashboard dependencies
                dependencies = self._analyze_dashboard_dependencies(dashboard["path"])
                dashboard_result["module_dependencies"] = dependencies
                
                # Check for access restrictions
                restrictions = self._check_access_restrictions(dashboard["path"])
                dashboard_result["access_restrictions"] = restrictions
                
                # Validate UI components
                ui_components = self._validate_dashboard_ui_components(dashboard["path"])
                dashboard_result["ui_components"] = ui_components
                
                # Set unlock status based on restrictions
                if not restrictions:
                    dashboard_result["unlock_status"] = "unrestricted"
                else:
                    dashboard_result["unlock_status"] = "restricted"
            
            else:
                dashboard_result["unlock_status"] = "inaccessible"
                dashboard_result["validation_errors"].append("Dashboard file not found")
        
        except Exception as e:
            dashboard_result["unlock_status"] = "error"
            dashboard_result["validation_errors"].append(str(e))
            logger.error(f"Error validating dashboard {dashboard['name']}: {e}")
        
        return dashboard_result
    
    def _analyze_dashboard_dependencies(self, file_path: str) -> List[str]:
        """Analyze dashboard module dependencies"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for import statements and function calls
            import re
            
            # Python imports
            import_patterns = [
                r'from\s+([^\s]+)\s+import',
                r'import\s+([^\s]+)',
                r'from\s+([^\s]+)\s+import'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
            
            # JavaScript/API calls
            api_patterns = [
                r'fetch\([\'"]([^\'"]+)[\'"]',
                r'url_for\([\'"]([^\'"]+)[\'"]',
                r'href=[\'"]([^\'"]+)[\'"]'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {file_path}: {e}")
        
        return list(set(dependencies))  # Remove duplicates
    
    def _check_access_restrictions(self, file_path: str) -> List[str]:
        """Check for access restrictions in dashboard"""
        restrictions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            # Common restriction patterns
            restriction_patterns = {
                "authentication_required": ["@login_required", "session.get", "authenticate"],
                "permission_check": ["permission", "authorize", "role", "admin"],
                "api_key_required": ["api_key", "secret", "token"],
                "demo_mode": ["demo", "simulation", "mock"],
                "credential_check": ["credential", "password", "auth"]
            }
            
            for restriction_type, keywords in restriction_patterns.items():
                if any(keyword in content for keyword in keywords):
                    restrictions.append(restriction_type)
        
        except Exception as e:
            logger.warning(f"Failed to check restrictions for {file_path}: {e}")
        
        return restrictions
    
    def _validate_dashboard_ui_components(self, file_path: str) -> List[str]:
        """Validate UI components in dashboard"""
        ui_components = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for UI framework components
            ui_patterns = {
                "bootstrap": ["bootstrap", "btn-", "card-", "container"],
                "chart_js": ["chart.js", "Chart(", "canvas"],
                "font_awesome": ["fas fa-", "far fa-", "fab fa-"],
                "custom_css": ["<style>", ".css"],
                "javascript": ["<script>", "function", "addEventListener"],
                "forms": ["<form>", "input", "button"],
                "navigation": ["navbar", "nav-", "menu"],
                "tables": ["<table>", "dataTable", "thead"],
                "modals": ["modal", "dialog"],
                "alerts": ["alert", "notification"]
            }
            
            for component_type, keywords in ui_patterns.items():
                if any(keyword in content for keyword in keywords):
                    ui_components.append(component_type)
        
        except Exception as e:
            logger.warning(f"Failed to validate UI components for {file_path}: {e}")
        
        return ui_components
    
    def _validate_unrestricted_module_access(self) -> Dict[str, Any]:
        """Validate unrestricted access to all modules"""
        module_access = {
            "total_modules_scanned": 0,
            "unrestricted_modules": [],
            "restricted_modules": [],
            "inaccessible_modules": [],
            "module_categories": {
                "qq_modules": [],
                "automation_modules": [],
                "api_modules": [],
                "ui_modules": [],
                "core_modules": []
            }
        }
        
        # Scan all Python modules
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    module_access["total_modules_scanned"] += 1
                    
                    # Categorize module
                    module_category = self._categorize_module(file)
                    if module_category:
                        module_access["module_categories"][module_category].append(file)
                    
                    # Check access restrictions
                    restrictions = self._check_module_restrictions(file_path)
                    
                    if not restrictions:
                        module_access["unrestricted_modules"].append(file)
                    elif "inaccessible" in restrictions:
                        module_access["inaccessible_modules"].append(file)
                    else:
                        module_access["restricted_modules"].append({
                            "module": file,
                            "restrictions": restrictions
                        })
        
        # Calculate access statistics
        total = module_access["total_modules_scanned"]
        unrestricted = len(module_access["unrestricted_modules"])
        
        module_access["access_statistics"] = {
            "unrestricted_percentage": round((unrestricted / total) * 100, 2) if total > 0 else 0,
            "total_scanned": total,
            "unrestricted_count": unrestricted,
            "restricted_count": len(module_access["restricted_modules"]),
            "inaccessible_count": len(module_access["inaccessible_modules"])
        }
        
        logger.info(f"Module access validation: {unrestricted}/{total} modules unrestricted")
        return module_access
    
    def _categorize_module(self, filename: str) -> Optional[str]:
        """Categorize module by filename pattern"""
        if filename.startswith('qq_'):
            return "qq_modules"
        elif any(keyword in filename for keyword in ['automation', 'agent', 'bot']):
            return "automation_modules"
        elif any(keyword in filename for keyword in ['api', 'endpoint', 'service']):
            return "api_modules"
        elif any(keyword in filename for keyword in ['ui', 'template', 'render']):
            return "ui_modules"
        elif filename in ['app.py', 'main.py', 'models.py', 'config.py']:
            return "core_modules"
        
        return None
    
    def _check_module_restrictions(self, file_path: str) -> List[str]:
        """Check for module-level access restrictions"""
        restrictions = []
        
        try:
            # Check file permissions
            if not os.access(file_path, os.R_OK):
                restrictions.append("read_protected")
            
            if not os.access(file_path, os.W_OK):
                restrictions.append("write_protected")
            
            # Check file content for restrictions
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for restriction indicators
            if "# RESTRICTED" in content or "# ACCESS_DENIED" in content:
                restrictions.append("content_restricted")
            
            if "raise PermissionError" in content:
                restrictions.append("permission_error")
            
        except Exception as e:
            restrictions.append("inaccessible")
            logger.warning(f"Cannot access module {file_path}: {e}")
        
        return restrictions
    
    def _validate_fingerprint_matches(self) -> Dict[str, Any]:
        """Validate fingerprint matches across the system"""
        fingerprint_validation = {
            "system_fingerprint": None,
            "patch_fingerprint": None,
            "fingerprint_match": False,
            "validation_errors": [],
            "fingerprint_components": {}
        }
        
        try:
            # Generate current system fingerprint
            system_fingerprint = self._generate_system_fingerprint()
            fingerprint_validation["system_fingerprint"] = system_fingerprint
            
            # Check for Kaizen introspection system
            try:
                from kaizen_system_introspection import get_kaizen_introspection
                introspection = get_kaizen_introspection()
                
                if not introspection.fingerprint:
                    introspection.perform_full_introspection()
                
                if introspection.fingerprint:
                    fingerprint_validation["patch_fingerprint"] = {
                        "dashboard_purpose": introspection.fingerprint.dashboard_purpose,
                        "patch_version": introspection.fingerprint.patch_version,
                        "sync_status": introspection.fingerprint.sync_status
                    }
                    
                    # Check fingerprint match
                    if introspection.fingerprint.sync_status == "validated":
                        fingerprint_validation["fingerprint_match"] = True
            
            except ImportError:
                fingerprint_validation["validation_errors"].append("Kaizen introspection system not available")
            
        except Exception as e:
            fingerprint_validation["validation_errors"].append(str(e))
            logger.error(f"Fingerprint validation error: {e}")
        
        return fingerprint_validation
    
    def _generate_system_fingerprint(self) -> str:
        """Generate current system fingerprint"""
        # Collect system information
        system_info = {
            "python_files": [],
            "template_files": [],
            "config_files": []
        }
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    system_info["python_files"].append(file)
                elif file.endswith('.html'):
                    system_info["template_files"].append(file)
                elif file.endswith(('.json', '.yaml', '.yml', '.toml')):
                    system_info["config_files"].append(file)
        
        # Generate hash
        system_string = json.dumps(system_info, sort_keys=True)
        return hashlib.md5(system_string.encode()).hexdigest()
    
    def _validate_ui_readiness(self) -> Dict[str, Any]:
        """Validate UI readiness across all dashboards"""
        ui_readiness = {
            "total_ui_components": 0,
            "ready_components": [],
            "broken_components": [],
            "missing_dependencies": [],
            "css_frameworks": [],
            "js_frameworks": [],
            "ui_readiness_score": 0
        }
        
        # Check for CSS frameworks
        css_frameworks = ["bootstrap", "tailwind", "bulma", "foundation"]
        js_frameworks = ["jquery", "chart.js", "d3.js", "vue.js", "react"]
        
        # Scan templates for UI readiness
        templates_dir = Path('./templates')
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.html'):
                try:
                    with open(template_file, 'r') as f:
                        content = f.read()
                    
                    ui_readiness["total_ui_components"] += 1
                    
                    # Check for CSS frameworks
                    for framework in css_frameworks:
                        if framework in content.lower():
                            ui_readiness["css_frameworks"].append(framework)
                    
                    # Check for JS frameworks
                    for framework in js_frameworks:
                        if framework in content.lower():
                            ui_readiness["js_frameworks"].append(framework)
                    
                    # Check for broken links or missing resources
                    if "404" not in content and "error" not in content.lower():
                        ui_readiness["ready_components"].append(str(template_file))
                    else:
                        ui_readiness["broken_components"].append(str(template_file))
                
                except Exception as e:
                    ui_readiness["broken_components"].append(str(template_file))
                    logger.warning(f"Failed to validate UI for {template_file}: {e}")
        
        # Calculate readiness score
        total = ui_readiness["total_ui_components"]
        ready = len(ui_readiness["ready_components"])
        
        if total > 0:
            ui_readiness["ui_readiness_score"] = round((ready / total) * 100, 2)
        
        # Remove duplicates
        ui_readiness["css_frameworks"] = list(set(ui_readiness["css_frameworks"]))
        ui_readiness["js_frameworks"] = list(set(ui_readiness["js_frameworks"]))
        
        return ui_readiness
    
    def _generate_unlock_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive unlock summary"""
        dashboards_count = len(validation_results["dashboards_validated"])
        unrestricted_dashboards = len([d for d in validation_results["dashboards_validated"] if d["unlock_status"] == "unrestricted"])
        
        module_stats = validation_results["module_access_status"]["access_statistics"]
        fingerprint_match = validation_results["fingerprint_validation"]["fingerprint_match"]
        ui_score = validation_results["ui_readiness_status"]["ui_readiness_score"]
        
        # Calculate overall unlock score
        dashboard_score = (unrestricted_dashboards / dashboards_count * 100) if dashboards_count > 0 else 0
        module_score = module_stats["unrestricted_percentage"]
        fingerprint_score = 100 if fingerprint_match else 0
        
        overall_score = (dashboard_score + module_score + fingerprint_score + ui_score) / 4
        
        unlock_summary = {
            "overall_unlock_score": round(overall_score, 2),
            "unlock_status": "FULLY_UNLOCKED" if overall_score >= 90 else "PARTIALLY_UNLOCKED" if overall_score >= 50 else "LOCKED",
            "dashboard_unlock_rate": round(dashboard_score, 2),
            "module_unlock_rate": module_score,
            "fingerprint_validation_status": "PASSED" if fingerprint_match else "FAILED",
            "ui_readiness_score": ui_score,
            "unlock_categories": {
                "dashboards": f"{unrestricted_dashboards}/{dashboards_count} unrestricted",
                "modules": f"{module_stats['unrestricted_count']}/{module_stats['total_scanned']} unrestricted",
                "fingerprint": "VALIDATED" if fingerprint_match else "PENDING",
                "ui_components": f"{len(validation_results['ui_readiness_status']['ready_components'])} ready"
            },
            "recommendations": self._generate_unlock_recommendations(validation_results)
        }
        
        return unlock_summary
    
    def _generate_unlock_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving unlock status"""
        recommendations = []
        
        # Check dashboard restrictions
        restricted_dashboards = [d for d in validation_results["dashboards_validated"] if d["unlock_status"] == "restricted"]
        if restricted_dashboards:
            recommendations.append(f"Remove access restrictions from {len(restricted_dashboards)} dashboards")
        
        # Check module restrictions
        module_stats = validation_results["module_access_status"]["access_statistics"]
        if module_stats["unrestricted_percentage"] < 90:
            recommendations.append("Unlock remaining restricted modules for full access")
        
        # Check fingerprint validation
        if not validation_results["fingerprint_validation"]["fingerprint_match"]:
            recommendations.append("Complete fingerprint validation and patch synchronization")
        
        # Check UI readiness
        if validation_results["ui_readiness_status"]["ui_readiness_score"] < 90:
            recommendations.append("Fix broken UI components and missing dependencies")
        
        if not recommendations:
            recommendations.append("System fully unlocked - all validations passed")
        
        return recommendations

def run_final_unlock_test() -> Dict[str, Any]:
    """
    Run the final unlock test sequence
    Main entry point for KAIZEN Final Push Test Bundle
    """
    logger.info("Starting KAIZEN Final Unlock Test...")
    
    validator = KaizenUnlockValidator()
    
    try:
        # Execute TRD validation sequence
        validation_results = validator.validate_all_dashboards()
        
        # Save results to file
        output_file = f"kaizen_unlock_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Unlock test results saved to {output_file}")
        
        # Print summary
        summary = validation_results["unlock_summary"]
        logger.info(f"Overall Unlock Score: {summary['overall_unlock_score']}%")
        logger.info(f"Unlock Status: {summary['unlock_status']}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Final unlock test failed: {e}")
        return {
            "error": str(e),
            "status": "FAILED",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Execute final unlock test when run directly
    results = run_final_unlock_test()
    
    # Print key results
    if "error" not in results:
        print("\n" + "="*60)
        print("KAIZEN FINAL UNLOCK TEST RESULTS")
        print("="*60)
        
        summary = results["unlock_summary"]
        print(f"Overall Unlock Score: {summary['overall_unlock_score']}%")
        print(f"Status: {summary['unlock_status']}")
        print(f"Dashboard Unlock Rate: {summary['dashboard_unlock_rate']}%")
        print(f"Module Unlock Rate: {summary['module_unlock_rate']}%")
        print(f"Fingerprint Validation: {summary['fingerprint_validation_status']}")
        print(f"UI Readiness Score: {summary['ui_readiness_score']}%")
        
        print("\nRecommendations:")
        for rec in summary['recommendations']:
            print(f"- {rec}")
        
        print("\n" + "="*60)
    else:
        print(f"Test failed: {results['error']}")