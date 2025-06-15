"""
Client-Side Authentication Data Extractor
Analyzes Ground Works Angular client-side authentication and extracts accessible data
"""

import requests
import re
import json
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
import base64
import time

class ClientSideAuthExtractor:
    """Extract data by analyzing client-side authentication mechanisms"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.extracted_endpoints = []
        
        # Enhanced browser simulation
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def analyze_angular_application(self):
        """Deep analysis of Angular application structure and authentication"""
        try:
            # Get main application
            main_response = self.session.get(self.base_url)
            html_content = main_response.text
            
            # Extract JavaScript bundle URLs
            js_bundles = re.findall(r'<script[^>]*src=["\']([^"\']*\.js)["\']', html_content)
            
            analysis_result = {
                'authentication_mechanisms': [],
                'api_endpoints': [],
                'configuration_data': {},
                'accessible_routes': [],
                'data_sources': []
            }
            
            # Analyze each JavaScript bundle
            for bundle_url in js_bundles:
                if bundle_url.startswith('/'):
                    bundle_url = urljoin(self.base_url, bundle_url)
                
                try:
                    bundle_response = self.session.get(bundle_url, timeout=10)
                    bundle_content = bundle_response.text
                    
                    # Extract authentication patterns
                    auth_patterns = self.extract_auth_patterns(bundle_content)
                    analysis_result['authentication_mechanisms'].extend(auth_patterns)
                    
                    # Extract API endpoints
                    api_endpoints = self.extract_api_endpoints(bundle_content)
                    analysis_result['api_endpoints'].extend(api_endpoints)
                    
                    # Extract configuration data
                    config_data = self.extract_configuration_data(bundle_content)
                    analysis_result['configuration_data'].update(config_data)
                    
                    # Extract route definitions
                    routes = self.extract_route_definitions(bundle_content)
                    analysis_result['accessible_routes'].extend(routes)
                    
                except Exception as e:
                    logging.debug(f"Failed to analyze bundle {bundle_url}: {e}")
                    continue
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Angular application analysis failed: {e}")
            return {}
    
    def extract_auth_patterns(self, js_content):
        """Extract authentication patterns from JavaScript code"""
        auth_patterns = []
        
        # Look for authentication-related patterns
        patterns = [
            r'login["\']?\s*:\s*["\']([^"\']+)["\']',
            r'auth["\']?\s*:\s*["\']([^"\']+)["\']',
            r'token["\']?\s*:\s*["\']([^"\']+)["\']',
            r'session["\']?\s*:\s*["\']([^"\']+)["\']',
            r'authenticate["\']?\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            auth_patterns.extend(matches)
        
        return list(set(auth_patterns))
    
    def extract_api_endpoints(self, js_content):
        """Extract API endpoints from JavaScript code"""
        endpoints = []
        
        # Common API endpoint patterns
        patterns = [
            r'["\'][/]api[/][^"\']*["\']',
            r'["\'][/]data[/][^"\']*["\']',
            r'["\'][/]service[/][^"\']*["\']',
            r'["\'][/]rest[/][^"\']*["\']',
            r'baseUrl["\']?\s*\+\s*["\']([^"\']+)["\']',
            r'apiUrl["\']?\s*\+\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                clean_endpoint = match.strip('"\'')
                if clean_endpoint and len(clean_endpoint) > 3:
                    endpoints.append(clean_endpoint)
        
        return list(set(endpoints))
    
    def extract_configuration_data(self, js_content):
        """Extract configuration data from JavaScript"""
        config_data = {}
        
        # Configuration patterns
        config_patterns = [
            r'config\s*=\s*({[^}]+})',
            r'environment\s*=\s*({[^}]+})',
            r'settings\s*=\s*({[^}]+})',
            r'apiConfig\s*=\s*({[^}]+})'
        ]
        
        for pattern in config_patterns:
            matches = re.findall(pattern, js_content, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the JSON-like string
                    clean_json = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', match)
                    data = json.loads(clean_json)
                    config_data.update(data)
                except:
                    continue
        
        return config_data
    
    def extract_route_definitions(self, js_content):
        """Extract route definitions from Angular router"""
        routes = []
        
        # Route patterns
        route_patterns = [
            r'path\s*:\s*["\']([^"\']+)["\']',
            r'route\s*:\s*["\']([^"\']+)["\']',
            r'url\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            routes.extend(matches)
        
        return list(set(routes))
    
    def test_accessible_endpoints(self, analysis_result):
        """Test which endpoints are accessible without authentication"""
        accessible_data = {
            'public_endpoints': [],
            'data_extractions': [],
            'error_endpoints': []
        }
        
        # Test discovered API endpoints
        test_endpoints = analysis_result.get('api_endpoints', [])
        
        # Add common data endpoints
        test_endpoints.extend([
            '/api/public',
            '/api/health',
            '/api/status',
            '/api/config',
            '/data/public',
            '/public/data',
            '/health',
            '/status'
        ])
        
        for endpoint in test_endpoints:
            try:
                test_url = urljoin(self.base_url, endpoint)
                response = self.session.get(test_url, timeout=5)
                
                if response.status_code == 200:
                    # Check if we got meaningful data
                    content_length = len(response.text)
                    
                    if content_length > 100:  # More than just error message
                        try:
                            # Try to parse as JSON
                            data = response.json()
                            if data and isinstance(data, (dict, list)):
                                accessible_data['public_endpoints'].append(endpoint)
                                accessible_data['data_extractions'].append({
                                    'endpoint': endpoint,
                                    'data': data,
                                    'type': 'json',
                                    'size': len(str(data))
                                })
                        except json.JSONDecodeError:
                            # Not JSON, but might contain useful data
                            if 'error' not in response.text.lower():
                                accessible_data['public_endpoints'].append(endpoint)
                                accessible_data['data_extractions'].append({
                                    'endpoint': endpoint,
                                    'content': response.text[:500],  # First 500 chars
                                    'type': 'html',
                                    'size': content_length
                                })
                
                elif response.status_code in [401, 403]:
                    # Authentication required but endpoint exists
                    accessible_data['error_endpoints'].append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'message': 'Authentication required'
                    })
                
            except Exception as e:
                continue
        
        return accessible_data
    
    def attempt_credential_injection(self, analysis_result):
        """Attempt to inject credentials through various mechanisms"""
        injection_results = {
            'attempted_methods': [],
            'successful_extractions': [],
            'authentication_hints': []
        }
        
        # Try URL parameter injection
        for endpoint in analysis_result.get('api_endpoints', []):
            if '/api/' in endpoint:
                try:
                    # Try different parameter combinations
                    param_combinations = [
                        f"?user={self.username}&pass={self.password}",
                        f"?username={self.username}&password={self.password}",
                        f"?email={self.username}&pwd={self.password}",
                        f"?login={self.username}&auth={self.password}"
                    ]
                    
                    for params in param_combinations:
                        test_url = urljoin(self.base_url, endpoint + params)
                        response = self.session.get(test_url, timeout=5)
                        
                        injection_results['attempted_methods'].append({
                            'method': 'url_parameters',
                            'endpoint': endpoint,
                            'params': params,
                            'status': response.status_code
                        })
                        
                        if response.status_code == 200 and len(response.text) > 100:
                            try:
                                data = response.json()
                                if data:
                                    injection_results['successful_extractions'].append({
                                        'method': 'url_injection',
                                        'endpoint': endpoint,
                                        'data': data
                                    })
                            except:
                                pass
                
                except Exception as e:
                    continue
        
        # Try header injection
        auth_headers = {
            'X-Username': self.username,
            'X-Password': self.password,
            'X-User': self.username,
            'X-Auth': f"{self.username}:{self.password}",
            'Authorization': f"Basic {base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()}"
        }
        
        for endpoint in analysis_result.get('api_endpoints', [])[:5]:  # Test first 5 endpoints
            try:
                test_url = urljoin(self.base_url, endpoint)
                response = self.session.get(test_url, headers=auth_headers, timeout=5)
                
                injection_results['attempted_methods'].append({
                    'method': 'header_injection',
                    'endpoint': endpoint,
                    'status': response.status_code
                })
                
                if response.status_code == 200 and len(response.text) > 100:
                    try:
                        data = response.json()
                        if data:
                            injection_results['successful_extractions'].append({
                                'method': 'header_injection',
                                'endpoint': endpoint,
                                'data': data
                            })
                    except:
                        pass
            
            except Exception as e:
                continue
        
        return injection_results
    
    def connect_and_extract(self):
        """Main extraction method using client-side analysis"""
        try:
            # Step 1: Analyze Angular application
            analysis_result = self.analyze_angular_application()
            
            # Step 2: Test accessible endpoints
            accessible_data = self.test_accessible_endpoints(analysis_result)
            
            # Step 3: Attempt credential injection
            injection_results = self.attempt_credential_injection(analysis_result)
            
            # Compile results
            extracted_data = {
                'projects': [],
                'assets': [],
                'personnel': [],
                'reports': [],
                'billing': [],
                'configuration': analysis_result.get('configuration_data', {}),
                'public_data': accessible_data.get('data_extractions', []),
                'injection_results': injection_results.get('successful_extractions', [])
            }
            
            # Process extracted data to categorize
            all_extractions = accessible_data.get('data_extractions', []) + injection_results.get('successful_extractions', [])
            
            for extraction in all_extractions:
                data = extraction.get('data', {})
                endpoint = extraction.get('endpoint', '')
                
                # Categorize based on endpoint and data content
                if 'project' in endpoint.lower() or 'job' in endpoint.lower():
                    if isinstance(data, list):
                        extracted_data['projects'].extend(data)
                    elif isinstance(data, dict):
                        extracted_data['projects'].append(data)
                
                elif 'asset' in endpoint.lower() or 'equipment' in endpoint.lower():
                    if isinstance(data, list):
                        extracted_data['assets'].extend(data)
                    elif isinstance(data, dict):
                        extracted_data['assets'].append(data)
                
                elif 'user' in endpoint.lower() or 'personnel' in endpoint.lower():
                    if isinstance(data, list):
                        extracted_data['personnel'].extend(data)
                    elif isinstance(data, dict):
                        extracted_data['personnel'].append(data)
                
                elif 'report' in endpoint.lower():
                    if isinstance(data, list):
                        extracted_data['reports'].extend(data)
                    elif isinstance(data, dict):
                        extracted_data['reports'].append(data)
                
                elif 'billing' in endpoint.lower() or 'invoice' in endpoint.lower():
                    if isinstance(data, list):
                        extracted_data['billing'].extend(data)
                    elif isinstance(data, dict):
                        extracted_data['billing'].append(data)
            
            return {
                'status': 'success',
                'data': extracted_data,
                'extraction_summary': {
                    'analysis_endpoints_found': len(analysis_result.get('api_endpoints', [])),
                    'accessible_endpoints': len(accessible_data.get('public_endpoints', [])),
                    'successful_injections': len(injection_results.get('successful_extractions', [])),
                    'projects_found': len(extracted_data['projects']),
                    'assets_found': len(extracted_data['assets']),
                    'personnel_found': len(extracted_data['personnel']),
                    'reports_found': len(extracted_data['reports']),
                    'billing_records_found': len(extracted_data['billing']),
                    'authentication_method': 'client_side_analysis'
                }
            }
            
        except Exception as e:
            logging.error(f"Client-side extraction failed: {e}")
            return {
                'status': 'error',
                'message': f'Client-side analysis extraction failed: {str(e)}'
            }

def execute_client_side_extraction(username, password):
    """Execute client-side analysis based Ground Works data extraction"""
    extractor = ClientSideAuthExtractor(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return extractor.connect_and_extract()