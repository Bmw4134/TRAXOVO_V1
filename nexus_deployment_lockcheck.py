"""
NEXUS Deployment Lockcheck
Pre-deployment validation system to ensure production readiness
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
import logging

class NexusDeploymentLockcheck:
    """Comprehensive pre-deployment validation system"""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        self.deployment_ready = False
        
    def run_full_lockcheck(self) -> dict:
        """Execute complete deployment lockcheck"""
        
        print("🔐 NEXUS DEPLOYMENT LOCKCHECK INITIATED")
        print("=" * 50)
        
        # Execute all validation checks
        self.check_branding_configuration()
        self.check_credential_security()
        self.check_broker_api_protection()
        self.check_landing_page_security()
        self.check_nexus_lite_mode()
        self.check_trading_system_configuration()
        self.check_web_scraper_intelligence()
        self.check_file_structure_integrity()
        
        # Generate final report
        return self.generate_lockcheck_report()
    
    def check_branding_configuration(self):
        """Verify Nexus Control Panel branding"""
        print("🏢 Checking branding configuration...")
        
        try:
            # Check app_nexus.py for hardcoded company references
            with open('app_nexus.py', 'r') as f:
                content = f.read()
            
            # Look for configurable branding
            if 'TRAXOVO' in content and 'NEXUS' in content:
                self.checks.append("✅ Nexus branding present")
            else:
                self.errors.append("❌ Missing Nexus branding in control panel")
            
            # Check for company customization capability
            if 'Ragle' in content or 'Select' in content or 'SSS' in content:
                self.warnings.append("⚠️ Hardcoded company names found - should be configurable")
            else:
                self.checks.append("✅ No hardcoded company references")
                
        except Exception as e:
            self.errors.append(f"❌ Branding check failed: {e}")
    
    def check_credential_security(self):
        """Verify no dev credentials or personal tokens in runtime"""
        print("🔐 Checking credential security...")
        
        sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
            r'pk_live_[a-zA-Z0-9]+',  # Stripe live keys
            r'rk_live_[a-zA-Z0-9]+',  # Robinhood keys
            r'AKIA[a-zA-Z0-9]{16}',   # AWS keys
            r'[a-zA-Z0-9]{32}@[a-zA-Z0-9]+',  # Personal email patterns
        ]
        
        files_to_check = ['app_nexus.py', 'nexus_trading_intelligence.py', 'nexus_web_relay_scraper.py']
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in sensitive_patterns:
                    if re.search(pattern, content):
                        self.errors.append(f"❌ Potential hardcoded credential in {file_path}")
                        return
        
        # Check for proper environment variable usage
        env_usage_count = 0
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                env_usage_count += content.count('os.environ.get')
        
        if env_usage_count > 5:
            self.checks.append("✅ Proper environment variable usage detected")
        else:
            self.warnings.append("⚠️ Limited environment variable usage - verify API key handling")
    
    def check_broker_api_protection(self):
        """Verify broker APIs require user input"""
        print("💼 Checking broker API protection...")
        
        try:
            with open('nexus_trading_intelligence.py', 'r') as f:
                content = f.read()
            
            # Check for user input requirements
            if 'ALPACA_API_KEY' in content and 'TD_AMERITRADE_API_KEY' in content:
                self.checks.append("✅ Broker API keys properly externalized")
            else:
                self.errors.append("❌ Broker API configuration incomplete")
            
            # Verify no hardcoded trading credentials
            if 'alpaca_key =' in content or 'td_key =' in content:
                self.errors.append("❌ Hardcoded broker credentials detected")
            else:
                self.checks.append("✅ No hardcoded broker credentials")
                
        except Exception as e:
            self.errors.append(f"❌ Broker protection check failed: {e}")
    
    def check_landing_page_security(self):
        """Verify landing page requires login"""
        print("🔒 Checking landing page security...")
        
        try:
            with open('app_nexus.py', 'r') as f:
                content = f.read()
            
            # Check for authentication requirements
            auth_patterns = [
                "if not session.get('authenticated')",
                "@require_login",
                "return redirect(url_for('login'))"
            ]
            
            auth_found = any(pattern in content for pattern in auth_patterns)
            
            if auth_found:
                self.checks.append("✅ Authentication protection implemented")
            else:
                self.errors.append("❌ Missing authentication protection")
            
            # Check for public endpoints that should be protected
            if "'/trading-tools/scalp'" in content and "authenticated" in content:
                self.checks.append("✅ Trading tools properly protected")
            else:
                self.warnings.append("⚠️ Verify trading tools require authentication")
                
        except Exception as e:
            self.errors.append(f"❌ Landing page security check failed: {e}")
    
    def check_nexus_lite_mode(self):
        """Verify Nexus Lite Mode is available for new users"""
        print("🎯 Checking Nexus Lite Mode configuration...")
        
        try:
            with open('app_nexus.py', 'r') as f:
                content = f.read()
            
            # Check for user role management
            if "'role'" in content and "'user'" in content:
                self.checks.append("✅ User role system implemented")
            else:
                self.warnings.append("⚠️ User role system may need enhancement")
            
            # Check for feature limiting
            if "lite_mode" in content or "role == 'admin'" in content:
                self.checks.append("✅ Feature access control detected")
            else:
                self.warnings.append("⚠️ Consider implementing Lite Mode restrictions")
                
        except Exception as e:
            self.errors.append(f"❌ Nexus Lite Mode check failed: {e}")
    
    def check_trading_system_configuration(self):
        """Verify trading system logs and endpoints"""
        print("📊 Checking trading system configuration...")
        
        # Check trading logs directory
        if os.path.exists('trading/logs'):
            self.checks.append("✅ Trading logs directory exists")
        else:
            try:
                os.makedirs('trading/logs', exist_ok=True)
                self.checks.append("✅ Trading logs directory created")
            except:
                self.errors.append("❌ Cannot create trading logs directory")
        
        # Check trading endpoint
        try:
            with open('app_nexus.py', 'r') as f:
                content = f.read()
            
            if "'/trading-tools/scalp'" in content:
                self.checks.append("✅ Trading scalp endpoint configured")
            else:
                self.errors.append("❌ Trading scalp endpoint missing")
            
            if "scalp-ops.json" in content or "scan-results.json" in content:
                self.checks.append("✅ Trading logging system configured")
            else:
                self.warnings.append("⚠️ Verify trading logging implementation")
                
        except Exception as e:
            self.errors.append(f"❌ Trading system check failed: {e}")
    
    def check_web_scraper_intelligence(self):
        """Verify web scraper uses Nexus intelligence"""
        print("🕷️ Checking web scraper intelligence...")
        
        try:
            if os.path.exists('nexus_web_relay_scraper.py'):
                with open('nexus_web_relay_scraper.py', 'r') as f:
                    content = f.read()
                
                # Check for Nexus-specific features
                nexus_features = [
                    'inject_nexus_prompt',
                    'NexusWebRelayScraper',
                    'NEXUS SCRAPER',
                    'quantum_scalp'
                ]
                
                features_found = sum(1 for feature in nexus_features if feature in content)
                
                if features_found >= 3:
                    self.checks.append("✅ Nexus-intelligent web scraper implemented")
                else:
                    self.errors.append("❌ Web scraper lacks Nexus intelligence features")
                
                # Check for default Playwright usage
                if 'playwright' in content.lower() and 'nexus' not in content.lower():
                    self.warnings.append("⚠️ Possible default Playwright usage detected")
                else:
                    self.checks.append("✅ No default Playwright dependency detected")
            else:
                self.errors.append("❌ Nexus web scraper module missing")
                
        except Exception as e:
            self.errors.append(f"❌ Web scraper intelligence check failed: {e}")
    
    def check_file_structure_integrity(self):
        """Verify critical files are present"""
        print("📁 Checking file structure integrity...")
        
        critical_files = [
            'app_nexus.py',
            'nexus_trading_intelligence.py',
            'nexus_web_relay_scraper.py',
            'nexus_infinity_core.py',
            'main.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                self.checks.append(f"✅ {file_path} present")
            else:
                self.errors.append(f"❌ {file_path} missing")
        
        # Check for proper imports
        try:
            with open('main.py', 'r') as f:
                main_content = f.read()
            
            if 'app_nexus' in main_content:
                self.checks.append("✅ Main module properly imports Nexus app")
            else:
                self.errors.append("❌ Main module import configuration issue")
                
        except Exception as e:
            self.errors.append(f"❌ File structure check failed: {e}")
    
    def generate_lockcheck_report(self) -> dict:
        """Generate final lockcheck report"""
        
        print("\n" + "=" * 50)
        print("📋 NEXUS DEPLOYMENT LOCKCHECK REPORT")
        print("=" * 50)
        
        # Display checks
        for check in self.checks:
            print(check)
        
        # Display warnings
        for warning in self.warnings:
            print(warning)
        
        # Display errors
        for error in self.errors:
            print(error)
        
        # Determine deployment readiness
        self.deployment_ready = len(self.errors) == 0
        
        if self.deployment_ready:
            status = "✅ READY TO DEPLOY"
            print(f"\n🚀 {status}")
        else:
            status = "❌ DEPLOYMENT BLOCKED"
            print(f"\n🛑 {status}")
            print("\n🔧 REQUIRED FIXES:")
            for error in self.errors:
                print(f"   • {error.replace('❌ ', '')}")
        
        report = {
            "status": status,
            "deployment_ready": self.deployment_ready,
            "checks_passed": len(self.checks),
            "warnings": [w.replace('⚠️ ', '') for w in self.warnings],
            "errors": [e.replace('❌ ', '') for e in self.errors],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save report
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/deployment_lockcheck.json', 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: logs/deployment_lockcheck.json")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        return report

def run_nexus_deployment_lockcheck():
    """Main function to run NEXUS deployment lockcheck"""
    lockcheck = NexusDeploymentLockcheck()
    return lockcheck.run_full_lockcheck()

if __name__ == "__main__":
    run_nexus_deployment_lockcheck()