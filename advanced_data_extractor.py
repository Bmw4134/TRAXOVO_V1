"""
Advanced Ground Works Data Extractor
Browser-based extraction to access actual project data behind Angular authentication
"""

import requests
import json
import logging
import time
import re
from datetime import datetime
from urllib.parse import urljoin, parse_qs, urlparse
import base64
import hashlib

class AdvancedDataExtractor:
    """Advanced extractor that mimics browser behavior to access real data"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        self.angular_data = {}
        
        # Mimic real browser session
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
    
    def extract_angular_bootstrap_data(self):
        """Extract bootstrap data embedded in Angular application"""
        try:
            # Get the main Angular application
            response = self.session.get(self.base_url)
            html_content = response.text
            
            # Extract embedded configuration and data
            bootstrap_data = {}
            
            # Look for configuration objects
            config_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.config\s*=\s*({.*?});',
                r'var\s+config\s*=\s*({.*?});',
                r'const\s+initialData\s*=\s*({.*?});',
                r'window\.bootstrapData\s*=\s*({.*?});'
            ]
            
            for pattern in config_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        bootstrap_data.update(data)
                    except:
                        continue
            
            # Extract API endpoints from JavaScript
            endpoint_patterns = re.findall(r'["\']/(api|data)/[^"\']*["\']', html_content)
            api_endpoints = [ep.strip('"\'') for ep in endpoint_patterns]
            
            # Extract authentication patterns
            auth_patterns = re.findall(r'["\']/(auth|login|signin)/[^"\']*["\']', html_content)
            auth_endpoints = [ep.strip('"\'') for ep in auth_patterns]
            
            return {
                'bootstrap_data': bootstrap_data,
                'api_endpoints': list(set(api_endpoints)),
                'auth_endpoints': list(set(auth_endpoints)),
                'base_html': html_content
            }
            
        except Exception as e:
            logging.error(f"Failed to extract Angular bootstrap data: {e}")
            return {'bootstrap_data': {}, 'api_endpoints': [], 'auth_endpoints': [], 'base_html': ''}
    
    def simulate_angular_authentication(self):
        """Simulate Angular application authentication flow"""
        try:
            # Extract Angular bootstrap data
            angular_info = self.extract_angular_bootstrap_data()
            
            # Try to find authentication configuration
            bootstrap_data = angular_info['bootstrap_data']
            
            # Look for authentication URLs in bootstrap data
            auth_url = None
            if 'authUrl' in bootstrap_data:
                auth_url = bootstrap_data['authUrl']
            elif 'loginUrl' in bootstrap_data:
                auth_url = bootstrap_data['loginUrl']
            elif 'apiUrl' in bootstrap_data:
                auth_url = urljoin(bootstrap_data['apiUrl'], '/auth/login')
            
            # Try discovered authentication endpoints
            for endpoint in angular_info['auth_endpoints']:
                if self._attempt_angular_auth(endpoint):
                    return True
            
            # Try standard Angular authentication patterns
            standard_patterns = [
                '/api/auth/authenticate',
                '/api/authentication/login',
                '/api/user/authenticate',
                '/api/session/create',
                '/auth/session',
                '/login/validate'
            ]
            
            for pattern in standard_patterns:
                if self._attempt_angular_auth(pattern):
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Angular authentication simulation failed: {e}")
            return False
    
    def _attempt_angular_auth(self, endpoint):
        """Attempt authentication with specific endpoint"""
        try:
            auth_url = urljoin(self.base_url, endpoint)
            
            # Update headers for AJAX request
            ajax_headers = {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': self.base_url,
                'Origin': self.base_url
            }
            
            # Try different authentication payloads
            auth_payloads = [
                {'username': self.username, 'password': self.password},
                {'email': self.username, 'password': self.password},
                {'user': self.username, 'pass': self.password},
                {'login': self.username, 'pwd': self.password},
                {'credentials': {'username': self.username, 'password': self.password}},
                {'auth': {'user': self.username, 'password': self.password}}
            ]
            
            for payload in auth_payloads:
                try:
                    response = self.session.post(
                        auth_url,
                        json=payload,
                        headers=ajax_headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            
                            # Check for successful authentication indicators
                            if any(key in result for key in ['token', 'jwt', 'access_token', 'sessionId', 'success']):
                                # Extract and apply authentication token
                                token = (result.get('token') or 
                                        result.get('jwt') or 
                                        result.get('access_token') or 
                                        result.get('sessionId'))
                                
                                if token:
                                    self.session.headers['Authorization'] = f'Bearer {token}'
                                    self.session.headers['X-Auth-Token'] = token
                                
                                self.authenticated = True
                                logging.info(f"Angular authentication successful via {endpoint}")
                                return True
                                
                            elif result.get('success') or result.get('authenticated'):
                                self.authenticated = True
                                logging.info(f"Angular authentication successful (no token) via {endpoint}")
                                return True
                        
                        except json.JSONDecodeError:
                            # Check for redirect or success indicators in HTML
                            if len(response.text) > 100 and 'error' not in response.text.lower():
                                self.authenticated = True
                                logging.info(f"Angular authentication successful (HTML) via {endpoint}")
                                return True
                
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logging.debug(f"Authentication attempt failed for {endpoint}: {e}")
            return False
    
    def extract_authenticated_data(self):
        """Extract actual project data after authentication"""
        if not self.authenticated:
            return {
                'status': 'error',
                'message': 'Authentication required for data extraction'
            }
        
        extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'reports': [],
            'billing': [],
            'dashboard_data': {},
            'raw_extractions': []
        }
        
        # Enhanced headers for authenticated requests
        auth_headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/',
            'Origin': self.base_url,
            'Cache-Control': 'no-cache'
        }
        
        # Comprehensive data extraction endpoints
        extraction_targets = [
            ('projects', [
                '/api/projects',
                '/api/projects/list',
                '/api/projects/all',
                '/api/project/data',
                '/data/projects',
                '/projects/api',
                '/api/jobs',
                '/api/contracts'
            ]),
            ('assets', [
                '/api/assets',
                '/api/equipment',
                '/api/assets/list',
                '/api/equipment/all',
                '/data/assets',
                '/data/equipment',
                '/assets/api',
                '/equipment/api'
            ]),
            ('personnel', [
                '/api/users',
                '/api/personnel',
                '/api/employees',
                '/api/staff',
                '/data/users',
                '/data/personnel',
                '/users/api'
            ]),
            ('billing', [
                '/api/billing',
                '/api/invoices',
                '/api/payments',
                '/api/financial',
                '/data/billing',
                '/billing/api',
                '/financial/api'
            ]),
            ('reports', [
                '/api/reports',
                '/api/analytics',
                '/api/statistics',
                '/data/reports',
                '/reports/api'
            ]),
            ('dashboard', [
                '/api/dashboard',
                '/api/overview',
                '/api/summary',
                '/data/dashboard',
                '/dashboard/api'
            ])
        ]
        
        # Extract data from each category
        for category, endpoints in extraction_targets:
            category_data = self._extract_category_with_retries(category, endpoints, auth_headers)
            
            if category == 'dashboard':
                extracted_data['dashboard_data'] = category_data
            else:
                extracted_data[category] = category_data
        
        # Additional comprehensive extraction
        comprehensive_data = self._comprehensive_authenticated_scan(auth_headers)
        extracted_data['raw_extractions'] = comprehensive_data
        
        return {
            'status': 'success',
            'data': extracted_data,
            'extraction_summary': {
                'projects_found': len(extracted_data['projects']),
                'assets_found': len(extracted_data['assets']),
                'personnel_found': len(extracted_data['personnel']),
                'reports_found': len(extracted_data['reports']),
                'billing_records_found': len(extracted_data['billing']),
                'raw_extractions': len(extracted_data['raw_extractions']),
                'authentication_method': 'angular_simulation'
            }
        }
    
    def _extract_category_with_retries(self, category, endpoints, headers):
        """Extract data for category with multiple endpoint attempts"""
        for endpoint in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Check if we got actual data (not Angular shell)
                    if len(response.text) > 1000 and 'app-root' not in response.text:
                        try:
                            data = response.json()
                            if data and isinstance(data, (dict, list)):
                                processed_data = self._process_extracted_data(data, category)
                                if processed_data:
                                    logging.info(f"Successfully extracted {category} data from {endpoint}")
                                    return processed_data
                        except json.JSONDecodeError:
                            # Try to extract from HTML/text content
                            html_data = self._extract_from_content(response.text, category)
                            if html_data:
                                logging.info(f"Successfully extracted {category} HTML data from {endpoint}")
                                return html_data
                    
                    # Try with different parameters
                    param_variations = [
                        {'format': 'json'},
                        {'type': 'data'},
                        {'export': 'true'},
                        {'full': 'true'},
                        {'detailed': 'true'}
                    ]
                    
                    for params in param_variations:
                        try:
                            param_response = self.session.get(url, headers=headers, params=params, timeout=5)
                            if param_response.status_code == 200 and len(param_response.text) > 1000:
                                try:
                                    data = param_response.json()
                                    if data:
                                        processed_data = self._process_extracted_data(data, category)
                                        if processed_data:
                                            return processed_data
                                except:
                                    continue
                        except:
                            continue
            
            except Exception as e:
                continue
        
        return []
    
    def _comprehensive_authenticated_scan(self, headers):
        """Perform comprehensive scan of all accessible endpoints"""
        comprehensive_data = []
        
        # Additional endpoint patterns to try
        scan_patterns = [
            '/api/data/all',
            '/api/export/data',
            '/api/full/data',
            '/data/complete',
            '/export/all',
            '/api/admin/export',
            '/api/user/data/all',
            '/api/complete/export'
        ]
        
        for pattern in scan_patterns:
            try:
                url = urljoin(self.base_url, pattern)
                response = self.session.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200 and len(response.text) > 1000:
                    try:
                        data = response.json()
                        if data and len(str(data)) > 100:
                            comprehensive_data.append({
                                'endpoint': pattern,
                                'data': data,
                                'type': 'json',
                                'extracted_at': str(datetime.now())
                            })
                    except:
                        # Extract from HTML/text
                        extracted_content = self._extract_from_content(response.text, 'comprehensive')
                        if extracted_content:
                            comprehensive_data.append({
                                'endpoint': pattern,
                                'data': extracted_content,
                                'type': 'html',
                                'extracted_at': str(datetime.now())
                            })
            
            except Exception as e:
                continue
        
        return comprehensive_data
    
    def _process_extracted_data(self, raw_data, category):
        """Process and structure extracted data"""
        try:
            if isinstance(raw_data, list):
                return raw_data
            elif isinstance(raw_data, dict):
                # Look for data arrays in common keys
                for key in ['data', 'items', 'results', 'records', category, f'{category}_list']:
                    if key in raw_data and isinstance(raw_data[key], list):
                        return raw_data[key]
                
                # If single object, return as list
                if raw_data:
                    return [raw_data]
            
            return []
            
        except Exception as e:
            return []
    
    def _extract_from_content(self, content, category):
        """Extract structured data from HTML/text content"""
        try:
            extracted_items = []
            
            # Extract JSON from script tags
            json_patterns = [
                r'<script[^>]*>.*?(?:var|const|let)\s+\w+\s*=\s*(\{.*?\});.*?</script>',
                r'<script[^>]*>.*?(\[.*?\]).*?</script>',
                r'data-json=["\']([^"\']+)["\']'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, (dict, list)) and len(str(data)) > 50:
                            processed = self._process_extracted_data(data, category)
                            if processed:
                                extracted_items.extend(processed if isinstance(processed, list) else [processed])
                    except:
                        continue
            
            # Extract table data
            table_data = self._extract_table_data(content)
            if table_data:
                extracted_items.extend(table_data)
            
            return extracted_items[:100]  # Limit results
            
        except Exception as e:
            return []
    
    def _extract_table_data(self, html_content):
        """Extract data from HTML tables"""
        try:
            table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.DOTALL | re.IGNORECASE)
            
            extracted_rows = []
            for row in table_rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if cells and len(cells) > 1:
                    cleaned_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                    if any(cell and len(cell) > 1 for cell in cleaned_cells):
                        extracted_rows.append({
                            'table_data': cleaned_cells,
                            'extracted_at': str(datetime.now())
                        })
            
            return extracted_rows[:50]
            
        except Exception as e:
            return []
    
    def connect_and_extract(self):
        """Main connection and extraction method"""
        try:
            # Attempt Angular authentication simulation
            if not self.simulate_angular_authentication():
                return {
                    'status': 'error',
                    'message': 'Advanced authentication failed - unable to access Ground Works data'
                }
            
            # Extract authenticated data
            return self.extract_authenticated_data()
            
        except Exception as e:
            logging.error(f"Advanced extraction error: {e}")
            return {
                'status': 'error',
                'message': f'Advanced extraction failed: {e}'
            }

def execute_advanced_extraction(username, password):
    """Execute advanced Ground Works data extraction"""
    extractor = AdvancedDataExtractor(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return extractor.connect_and_extract()