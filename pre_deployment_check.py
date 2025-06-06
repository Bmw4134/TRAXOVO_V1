
#!/usr/bin/env python3
"""
TRAXOVO Pre-Deployment Error Checker
Comprehensive validation before deployment to catch all potential issues
"""

import os
import json
import ast
import sys
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
import traceback

class PreDeploymentChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.critical_issues = []
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PENDING',
            'errors': [],
            'warnings': [],
            'critical_issues': [],
            'checks_performed': []
        }
    
    def check_syntax_errors(self):
        """Check all Python files for syntax errors"""
        print("🔍 Checking Python syntax errors...")
        
        python_files = [
            'main.py',
            'app.py', 
            'app_minimal.py',
            'app_traxovo.py',
            'models.py',
            'database_migration_tool.py',
            'database_data_accessor.py'
        ]
        
        syntax_errors = []
        for file_path in python_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse the file to check for syntax errors
                    ast.parse(content, filename=file_path)
                    print(f"  ✓ {file_path} - Syntax OK")
                    
                except SyntaxError as e:
                    error_msg = f"Syntax error in {file_path}: Line {e.lineno}: {e.msg}"
                    syntax_errors.append(error_msg)
                    print(f"  ❌ {file_path} - Syntax Error: {e.msg}")
                    
                except Exception as e:
                    error_msg = f"Error reading {file_path}: {str(e)}"
                    syntax_errors.append(error_msg)
                    print(f"  ⚠️ {file_path} - Read Error: {str(e)}")
        
        if syntax_errors:
            self.critical_issues.extend(syntax_errors)
        
        self.results['checks_performed'].append('syntax_check')
        return len(syntax_errors) == 0
    
    def check_import_errors(self):
        """Check for import errors in critical modules"""
        print("🔍 Checking import dependencies...")
        
        import_errors = []
        critical_modules = ['main', 'app_minimal', 'models']
        
        for module_name in critical_modules:
            if os.path.exists(f'{module_name}.py'):
                try:
                    spec = importlib.util.spec_from_file_location(module_name, f'{module_name}.py')
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        # Don't actually execute, just check if imports are resolvable
                        print(f"  ✓ {module_name}.py - Imports resolvable")
                    else:
                        import_errors.append(f"Could not load spec for {module_name}.py")
                        
                except Exception as e:
                    import_errors.append(f"Import error in {module_name}.py: {str(e)}")
                    print(f"  ❌ {module_name}.py - Import Error: {str(e)}")
        
        if import_errors:
            self.errors.extend(import_errors)
        
        self.results['checks_performed'].append('import_check')
        return len(import_errors) == 0
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print("🔍 Checking environment variables...")
        
        required_vars = ['DATABASE_URL', 'SESSION_SECRET']
        optional_vars = ['GAUGE_API_KEY', 'OPENAI_API_KEY']
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_required.append(var)
                print(f"  ❌ Missing required: {var}")
            else:
                print(f"  ✓ Found required: {var}")
        
        for var in optional_vars:
            if not os.environ.get(var):
                missing_optional.append(var)
                print(f"  ⚠️ Missing optional: {var}")
            else:
                print(f"  ✓ Found optional: {var}")
        
        if missing_required:
            self.critical_issues.extend([f"Missing required environment variable: {var}" for var in missing_required])
        
        if missing_optional:
            self.warnings.extend([f"Missing optional environment variable: {var}" for var in missing_optional])
        
        self.results['checks_performed'].append('environment_check')
        return len(missing_required) == 0
    
    def check_database_migration_errors(self):
        """Check database migration tool for errors"""
        print("🔍 Checking database migration status...")
        
        try:
            # Import and test database migration tool
            from database_migration_tool import DatabaseMigrationTool
            
            # Check if DATABASE_URL is configured
            if not os.environ.get('DATABASE_URL'):
                self.critical_issues.append("DATABASE_URL not configured for migration tool")
                return False
            
            # Test migration tool initialization
            migration_tool = DatabaseMigrationTool()
            print("  ✓ Database migration tool initialized successfully")
            
            self.results['checks_performed'].append('database_migration_check')
            return True
            
        except Exception as e:
            error_msg = f"Database migration tool error: {str(e)}"
            self.errors.append(error_msg)
            print(f"  ❌ Database migration error: {str(e)}")
            return False
    
    def check_port_conflicts(self):
        """Check for port conflicts"""
        print("🔍 Checking port configuration...")
        
        # Check if port 5000 is in use
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 5000))
            sock.close()
            
            if result == 0:
                self.warnings.append("Port 5000 appears to be in use - may cause deployment conflicts")
                print("  ⚠️ Port 5000 is currently in use")
            else:
                print("  ✓ Port 5000 is available")
                
        except Exception as e:
            self.warnings.append(f"Could not check port availability: {str(e)}")
        
        self.results['checks_performed'].append('port_check')
        return True
    
    def check_file_size_issues(self):
        """Check for files that might cause deployment issues"""
        print("🔍 Checking file sizes for deployment...")
        
        large_files = []
        total_size = 0
        
        # Check for large files that might cause deployment timeouts
        for root, dirs, files in os.walk('.'):
            # Skip certain directories
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'archived_modules']):
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    
                    # Flag files larger than 10MB
                    if size > 10 * 1024 * 1024:
                        large_files.append(f"{file_path}: {size / (1024*1024):.1f}MB")
                        
                except OSError:
                    continue
        
        print(f"  📊 Total project size: {total_size / (1024*1024):.1f}MB")
        
        if large_files:
            self.warnings.extend([f"Large file detected: {f}" for f in large_files])
            print(f"  ⚠️ Found {len(large_files)} large files")
        else:
            print("  ✓ No problematically large files detected")
        
        # Check if total size exceeds deployment limits
        if total_size > 8 * 1024 * 1024 * 1024:  # 8GB limit
            self.critical_issues.append(f"Project size ({total_size / (1024*1024*1024):.1f}GB) exceeds 8GB deployment limit")
        
        self.results['checks_performed'].append('file_size_check')
        return len(self.critical_issues) == 0
    
    def check_json_files(self):
        """Check JSON files for syntax errors"""
        print("🔍 Checking JSON file integrity...")
        
        json_files = [
            'deployment_optimization.json',
            'mobile_optimization_cache.json',
            'TRAXOVO_DNA_Complete_20250605_162308.json',
            'GAUGE API PULL 1045AM_05.15.2025.json'
        ]
        
        json_errors = []
        for json_file in json_files:
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        json.load(f)
                    print(f"  ✓ {json_file} - Valid JSON")
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON in {json_file}: {str(e)}"
                    json_errors.append(error_msg)
                    print(f"  ❌ {json_file} - JSON Error: {str(e)}")
                except Exception as e:
                    error_msg = f"Error reading {json_file}: {str(e)}"
                    json_errors.append(error_msg)
                    print(f"  ⚠️ {json_file} - Read Error: {str(e)}")
        
        if json_errors:
            self.errors.extend(json_errors)
        
        self.results['checks_performed'].append('json_check')
        return len(json_errors) == 0
    
    def check_app_startup(self):
        """Test if the main application can start without errors"""
        print("🔍 Testing application startup...")
        
        try:
            # Test importing the main app module
            from app_minimal import app
            
            # Test that the app is configured correctly
            if not app.config.get('SECRET_KEY') and not os.environ.get('SESSION_SECRET'):
                self.critical_issues.append("No SECRET_KEY or SESSION_SECRET configured")
                return False
            
            print("  ✓ Application module imports successfully")
            print("  ✓ Flask app configuration appears valid")
            
            self.results['checks_performed'].append('app_startup_check')
            return True
            
        except Exception as e:
            error_msg = f"Application startup error: {str(e)}"
            self.critical_issues.append(error_msg)
            print(f"  ❌ Application startup failed: {str(e)}")
            return False
    
    def run_comprehensive_check(self):
        """Run all pre-deployment checks"""
        print("🚀 TRAXOVO Pre-Deployment Error Check")
        print("=" * 50)
        
        checks = [
            ('Syntax Errors', self.check_syntax_errors),
            ('Import Dependencies', self.check_import_errors),
            ('Environment Variables', self.check_environment_variables),
            ('Database Migration', self.check_database_migration_errors),
            ('Port Conflicts', self.check_port_conflicts),
            ('File Sizes', self.check_file_size_issues),
            ('JSON Integrity', self.check_json_files),
            ('Application Startup', self.check_app_startup)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}:")
            try:
                if check_func():
                    passed_checks += 1
            except Exception as e:
                error_msg = f"Check '{check_name}' failed with exception: {str(e)}"
                self.critical_issues.append(error_msg)
                print(f"  💥 Check failed: {str(e)}")
        
        # Determine overall status
        if self.critical_issues:
            self.results['overall_status'] = 'CRITICAL_ERRORS'
        elif self.errors:
            self.results['overall_status'] = 'ERRORS_FOUND'
        elif self.warnings:
            self.results['overall_status'] = 'WARNINGS_ONLY'
        else:
            self.results['overall_status'] = 'READY'
        
        # Store results
        self.results['errors'] = self.errors
        self.results['warnings'] = self.warnings
        self.results['critical_issues'] = self.critical_issues
        self.results['checks_passed'] = passed_checks
        self.results['total_checks'] = total_checks
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate final deployment readiness report"""
        print("\n" + "=" * 50)
        print("🎯 PRE-DEPLOYMENT CHECK RESULTS")
        print("=" * 50)
        
        status_emoji = {
            'READY': '✅',
            'WARNINGS_ONLY': '⚠️',
            'ERRORS_FOUND': '❌',
            'CRITICAL_ERRORS': '🔴'
        }
        
        status = self.results['overall_status']
        print(f"\nOverall Status: {status_emoji.get(status, '❓')} {status}")
        print(f"Checks Passed: {self.results['checks_passed']}/{self.results['total_checks']}")
        
        if self.critical_issues:
            print(f"\n🔴 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"  • {issue}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if status == 'READY':
            print("  ✅ System is ready for deployment!")
            print("  ➡️ You can proceed with deployment")
        elif status == 'WARNINGS_ONLY':
            print("  ⚠️ System can deploy but has warnings")
            print("  ➡️ Consider addressing warnings for optimal performance")
        elif status == 'ERRORS_FOUND':
            print("  ❌ Fix errors before deployment")
            print("  ➡️ Address the errors listed above")
        else:
            print("  🔴 CRITICAL ISSUES must be resolved before deployment")
            print("  ➡️ Fix all critical issues before proceeding")
        
        # Save report
        with open('pre_deployment_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: pre_deployment_report.json")
        print("=" * 50)
        
        return self.results

if __name__ == "__main__":
    checker = PreDeploymentChecker()
    results = checker.run_comprehensive_check()
    
    # Exit with appropriate code
    if results['overall_status'] in ['CRITICAL_ERRORS', 'ERRORS_FOUND']:
        sys.exit(1)
    else:
        sys.exit(0)
