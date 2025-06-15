#!/usr/bin/env python3
"""
DWC Evolution QA Validation System
Comprehensive module testing and validation for production readiness
"""

import subprocess
import json
import os
import time
from datetime import datetime
import requests

class DWCQAValidator:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, module_name, test_name, status, details=""):
        """Log test results"""
        result = {
            'module': module_name,
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status}] {module_name} - {test_name}: {details}")
        
    def test_landing_page(self):
        """Test landing page functionality"""
        try:
            response = requests.get('http://localhost:5000/', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Check for key landing page elements
                checks = [
                    ('Hero Section', 'DWC Evolution' in content),
                    ('AI Demo Module', 'Let Us Reinvent Your Website' in content),
                    ('Investor Mode', 'investor-mode-toggle' in content),
                    ('Feature Cards', 'feature-card' in content),
                    ('Navigation', 'Access Platform' in content)
                ]
                
                for check_name, passed in checks:
                    status = 'PASS' if passed else 'FAIL'
                    self.log_test('Landing Page', check_name, status)
                    
                return True
            else:
                self.log_test('Landing Page', 'HTTP Response', 'FAIL', f'Status: {response.status_code}')
                return False
                
        except Exception as e:
            self.log_test('Landing Page', 'Connection', 'FAIL', str(e))
            return False
    
    def test_authentication_system(self):
        """Test authentication functionality"""
        try:
            # Test login page access
            response = requests.get('http://localhost:5000/login', timeout=10)
            if response.status_code == 200:
                self.log_test('Authentication', 'Login Page Access', 'PASS')
                
                # Test login form elements
                content = response.text
                form_elements = [
                    ('Username Field', 'name="username"' in content),
                    ('Password Field', 'name="password"' in content),
                    ('Security Notice', 'Multi-factor authentication' in content),
                    ('Login Button', 'Access Platform' in content)
                ]
                
                for element_name, present in form_elements:
                    status = 'PASS' if present else 'FAIL'
                    self.log_test('Authentication', element_name, status)
                    
                return True
            else:
                self.log_test('Authentication', 'Login Page', 'FAIL', f'Status: {response.status_code}')
                return False
                
        except Exception as e:
            self.log_test('Authentication', 'Login Test', 'FAIL', str(e))
            return False
    
    def test_api_endpoints(self):
        """Test API endpoint functionality"""
        endpoints = [
            ('/health', 'Health Check'),
            ('/api/system-metrics', 'System Metrics'),
            ('/api/ragle-fleet-data', 'Fleet Data')
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f'http://localhost:5000{endpoint}', timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test('API Endpoints', name, 'PASS', f'Data keys: {list(data.keys())[:3]}')
                    except:
                        self.log_test('API Endpoints', name, 'PASS', 'Response received')
                else:
                    self.log_test('API Endpoints', name, 'FAIL', f'Status: {response.status_code}')
            except Exception as e:
                self.log_test('API Endpoints', name, 'FAIL', str(e))
    
    def test_system_metrics(self):
        """Test real system metrics collection"""
        try:
            import psutil
            
            # Test memory metrics
            memory = psutil.virtual_memory()
            self.log_test('System Metrics', 'Memory Collection', 'PASS', f'{memory.percent}% used')
            
            # Test CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.log_test('System Metrics', 'CPU Collection', 'PASS', f'{cpu_percent}% usage')
            
            # Test disk metrics
            disk = psutil.disk_usage('/')
            self.log_test('System Metrics', 'Disk Collection', 'PASS', f'{disk.percent}% used')
            
            # Test process count
            process_count = len(psutil.pids())
            self.log_test('System Metrics', 'Process Count', 'PASS', f'{process_count} processes')
            
            return True
            
        except ImportError:
            self.log_test('System Metrics', 'PSUtil Import', 'FAIL', 'psutil not available')
            return False
        except Exception as e:
            self.log_test('System Metrics', 'Collection Error', 'FAIL', str(e))
            return False
    
    def test_ai_integration(self):
        """Test AI API integration"""
        # Check OpenAI API key
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            self.log_test('AI Integration', 'OpenAI Key', 'PASS', 'Key configured')
            
            # Test AI endpoint
            try:
                test_data = {'query': 'Test query', 'provider': 'openai'}
                response = requests.post('http://localhost:5000/api/ai-query', 
                                       json=test_data, timeout=30)
                if response.status_code == 200:
                    self.log_test('AI Integration', 'OpenAI Endpoint', 'PASS')
                else:
                    self.log_test('AI Integration', 'OpenAI Endpoint', 'FAIL', f'Status: {response.status_code}')
            except Exception as e:
                self.log_test('AI Integration', 'OpenAI Endpoint', 'FAIL', str(e))
        else:
            self.log_test('AI Integration', 'OpenAI Key', 'FAIL', 'Key not configured')
        
        # Check Perplexity API key
        perplexity_key = os.environ.get('PERPLEXITY_API_KEY')
        if perplexity_key:
            self.log_test('AI Integration', 'Perplexity Key', 'PASS', 'Key configured')
        else:
            self.log_test('AI Integration', 'Perplexity Key', 'FAIL', 'Key not configured')
    
    def test_fleet_data_processing(self):
        """Test RAGLE fleet data processing"""
        try:
            response = requests.get('http://localhost:5000/api/ragle-fleet-data', timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Validate fleet data structure
                    sample_asset = data[0]
                    required_fields = ['asset_id', 'location', 'status', 'utilization', 'driver_id']
                    
                    missing_fields = [field for field in required_fields if field not in sample_asset]
                    
                    if not missing_fields:
                        self.log_test('Fleet Data', 'Data Structure', 'PASS', f'{len(data)} assets')
                        
                        # Check for DFW operations data
                        dfw_assets = [a for a in data if 'DFW' in a.get('asset_id', '')]
                        if dfw_assets:
                            self.log_test('Fleet Data', 'DFW Operations', 'PASS', f'{len(dfw_assets)} DFW assets')
                        else:
                            self.log_test('Fleet Data', 'DFW Operations', 'FAIL', 'No DFW assets found')
                            
                    else:
                        self.log_test('Fleet Data', 'Data Structure', 'FAIL', f'Missing: {missing_fields}')
                else:
                    self.log_test('Fleet Data', 'Data Response', 'FAIL', 'Empty or invalid data')
            else:
                self.log_test('Fleet Data', 'API Response', 'FAIL', f'Status: {response.status_code}')
                
        except Exception as e:
            self.log_test('Fleet Data', 'Processing Error', 'FAIL', str(e))
    
    def test_database_connectivity(self):
        """Test database connectivity"""
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            self.log_test('Database', 'URL Configuration', 'PASS', 'DATABASE_URL configured')
            
            # Test basic connectivity through health endpoint
            try:
                response = requests.get('http://localhost:5000/health', timeout=10)
                if response.status_code == 200:
                    self.log_test('Database', 'Health Check', 'PASS', 'Application responding')
                else:
                    self.log_test('Database', 'Health Check', 'FAIL', f'Status: {response.status_code}')
            except Exception as e:
                self.log_test('Database', 'Health Check', 'FAIL', str(e))
        else:
            self.log_test('Database', 'URL Configuration', 'FAIL', 'DATABASE_URL not set')
    
    def test_ui_responsiveness(self):
        """Test UI responsiveness and mobile optimization"""
        try:
            # Test landing page mobile elements
            response = requests.get('http://localhost:5000/', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                mobile_checks = [
                    ('Responsive Meta Tag', 'viewport' in content),
                    ('Mobile CSS', '@media' in content),
                    ('Flexible Layout', 'flex' in content or 'grid' in content),
                    ('Touch Friendly', 'cursor: pointer' in content)
                ]
                
                for check_name, passed in mobile_checks:
                    status = 'PASS' if passed else 'FAIL'
                    self.log_test('UI Responsiveness', check_name, status)
                    
        except Exception as e:
            self.log_test('UI Responsiveness', 'Test Error', 'FAIL', str(e))
    
    def run_comprehensive_validation(self):
        """Run complete DWC Evolution validation suite"""
        print("=" * 60)
        print("DWC EVOLUTION QA VALIDATION SYSTEM")
        print("=" * 60)
        print(f"Started: {self.start_time}")
        print()
        
        # Run all test modules
        test_modules = [
            ('Landing Page', self.test_landing_page),
            ('Authentication', self.test_authentication_system),
            ('API Endpoints', self.test_api_endpoints),
            ('System Metrics', self.test_system_metrics),
            ('AI Integration', self.test_ai_integration),
            ('Fleet Data', self.test_fleet_data_processing),
            ('Database', self.test_database_connectivity),
            ('UI Responsiveness', self.test_ui_responsiveness)
        ]
        
        for module_name, test_function in test_modules:
            print(f"\n--- Testing {module_name} ---")
            try:
                test_function()
            except Exception as e:
                self.log_test(module_name, 'Module Error', 'FAIL', str(e))
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive QA summary report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("QA VALIDATION SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Completed: {end_time}")
        
        # Group results by module
        modules = {}
        for result in self.test_results:
            module = result['module']
            if module not in modules:
                modules[module] = {'pass': 0, 'fail': 0, 'tests': []}
            modules[module][result['status'].lower()] += 1
            modules[module]['tests'].append(result)
        
        print("\nMODULE BREAKDOWN:")
        print("-" * 40)
        for module, stats in modules.items():
            total = stats['pass'] + stats['fail']
            module_success = (stats['pass'] / total * 100) if total > 0 else 0
            print(f"{module}: {stats['pass']}/{total} ({module_success:.1f}%)")
        
        # Show failed tests
        failed_results = [r for r in self.test_results if r['status'] == 'FAIL']
        if failed_results:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in failed_results:
                print(f"• {result['module']} - {result['test']}: {result['details']}")
        
        # Production readiness assessment
        print(f"\nPRODUCTION READINESS: {'READY' if success_rate >= 85 else 'NEEDS ATTENTION'}")
        
        # Save results to file
        report_data = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'duration': duration,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'modules': modules,
            'detailed_results': self.test_results
        }
        
        with open('dwc_qa_validation_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: dwc_qa_validation_report.json")
        print("=" * 60)

def main():
    """Run DWC Evolution QA validation"""
    validator = DWCQAValidator()
    validator.run_comprehensive_validation()

if __name__ == '__main__':
    main()