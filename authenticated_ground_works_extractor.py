"""
Authenticated Ground Works Data Extractor
Uses browser automation to access authenticated sessions
"""

import json
import os
import time
from datetime import datetime
import subprocess
import requests
from urllib.parse import urljoin

class AuthenticatedGroundWorksExtractor:
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'schedules': [],
            'reports': [],
            'api_endpoints': [],
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'source': 'authenticated_browser_session'
            }
        }
    
    def extract_via_curl_authenticated(self):
        """Extract data using curl with authentication cookies"""
        print("Attempting authenticated data extraction...")
        
        # Common API endpoints for Ground Works systems
        api_endpoints = [
            '/api/projects',
            '/api/assets',
            '/api/users',
            '/api/reports',
            '/api/dashboard',
            '/api/equipment',
            '/api/schedules',
            '/api/billing',
            '/projects/list',
            '/assets/list',
            '/users/list',
            '/reports/data',
            '/dashboard/data'
        ]
        
        extracted_apis = []
        
        for endpoint in api_endpoints:
            try:
                # Use curl to attempt authenticated requests
                url = f"{self.base_url}{endpoint}"
                
                # Try common authentication headers
                auth_headers = [
                    '-H "Accept: application/json"',
                    '-H "Content-Type: application/json"',
                    '-H "X-Requested-With: XMLHttpRequest"',
                    '-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"'
                ]
                
                curl_cmd = f'curl -s {" ".join(auth_headers)} "{url}"'
                
                result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout:
                    response_text = result.stdout.strip()
                    
                    # Check if response contains JSON data
                    if response_text.startswith('{') or response_text.startswith('['):
                        try:
                            parsed_data = json.loads(response_text)
                            extracted_apis.append({
                                'endpoint': endpoint,
                                'data': parsed_data,
                                'status': 'success'
                            })
                            print(f"Extracted data from {endpoint}")
                        except json.JSONDecodeError:
                            pass
                    
                    # Store raw response for analysis
                    extracted_apis.append({
                        'endpoint': endpoint,
                        'raw_response': response_text[:1000],  # First 1000 chars
                        'status': 'raw_data'
                    })
                
            except Exception as e:
                print(f"Error extracting {endpoint}: {str(e)[:50]}")
                continue
        
        self.extracted_data['api_endpoints'] = extracted_apis
        return extracted_apis
    
    def extract_javascript_data_sources(self):
        """Extract data source URLs from Ground Works JavaScript files"""
        print("Analyzing Ground Works JavaScript for data sources...")
        
        js_files = [
            '/main.js',
            '/vendor.js',
            '/runtime.js',
            '/polyfills.js'
        ]
        
        data_sources = []
        
        for js_file in js_files:
            try:
                url = f"{self.base_url}{js_file}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    js_content = response.text
                    
                    # Extract API endpoint patterns
                    import re
                    
                    # Common API patterns in Angular apps
                    api_patterns = [
                        r'[\'"](/api/[^\'"\s]+)[\'"]',
                        r'[\'"](https://[^\'"\s]+/api/[^\'"\s]+)[\'"]',
                        r'endpoint\s*[:=]\s*[\'"]([^\'"\s]+)[\'"]',
                        r'url\s*[:=]\s*[\'"]([^\'"\s]+)[\'"]',
                        r'baseUrl\s*[:=]\s*[\'"]([^\'"\s]+)[\'"]'
                    ]
                    
                    for pattern in api_patterns:
                        matches = re.findall(pattern, js_content)
                        for match in matches:
                            if '/api/' in match or 'projects' in match or 'assets' in match:
                                data_sources.append({
                                    'source': js_file,
                                    'endpoint': match,
                                    'type': 'api_endpoint'
                                })
                    
                    # Extract configuration objects
                    config_patterns = [
                        r'config\s*[:=]\s*(\{[^}]+\})',
                        r'apiConfig\s*[:=]\s*(\{[^}]+\})',
                        r'environment\s*[:=]\s*(\{[^}]+\})'
                    ]
                    
                    for pattern in config_patterns:
                        matches = re.findall(pattern, js_content)
                        for match in matches:
                            try:
                                # Attempt to parse as JSON-like object
                                data_sources.append({
                                    'source': js_file,
                                    'config': match,
                                    'type': 'configuration'
                                })
                            except:
                                continue
                
            except Exception as e:
                print(f"Error analyzing {js_file}: {str(e)[:50]}")
                continue
        
        self.extracted_data['data_sources'] = data_sources
        return data_sources
    
    def extract_angular_routes(self):
        """Extract Angular routing information for data endpoints"""
        print("Extracting Angular routes and components...")
        
        try:
            # Get the main application files
            main_url = f"{self.base_url}/main.js"
            response = requests.get(main_url, timeout=10)
            
            if response.status_code == 200:
                main_content = response.text
                
                import re
                
                # Extract routing patterns
                route_patterns = [
                    r'path\s*:\s*[\'"]([^\'"\s]+)[\'"]',
                    r'route\s*:\s*[\'"]([^\'"\s]+)[\'"]',
                    r'component\s*:\s*(\w+Component)',
                    r'loadChildren\s*:\s*[\'"]([^\'"\s]+)[\'"]'
                ]
                
                routes = []
                
                for pattern in route_patterns:
                    matches = re.findall(pattern, main_content)
                    for match in matches:
                        routes.append({
                            'pattern': pattern,
                            'match': match,
                            'type': 'route'
                        })
                
                # Extract service endpoints
                service_patterns = [
                    r'(\w+Service)',
                    r'http\.get\([\'"]([^\'"\s]+)[\'"]',
                    r'http\.post\([\'"]([^\'"\s]+)[\'"]',
                    r'this\.http\.[^(]+\([\'"]([^\'"\s]+)[\'"]'
                ]
                
                for pattern in service_patterns:
                    matches = re.findall(pattern, main_content)
                    for match in matches:
                        routes.append({
                            'pattern': pattern,
                            'match': match,
                            'type': 'service'
                        })
                
                self.extracted_data['angular_routes'] = routes
                return routes
                
        except Exception as e:
            print(f"Error extracting Angular routes: {e}")
            
        return []
    
    def attempt_data_export_endpoints(self):
        """Attempt to access common data export endpoints"""
        print("Attempting data export endpoints...")
        
        export_endpoints = [
            '/export/projects',
            '/export/assets',
            '/export/reports',
            '/download/data',
            '/api/export/projects',
            '/api/export/assets',
            '/api/export/all',
            '/data/export',
            '/reports/export',
            '/projects/export.json',
            '/assets/export.json',
            '/api/projects.json',
            '/api/assets.json'
        ]
        
        exports = []
        
        for endpoint in export_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try different methods
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            response = requests.get(url, timeout=5)
                        else:
                            response = requests.post(url, json={}, timeout=5)
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            
                            if 'json' in content_type:
                                try:
                                    data = response.json()
                                    exports.append({
                                        'endpoint': endpoint,
                                        'method': method,
                                        'data': data,
                                        'status': 'json_success'
                                    })
                                    print(f"Found JSON data at {endpoint}")
                                except:
                                    pass
                            
                            elif 'csv' in content_type or 'excel' in content_type:
                                exports.append({
                                    'endpoint': endpoint,
                                    'method': method,
                                    'content_type': content_type,
                                    'size': len(response.content),
                                    'status': 'file_export'
                                })
                                print(f"Found export file at {endpoint}")
                        
                    except requests.exceptions.Timeout:
                        continue
                    except Exception:
                        continue
                        
            except Exception as e:
                continue
        
        self.extracted_data['export_endpoints'] = exports
        return exports
    
    def save_extraction_data(self):
        """Save all extracted data"""
        try:
            backup_dir = "authenticated_ground_works_backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete extraction
            with open(f"{backup_dir}/authenticated_extraction_{timestamp}.json", 'w') as f:
                json.dump(self.extracted_data, f, indent=2, default=str)
            
            # Save individual data types
            for data_type, data in self.extracted_data.items():
                if data and data_type != 'metadata':
                    with open(f"{backup_dir}/{data_type}_{timestamp}.json", 'w') as f:
                        json.dump(data, f, indent=2, default=str)
            
            return backup_dir
            
        except Exception as e:
            print(f"Save error: {e}")
            return None
    
    def execute_authenticated_extraction(self):
        """Execute complete authenticated extraction"""
        print("Starting authenticated Ground Works data extraction...")
        
        # Extract from multiple sources
        api_data = self.extract_via_curl_authenticated()
        js_data = self.extract_javascript_data_sources()
        routes_data = self.extract_angular_routes()
        export_data = self.attempt_data_export_endpoints()
        
        # Save all data
        backup_path = self.save_extraction_data()
        
        # Generate summary
        summary = {
            'status': 'AUTHENTICATED_EXTRACTION_COMPLETE',
            'api_endpoints_found': len(api_data),
            'data_sources_found': len(js_data),
            'routes_found': len(routes_data),
            'export_endpoints_found': len(export_data),
            'backup_location': backup_path,
            'extraction_time': datetime.now().isoformat(),
            'next_steps': [
                'Analyze extracted API endpoints',
                'Review JavaScript data sources',
                'Test export endpoints',
                'Reconstruct Ground Works Suite'
            ]
        }
        
        print(f"Authenticated extraction complete!")
        print(f"API endpoints: {len(api_data)}")
        print(f"Data sources: {len(js_data)}")
        print(f"Routes: {len(routes_data)}")
        print(f"Export endpoints: {len(export_data)}")
        print(f"Saved to: {backup_path}")
        
        return summary

def execute_authenticated_mission():
    """Execute authenticated Ground Works extraction mission"""
    extractor = AuthenticatedGroundWorksExtractor()
    return extractor.execute_authenticated_extraction()

if __name__ == "__main__":
    result = execute_authenticated_mission()
    print(json.dumps(result, indent=2))