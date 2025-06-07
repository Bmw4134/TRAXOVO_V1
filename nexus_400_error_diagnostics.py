"""
NEXUS PTNI Auto-Sanitizer and 400 Error Diagnostic System
Systematic validation and remediation for all TRAXOVO/Nexus endpoints
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3

class PTNI400ErrorDiagnostics:
    """Comprehensive 400 error detection and auto-correction system"""
    
    def __init__(self):
        self.error_log_db = "nexus_400_errors.db"
        self.endpoint_schemas = self._load_endpoint_schemas()
        self.initialize_error_tracking()
        
    def initialize_error_tracking(self):
        """Initialize error tracking database"""
        try:
            conn = sqlite3.connect(self.error_log_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    error_type TEXT,
                    payload_sent TEXT,
                    expected_schema TEXT,
                    validation_errors TEXT,
                    timestamp TIMESTAMP,
                    resolution_status TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS endpoint_schemas (
                    endpoint TEXT PRIMARY KEY,
                    schema_definition TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("400 error tracking database initialized")
            
        except Exception as e:
            logging.error(f"Error tracking initialization failed: {e}")
    
    def _load_endpoint_schemas(self) -> Dict[str, Dict]:
        """Load predefined endpoint schemas for validation"""
        return {
            '/api/crypto/market-patch': {
                'override_active': bool,
                'force_24_7': bool
            },
            '/api/traxovo/daily-driver-report': {
                'driver_id': str,
                'date': str,
                'hours': (int, float),
                'miles': int,
                'equipment': list
            },
            '/api/traxovo/equipment-billing': {
                'period': str
            },
            '/api/nexus/mesh-sync-repair': {
                'nodes': list,
                'sync_mode': str
            },
            '/api/browser/create-session': {
                'url': str,
                'automation_type': str
            },
            '/api/ptni/browser-navigate': {
                'session_id': str,
                'url': str
            },
            '/api/nexus/master-override': {
                'override_type': str,
                'authorization_code': str
            }
        }
    
    def validate_payload_format(self, endpoint: str, payload: Dict, schema: Dict) -> List[str]:
        """Validate payload against expected schema"""
        errors = []
        
        if not isinstance(payload, dict):
            errors.append(f"Payload must be a dictionary, got {type(payload)}")
            return errors
        
        for key, expected_type in schema.items():
            if key not in payload:
                errors.append(f"Missing required key: {key}")
            else:
                value = payload[key]
                if isinstance(expected_type, tuple):
                    # Multiple allowed types
                    if not any(isinstance(value, t) for t in expected_type):
                        errors.append(f"Invalid type for {key}: expected {expected_type}, got {type(value)}")
                else:
                    # Single expected type
                    if not isinstance(value, expected_type):
                        errors.append(f"Invalid type for {key}: expected {expected_type}, got {type(value)}")
        
        return errors
    
    def ptni_safe_request(self, url: str, payload: Dict, method: str = 'POST') -> Dict[str, Any]:
        """Safe request wrapper with automatic validation and correction"""
        endpoint = url.split('?')[0]  # Remove query parameters for schema lookup
        schema = self.endpoint_schemas.get(endpoint, {})
        
        # Validate payload if schema exists
        if schema:
            errors = self.validate_payload_format(endpoint, payload, schema)
            if errors:
                corrected_payload = self._auto_correct_payload(payload, schema, errors)
                if corrected_payload:
                    payload = corrected_payload
                    logging.info(f"Auto-corrected payload for {endpoint}")
                else:
                    self._log_validation_error(endpoint, payload, schema, errors)
                    return {
                        'status': 'validation_failed',
                        'errors': errors,
                        'endpoint': endpoint
                    }
        
        # Make the request
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=payload, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=payload, timeout=10)
            elif method.upper() == 'GET':
                response = requests.get(url, params=payload, timeout=10)
            else:
                response = requests.request(method, url, json=payload, timeout=10)
            
            if response.status_code == 400:
                self._log_400_error(endpoint, payload, response.text)
                return {
                    'status': 'error',
                    'status_code': 400,
                    'error_details': response.text,
                    'endpoint': endpoint,
                    'suggested_fix': self._generate_fix_suggestion(endpoint, payload, response.text)
                }
            
            return {
                'status': 'success',
                'status_code': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
        except requests.RequestException as e:
            logging.error(f"Request failed for {endpoint}: {e}")
            return {
                'status': 'request_failed',
                'error': str(e),
                'endpoint': endpoint
            }
    
    def _auto_correct_payload(self, payload: Dict, schema: Dict, errors: List[str]) -> Optional[Dict]:
        """Attempt to auto-correct common payload issues"""
        corrected = payload.copy()
        
        for error in errors:
            if "Missing required key:" in error:
                missing_key = error.split(": ")[1]
                expected_type = schema.get(missing_key)
                
                # Provide default values based on type
                if expected_type == str:
                    corrected[missing_key] = ""
                elif expected_type == int:
                    corrected[missing_key] = 0
                elif expected_type == float:
                    corrected[missing_key] = 0.0
                elif expected_type == bool:
                    corrected[missing_key] = False
                elif expected_type == list:
                    corrected[missing_key] = []
                elif expected_type == dict:
                    corrected[missing_key] = {}
            
            elif "Invalid type for" in error:
                parts = error.split()
                key = parts[3].rstrip(':')
                expected_type_str = error.split("expected ")[1].split(",")[0]
                
                # Attempt type conversion
                if key in corrected:
                    try:
                        if 'str' in expected_type_str:
                            corrected[key] = str(corrected[key])
                        elif 'int' in expected_type_str:
                            corrected[key] = int(float(corrected[key]))
                        elif 'float' in expected_type_str:
                            corrected[key] = float(corrected[key])
                        elif 'bool' in expected_type_str:
                            corrected[key] = bool(corrected[key])
                        elif 'list' in expected_type_str:
                            if not isinstance(corrected[key], list):
                                corrected[key] = [corrected[key]] if corrected[key] is not None else []
                    except (ValueError, TypeError):
                        continue
        
        # Validate corrected payload
        new_errors = self.validate_payload_format("", corrected, schema)
        return corrected if not new_errors else None
    
    def _log_validation_error(self, endpoint: str, payload: Dict, schema: Dict, errors: List[str]):
        """Log validation errors to database"""
        try:
            conn = sqlite3.connect(self.error_log_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO error_logs 
                (endpoint, error_type, payload_sent, expected_schema, validation_errors, timestamp, resolution_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint, 
                'validation_error', 
                json.dumps(payload), 
                json.dumps(schema), 
                json.dumps(errors), 
                datetime.now(), 
                'pending'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to log validation error: {e}")
    
    def _log_400_error(self, endpoint: str, payload: Dict, response_text: str):
        """Log 400 errors to database"""
        try:
            conn = sqlite3.connect(self.error_log_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO error_logs 
                (endpoint, error_type, payload_sent, validation_errors, timestamp, resolution_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                endpoint, 
                '400_bad_request', 
                json.dumps(payload), 
                response_text, 
                datetime.now(), 
                'needs_analysis'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to log 400 error: {e}")
    
    def _generate_fix_suggestion(self, endpoint: str, payload: Dict, error_response: str) -> str:
        """Generate intelligent fix suggestions based on error patterns"""
        suggestions = []
        
        # Common 400 error patterns and fixes
        if "missing" in error_response.lower():
            suggestions.append("Add missing required fields to payload")
        
        if "invalid" in error_response.lower():
            suggestions.append("Check data types and format validation")
        
        if "malformed" in error_response.lower():
            suggestions.append("Verify JSON structure and encoding")
        
        if "authentication" in error_response.lower():
            suggestions.append("Verify authentication headers and session")
        
        if "schema" in error_response.lower():
            suggestions.append("Update payload to match current API schema")
        
        return "; ".join(suggestions) if suggestions else "Review API documentation for correct payload format"
    
    def run_comprehensive_400_scan(self) -> Dict[str, Any]:
        """Run comprehensive scan across all known endpoints"""
        scan_results = {
            'total_endpoints_checked': 0,
            'errors_found': 0,
            'errors_auto_fixed': 0,
            'endpoints_requiring_attention': [],
            'scan_timestamp': datetime.now().isoformat()
        }
        
        # Test each known endpoint with sample data
        for endpoint, schema in self.endpoint_schemas.items():
            try:
                # Generate test payload based on schema
                test_payload = self._generate_test_payload(schema)
                
                # Test the endpoint
                result = self.ptni_safe_request(f"http://localhost:5000{endpoint}", test_payload)
                
                scan_results['total_endpoints_checked'] += 1
                
                if result['status'] == 'validation_failed':
                    scan_results['errors_found'] += 1
                    scan_results['endpoints_requiring_attention'].append({
                        'endpoint': endpoint,
                        'issue': 'validation_failed',
                        'errors': result['errors']
                    })
                elif result['status'] == 'error' and result['status_code'] == 400:
                    scan_results['errors_found'] += 1
                    scan_results['endpoints_requiring_attention'].append({
                        'endpoint': endpoint,
                        'issue': '400_bad_request',
                        'details': result['error_details']
                    })
                
            except Exception as e:
                logging.error(f"Error testing endpoint {endpoint}: {e}")
                scan_results['endpoints_requiring_attention'].append({
                    'endpoint': endpoint,
                    'issue': 'test_failed',
                    'error': str(e)
                })
        
        return scan_results
    
    def _generate_test_payload(self, schema: Dict) -> Dict:
        """Generate test payload based on schema"""
        payload = {}
        
        for key, expected_type in schema.items():
            if isinstance(expected_type, tuple):
                expected_type = expected_type[0]  # Use first type for testing
            
            if expected_type == str:
                payload[key] = "test_value"
            elif expected_type == int:
                payload[key] = 1
            elif expected_type == float:
                payload[key] = 1.0
            elif expected_type == bool:
                payload[key] = True
            elif expected_type == list:
                payload[key] = ["test_item"]
            elif expected_type == dict:
                payload[key] = {"test": "data"}
        
        return payload
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all logged errors"""
        try:
            conn = sqlite3.connect(self.error_log_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT endpoint, error_type, COUNT(*) as error_count, 
                       MAX(timestamp) as last_occurrence
                FROM error_logs 
                WHERE resolution_status != 'resolved'
                GROUP BY endpoint, error_type
                ORDER BY error_count DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return {
                'unresolved_errors': len(results),
                'error_breakdown': [
                    {
                        'endpoint': row[0],
                        'error_type': row[1],
                        'count': row[2],
                        'last_occurrence': row[3]
                    }
                    for row in results
                ],
                'summary_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to get error summary: {e}")
            return {'error': str(e)}

# Global instance
ptni_diagnostics = PTNI400ErrorDiagnostics()

def validate_and_fix_400_errors():
    """Main function to validate and fix 400 errors"""
    return ptni_diagnostics.run_comprehensive_400_scan()

def get_400_error_summary():
    """Get summary of 400 errors"""
    return ptni_diagnostics.get_error_summary()

def safe_api_request(url, payload, method='POST'):
    """Safe API request wrapper"""
    return ptni_diagnostics.ptni_safe_request(url, payload, method)