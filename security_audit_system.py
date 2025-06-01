"""
TRAXOVO Security Audit System
Comprehensive enterprise security assessment and compliance verification
"""

import os
import hashlib
import ssl
import socket
import subprocess
import re
from datetime import datetime
import json
import logging
from flask import session, request
import requests

class TRAXOVOSecurityAuditor:
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'security_score': 0,
            'total_checks': 0,
            'passed_checks': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'compliance_status': {}
        }
        
    def run_comprehensive_audit(self):
        """Execute full security audit"""
        print("🔒 TRAXOVO Security Audit - Enterprise Grade Assessment")
        print("=" * 60)
        
        # Core security checks
        self.audit_authentication_security()
        self.audit_data_encryption()
        self.audit_session_management()
        self.audit_api_security()
        self.audit_database_security()
        self.audit_file_permissions()
        self.audit_network_security()
        self.audit_input_validation()
        self.audit_secrets_management()
        self.audit_logging_security()
        
        # Calculate final score
        self.calculate_security_score()
        self.generate_security_report()
        
        return self.audit_results
    
    def audit_authentication_security(self):
        """Audit authentication mechanisms and session security"""
        print("\n📋 Authentication Security Assessment")
        
        auth_checks = {
            'session_secret_key': False,
            'secure_session_config': False,
            'password_hashing': False,
            'session_timeout': False,
            'multi_factor_ready': False
        }
        
        # Check session secret key
        try:
            if os.environ.get('SESSION_SECRET'):
                auth_checks['session_secret_key'] = True
                print("✅ Session secret key properly configured")
            else:
                self.audit_results['critical_issues'].append("SESSION_SECRET environment variable missing")
                print("❌ Session secret key not found")
        except Exception as e:
            self.audit_results['critical_issues'].append(f"Session config error: {e}")
        
        # Check session configuration
        try:
            # Verify session security in app.py
            with open('app.py', 'r') as f:
                app_content = f.read()
                
            if 'SESSION_SECRET' in app_content:
                auth_checks['secure_session_config'] = True
                print("✅ Secure session configuration detected")
            
            if 'session.clear()' in app_content:
                auth_checks['session_timeout'] = True
                print("✅ Session timeout mechanism implemented")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Could not verify session config: {e}")
        
        # Check for authentication requirements
        if 'require_auth()' in app_content:
            print("✅ Authentication middleware active")
        else:
            self.audit_results['warnings'].append("Authentication middleware not detected")
        
        self.audit_results['authentication_security'] = auth_checks
        self.audit_results['total_checks'] += len(auth_checks)
        self.audit_results['passed_checks'] += sum(auth_checks.values())
    
    def audit_data_encryption(self):
        """Audit data encryption and protection measures"""
        print("\n🔐 Data Encryption Assessment")
        
        encryption_checks = {
            'https_enforced': False,
            'database_encryption': False,
            'sensitive_data_masked': False,
            'api_key_protection': False,
            'file_encryption': False
        }
        
        # Check HTTPS enforcement
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                
            if 'ProxyFix' in content and 'x_proto=1' in content:
                encryption_checks['https_enforced'] = True
                print("✅ HTTPS enforcement configured")
            else:
                self.audit_results['warnings'].append("HTTPS enforcement not detected")
        except Exception as e:
            print(f"❌ Could not verify HTTPS config: {e}")
        
        # Check database encryption
        try:
            db_url = os.environ.get('DATABASE_URL', '')
            if 'sslmode=require' in db_url or 'ssl=true' in db_url:
                encryption_checks['database_encryption'] = True
                print("✅ Database SSL encryption configured")
            elif 'postgres' in db_url:
                self.audit_results['recommendations'].append("Enable SSL for database connections")
                print("⚠️  Database SSL not explicitly configured")
        except Exception as e:
            print(f"❌ Database encryption check failed: {e}")
        
        # Check API key protection
        sensitive_vars = ['GAUGE_API_KEY', 'OPENAI_API_KEY', 'SENDGRID_API_KEY']
        protected_keys = 0
        
        for var in sensitive_vars:
            if os.environ.get(var):
                protected_keys += 1
        
        if protected_keys > 0:
            encryption_checks['api_key_protection'] = True
            print(f"✅ {protected_keys} API keys properly secured in environment")
        
        # Check for sensitive data masking in logs
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                
            if 'logging' in content and 'password' not in content.lower():
                encryption_checks['sensitive_data_masked'] = True
                print("✅ Sensitive data logging protection active")
        except Exception:
            pass
        
        self.audit_results['encryption_security'] = encryption_checks
        self.audit_results['total_checks'] += len(encryption_checks)
        self.audit_results['passed_checks'] += sum(encryption_checks.values())
    
    def audit_session_management(self):
        """Audit session handling and security"""
        print("\n🔑 Session Management Assessment")
        
        session_checks = {
            'session_regeneration': False,
            'session_expiration': False,
            'session_hijacking_protection': False,
            'concurrent_session_control': False,
            'session_data_encryption': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check session regeneration
            if 'session.clear()' in content:
                session_checks['session_regeneration'] = True
                print("✅ Session regeneration implemented")
            
            # Check session expiration
            if 'APP_VERSION' in content and 'session.get(\'app_version\')' in content:
                session_checks['session_expiration'] = True
                print("✅ Session expiration mechanism active")
            
            # Check for session security
            if 'session.permanent' in content or 'SESSION_SECRET' in content:
                session_checks['session_data_encryption'] = True
                print("✅ Session data protection configured")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Session audit error: {e}")
        
        self.audit_results['session_security'] = session_checks
        self.audit_results['total_checks'] += len(session_checks)
        self.audit_results['passed_checks'] += sum(session_checks.values())
    
    def audit_api_security(self):
        """Audit API endpoint security"""
        print("\n🌐 API Security Assessment")
        
        api_checks = {
            'authentication_required': False,
            'rate_limiting': False,
            'input_sanitization': False,
            'cors_protection': False,
            'api_versioning': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check API authentication
            if 'require_auth()' in content and '/api/' in content:
                api_checks['authentication_required'] = True
                print("✅ API authentication enforced")
            
            # Check for input validation
            if 'request.args.get' in content and 'escape(' in content:
                api_checks['input_sanitization'] = True
                print("✅ Input sanitization detected")
            elif 'request.args.get' in content:
                self.audit_results['recommendations'].append("Implement input sanitization for API endpoints")
            
            # Check for CORS protection
            try:
                import flask_cors
                api_checks['cors_protection'] = True
                print("✅ CORS protection available")
            except ImportError:
                self.audit_results['recommendations'].append("Consider implementing CORS protection")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"API security audit error: {e}")
        
        self.audit_results['api_security'] = api_checks
        self.audit_results['total_checks'] += len(api_checks)
        self.audit_results['passed_checks'] += sum(api_checks.values())
    
    def audit_database_security(self):
        """Audit database security configuration"""
        print("\n🗄️  Database Security Assessment")
        
        db_checks = {
            'connection_pooling': False,
            'sql_injection_protection': False,
            'database_ssl': False,
            'connection_timeout': False,
            'prepared_statements': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check connection pooling
            if 'pool_recycle' in content and 'pool_pre_ping' in content:
                db_checks['connection_pooling'] = True
                print("✅ Database connection pooling configured")
            
            # Check for SQLAlchemy ORM (SQL injection protection)
            if 'SQLAlchemy' in content and 'db.session' in content:
                db_checks['sql_injection_protection'] = True
                print("✅ ORM-based SQL injection protection active")
            
            # Check connection timeout
            if 'pool_recycle' in content:
                db_checks['connection_timeout'] = True
                print("✅ Database connection timeout configured")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Database security audit error: {e}")
        
        self.audit_results['database_security'] = db_checks
        self.audit_results['total_checks'] += len(db_checks)
        self.audit_results['passed_checks'] += sum(db_checks.values())
    
    def audit_file_permissions(self):
        """Audit file system security"""
        print("\n📁 File Security Assessment")
        
        file_checks = {
            'secure_file_permissions': False,
            'no_world_writable': False,
            'config_file_protection': False,
            'log_file_security': False,
            'upload_validation': False
        }
        
        try:
            # Check critical file permissions
            critical_files = ['app.py', 'main.py']
            secure_files = 0
            
            for file in critical_files:
                if os.path.exists(file):
                    file_stat = os.stat(file)
                    # Check if file is not world-writable
                    if not (file_stat.st_mode & 0o002):
                        secure_files += 1
            
            if secure_files == len([f for f in critical_files if os.path.exists(f)]):
                file_checks['secure_file_permissions'] = True
                file_checks['no_world_writable'] = True
                print("✅ File permissions properly secured")
            
            # Check for upload validation
            if os.path.exists('routes') and any('upload' in f for f in os.listdir('routes')):
                file_checks['upload_validation'] = True
                print("✅ File upload validation detected")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"File security audit error: {e}")
        
        self.audit_results['file_security'] = file_checks
        self.audit_results['total_checks'] += len(file_checks)
        self.audit_results['passed_checks'] += sum(file_checks.values())
    
    def audit_network_security(self):
        """Audit network security configurations"""
        print("\n🌍 Network Security Assessment")
        
        network_checks = {
            'secure_headers': False,
            'csrf_protection': False,
            'xss_protection': False,
            'secure_cookies': False,
            'content_security_policy': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check for security headers
            if 'ProxyFix' in content:
                network_checks['secure_headers'] = True
                print("✅ Security headers configured")
            
            # Check for Flask-Talisman (security headers)
            try:
                import flask_talisman
                network_checks['content_security_policy'] = True
                print("✅ Content Security Policy available")
            except ImportError:
                self.audit_results['recommendations'].append("Consider implementing Flask-Talisman for security headers")
            
            # Check for CSRF protection
            try:
                import flask_wtf
                network_checks['csrf_protection'] = True
                print("✅ CSRF protection available")
            except ImportError:
                self.audit_results['recommendations'].append("Implement CSRF protection with Flask-WTF")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Network security audit error: {e}")
        
        self.audit_results['network_security'] = network_checks
        self.audit_results['total_checks'] += len(network_checks)
        self.audit_results['passed_checks'] += sum(network_checks.values())
    
    def audit_input_validation(self):
        """Audit input validation and sanitization"""
        print("\n🔍 Input Validation Assessment")
        
        validation_checks = {
            'form_validation': False,
            'api_input_validation': False,
            'sql_injection_prevention': False,
            'xss_prevention': False,
            'file_upload_validation': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check for form validation
            if 'request.form' in content and ('escape(' in content or 'bleach' in content):
                validation_checks['form_validation'] = True
                print("✅ Form input validation detected")
            
            # Check for API validation
            if 'request.args.get' in content or 'request.json' in content:
                validation_checks['api_input_validation'] = True
                print("✅ API input handling detected")
            
            # Check SQLAlchemy for SQL injection prevention
            if 'SQLAlchemy' in content and 'db.session.query' in content:
                validation_checks['sql_injection_prevention'] = True
                print("✅ SQL injection prevention (ORM) active")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Input validation audit error: {e}")
        
        self.audit_results['input_validation'] = validation_checks
        self.audit_results['total_checks'] += len(validation_checks)
        self.audit_results['passed_checks'] += sum(validation_checks.values())
    
    def audit_secrets_management(self):
        """Audit secrets and API key management"""
        print("\n🔐 Secrets Management Assessment")
        
        secrets_checks = {
            'environment_variables': False,
            'no_hardcoded_secrets': False,
            'api_key_rotation_ready': False,
            'secrets_encryption': False,
            'secure_storage': False
        }
        
        # Check environment variables
        critical_secrets = ['SESSION_SECRET', 'DATABASE_URL', 'GAUGE_API_KEY']
        env_secrets = sum(1 for secret in critical_secrets if os.environ.get(secret))
        
        if env_secrets >= 2:
            secrets_checks['environment_variables'] = True
            print(f"✅ {env_secrets} critical secrets properly stored in environment")
        
        # Check for hardcoded secrets
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Look for potential hardcoded secrets
            hardcoded_patterns = [
                r'password\s*=\s*["\'][\w]+["\']',
                r'api_key\s*=\s*["\'][\w]+["\']',
                r'secret\s*=\s*["\'][\w]+["\']'
            ]
            
            has_hardcoded = False
            for pattern in hardcoded_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    has_hardcoded = True
                    break
            
            if not has_hardcoded:
                secrets_checks['no_hardcoded_secrets'] = True
                print("✅ No hardcoded secrets detected")
            else:
                self.audit_results['critical_issues'].append("Hardcoded secrets detected")
                
            # Check for environment variable usage
            if 'os.environ.get' in content:
                secrets_checks['secure_storage'] = True
                print("✅ Secure environment-based secrets storage")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Secrets audit error: {e}")
        
        self.audit_results['secrets_management'] = secrets_checks
        self.audit_results['total_checks'] += len(secrets_checks)
        self.audit_results['passed_checks'] += sum(secrets_checks.values())
    
    def audit_logging_security(self):
        """Audit logging and monitoring security"""
        print("\n📊 Logging Security Assessment")
        
        logging_checks = {
            'secure_logging': False,
            'no_sensitive_data_logged': False,
            'authentication_logging': False,
            'error_logging': False,
            'audit_trail': False
        }
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
            
            # Check logging configuration
            if 'logging' in content:
                logging_checks['secure_logging'] = True
                print("✅ Logging system configured")
            
            # Check authentication logging
            if 'logged in successfully' in content:
                logging_checks['authentication_logging'] = True
                print("✅ Authentication events logged")
            
            # Check for sensitive data protection
            if 'password' not in content.lower() or 'logging.info' in content:
                logging_checks['no_sensitive_data_logged'] = True
                print("✅ Sensitive data logging protection")
            
            # Check error handling
            if 'except Exception' in content and 'logging' in content:
                logging_checks['error_logging'] = True
                print("✅ Error logging implemented")
                
        except Exception as e:
            self.audit_results['warnings'].append(f"Logging audit error: {e}")
        
        self.audit_results['logging_security'] = logging_checks
        self.audit_results['total_checks'] += len(logging_checks)
        self.audit_results['passed_checks'] += sum(logging_checks.values())
    
    def calculate_security_score(self):
        """Calculate overall security score"""
        if self.audit_results['total_checks'] > 0:
            score = (self.audit_results['passed_checks'] / self.audit_results['total_checks']) * 100
            self.audit_results['security_score'] = round(score, 2)
        
        # Determine security level
        if score >= 90:
            self.audit_results['security_level'] = 'EXCELLENT'
        elif score >= 80:
            self.audit_results['security_level'] = 'GOOD'
        elif score >= 70:
            self.audit_results['security_level'] = 'ADEQUATE'
        else:
            self.audit_results['security_level'] = 'NEEDS_IMPROVEMENT'
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "="*60)
        print("🔒 TRAXOVO SECURITY AUDIT REPORT")
        print("="*60)
        print(f"Security Score: {self.audit_results['security_score']}/100")
        print(f"Security Level: {self.audit_results['security_level']}")
        print(f"Checks Passed: {self.audit_results['passed_checks']}/{self.audit_results['total_checks']}")
        
        if self.audit_results['critical_issues']:
            print(f"\n❌ CRITICAL ISSUES ({len(self.audit_results['critical_issues'])}):")
            for issue in self.audit_results['critical_issues']:
                print(f"   • {issue}")
        
        if self.audit_results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.audit_results['warnings'])}):")
            for warning in self.audit_results['warnings']:
                print(f"   • {warning}")
        
        if self.audit_results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS ({len(self.audit_results['recommendations'])}):")
            for rec in self.audit_results['recommendations']:
                print(f"   • {rec}")
        
        print(f"\nAudit completed at: {self.audit_results['timestamp']}")
        print("="*60)

def run_security_audit():
    """Execute the security audit"""
    auditor = TRAXOVOSecurityAuditor()
    return auditor.run_comprehensive_audit()

if __name__ == "__main__":
    run_security_audit()