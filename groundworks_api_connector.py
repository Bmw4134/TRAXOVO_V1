"""
Ground Works API Connector
Internal API integration system for TRAXOVO to connect directly to Ground Works
"""

import requests
import json
import time
from datetime import datetime
import logging
from urllib.parse import urljoin

class GroundWorksAPIConnector:
    """Direct API connector for Ground Works system integration"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        self.extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'billing': [],
            'schedules': [],
            'reports': []
        }
        
        # Set realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def authenticate(self):
        """Authenticate with Ground Works system using known login endpoint"""
        try:
            # Based on the URL provided, use the specific login endpoint
            login_url = f"{self.base_url}/login"
            
            # Get the login page first
            login_page = self.session.get(login_url)
            
            if login_page.status_code != 200:
                logging.error(f"Cannot access login page: {login_page.status_code}")
                return False
            
            # Extract any CSRF token from the login page
            csrf_token = self._extract_csrf_token(login_page.text)
            
            # Try different login data variations for Ground Works
            login_variations = [
                {
                    'username': self.username,
                    'password': self.password
                },
                {
                    'email': self.username,
                    'password': self.password
                },
                {
                    'user': self.username,
                    'password': self.password
                },
                {
                    'login': self.username,
                    'pwd': self.password
                },
                {
                    'user_name': self.username,
                    'user_password': self.password
                }
            ]
            
            # Add CSRF token if found
            for login_data in login_variations:
                if csrf_token:
                    login_data['_token'] = csrf_token
                    login_data['csrf_token'] = csrf_token
                    login_data['authenticity_token'] = csrf_token
                
                # Try form-based authentication
                try:
                    response = self.session.post(
                        login_url,
                        data=login_data,
                        allow_redirects=True,
                        timeout=15
                    )
                    
                    # Check for successful authentication
                    if self._check_authentication_success(response):
                        self.authenticated = True
                        logging.info(f"Successfully authenticated with Ground Works")
                        return True
                        
                except Exception as e:
                    logging.debug(f"Login attempt failed: {e}")
                    continue
            
            # Try alternative authentication methods for Ground Works
            alt_endpoints = [
                '/login/',  # With trailing slash
                '/auth',
                '/signin',
                '/user/login'
            ]
            
            for endpoint in alt_endpoints:
                for login_data in login_variations:
                    try:
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            data=login_data,
                            allow_redirects=True,
                            timeout=10
                        )
                        
                        if self._check_authentication_success(response):
                            self.authenticated = True
                            logging.info(f"Successfully authenticated via {endpoint}")
                            return True
                            
                    except Exception as e:
                        continue
            
            logging.warning("All authentication attempts failed")
            return False
            
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False
    
    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content"""
        import re
        
        # Common CSRF token patterns
        patterns = [
            r'<meta name="csrf-token" content="([^"]+)"',
            r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"',
            r'<input[^>]*name="_token"[^>]*value="([^"]+)"',
            r'"csrf_token":\s*"([^"]+)"',
            r'window\.csrf_token\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _check_authentication_success(self, response):
        """Check if authentication was successful"""
        # Check for successful redirect
        if response.status_code in [200, 302] and 'dashboard' in response.url.lower():
            return True
        
        # Check response content for success indicators
        if response.status_code == 200:
            content = response.text.lower()
            success_indicators = ['dashboard', 'welcome', 'logout', 'profile', 'projects']
            failure_indicators = ['login', 'signin', 'error', 'invalid', 'incorrect']
            
            has_success = any(indicator in content for indicator in success_indicators)
            has_failure = any(indicator in content for indicator in failure_indicators)
            
            return has_success and not has_failure
        
        return False
    
    def extract_all_data(self):
        """Extract all available data from Ground Works"""
        if not self.authenticated:
            return {'status': 'error', 'message': 'Not authenticated'}
        
        # Define comprehensive API endpoints to try
        api_endpoints = {
            'projects': [
                '/api/projects',
                '/api/v1/projects',
                '/projects/api',
                '/projects/list',
                '/data/projects',
                '/api/projects/list'
            ],
            'assets': [
                '/api/assets',
                '/api/v1/assets',
                '/assets/api',
                '/assets/list',
                '/equipment/list',
                '/fleet/data',
                '/api/equipment'
            ],
            'personnel': [
                '/api/users',
                '/api/v1/users',
                '/users/api',
                '/personnel/list',
                '/staff/data',
                '/api/personnel',
                '/employees/list'
            ],
            'billing': [
                '/api/billing',
                '/api/v1/billing',
                '/billing/api',
                '/invoices/list',
                '/finance/data',
                '/api/invoices',
                '/payments/data'
            ],
            'schedules': [
                '/api/schedules',
                '/api/v1/schedules',
                '/calendar/data',
                '/schedule/list',
                '/api/calendar',
                '/timesheet/data'
            ],
            'reports': [
                '/api/reports',
                '/api/v1/reports',
                '/reports/data',
                '/analytics/data',
                '/dashboard/data',
                '/api/analytics'
            ]
        }
        
        extracted_count = 0
        
        for data_type, endpoints in api_endpoints.items():
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'json' in content_type:
                            try:
                                data = response.json()
                                if data and len(str(data)) > 50:  # Skip empty responses
                                    if isinstance(data, list):
                                        self.extracted_data[data_type].extend(data)
                                    elif isinstance(data, dict):
                                        if 'data' in data and isinstance(data['data'], list):
                                            self.extracted_data[data_type].extend(data['data'])
                                        else:
                                            self.extracted_data[data_type].append(data)
                                    
                                    extracted_count += 1
                                    logging.info(f"Extracted {data_type} data from {endpoint}")
                                    break  # Move to next data type once we get data
                                    
                            except json.JSONDecodeError:
                                continue
                        else:
                            # Try to extract data from HTML responses
                            if len(response.text) > 1000:
                                html_data = self._extract_data_from_html(response.text, data_type)
                                if html_data:
                                    self.extracted_data[data_type].extend(html_data)
                                    extracted_count += 1
                                    logging.info(f"Extracted {data_type} HTML data from {endpoint}")
                                    break
                
                except Exception as e:
                    continue
        
        # Try export endpoints for bulk data
        export_endpoints = [
            '/export/all',
            '/api/export/all',
            '/data/export',
            '/export/projects',
            '/export/assets',
            '/download/data'
        ]
        
        for endpoint in export_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data:
                            # Merge export data with extracted data
                            for key, value in data.items():
                                if key in self.extracted_data and isinstance(value, list):
                                    self.extracted_data[key].extend(value)
                                    extracted_count += 1
                    except:
                        pass
                        
            except:
                continue
        
        return {
            'status': 'success',
            'extracted_endpoints': extracted_count,
            'data_summary': {
                'projects': len(self.extracted_data['projects']),
                'assets': len(self.extracted_data['assets']),
                'personnel': len(self.extracted_data['personnel']),
                'billing': len(self.extracted_data['billing']),
                'schedules': len(self.extracted_data['schedules']),
                'reports': len(self.extracted_data['reports'])
            }
        }
    
    def _extract_data_from_html(self, html_content, data_type):
        """Extract structured data from HTML content"""
        import re
        
        extracted_items = []
        
        # Look for table data
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for table in tables:
            # Extract table rows
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, table, re.DOTALL | re.IGNORECASE)
            
            headers = []
            for i, row in enumerate(rows):
                cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
                cells = re.findall(cell_pattern, row, re.DOTALL | re.IGNORECASE)
                
                if i == 0:  # Header row
                    headers = [self._clean_html_text(cell) for cell in cells]
                else:  # Data row
                    if len(cells) >= len(headers) and headers:
                        item = {}
                        for j, cell in enumerate(cells[:len(headers)]):
                            if j < len(headers):
                                item[headers[j].lower().replace(' ', '_')] = self._clean_html_text(cell)
                        if item:
                            extracted_items.append(item)
        
        # Look for JSON data in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for script in scripts:
            # Look for arrays of objects
            json_patterns = [
                rf'{data_type}\s*[:=]\s*(\[.*?\])',
                r'data\s*[:=]\s*(\[.*?\])',
                r'items\s*[:=]\s*(\[.*?\])'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, script, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            extracted_items.extend(data)
                    except:
                        continue
        
        return extracted_items
    
    def _clean_html_text(self, text):
        """Clean HTML text and extract meaningful content"""
        import re
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        # Decode HTML entities
        clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return clean_text.strip()
    
    def connect_and_extract(self):
        """Main method to connect and extract all data"""
        try:
            # Step 1: Authenticate
            if not self.authenticate():
                return {
                    'status': 'error',
                    'message': 'Authentication failed. Please check your username and password.'
                }
            
            # Step 2: Extract all data
            extraction_result = self.extract_all_data()
            
            if extraction_result['status'] == 'success':
                # Save extracted data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"groundworks_extraction_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(self.extracted_data, f, indent=2, default=str)
                
                return {
                    'status': 'success',
                    'message': 'Ground Works data extracted successfully',
                    'data': self.extracted_data,
                    'summary': extraction_result['data_summary'],
                    'backup_file': filename
                }
            else:
                return extraction_result
                
        except Exception as e:
            logging.error(f"Connection and extraction error: {e}")
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)}'
            }
    
    @classmethod
    def from_session(cls, session_data):
        """Create connector from stored session data"""
        return cls(
            base_url=session_data.get('groundworks_base_url', 'https://groundworks.ragleinc.com'),
            username=session_data.get('groundworks_username'),
            password=session_data.get('groundworks_password')
        )
    
    def refresh_data(self):
        """Refresh data using existing authentication"""
        if not self.authenticated:
            # Re-authenticate if needed
            if not self.authenticate():
                return {
                    'status': 'error',
                    'message': 'Re-authentication failed'
                }
        
        # Clear existing data
        for key in self.extracted_data:
            self.extracted_data[key] = []
        
        # Extract fresh data
        return self.extract_all_data()

def test_groundworks_connection(username, password, base_url="https://groundworks.ragleinc.com"):
    """Test Ground Works connection with provided credentials"""
    connector = GroundWorksAPIConnector(base_url, username, password)
    return connector.connect_and_extract()

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        base_url = sys.argv[3] if len(sys.argv) > 3 else "https://groundworks.ragleinc.com"
        
        print(f"Testing Ground Works connection for {username}...")
        result = test_groundworks_connection(username, password, base_url)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python groundworks_api_connector.py <username> <password> [base_url]")