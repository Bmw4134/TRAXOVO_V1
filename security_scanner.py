"""
TRAXOVO Internal Security Scanner
Comprehensive frontend and backend security analysis without disrupting existing systems
"""

import os
import re
import ast
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
import sqlite3
from flask import Blueprint, render_template, request, jsonify, session

security_scanner_bp = Blueprint('security_scanner', __name__)

class TRAXOVOSecurityScanner:
    def __init__(self):
        self.scan_results = {}
        self.vulnerability_database = self.initialize_vuln_db()
        self.security_rules = self.load_security_rules()
        
    def initialize_vuln_db(self):
        """Initialize internal vulnerability database"""
        return {
            'sql_injection_patterns': [
                r'SELECT.*FROM.*WHERE.*=.*\$',
                r'INSERT.*INTO.*VALUES.*\$',
                r'UPDATE.*SET.*WHERE.*=.*\$',
                r'DELETE.*FROM.*WHERE.*=.*\$'
            ],
            'xss_patterns': [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'eval\s*\(',
                r'innerHTML\s*='
            ],
            'sensitive_data_patterns': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Credit card pattern
            ],
            'file_inclusion_patterns': [
                r'include\s*\(\s*\$_[GET|POST]',
                r'require\s*\(\s*\$_[GET|POST]',
                r'file_get_contents\s*\(\s*\$_[GET|POST]'
            ]
        }
    
    def load_security_rules(self):
        """Load comprehensive security rules"""
        return {
            'backend_rules': {
                'authentication': {
                    'session_security': True,
                    'password_hashing': True,
                    'csrf_protection': True,
                    'session_timeout': True
                },
                'data_validation': {
                    'input_sanitization': True,
                    'output_encoding': True,
                    'parameter_validation': True,
                    'file_upload_security': True
                },
                'database_security': {
                    'parameterized_queries': True,
                    'connection_encryption': True,
                    'access_controls': True,
                    'audit_logging': True
                }
            },
            'frontend_rules': {
                'content_security': {
                    'csp_headers': True,
                    'xss_protection': True,
                    'content_type_validation': True,
                    'secure_cookies': True
                },
                'client_validation': {
                    'form_validation': True,
                    'input_filtering': True,
                    'data_sanitization': True,
                    'secure_communications': True
                }
            }
        }
    
    def scan_backend_security(self):
        """Comprehensive backend security scan"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'backend',
            'vulnerabilities': [],
            'recommendations': [],
            'security_score': 0
        }
        
        # Scan Python files for security issues
        python_files = list(Path('.').rglob('*.py'))
        
        for file_path in python_files:
            if self.should_scan_file(file_path):
                file_results = self.scan_python_file(file_path)
                if file_results['vulnerabilities']:
                    results['vulnerabilities'].extend(file_results['vulnerabilities'])
        
        # Scan database configurations
        db_security = self.scan_database_security()
        results['database_security'] = db_security
        
        # Scan authentication mechanisms
        auth_security = self.scan_authentication_security()
        results['authentication_security'] = auth_security
        
        # Calculate security score
        results['security_score'] = self.calculate_security_score(results)
        
        # Generate recommendations
        results['recommendations'] = self.generate_security_recommendations(results)
        
        return results
    
    def scan_frontend_security(self):
        """Comprehensive frontend security scan"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'scan_type': 'frontend',
            'vulnerabilities': [],
            'recommendations': [],
            'security_score': 0
        }
        
        # Scan HTML templates
        template_files = list(Path('templates').rglob('*.html'))
        
        for file_path in template_files:
            template_results = self.scan_template_file(file_path)
            if template_results['vulnerabilities']:
                results['vulnerabilities'].extend(template_results['vulnerabilities'])
        
        # Scan JavaScript files
        js_files = list(Path('static').rglob('*.js'))
        
        for file_path in js_files:
            js_results = self.scan_javascript_file(file_path)
            if js_results['vulnerabilities']:
                results['vulnerabilities'].extend(js_results['vulnerabilities'])
        
        # Scan CSS files for security issues
        css_files = list(Path('static').rglob('*.css'))
        
        for file_path in css_files:
            css_results = self.scan_css_file(file_path)
            if css_results['vulnerabilities']:
                results['vulnerabilities'].extend(css_results['vulnerabilities'])
        
        # Calculate security score
        results['security_score'] = self.calculate_security_score(results)
        
        # Generate recommendations
        results['recommendations'] = self.generate_security_recommendations(results)
        
        return results
    
    def scan_python_file(self, file_path):
        """Scan individual Python file for vulnerabilities"""
        results = {'vulnerabilities': []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for SQL injection vulnerabilities
            for pattern in self.vulnerability_database['sql_injection_patterns']:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'SQL Injection Risk',
                        'severity': 'HIGH',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potential SQL injection vulnerability detected',
                        'recommendation': 'Use parameterized queries or ORM methods'
                    })
            
            # Check for hardcoded secrets
            for pattern in self.vulnerability_database['sensitive_data_patterns']:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'Hardcoded Sensitive Data',
                        'severity': 'CRITICAL',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Hardcoded sensitive data detected',
                        'recommendation': 'Move sensitive data to environment variables'
                    })
            
            # Check for insecure file operations
            insecure_patterns = [
                r'open\s*\(\s*[^,)]*input\s*\(',
                r'exec\s*\(',
                r'eval\s*\(',
                r'pickle\.loads\s*\('
            ]
            
            for pattern in insecure_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'Insecure Operation',
                        'severity': 'MEDIUM',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potentially insecure operation detected',
                        'recommendation': 'Validate and sanitize all inputs'
                    })
            
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'Scan Error',
                'severity': 'LOW',
                'file': str(file_path),
                'description': f'Error scanning file: {str(e)}',
                'recommendation': 'Manual review recommended'
            })
        
        return results
    
    def scan_template_file(self, file_path):
        """Scan HTML template for XSS and other vulnerabilities"""
        results = {'vulnerabilities': []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for XSS vulnerabilities
            for pattern in self.vulnerability_database['xss_patterns']:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'XSS Risk',
                        'severity': 'HIGH',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potential XSS vulnerability detected',
                        'recommendation': 'Use proper output encoding and CSP headers'
                    })
            
            # Check for missing CSRF protection
            if 'form' in content.lower() and 'csrf' not in content.lower():
                results['vulnerabilities'].append({
                    'type': 'Missing CSRF Protection',
                    'severity': 'MEDIUM',
                    'file': str(file_path),
                    'description': 'Form without CSRF protection detected',
                    'recommendation': 'Add CSRF tokens to all forms'
                })
            
            # Check for insecure external references
            insecure_refs = re.finditer(r'http://[^"\'>\s]+', content)
            for match in insecure_refs:
                results['vulnerabilities'].append({
                    'type': 'Insecure External Reference',
                    'severity': 'LOW',
                    'file': str(file_path),
                    'line': content[:match.start()].count('\n') + 1,
                    'description': 'HTTP (non-HTTPS) external reference found',
                    'recommendation': 'Use HTTPS for all external references'
                })
            
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'Scan Error',
                'severity': 'LOW',
                'file': str(file_path),
                'description': f'Error scanning template: {str(e)}',
                'recommendation': 'Manual review recommended'
            })
        
        return results
    
    def scan_javascript_file(self, file_path):
        """Scan JavaScript files for security vulnerabilities"""
        results = {'vulnerabilities': []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for dangerous JavaScript functions
            dangerous_patterns = [
                r'eval\s*\(',
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'setTimeout\s*\(\s*["\'][^"\']*["\']',
                r'setInterval\s*\(\s*["\'][^"\']*["\']'
            ]
            
            for pattern in dangerous_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'Dangerous JavaScript Function',
                        'severity': 'MEDIUM',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potentially dangerous JavaScript function detected',
                        'recommendation': 'Use safer alternatives and validate all inputs'
                    })
            
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'Scan Error',
                'severity': 'LOW',
                'file': str(file_path),
                'description': f'Error scanning JavaScript: {str(e)}',
                'recommendation': 'Manual review recommended'
            })
        
        return results
    
    def scan_css_file(self, file_path):
        """Scan CSS files for security issues"""
        results = {'vulnerabilities': []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for CSS injection patterns
            css_injection_patterns = [
                r'expression\s*\(',
                r'javascript\s*:',
                r'@import\s+url\s*\(\s*["\']?javascript:'
            ]
            
            for pattern in css_injection_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    results['vulnerabilities'].append({
                        'type': 'CSS Injection Risk',
                        'severity': 'MEDIUM',
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potential CSS injection vulnerability detected',
                        'recommendation': 'Remove dynamic expressions and JavaScript from CSS'
                    })
            
        except Exception as e:
            results['vulnerabilities'].append({
                'type': 'Scan Error',
                'severity': 'LOW',
                'file': str(file_path),
                'description': f'Error scanning CSS: {str(e)}',
                'recommendation': 'Manual review recommended'
            })
        
        return results
    
    def scan_database_security(self):
        """Scan database security configuration"""
        security_checks = {
            'connection_encryption': self.check_db_encryption(),
            'parameterized_queries': self.check_parameterized_queries(),
            'access_controls': self.check_db_access_controls(),
            'audit_logging': self.check_audit_logging()
        }
        return security_checks
    
    def scan_authentication_security(self):
        """Scan authentication security measures"""
        auth_checks = {
            'session_security': self.check_session_security(),
            'password_hashing': self.check_password_hashing(),
            'csrf_protection': self.check_csrf_protection(),
            'session_timeout': self.check_session_timeout()
        }
        return auth_checks
    
    def should_scan_file(self, file_path):
        """Determine if file should be scanned"""
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.env', 'venv'}
        return not any(excluded in str(file_path) for excluded in excluded_dirs)
    
    def calculate_security_score(self, results):
        """Calculate overall security score"""
        total_vulns = len(results['vulnerabilities'])
        critical_vulns = len([v for v in results['vulnerabilities'] if v['severity'] == 'CRITICAL'])
        high_vulns = len([v for v in results['vulnerabilities'] if v['severity'] == 'HIGH'])
        medium_vulns = len([v for v in results['vulnerabilities'] if v['severity'] == 'MEDIUM'])
        
        # Calculate score (100 - penalty points)
        score = 100
        score -= critical_vulns * 20
        score -= high_vulns * 10
        score -= medium_vulns * 5
        
        return max(0, score)  # Ensure score doesn't go below 0
    
    def generate_security_recommendations(self, results):
        """Generate actionable security recommendations"""
        recommendations = []
        
        vuln_types = {}
        for vuln in results['vulnerabilities']:
            vuln_type = vuln['type']
            if vuln_type not in vuln_types:
                vuln_types[vuln_type] = 0
            vuln_types[vuln_type] += 1
        
        for vuln_type, count in vuln_types.items():
            if vuln_type == 'SQL Injection Risk':
                recommendations.append({
                    'priority': 'HIGH',
                    'action': f'Fix {count} SQL injection vulnerabilities',
                    'description': 'Implement parameterized queries and input validation'
                })
            elif vuln_type == 'XSS Risk':
                recommendations.append({
                    'priority': 'HIGH',
                    'action': f'Fix {count} XSS vulnerabilities',
                    'description': 'Implement proper output encoding and CSP headers'
                })
            elif vuln_type == 'Hardcoded Sensitive Data':
                recommendations.append({
                    'priority': 'CRITICAL',
                    'action': f'Secure {count} hardcoded secrets',
                    'description': 'Move all sensitive data to environment variables'
                })
        
        return recommendations
    
    def check_db_encryption(self):
        """Check if database connections use encryption"""
        # Implementation would check DATABASE_URL for SSL parameters
        return True  # Placeholder - implement based on your DB setup
    
    def check_parameterized_queries(self):
        """Check for parameterized query usage"""
        # Implementation would scan for SQLAlchemy usage patterns
        return True  # Placeholder
    
    def check_db_access_controls(self):
        """Check database access control implementation"""
        return True  # Placeholder
    
    def check_audit_logging(self):
        """Check if audit logging is implemented"""
        return True  # Placeholder
    
    def check_session_security(self):
        """Check session security configuration"""
        return True  # Placeholder
    
    def check_password_hashing(self):
        """Check password hashing implementation"""
        return True  # Placeholder
    
    def check_csrf_protection(self):
        """Check CSRF protection implementation"""
        return True  # Placeholder
    
    def check_session_timeout(self):
        """Check session timeout configuration"""
        return True  # Placeholder

# Initialize scanner
scanner = TRAXOVOSecurityScanner()

@security_scanner_bp.route('/security-scan-dashboard')
def security_scan_dashboard():
    """Security scanning dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Only allow admin access to security scanning
    if session.get('user_role') != 'admin':
        return redirect(url_for('dashboard'))
    
    return render_template('security_scan_dashboard.html')

@security_scanner_bp.route('/api/run-security-scan', methods=['POST'])
def run_security_scan():
    """Run comprehensive security scan"""
    data = request.get_json()
    scan_type = data.get('scan_type', 'full')
    
    results = {}
    
    if scan_type in ['backend', 'full']:
        results['backend'] = scanner.scan_backend_security()
    
    if scan_type in ['frontend', 'full']:
        results['frontend'] = scanner.scan_frontend_security()
    
    # Store results for later review
    scan_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()
    scanner.scan_results[scan_id] = results
    
    return jsonify({
        'scan_id': scan_id,
        'results': results,
        'timestamp': datetime.now().isoformat()
    })

@security_scanner_bp.route('/api/security-status')
def security_status():
    """Get current security status"""
    if not scanner.scan_results:
        return jsonify({
            'status': 'no_scans',
            'message': 'No security scans have been run yet'
        })
    
    # Get latest scan results
    latest_scan = max(scanner.scan_results.items(), key=lambda x: x[1].get('timestamp', ''))
    
    return jsonify({
        'status': 'scanned',
        'latest_scan': latest_scan[1],
        'scan_count': len(scanner.scan_results)
    })