"""
Web Browser Data Extractor
Uses HTTP session management to simulate browser login and extract Ground Works data
"""

import requests
import re
import json
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import time

class WebBrowserExtractor:
    """Browser simulation extractor for Ground Works data"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        
        # Comprehensive browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def extract_csrf_and_form_data(self, html_content):
        """Extract CSRF tokens and form data from HTML"""
        csrf_patterns = [
            r'<meta[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
            r'<input[^>]*name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']',
            r'<input[^>]*name=["\']authenticity_token["\'][^>]*value=["\']([^"\']+)["\']',
            r'window\._token\s*=\s*["\']([^"\']+)["\']',
            r'csrf_token["\']:\s*["\']([^"\']+)["\']'
        ]
        
        tokens = {}
        for pattern in csrf_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                tokens['csrf_token'] = matches[0]
                break
        
        # Extract form action URLs
        form_actions = re.findall(r'<form[^>]*action=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        
        # Extract hidden input fields
        hidden_inputs = {}
        hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']'
        hidden_matches = re.findall(hidden_pattern, html_content, re.IGNORECASE)
        
        for name, value in hidden_matches:
            hidden_inputs[name] = value
        
        return {
            'tokens': tokens,
            'form_actions': form_actions,
            'hidden_inputs': hidden_inputs
        }
    
    def simulate_browser_login(self):
        """Simulate complete browser login process"""
        try:
            # Step 1: Get the login page and extract form data
            login_page_response = self.session.get(f"{self.base_url}/login")
            
            if login_page_response.status_code != 200:
                logging.error(f"Failed to access login page: {login_page_response.status_code}")
                return False
            
            form_data = self.extract_csrf_and_form_data(login_page_response.text)
            
            # Step 2: Build login payload with extracted data
            login_payload = {
                'username': self.username,
                'password': self.password,
                'email': self.username,  # Try both username and email
                'user': self.username,
                'login': self.username
            }
            
            # Add any extracted tokens and hidden fields
            login_payload.update(form_data['hidden_inputs'])
            if 'csrf_token' in form_data['tokens']:
                login_payload['_token'] = form_data['tokens']['csrf_token']
                login_payload['csrf_token'] = form_data['tokens']['csrf_token']
                login_payload['authenticity_token'] = form_data['tokens']['csrf_token']
            
            # Step 3: Determine login endpoint
            login_endpoints = [
                '/login',
                '/auth/login',
                '/user/login',
                '/signin',
                '/authenticate'
            ]
            
            # If form action was found, use it
            if form_data['form_actions']:
                login_endpoints.insert(0, form_data['form_actions'][0])
            
            # Step 4: Attempt login with form submission headers
            form_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f"{self.base_url}/login",
                'Origin': self.base_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            for endpoint in login_endpoints:
                try:
                    login_url = urljoin(self.base_url, endpoint)
                    login_response = self.session.post(
                        login_url,
                        data=login_payload,
                        headers=form_headers,
                        allow_redirects=True,
                        timeout=15
                    )
                    
                    # Check for successful login indicators
                    if self.check_login_success(login_response):
                        self.authenticated = True
                        logging.info(f"Browser login successful via {endpoint}")
                        return True
                        
                except Exception as e:
                    logging.debug(f"Login attempt failed for {endpoint}: {e}")
                    continue
            
            # Step 5: Try GET-based authentication (some systems use this)
            for endpoint in login_endpoints:
                try:
                    auth_url = f"{urljoin(self.base_url, endpoint)}?username={self.username}&password={self.password}"
                    get_response = self.session.get(auth_url, allow_redirects=True, timeout=10)
                    
                    if self.check_login_success(get_response):
                        self.authenticated = True
                        logging.info(f"GET-based login successful via {endpoint}")
                        return True
                        
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"Browser login simulation failed: {e}")
            return False
    
    def check_login_success(self, response):
        """Check if login was successful based on response"""
        success_indicators = [
            'dashboard',
            'welcome',
            'logout',
            'profile',
            'home',
            'main',
            'projects',
            'assets'
        ]
        
        failure_indicators = [
            'login failed',
            'invalid credentials',
            'authentication failed',
            'error',
            'username',
            'password'
        ]
        
        response_text = response.text.lower()
        
        # Check for success indicators
        success_count = sum(1 for indicator in success_indicators if indicator in response_text)
        failure_count = sum(1 for indicator in failure_indicators if indicator in response_text)
        
        # Check for redirects to dashboard/home
        if response.history:
            for redirect in response.history:
                redirect_url = redirect.headers.get('Location', '').lower()
                if any(indicator in redirect_url for indicator in ['dashboard', 'home', 'main']):
                    return True
        
        # Check final URL
        final_url = response.url.lower()
        if any(indicator in final_url for indicator in success_indicators):
            return True
        
        # If we have more success indicators than failure indicators
        return success_count > failure_count and success_count > 2
    
    def extract_authenticated_data(self):
        """Extract data after successful authentication"""
        if not self.authenticated:
            return {
                'status': 'error',
                'message': 'Authentication required'
            }
        
        extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'reports': [],
            'billing': [],
            'dashboard_data': {},
            'raw_pages': []
        }
        
        # Data extraction endpoints to try
        data_pages = [
            ('/dashboard', 'dashboard_data'),
            ('/projects', 'projects'),
            ('/assets', 'assets'),
            ('/equipment', 'assets'),
            ('/users', 'personnel'),
            ('/personnel', 'personnel'),
            ('/reports', 'reports'),
            ('/billing', 'billing'),
            ('/invoices', 'billing')
        ]
        
        # Extract data from each page
        for page_path, data_key in data_pages:
            try:
                page_url = urljoin(self.base_url, page_path)
                page_response = self.session.get(page_url, timeout=10)
                
                if page_response.status_code == 200:
                    # Extract structured data from the page
                    page_data = self.extract_data_from_page(page_response.text, data_key)
                    
                    if page_data:
                        if data_key == 'dashboard_data':
                            extracted_data[data_key] = page_data
                        else:
                            extracted_data[data_key].extend(page_data)
                    
                    # Store raw page content for analysis
                    extracted_data['raw_pages'].append({
                        'url': page_url,
                        'content_length': len(page_response.text),
                        'extracted_items': len(page_data) if page_data else 0,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logging.debug(f"Failed to extract from {page_path}: {e}")
                continue
        
        return {
            'status': 'success',
            'data': extracted_data,
            'extraction_summary': {
                'total_pages_accessed': len(extracted_data['raw_pages']),
                'projects_found': len(extracted_data['projects']),
                'assets_found': len(extracted_data['assets']),
                'personnel_found': len(extracted_data['personnel']),
                'reports_found': len(extracted_data['reports']),
                'billing_records_found': len(extracted_data['billing']),
                'authentication_method': 'browser_simulation'
            }
        }
    
    def extract_data_from_page(self, html_content, data_type):
        """Extract structured data from HTML page content"""
        try:
            extracted_items = []
            
            # Extract JSON data from script tags
            json_patterns = [
                r'var\s+data\s*=\s*(\{.*?\});',
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'window\.data\s*=\s*(\{.*?\});',
                r'initialData\s*=\s*(\{.*?\});',
                r'"data":\s*(\[.*?\])',
                r'"items":\s*(\[.*?\])',
                r'"results":\s*(\[.*?\])'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            extracted_items.extend(data)
                        elif isinstance(data, dict) and len(data) > 0:
                            extracted_items.append(data)
                    except json.JSONDecodeError:
                        continue
            
            # Extract table data
            table_data = self.extract_table_data(html_content)
            extracted_items.extend(table_data)
            
            # Extract list items
            list_data = self.extract_list_data(html_content)
            extracted_items.extend(list_data)
            
            return extracted_items[:100]  # Limit results
            
        except Exception as e:
            logging.debug(f"Failed to extract data from page: {e}")
            return []
    
    def extract_table_data(self, html_content):
        """Extract data from HTML tables"""
        try:
            table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.DOTALL | re.IGNORECASE)
            
            extracted_rows = []
            for row in table_rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if cells and len(cells) > 1:
                    cleaned_cells = []
                    for cell in cells:
                        # Remove HTML tags and clean text
                        clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                        if clean_cell and len(clean_cell) > 0:
                            cleaned_cells.append(clean_cell)
                    
                    if len(cleaned_cells) > 1:
                        extracted_rows.append({
                            'type': 'table_row',
                            'data': cleaned_cells,
                            'extracted_at': datetime.now().isoformat()
                        })
            
            return extracted_rows[:50]
            
        except Exception as e:
            return []
    
    def extract_list_data(self, html_content):
        """Extract data from HTML lists and structured content"""
        try:
            extracted_items = []
            
            # Extract list items
            list_items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL | re.IGNORECASE)
            for item in list_items:
                clean_item = re.sub(r'<[^>]+>', '', item).strip()
                if clean_item and len(clean_item) > 10:
                    extracted_items.append({
                        'type': 'list_item',
                        'content': clean_item,
                        'extracted_at': datetime.now().isoformat()
                    })
            
            # Extract div content with data attributes
            div_data = re.findall(r'<div[^>]*data-[^>]*>(.*?)</div>', html_content, re.DOTALL | re.IGNORECASE)
            for item in div_data:
                clean_item = re.sub(r'<[^>]+>', '', item).strip()
                if clean_item and len(clean_item) > 10:
                    extracted_items.append({
                        'type': 'data_div',
                        'content': clean_item,
                        'extracted_at': datetime.now().isoformat()
                    })
            
            return extracted_items[:50]
            
        except Exception as e:
            return []
    
    def connect_and_extract(self):
        """Main method to connect and extract data"""
        try:
            # Attempt browser login
            if not self.simulate_browser_login():
                return {
                    'status': 'error',
                    'message': 'Browser authentication failed - unable to log in to Ground Works'
                }
            
            # Extract data after successful login
            return self.extract_authenticated_data()
            
        except Exception as e:
            logging.error(f"Web browser extraction failed: {e}")
            return {
                'status': 'error',
                'message': f'Web browser extraction failed: {str(e)}'
            }

def execute_web_browser_extraction(username, password):
    """Execute web browser-based Ground Works data extraction"""
    extractor = WebBrowserExtractor(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return extractor.connect_and_extract()