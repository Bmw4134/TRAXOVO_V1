"""
TRAXOVO Build Validator - Pre-deployment System Check
Validates all modules and files before deployment
"""
import os
import sys
import json
import logging
from datetime import datetime
import subprocess
import hashlib

class TRAXOVOBuildValidator:
    """Comprehensive build validation for TRAXOVO deployment"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {
            'status': 'pending',
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': [],
            'warnings': [],
            'deployment_ready': False
        }
        
    def validate_all_modules(self):
        """Run complete validation suite"""
        self.logger.info("Starting TRAXOVO build validation...")
        
        # Core application checks
        self.validate_core_files()
        self.validate_templates()
        self.validate_data_integrity()
        self.validate_routes()
        self.validate_dependencies()
        self.validate_mobile_responsiveness()
        self.validate_foundation_integration()
        self.generate_deployment_checksum()
        
        # Final assessment
        self.assess_deployment_readiness()
        
        return self.validation_results
    
    def validate_core_files(self):
        """Validate core application files"""
        required_files = [
            'main.py',
            'authentic_data_service.py', 
            'foundation_export.py',
            'templates/dashboard_clickable.html',
            'templates/fleet_map_enhanced.html',
            'templates/includes/sidebar.html'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.validation_results['errors'].append(f"Missing required files: {missing_files}")
        else:
            self.validation_results['checks']['core_files'] = 'PASS'
            
    def validate_templates(self):
        """Validate template files for mobile responsiveness"""
        template_checks = []
        
        # Check dashboard template for mobile features
        dashboard_path = 'templates/dashboard_clickable.html'
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                content = f.read()
                
            mobile_features = [
                'mobile-menu-toggle',
                '@media (max-width: 767px)',
                'toggleSidebar()',
                'col-12 col-md-9'
            ]
            
            for feature in mobile_features:
                if feature in content:
                    template_checks.append(f"Mobile feature '{feature}': PASS")
                else:
                    self.validation_results['warnings'].append(f"Missing mobile feature: {feature}")
        
        self.validation_results['checks']['templates'] = template_checks
        
    def validate_data_integrity(self):
        """Validate authentic data integration"""
        try:
            from authentic_data_service import authentic_data
            
            # Test revenue data
            revenue_data = authentic_data.get_revenue_data()
            if revenue_data['total_revenue'] == 2210400.4:
                self.validation_results['checks']['revenue_data'] = 'PASS - Authentic $2.21M'
            else:
                self.validation_results['errors'].append("Revenue data mismatch")
            
            # Test asset data
            asset_data = authentic_data.get_asset_data()
            if asset_data['total_assets'] == 33:  # Updated count including all billing methods
                self.validation_results['checks']['asset_data'] = 'PASS - 33 billable assets'
            else:
                self.validation_results['warnings'].append(f"Asset count: {asset_data['total_assets']} (expected 33)")
                
        except Exception as e:
            self.validation_results['errors'].append(f"Data validation error: {str(e)}")
    
    def validate_routes(self):
        """Validate all routes are accessible"""
        critical_routes = [
            '/',
            '/fleet-map',
            '/billing',
            '/revenue-analytics',
            '/attendance-matrix',
            '/equipment-dispatch',
            '/api/metrics-detail/billable_assets',
            '/api/foundation-export'
        ]
        
        # This would require running the app - for now just check route definitions
        try:
            with open('main.py', 'r') as f:
                main_content = f.read()
                
            route_checks = []
            for route in critical_routes:
                if f"@app.route('{route}')" in main_content or f'@app.route("{route}")' in main_content:
                    route_checks.append(f"Route {route}: DEFINED")
                else:
                    self.validation_results['warnings'].append(f"Route {route} not found in main.py")
                    
            self.validation_results['checks']['routes'] = route_checks
            
        except Exception as e:
            self.validation_results['errors'].append(f"Route validation error: {str(e)}")
    
    def validate_dependencies(self):
        """Check if all required dependencies are available"""
        required_packages = [
            'flask',
            'pandas', 
            'sqlalchemy',
            'openpyxl',
            'psycopg2-binary',
            'requests'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.validation_results['errors'].append(f"Missing packages: {missing_packages}")
        else:
            self.validation_results['checks']['dependencies'] = 'PASS'
    
    def validate_mobile_responsiveness(self):
        """Validate mobile responsiveness implementation"""
        mobile_checks = []
        
        # Check for responsive CSS
        dashboard_path = 'templates/dashboard_clickable.html'
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                content = f.read()
                
            if '@media (max-width: 767px)' in content:
                mobile_checks.append("Responsive CSS: PASS")
            else:
                self.validation_results['errors'].append("Missing responsive CSS")
                
            if 'mobile-menu-toggle' in content:
                mobile_checks.append("Mobile menu toggle: PASS")
            else:
                self.validation_results['errors'].append("Missing mobile menu toggle")
        
        self.validation_results['checks']['mobile_responsive'] = mobile_checks
    
    def validate_foundation_integration(self):
        """Validate Foundation accounting export capability"""
        try:
            from foundation_export import foundation_exporter
            
            # Test export preparation
            records = foundation_exporter.prepare_eq_billing_export()
            if len(records) > 0:
                self.validation_results['checks']['foundation_export'] = f'PASS - {len(records)} records ready'
            else:
                self.validation_results['warnings'].append("Foundation export returned no records")
                
        except Exception as e:
            self.validation_results['errors'].append(f"Foundation integration error: {str(e)}")
    
    def generate_deployment_checksum(self):
        """Generate deployment checksum for traceability"""
        files_to_hash = [
            'main.py',
            'authentic_data_service.py',
            'foundation_export.py'
        ]
        
        combined_hash = hashlib.md5()
        for file_path in files_to_hash:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    combined_hash.update(f.read())
        
        self.validation_results['deployment_checksum'] = combined_hash.hexdigest()
        self.validation_results['deployment_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def assess_deployment_readiness(self):
        """Final deployment readiness assessment"""
        if len(self.validation_results['errors']) == 0:
            self.validation_results['deployment_ready'] = True
            self.validation_results['status'] = 'READY FOR DEPLOYMENT'
        else:
            self.validation_results['deployment_ready'] = False
            self.validation_results['status'] = 'DEPLOYMENT BLOCKED'
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        report = [
            "=" * 60,
            "TRAXOVO V10+ DEPLOYMENT VALIDATION REPORT",
            "=" * 60,
            f"Validation Time: {self.validation_results['timestamp']}",
            f"Status: {self.validation_results['status']}",
            f"Deployment Ready: {self.validation_results['deployment_ready']}",
            "",
            "VALIDATION CHECKS:",
            "-" * 30
        ]
        
        for check, result in self.validation_results['checks'].items():
            if isinstance(result, list):
                report.append(f"{check.upper()}:")
                for item in result:
                    report.append(f"  - {item}")
            else:
                report.append(f"{check.upper()}: {result}")
        
        if self.validation_results['warnings']:
            report.extend([
                "",
                "WARNINGS:",
                "-" * 30
            ])
            for warning in self.validation_results['warnings']:
                report.append(f"⚠️  {warning}")
        
        if self.validation_results['errors']:
            report.extend([
                "",
                "ERRORS (DEPLOYMENT BLOCKERS):",
                "-" * 30
            ])
            for error in self.validation_results['errors']:
                report.append(f"❌ {error}")
        
        report.extend([
            "",
            f"Deployment Checksum: {self.validation_results.get('deployment_checksum', 'N/A')}",
            f"Deployment Timestamp: {self.validation_results.get('deployment_timestamp', 'N/A')}",
            "=" * 60
        ])
        
        return "\n".join(report)

def run_validation():
    """Run complete validation and return results"""
    validator = TRAXOVOBuildValidator()
    results = validator.validate_all_modules()
    
    # Print report
    print(validator.generate_report())
    
    # Save results to file
    with open('validation_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    run_validation()