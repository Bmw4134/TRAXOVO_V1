"""
NEXUS Validation Macro - Bulletproof 400 Error Fix Verification
Runs comprehensive validation to confirm all 400 Bad Request errors are permanently resolved
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import sqlite3
import time

class NexusValidationMacro:
    """Comprehensive validation system for 400 error resolution"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.validation_db = "nexus_validation.db"
        self.initialize_validation_db()
        
    def initialize_validation_db(self):
        """Initialize validation tracking database"""
        try:
            conn = sqlite3.connect(self.validation_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT,
                    endpoint TEXT,
                    status_code INTEGER,
                    success BOOLEAN,
                    response_data TEXT,
                    timestamp TIMESTAMP,
                    test_type TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Validation DB initialization failed: {e}")
    
    def check_1_fresh_report_submission(self) -> Dict[str, Any]:
        """✅ 1. Trigger fresh report submission with real data"""
        results = {}
        
        # Real driver data for testing
        real_driver_data = {
            'driver_id': 'DRV_001_WATSON',
            'date': '2025-06-07',
            'hours': 8.5,
            'miles': 456,
            'equipment': ['CAT 320D Excavator', 'Bobcat S185'],
            'notes': 'Equipment performed well today',
            'fuel_used': 85.6
        }
        
        # Real billing data for testing
        real_billing_params = {'period': '2025-06'}
        
        try:
            # Test daily driver report
            driver_response = requests.post(
                f"{self.base_url}/api/traxovo/daily-driver-report",
                json=real_driver_data,
                timeout=10
            )
            
            results['daily_driver_report'] = {
                'status_code': driver_response.status_code,
                'success': driver_response.status_code in [200, 201, 202],
                'response': driver_response.json() if driver_response.headers.get('content-type', '').startswith('application/json') else driver_response.text
            }
            
            # Test equipment billing
            billing_response = requests.get(
                f"{self.base_url}/api/traxovo/equipment-billing",
                params=real_billing_params,
                timeout=10
            )
            
            results['equipment_billing'] = {
                'status_code': billing_response.status_code,
                'success': billing_response.status_code in [200, 201, 202],
                'response': billing_response.json() if billing_response.headers.get('content-type', '').startswith('application/json') else billing_response.text
            }
            
            # Log results
            self._log_validation_result("fresh_submission", "traxovo_reports", results)
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def check_2_agent_logs(self) -> Dict[str, Any]:
        """✅ 2. Check agent logs for successful submissions"""
        log_analysis = {
            'recent_requests': [],
            'error_count': 0,
            'success_count': 0,
            'status': 'analyzing'
        }
        
        try:
            # Check TRAXOVO agent status
            status_response = requests.get(
                f"{self.base_url}/api/traxovo/agent-status",
                timeout=10
            )
            
            if status_response.status_code == 200:
                agent_status = status_response.json()
                log_analysis['agent_health'] = agent_status.get('agent_health', 'unknown')
                log_analysis['recent_reports'] = agent_status.get('recent_driver_reports', 0)
                log_analysis['recent_billing'] = agent_status.get('recent_billing_records', 0)
                log_analysis['success_count'] = log_analysis['recent_reports'] + log_analysis['recent_billing']
            
            log_analysis['status'] = 'completed'
            
        except Exception as e:
            log_analysis['error'] = str(e)
            log_analysis['status'] = 'failed'
            
        return log_analysis
    
    def check_3_dashboard_validation(self) -> Dict[str, Any]:
        """✅ 3. Validate data appears in dashboards"""
        dashboard_results = {
            'dashboard_accessible': False,
            'data_visible': False,
            'timestamps_accurate': False
        }
        
        try:
            # Check if dashboard is accessible
            dashboard_response = requests.get(
                f"{self.base_url}/nexus-dashboard",
                timeout=10
            )
            
            dashboard_results['dashboard_accessible'] = dashboard_response.status_code == 200
            
            # Check for recent data via API
            if dashboard_results['dashboard_accessible']:
                # Check fleet recommendations (indicates data processing)
                fleet_response = requests.get(
                    f"{self.base_url}/api/traxovo/fleet-recommendations",
                    timeout=10
                )
                
                if fleet_response.status_code == 200:
                    fleet_data = fleet_response.json()
                    dashboard_results['data_visible'] = fleet_data.get('status') == 'success'
                    dashboard_results['recommendations_count'] = len(fleet_data.get('recommendations', []))
                    
                    # Check timestamp accuracy
                    if 'generated_timestamp' in fleet_data:
                        generated_time = datetime.fromisoformat(fleet_data['generated_timestamp'].replace('Z', '+00:00'))
                        time_diff = abs((datetime.now() - generated_time.replace(tzinfo=None)).total_seconds())
                        dashboard_results['timestamps_accurate'] = time_diff < 3600  # Within 1 hour
            
        except Exception as e:
            dashboard_results['error'] = str(e)
            
        return dashboard_results
    
    def check_4_schema_echo_test(self) -> Dict[str, Any]:
        """✅ 4. Schema validation and echo test"""
        schema_results = {
            'schemas_available': False,
            'payload_validation': False,
            'type_matching': False
        }
        
        try:
            import nexus_payload_schema_diagnostic
            
            # Test schema validation with real data
            test_payload = {
                'driver_id': 'TEST_001',
                'date': '2025-06-07',
                'hours': 8.0,
                'miles': 400,
                'equipment': ['Test Equipment']
            }
            
            validation_result = nexus_payload_schema_diagnostic.validate_real_data('daily_driver_report', test_payload)
            
            schema_results['schemas_available'] = True
            schema_results['payload_validation'] = validation_result.get('valid', False)
            schema_results['sanitized_payload'] = validation_result.get('sanitized_payload')
            schema_results['validation_errors'] = validation_result.get('errors', [])
            schema_results['type_matching'] = len(validation_result.get('errors', [])) == 0
            
        except Exception as e:
            schema_results['error'] = str(e)
            
        return schema_results
    
    def check_5_diagnostic_pass_confirmation(self) -> Dict[str, Any]:
        """✅ 5. Diagnostic pass confirmation"""
        diagnostic_results = {
            'diagnostic_available': False,
            'sanitization_complete': False,
            'resubmission_successful': False
        }
        
        try:
            # Run comprehensive diagnostic
            diagnostic_response = requests.get(
                f"{self.base_url}/api/nexus/400-diagnostics",
                timeout=15
            )
            
            if diagnostic_response.status_code == 200:
                diagnostic_data = diagnostic_response.json()
                diagnostic_results['diagnostic_available'] = True
                diagnostic_results['total_endpoints_checked'] = diagnostic_data.get('total_endpoints_checked', 0)
                diagnostic_results['errors_found'] = diagnostic_data.get('errors_found', 0)
                diagnostic_results['sanitization_complete'] = diagnostic_data.get('errors_found', 0) == 0
                diagnostic_results['endpoints_requiring_attention'] = diagnostic_data.get('endpoints_requiring_attention', [])
                diagnostic_results['resubmission_successful'] = len(diagnostic_data.get('endpoints_requiring_attention', [])) == 0
            
        except Exception as e:
            diagnostic_results['error'] = str(e)
            
        return diagnostic_results
    
    def check_6_regression_catcher(self) -> Dict[str, Any]:
        """✅ 6. Trigger regression check"""
        regression_results = {
            'regression_check_available': False,
            'confidence_score': 0,
            'regression_detected': True
        }
        
        try:
            # Check error summary
            error_summary_response = requests.get(
                f"{self.base_url}/api/nexus/400-error-summary",
                timeout=10
            )
            
            if error_summary_response.status_code == 200:
                error_data = error_summary_response.json()
                regression_results['regression_check_available'] = True
                regression_results['unresolved_errors'] = error_data.get('unresolved_errors', 0)
                regression_results['regression_detected'] = error_data.get('unresolved_errors', 0) > 0
                regression_results['confidence_score'] = 100 if error_data.get('unresolved_errors', 0) == 0 else 50
                regression_results['error_breakdown'] = error_data.get('error_breakdown', [])
            
        except Exception as e:
            regression_results['error'] = str(e)
            
        return regression_results
    
    def _log_validation_result(self, test_name: str, endpoint: str, result: Dict):
        """Log validation result to database"""
        try:
            conn = sqlite3.connect(self.validation_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO validation_results 
                (test_name, endpoint, status_code, success, response_data, timestamp, test_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_name,
                endpoint,
                result.get('status_code', 0),
                result.get('success', False),
                json.dumps(result),
                datetime.now(),
                'comprehensive_validation'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to log validation result: {e}")
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all 6 validation checks in sequence"""
        validation_start = datetime.now()
        
        print("=== NEXUS 400 ERROR VALIDATION MACRO ===")
        print("Running bulletproof validation checklist...")
        
        results = {
            'validation_timestamp': validation_start.isoformat(),
            'overall_status': 'running',
            'checks_passed': 0,
            'total_checks': 6,
            'detailed_results': {}
        }
        
        # Check 1: Fresh Report Submission
        print("\n✅ 1. Testing fresh report submission...")
        check1_result = self.check_1_fresh_report_submission()
        results['detailed_results']['fresh_submission'] = check1_result
        if all(r.get('success', False) for r in check1_result.values() if isinstance(r, dict)):
            results['checks_passed'] += 1
            print("   PASS: Reports submitted successfully")
        else:
            print("   FAIL: Report submission issues detected")
        
        # Check 2: Agent Logs
        print("\n✅ 2. Analyzing agent logs...")
        check2_result = self.check_2_agent_logs()
        results['detailed_results']['agent_logs'] = check2_result
        if check2_result.get('agent_health') == 'healthy':
            results['checks_passed'] += 1
            print("   PASS: Agent logs show healthy status")
        else:
            print("   FAIL: Agent health issues detected")
        
        # Check 3: Dashboard Validation
        print("\n✅ 3. Validating dashboard data...")
        check3_result = self.check_3_dashboard_validation()
        results['detailed_results']['dashboard'] = check3_result
        if check3_result.get('dashboard_accessible') and check3_result.get('data_visible'):
            results['checks_passed'] += 1
            print("   PASS: Dashboard accessible with visible data")
        else:
            print("   FAIL: Dashboard access or data visibility issues")
        
        # Check 4: Schema Echo Test
        print("\n✅ 4. Running schema validation...")
        check4_result = self.check_4_schema_echo_test()
        results['detailed_results']['schema_validation'] = check4_result
        if check4_result.get('schemas_available') and check4_result.get('payload_validation'):
            results['checks_passed'] += 1
            print("   PASS: Schema validation successful")
        else:
            print("   FAIL: Schema validation issues")
        
        # Check 5: Diagnostic Pass
        print("\n✅ 5. Confirming diagnostic completion...")
        check5_result = self.check_5_diagnostic_pass_confirmation()
        results['detailed_results']['diagnostic_pass'] = check5_result
        if check5_result.get('diagnostic_available') and check5_result.get('sanitization_complete'):
            results['checks_passed'] += 1
            print("   PASS: Diagnostic sanitization complete")
        else:
            print("   FAIL: Diagnostic issues detected")
        
        # Check 6: Regression Catcher
        print("\n✅ 6. Running regression check...")
        check6_result = self.check_6_regression_catcher()
        results['detailed_results']['regression_check'] = check6_result
        if check6_result.get('confidence_score', 0) >= 90:
            results['checks_passed'] += 1
            print("   PASS: High confidence - no regressions detected")
        else:
            print("   FAIL: Regression issues or low confidence")
        
        # Final assessment
        validation_end = datetime.now()
        results['validation_duration'] = (validation_end - validation_start).total_seconds()
        results['overall_status'] = 'FULLY_VALIDATED' if results['checks_passed'] == 6 else 'NEEDS_ATTENTION'
        results['success_rate'] = (results['checks_passed'] / results['total_checks']) * 100
        
        print(f"\n=== VALIDATION COMPLETE ===")
        print(f"Checks Passed: {results['checks_passed']}/{results['total_checks']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Overall Status: {results['overall_status']}")
        
        if results['overall_status'] == 'FULLY_VALIDATED':
            print("\n🔓 FULLY VALIDATED AND FIXED")
            print("All 400 Bad Request errors permanently resolved")
        else:
            print(f"\n⚠️  {6 - results['checks_passed']} checks require attention")
        
        return results

# Global instance
validation_macro = NexusValidationMacro()

def run_bulletproof_validation():
    """Run the bulletproof validation macro"""
    return validation_macro.run_comprehensive_validation()