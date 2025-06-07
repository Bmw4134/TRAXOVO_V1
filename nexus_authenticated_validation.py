"""
NEXUS Authenticated Validation System
Performs comprehensive validation with proper session authentication
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any

class AuthenticatedValidator:
    """Validation system with proper NEXUS authentication"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with NEXUS system"""
        try:
            # Use admin credentials for validation
            auth_data = {
                'username': 'admin',
                'password': 'nexus_admin_2025'
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=auth_data,
                timeout=10
            )
            
            self.authenticated = response.status_code == 302 or 'authenticated' in str(response.text)
            return self.authenticated
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def test_traxovo_endpoints(self) -> Dict[str, Any]:
        """Test TRAXOVO endpoints with authentication"""
        if not self.authenticated:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'authentication_status': 'authenticated',
            'endpoint_tests': {}
        }
        
        # Test daily driver report
        driver_data = {
            'driver_id': 'VAL_001',
            'date': '2025-06-07',
            'hours': 8.0,
            'miles': 400,
            'equipment': ['Validation Equipment']
        }
        
        try:
            driver_response = self.session.post(
                f"{self.base_url}/api/traxovo/daily-driver-report",
                json=driver_data,
                timeout=10
            )
            
            results['endpoint_tests']['daily_driver_report'] = {
                'status_code': driver_response.status_code,
                'success': driver_response.status_code in [200, 201, 202],
                'authenticated_request': True
            }
            
        except Exception as e:
            results['endpoint_tests']['daily_driver_report'] = {
                'error': str(e),
                'success': False
            }
        
        # Test equipment billing
        try:
            billing_response = self.session.get(
                f"{self.base_url}/api/traxovo/equipment-billing",
                params={'period': '2025-06'},
                timeout=10
            )
            
            results['endpoint_tests']['equipment_billing'] = {
                'status_code': billing_response.status_code,
                'success': billing_response.status_code in [200, 201, 202],
                'authenticated_request': True
            }
            
        except Exception as e:
            results['endpoint_tests']['equipment_billing'] = {
                'error': str(e),
                'success': False
            }
        
        # Test agent status
        try:
            status_response = self.session.get(
                f"{self.base_url}/api/traxovo/agent-status",
                timeout=10
            )
            
            results['endpoint_tests']['agent_status'] = {
                'status_code': status_response.status_code,
                'success': status_response.status_code in [200, 201, 202],
                'authenticated_request': True
            }
            
        except Exception as e:
            results['endpoint_tests']['agent_status'] = {
                'error': str(e),
                'success': False
            }
        
        return results
    
    def test_crypto_endpoints(self) -> Dict[str, Any]:
        """Test crypto market endpoints"""
        if not self.authenticated:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        results = {
            'crypto_market_tests': {}
        }
        
        # Test crypto market status
        try:
            crypto_response = self.session.get(
                f"{self.base_url}/api/crypto/market-status",
                timeout=10
            )
            
            results['crypto_market_tests']['market_status'] = {
                'status_code': crypto_response.status_code,
                'success': crypto_response.status_code == 200,
                'authenticated_request': True
            }
            
            if crypto_response.status_code == 200:
                market_data = crypto_response.json()
                results['crypto_market_tests']['market_status']['market_open'] = market_data.get('market_open')
                results['crypto_market_tests']['market_status']['trading_enabled'] = market_data.get('trading_enabled')
            
        except Exception as e:
            results['crypto_market_tests']['market_status'] = {
                'error': str(e),
                'success': False
            }
        
        # Test crypto patch
        try:
            patch_response = self.session.post(
                f"{self.base_url}/api/crypto/market-patch",
                json={},
                timeout=10
            )
            
            results['crypto_market_tests']['market_patch'] = {
                'status_code': patch_response.status_code,
                'success': patch_response.status_code == 200,
                'authenticated_request': True
            }
            
        except Exception as e:
            results['crypto_market_tests']['market_patch'] = {
                'error': str(e),
                'success': False
            }
        
        return results
    
    def test_diagnostics_endpoints(self) -> Dict[str, Any]:
        """Test diagnostic endpoints"""
        if not self.authenticated:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        results = {
            'diagnostic_tests': {}
        }
        
        # Test 400 diagnostics
        try:
            diag_response = self.session.get(
                f"{self.base_url}/api/nexus/400-diagnostics",
                timeout=15
            )
            
            results['diagnostic_tests']['400_diagnostics'] = {
                'status_code': diag_response.status_code,
                'success': diag_response.status_code == 200,
                'authenticated_request': True
            }
            
            if diag_response.status_code == 200:
                diag_data = diag_response.json()
                results['diagnostic_tests']['400_diagnostics']['errors_found'] = diag_data.get('errors_found', 0)
                results['diagnostic_tests']['400_diagnostics']['endpoints_checked'] = diag_data.get('total_endpoints_checked', 0)
            
        except Exception as e:
            results['diagnostic_tests']['400_diagnostics'] = {
                'error': str(e),
                'success': False
            }
        
        # Test error summary
        try:
            summary_response = self.session.get(
                f"{self.base_url}/api/nexus/400-error-summary",
                timeout=10
            )
            
            results['diagnostic_tests']['error_summary'] = {
                'status_code': summary_response.status_code,
                'success': summary_response.status_code == 200,
                'authenticated_request': True
            }
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                results['diagnostic_tests']['error_summary']['unresolved_errors'] = summary_data.get('unresolved_errors', 0)
            
        except Exception as e:
            results['diagnostic_tests']['error_summary'] = {
                'error': str(e),
                'success': False
            }
        
        return results
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete authenticated validation"""
        print("=== NEXUS AUTHENTICATED VALIDATION ===")
        
        # Authenticate first
        if not self.authenticate():
            return {
                'status': 'FAILED',
                'error': 'Authentication failed',
                'timestamp': datetime.now().isoformat()
            }
        
        print("Authentication successful")
        
        # Run all tests
        traxovo_results = self.test_traxovo_endpoints()
        crypto_results = self.test_crypto_endpoints()
        diagnostic_results = self.test_diagnostics_endpoints()
        
        # Compile final results
        final_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'authentication_status': 'successful',
            'traxovo_tests': traxovo_results,
            'crypto_tests': crypto_results,
            'diagnostic_tests': diagnostic_results,
            'overall_status': 'ANALYZING'
        }
        
        # Calculate success metrics
        total_tests = 0
        successful_tests = 0
        
        for test_category in [traxovo_results, crypto_results, diagnostic_results]:
            for test_group in test_category.values():
                if isinstance(test_group, dict):
                    for test_name, test_result in test_group.items():
                        if isinstance(test_result, dict) and 'success' in test_result:
                            total_tests += 1
                            if test_result['success']:
                                successful_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        final_results['success_rate'] = success_rate
        final_results['tests_passed'] = successful_tests
        final_results['total_tests'] = total_tests
        
        if success_rate >= 90:
            final_results['overall_status'] = 'VALIDATED'
            print(f"VALIDATION SUCCESSFUL: {success_rate:.1f}% success rate")
        elif success_rate >= 70:
            final_results['overall_status'] = 'PARTIAL_SUCCESS'
            print(f"PARTIAL SUCCESS: {success_rate:.1f}% success rate")
        else:
            final_results['overall_status'] = 'NEEDS_ATTENTION'
            print(f"ATTENTION REQUIRED: {success_rate:.1f}% success rate")
        
        return final_results

# Global instance
authenticated_validator = AuthenticatedValidator()

def run_authenticated_validation():
    """Run authenticated validation"""
    return authenticated_validator.run_complete_validation()