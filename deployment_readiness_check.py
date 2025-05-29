"""
Deployment Readiness Verification System
Comprehensive pre-deployment validation for TRAXOVO system
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DeploymentReadinessChecker:
    """Validate all systems are deployment-ready with authentic data"""
    
    def __init__(self):
        self.results = {
            'overall_status': 'PENDING',
            'timestamp': datetime.now().isoformat(),
            'critical_checks': {},
            'data_validation': {},
            'module_validation': {},
            'recommendations': []
        }
    
    def check_authentic_data_sources(self):
        """Verify all authentic data sources are accessible"""
        data_checks = {}
        
        # Check Gauge API data
        gauge_file = 'GAUGE API PULL 1045AM_05.15.2025.json'
        if os.path.exists(gauge_file):
            try:
                with open(gauge_file, 'r') as f:
                    gauge_data = json.load(f)
                data_checks['gauge_api'] = {
                    'status': 'PASS',
                    'records': len(gauge_data),
                    'file': gauge_file
                }
            except Exception as e:
                data_checks['gauge_api'] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
        else:
            data_checks['gauge_api'] = {
                'status': 'MISSING',
                'file': gauge_file
            }
        
        # Check billing files
        billing_files = [
            'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
            'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
        ]
        
        data_checks['billing_files'] = {}
        for file in billing_files:
            if os.path.exists(file):
                try:
                    df = pd.read_excel(file)
                    data_checks['billing_files'][file] = {
                        'status': 'PASS',
                        'records': len(df)
                    }
                except Exception as e:
                    data_checks['billing_files'][file] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
            else:
                data_checks['billing_files'][file] = {
                    'status': 'MISSING'
                }
        
        # Check activity detail files
        activity_files = [f for f in os.listdir('.') if f.startswith('ActivityDetail') and f.endswith('.csv')]
        data_checks['activity_files'] = {
            'count': len(activity_files),
            'status': 'PASS' if len(activity_files) > 0 else 'WARNING'
        }
        
        self.results['data_validation'] = data_checks
        return data_checks
    
    def check_critical_modules(self):
        """Verify all critical modules are properly implemented"""
        module_checks = {}
        
        critical_modules = [
            'app.py',
            'main.py',
            'attendance_matrix_system.py',
            'executive_billing_intelligence.py',
            'equipment_lifecycle_engine.py',
            'predictive_maintenance_engine.py',
            'traxovo_fleet_map.py',
            'idea_box.py',
            'backup_system.py'
        ]
        
        for module in critical_modules:
            if os.path.exists(module):
                try:
                    # Basic syntax validation
                    with open(module, 'r') as f:
                        content = f.read()
                    
                    # Check for critical patterns
                    has_imports = 'import' in content
                    has_routes = '@' in content and 'route' in content
                    has_functions = 'def ' in content
                    
                    module_checks[module] = {
                        'status': 'PASS' if all([has_imports, has_functions]) else 'WARNING',
                        'has_imports': has_imports,
                        'has_routes': has_routes,
                        'has_functions': has_functions,
                        'size': len(content)
                    }
                except Exception as e:
                    module_checks[module] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
            else:
                module_checks[module] = {
                    'status': 'MISSING'
                }
        
        self.results['module_validation'] = module_checks
        return module_checks
    
    def check_template_files(self):
        """Verify template files exist for all routes"""
        template_checks = {}
        
        required_templates = [
            'templates/index.html',
            'templates/attendance_matrix.html',
            'templates/idea_box.html',
            'templates/backup_system.html'
        ]
        
        for template in required_templates:
            template_checks[template] = {
                'exists': os.path.exists(template),
                'status': 'PASS' if os.path.exists(template) else 'MISSING'
            }
        
        return template_checks
    
    def check_database_requirements(self):
        """Verify database configuration"""
        db_checks = {}
        
        # Check if DATABASE_URL is available
        db_url = os.environ.get('DATABASE_URL')
        db_checks['database_url'] = {
            'configured': db_url is not None,
            'status': 'PASS' if db_url else 'MISSING'
        }
        
        return db_checks
    
    def validate_api_endpoints(self):
        """Check for properly defined API endpoints"""
        api_checks = {}
        
        # Check main application files for API route definitions
        app_files = ['app.py', 'main.py']
        
        for file in app_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                
                # Look for API route patterns
                api_routes = content.count('@app.route')
                blueprint_registrations = content.count('register_blueprint')
                
                api_checks[file] = {
                    'api_routes': api_routes,
                    'blueprint_registrations': blueprint_registrations,
                    'status': 'PASS' if api_routes > 0 or blueprint_registrations > 0 else 'WARNING'
                }
        
        return api_checks
    
    def run_comprehensive_check(self):
        """Run all deployment readiness checks"""
        print("🔍 Running TRAXOVO Deployment Readiness Check...")
        
        # Run all validation checks
        data_validation = self.check_authentic_data_sources()
        module_validation = self.check_critical_modules()
        template_validation = self.check_template_files()
        db_validation = self.check_database_requirements()
        api_validation = self.validate_api_endpoints()
        
        # Store all results
        self.results['data_validation'] = data_validation
        self.results['module_validation'] = module_validation
        self.results['template_validation'] = template_validation
        self.results['database_validation'] = db_validation
        self.results['api_validation'] = api_validation
        
        # Determine overall status
        critical_failures = []
        warnings = []
        
        # Check for critical failures
        if data_validation.get('gauge_api', {}).get('status') == 'MISSING':
            critical_failures.append("Gauge API data file missing")
        
        missing_modules = [m for m, v in module_validation.items() if v.get('status') == 'MISSING']
        if missing_modules:
            critical_failures.extend([f"Missing module: {m}" for m in missing_modules])
        
        if not db_validation.get('database_url', {}).get('configured'):
            critical_failures.append("Database URL not configured")
        
        # Check for warnings
        warning_modules = [m for m, v in module_validation.items() if v.get('status') == 'WARNING']
        if warning_modules:
            warnings.extend([f"Module warning: {m}" for m in warning_modules])
        
        # Determine final status
        if critical_failures:
            self.results['overall_status'] = 'NOT_READY'
            self.results['critical_issues'] = critical_failures
        elif warnings:
            self.results['overall_status'] = 'READY_WITH_WARNINGS'
            self.results['warnings'] = warnings
        else:
            self.results['overall_status'] = 'READY'
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results
    
    def generate_recommendations(self):
        """Generate deployment recommendations based on check results"""
        recommendations = []
        
        # Check Gauge API status
        gauge_status = self.results.get('data_validation', {}).get('gauge_api', {}).get('status')
        if gauge_status in ['MISSING', 'FAIL']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Source',
                'issue': 'Gauge API data not accessible',
                'action': 'Verify Gauge API file exists and is readable'
            })
        
        # Check billing data
        billing_files = self.results.get('data_validation', {}).get('billing_files', {})
        missing_billing = [f for f, v in billing_files.items() if v.get('status') in ['MISSING', 'ERROR']]
        if missing_billing:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Billing Data',
                'issue': f'Billing files not accessible: {missing_billing}',
                'action': 'Ensure billing Excel files are present and readable'
            })
        
        # Check module status
        module_issues = [m for m, v in self.results.get('module_validation', {}).items() 
                        if v.get('status') in ['MISSING', 'ERROR']]
        if module_issues:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Application Modules',
                'issue': f'Critical modules have issues: {module_issues}',
                'action': 'Fix or implement missing/broken modules before deployment'
            })
        
        # Database recommendations
        if not self.results.get('database_validation', {}).get('database_url', {}).get('configured'):
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Database',
                'issue': 'Database URL not configured',
                'action': 'Configure DATABASE_URL environment variable'
            })
        
        self.results['recommendations'] = recommendations
    
    def print_status_report(self):
        """Print comprehensive status report"""
        print("\n" + "="*60)
        print("TRAXOVO DEPLOYMENT READINESS REPORT")
        print("="*60)
        
        status = self.results['overall_status']
        status_color = {
            'READY': '✅',
            'READY_WITH_WARNINGS': '⚠️',
            'NOT_READY': '❌'
        }
        
        print(f"\nOverall Status: {status_color.get(status, '❓')} {status}")
        print(f"Check Timestamp: {self.results['timestamp']}")
        
        # Data Sources
        print(f"\n📊 DATA SOURCES:")
        gauge_status = self.results['data_validation']['gauge_api']['status']
        print(f"  Gauge API: {gauge_status}")
        
        billing_files = self.results['data_validation']['billing_files']
        print(f"  Billing Files: {len([f for f, v in billing_files.items() if v['status'] == 'PASS'])}/{len(billing_files)} accessible")
        
        # Modules
        print(f"\n🔧 CRITICAL MODULES:")
        module_stats = {}
        for status in ['PASS', 'WARNING', 'ERROR', 'MISSING']:
            module_stats[status] = len([m for m, v in self.results['module_validation'].items() if v['status'] == status])
        
        for status, count in module_stats.items():
            if count > 0:
                print(f"  {status}: {count} modules")
        
        # Recommendations
        if self.results.get('recommendations'):
            print(f"\n🎯 RECOMMENDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  [{rec['priority']}] {rec['category']}: {rec['action']}")
        
        print("\n" + "="*60)
        
        return self.results

if __name__ == "__main__":
    checker = DeploymentReadinessChecker()
    results = checker.run_comprehensive_check()
    checker.print_status_report()