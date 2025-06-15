"""
Session-Based Ground Works Extractor
Uses browser session cookies for authenticated data extraction
"""

import requests
import json
import os
from datetime import datetime
import re

class SessionBasedExtractor:
    """Extract Ground Works data using authenticated browser session"""
    
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.session = requests.Session()
        self.extracted_data = {}
        
    def extract_with_session_cookies(self, cookies_string=None):
        """Extract data using session cookies from browser"""
        print("Extracting Ground Works data with session authentication...")
        
        # If cookies provided, use them
        if cookies_string:
            self.parse_and_set_cookies(cookies_string)
        
        # Set authenticated headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{self.base_url}/',
            'Origin': self.base_url,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        self.session.headers.update(headers)
        
        # Try Angular/SPA API endpoints that would be used by the authenticated app
        api_endpoints = [
            # Main data endpoints
            '/api/v1/projects',
            '/api/v1/assets',
            '/api/v1/users',
            '/api/v1/dashboard',
            '/api/v1/reports',
            
            # Alternative API patterns
            '/api/projects/list',
            '/api/assets/list', 
            '/api/users/list',
            '/api/dashboard/data',
            '/api/reports/data',
            
            # GraphQL endpoints
            '/graphql',
            '/api/graphql',
            
            # Common Angular endpoints
            '/api/data',
            '/data/projects',
            '/data/assets',
            '/data/users',
            
            # Export endpoints
            '/export/projects.json',
            '/export/assets.json',
            '/export/all.json'
        ]
        
        extracted_count = 0
        
        for endpoint in api_endpoints:
            try:
                # Try GET request
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and (isinstance(data, list) or isinstance(data, dict)):
                            self.extracted_data[endpoint] = data
                            extracted_count += 1
                            print(f"✓ Extracted data from {endpoint}")
                            
                            # If it's a list of items, count them
                            if isinstance(data, list):
                                print(f"  Found {len(data)} items")
                            elif isinstance(data, dict) and 'data' in data:
                                print(f"  Found data object with {len(data.get('data', []))} items")
                                
                    except json.JSONDecodeError:
                        # Not JSON, but might be useful data
                        if len(response.text) > 100:
                            self.extracted_data[f"{endpoint}_html"] = response.text
                            extracted_count += 1
                            print(f"✓ Extracted HTML from {endpoint}")
                
                # Also try POST for some endpoints
                if 'graphql' in endpoint or 'api' in endpoint:
                    try:
                        post_data = {'query': '{ projects { id name status } }'}
                        post_response = self.session.post(f"{self.base_url}{endpoint}", json=post_data, timeout=5)
                        
                        if post_response.status_code == 200:
                            try:
                                data = post_response.json()
                                if data:
                                    self.extracted_data[f"{endpoint}_post"] = data
                                    extracted_count += 1
                                    print(f"✓ Extracted POST data from {endpoint}")
                            except:
                                pass
                    except:
                        pass
                        
            except Exception as e:
                continue
        
        print(f"Extracted data from {extracted_count} endpoints")
        return extracted_count
    
    def parse_and_set_cookies(self, cookies_string):
        """Parse cookies string and set in session"""
        if not cookies_string:
            return
            
        cookies = {}
        for cookie in cookies_string.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name] = value
        
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
        
        print(f"Set {len(cookies)} cookies for authentication")
    
    def extract_angular_state(self):
        """Extract Angular application state from main page"""
        print("Extracting Angular application state...")
        
        try:
            # Get the main application page
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Look for Angular bootstrap data
                angular_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__DATA__\s*=\s*({.*?});',
                    r'window\.APP_DATA\s*=\s*({.*?});',
                    r'window\.BOOTSTRAP_DATA\s*=\s*({.*?});',
                    r'ng-init="[^"]*"\s*data-ng-init="([^"]*)"',
                    r'data-angular-state="([^"]*)"'
                ]
                
                extracted_state = 0
                
                for pattern in angular_patterns:
                    matches = re.findall(pattern, html_content, re.DOTALL)
                    for match in matches:
                        try:
                            if match.startswith('{'):
                                data = json.loads(match)
                                self.extracted_data['angular_state'] = data
                                extracted_state += 1
                                print(f"✓ Extracted Angular state data")
                        except:
                            continue
                
                # Also look for script tags with data
                script_pattern = r'<script[^>]*>(.*?)</script>'
                scripts = re.findall(script_pattern, html_content, re.DOTALL)
                
                for script in scripts:
                    # Look for variable assignments with data
                    var_patterns = [
                        r'var\s+projects\s*=\s*(\[.*?\]);',
                        r'var\s+assets\s*=\s*(\[.*?\]);',
                        r'var\s+users\s*=\s*(\[.*?\]);',
                        r'const\s+\w*[Dd]ata\s*=\s*(\{.*?\});'
                    ]
                    
                    for var_pattern in var_patterns:
                        var_matches = re.findall(var_pattern, script, re.DOTALL)
                        for var_match in var_matches:
                            try:
                                data = json.loads(var_match)
                                if data:
                                    self.extracted_data['script_data'] = data
                                    extracted_state += 1
                                    print(f"✓ Extracted script data")
                            except:
                                continue
                
                return extracted_state > 0
                
        except Exception as e:
            print(f"Error extracting Angular state: {e}")
            
        return False
    
    def try_common_endpoints(self):
        """Try common Ground Works specific endpoints"""
        print("Trying Ground Works specific endpoints...")
        
        # Ground Works specific patterns based on common project management systems
        gw_endpoints = [
            # Project management endpoints
            '/projects/api/list',
            '/projects/getall',
            '/projects/search',
            '/projects.json',
            
            # Asset management
            '/assets/api/list',
            '/assets/getall', 
            '/equipment/list',
            '/fleet/status',
            
            # User management
            '/users/api/list',
            '/personnel/list',
            '/employees/active',
            
            # Reports and dashboards
            '/dashboard/widgets',
            '/dashboard/summary',
            '/reports/summary',
            '/analytics/data',
            
            # Configuration
            '/config/app',
            '/settings/system',
            '/admin/data'
        ]
        
        extracted = 0
        
        for endpoint in gw_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data:
                            self.extracted_data[f"gw_{endpoint.replace('/', '_')}"] = data
                            extracted += 1
                            print(f"✓ Found data at {endpoint}")
                    except:
                        # Check if HTML contains useful data
                        if 'project' in response.text.lower() or 'asset' in response.text.lower():
                            # Extract any IDs or structured data from HTML
                            ids = re.findall(r'(?:project|asset|job)["\s]*[:\-=]\s*["\']?([A-Z0-9\-]+)["\']?', response.text, re.IGNORECASE)
                            if ids:
                                self.extracted_data[f"gw_{endpoint.replace('/', '_')}_ids"] = list(set(ids))
                                extracted += 1
                                print(f"✓ Found {len(set(ids))} IDs at {endpoint}")
                                
            except:
                continue
        
        return extracted
    
    def save_extracted_data(self):
        """Save all extracted data"""
        try:
            backup_dir = "session_ground_works_extraction"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete extraction
            with open(f"{backup_dir}/session_extraction_{timestamp}.json", 'w') as f:
                json.dump(self.extracted_data, f, indent=2, default=str)
            
            # Count and categorize extracted data
            total_items = 0
            projects = 0
            assets = 0
            users = 0
            
            for key, data in self.extracted_data.items():
                if isinstance(data, list):
                    total_items += len(data)
                    if 'project' in key.lower():
                        projects += len(data)
                    elif 'asset' in key.lower() or 'equipment' in key.lower():
                        assets += len(data)
                    elif 'user' in key.lower() or 'personnel' in key.lower():
                        users += len(data)
                elif isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], list):
                        total_items += len(data['data'])
            
            summary = {
                'extraction_time': datetime.now().isoformat(),
                'total_endpoints': len(self.extracted_data),
                'total_items': total_items,
                'projects_found': projects,
                'assets_found': assets,
                'users_found': users,
                'backup_location': backup_dir
            }
            
            # Save summary
            with open(f"{backup_dir}/extraction_summary_{timestamp}.json", 'w') as f:
                json.dump(summary, f, indent=2)
            
            return summary
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return None
    
    def execute_session_extraction(self, cookies=None):
        """Execute complete session-based extraction"""
        print("Starting session-based Ground Works extraction...")
        
        # Extract using API endpoints
        api_count = self.extract_with_session_cookies(cookies)
        
        # Extract Angular state
        state_extracted = self.extract_angular_state()
        
        # Try Ground Works specific endpoints
        gw_count = self.try_common_endpoints()
        
        # Save everything
        summary = self.save_extracted_data()
        
        if summary:
            print("\n" + "="*50)
            print("SESSION EXTRACTION SUMMARY")
            print("="*50)
            print(f"API Endpoints: {api_count} extracted")
            print(f"Angular State: {'✓' if state_extracted else '✗'}")
            print(f"GW Endpoints: {gw_count} extracted")
            print(f"Total Sources: {summary['total_endpoints']}")
            print(f"Total Items: {summary['total_items']}")
            print(f"Projects: {summary['projects_found']}")
            print(f"Assets: {summary['assets_found']}")
            print(f"Users: {summary['users_found']}")
            print(f"Saved to: {summary['backup_location']}")
            print("="*50)
            
            return summary
        
        return None

def extract_with_browser_session(cookies=None):
    """Main function to extract Ground Works data using browser session"""
    extractor = SessionBasedExtractor()
    return extractor.execute_session_extraction(cookies)

if __name__ == "__main__":
    result = extract_with_browser_session()
    if result:
        print(json.dumps(result, indent=2))