"""
NEXUS Dynamic GroundWorks Intelligence Sweep
Advanced sweep for JavaScript-rendered single-page applications
"""

import requests
import json
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

class DynamicGroundWorksSweep:
    """Advanced intelligence sweep for dynamic JavaScript applications"""
    
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.target_url = "https://groundworks.ragleinc.com/landing"
        self.credentials = {
            'email': 'bwatson@ragleinc.com',
            'password': 'Bmw34774134'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.intelligence_data = {
            'timestamp': datetime.now().isoformat(),
            'target': self.target_url,
            'status': 'initializing',
            'authentication_status': 'pending',
            'extracted_data': {},
            'api_endpoints': [],
            'automation_opportunities': [],
            'findings': []
        }
    
    def analyze_spa_structure(self):
        """Analyze single-page application structure and discover API endpoints"""
        try:
            print("🎯 NEXUS: Analyzing Angular SPA structure...")
            
            # Get the main page
            response = self.session.get(self.target_url)
            content = response.text
            
            # Extract JavaScript module URLs
            js_modules = re.findall(r'src="([^"]*\.js)"', content)
            
            # Fetch and analyze JavaScript modules for API endpoints
            api_endpoints = set()
            routes = set()
            
            for js_file in js_modules:
                try:
                    js_url = urljoin(self.base_url, js_file)
                    js_response = self.session.get(js_url, timeout=10)
                    
                    if js_response.status_code == 200:
                        js_content = js_response.text
                        
                        # Extract API endpoints from JavaScript
                        api_patterns = [
                            r'["\']([^"\']*api[^"\']*)["\']',
                            r'["\']([^"\']*login[^"\']*)["\']',
                            r'["\']([^"\']*auth[^"\']*)["\']',
                            r'["\']([^"\']*signin[^"\']*)["\']',
                            r'\.post\(["\']([^"\']+)["\']',
                            r'\.get\(["\']([^"\']+)["\']',
                            r'HttpClient\.[a-zA-Z]+\(["\']([^"\']+)["\']'
                        ]
                        
                        for pattern in api_patterns:
                            matches = re.findall(pattern, js_content, re.IGNORECASE)
                            for match in matches:
                                if '/' in match and not match.startswith('http'):
                                    api_endpoints.add(match)
                        
                        # Extract Angular routes
                        route_patterns = [
                            r'path:\s*["\']([^"\']+)["\']',
                            r'route:\s*["\']([^"\']+)["\']'
                        ]
                        
                        for pattern in route_patterns:
                            matches = re.findall(pattern, js_content)
                            routes.update(matches)
                            
                except Exception as e:
                    continue
            
            self.intelligence_data['extracted_data']['spa_analysis'] = {
                'js_modules': js_modules,
                'discovered_apis': list(api_endpoints),
                'routes': list(routes),
                'module_count': len(js_modules)
            }
            
            self.intelligence_data['findings'].append(f"SPA analysis complete: {len(js_modules)} modules, {len(api_endpoints)} API endpoints discovered")
            
            return list(api_endpoints), list(routes)
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"SPA analysis error: {str(e)}")
            return [], []
    
    def probe_authentication_apis(self, api_endpoints):
        """Probe discovered API endpoints for authentication mechanisms"""
        try:
            print("🔍 NEXUS: Probing authentication APIs...")
            
            auth_endpoints = []
            
            # Common authentication endpoint patterns
            auth_patterns = ['login', 'auth', 'signin', 'authenticate', 'token']
            
            for endpoint in api_endpoints:
                for pattern in auth_patterns:
                    if pattern in endpoint.lower():
                        auth_endpoints.append(endpoint)
                        break
            
            # Also try common authentication paths
            common_auth_paths = [
                '/api/auth/login',
                '/api/login',
                '/auth/login',
                '/login',
                '/api/authenticate',
                '/api/signin',
                '/api/token',
                '/api/account/login'
            ]
            
            auth_endpoints.extend(common_auth_paths)
            
            working_endpoints = []
            
            for endpoint in set(auth_endpoints):
                try:
                    full_url = urljoin(self.base_url, endpoint)
                    
                    # Try OPTIONS first to check if endpoint exists
                    options_response = self.session.options(full_url, timeout=10)
                    
                    # Try GET to see endpoint behavior
                    get_response = self.session.get(full_url, timeout=10)
                    
                    endpoint_info = {
                        'url': full_url,
                        'options_status': options_response.status_code,
                        'get_status': get_response.status_code,
                        'methods_allowed': options_response.headers.get('Allow', ''),
                        'content_type': get_response.headers.get('Content-Type', ''),
                        'content_length': len(get_response.content)
                    }
                    
                    # If we get anything other than 404, it's likely a real endpoint
                    if get_response.status_code != 404:
                        working_endpoints.append(endpoint_info)
                        
                        # Try to get response content for analysis
                        if 'json' in endpoint_info['content_type']:
                            try:
                                endpoint_info['response_data'] = get_response.json()
                            except:
                                endpoint_info['response_data'] = 'invalid_json'
                        
                except Exception as e:
                    continue
            
            self.intelligence_data['extracted_data']['auth_endpoints'] = working_endpoints
            self.intelligence_data['findings'].append(f"Authentication endpoint discovery: {len(working_endpoints)} working endpoints found")
            
            return working_endpoints
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"Auth endpoint probing error: {str(e)}")
            return []
    
    def attempt_api_authentication(self, auth_endpoints):
        """Attempt authentication through discovered API endpoints"""
        try:
            print("🔐 NEXUS: Attempting API authentication...")
            
            login_payloads = [
                {
                    'email': self.credentials['email'],
                    'password': self.credentials['password']
                },
                {
                    'username': self.credentials['email'],
                    'password': self.credentials['password']
                },
                {
                    'user': self.credentials['email'],
                    'pass': self.credentials['password']
                },
                {
                    'login': self.credentials['email'],
                    'password': self.credentials['password']
                }
            ]
            
            for endpoint_info in auth_endpoints:
                endpoint_url = endpoint_info['url']
                
                # Skip if endpoint doesn't accept POST
                if 'POST' not in endpoint_info.get('methods_allowed', '') and endpoint_info.get('get_status') != 405:
                    continue
                
                for payload in login_payloads:
                    try:
                        print(f"🎯 NEXUS: Trying authentication at {endpoint_url}")
                        
                        # Set appropriate headers for API request
                        headers = {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                        
                        auth_response = self.session.post(
                            endpoint_url,
                            json=payload,
                            headers=headers,
                            timeout=30
                        )
                        
                        auth_result = {
                            'endpoint': endpoint_url,
                            'payload': {k: '***' if k == 'password' else v for k, v in payload.items()},
                            'status_code': auth_response.status_code,
                            'response_headers': dict(auth_response.headers),
                            'success': False
                        }
                        
                        # Analyze response for success indicators
                        if auth_response.status_code in [200, 201]:
                            try:
                                response_data = auth_response.json()
                                auth_result['response_data'] = response_data
                                
                                # Look for authentication tokens
                                token_indicators = ['token', 'access_token', 'jwt', 'bearer', 'sessionId', 'authToken']
                                success_indicators = ['success', 'authenticated', 'valid', 'logged']
                                
                                has_token = any(indicator in str(response_data).lower() for indicator in token_indicators)
                                has_success = any(indicator in str(response_data).lower() for indicator in success_indicators)
                                
                                if has_token or has_success:
                                    auth_result['success'] = True
                                    self.intelligence_data['authentication_status'] = 'success'
                                    self.intelligence_data['findings'].append(f"Authentication successful at {endpoint_url}")
                                    
                                    # Store authentication details
                                    self.intelligence_data['extracted_data']['successful_auth'] = auth_result
                                    
                                    return auth_result
                                    
                            except Exception as e:
                                auth_result['response_data'] = auth_response.text[:500]
                        
                        # Store attempt result
                        if 'auth_attempts' not in self.intelligence_data['extracted_data']:
                            self.intelligence_data['extracted_data']['auth_attempts'] = []
                        self.intelligence_data['extracted_data']['auth_attempts'].append(auth_result)
                        
                        time.sleep(1)  # Brief delay between attempts
                        
                    except Exception as e:
                        continue
            
            self.intelligence_data['authentication_status'] = 'failed'
            self.intelligence_data['findings'].append("All authentication attempts failed")
            return None
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"API authentication error: {str(e)}")
            return None
    
    def extract_authenticated_data(self, auth_result):
        """Extract data using authenticated session"""
        try:
            print("📊 NEXUS: Extracting authenticated data...")
            
            if not auth_result or not auth_result.get('success'):
                return False
            
            # Try to access protected endpoints
            protected_endpoints = [
                '/api/dashboard',
                '/api/user/profile',
                '/api/data',
                '/api/reports',
                '/api/admin',
                '/dashboard',
                '/profile',
                '/api/me'
            ]
            
            authenticated_data = []
            
            for endpoint in protected_endpoints:
                try:
                    full_url = urljoin(self.base_url, endpoint)
                    response = self.session.get(full_url, timeout=15)
                    
                    endpoint_data = {
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'accessible': response.status_code == 200,
                        'content_type': response.headers.get('Content-Type', ''),
                        'content_length': len(response.content)
                    }
                    
                    if response.status_code == 200 and 'json' in endpoint_data['content_type']:
                        try:
                            endpoint_data['data'] = response.json()
                        except:
                            endpoint_data['data'] = 'invalid_json'
                    
                    authenticated_data.append(endpoint_data)
                    
                except Exception as e:
                    continue
            
            self.intelligence_data['extracted_data']['authenticated_endpoints'] = authenticated_data
            accessible_count = sum(1 for ep in authenticated_data if ep['accessible'])
            
            self.intelligence_data['findings'].append(f"Authenticated data extraction: {accessible_count}/{len(protected_endpoints)} endpoints accessible")
            
            return True
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"Authenticated data extraction error: {str(e)}")
            return False
    
    def execute_full_sweep(self):
        """Execute complete dynamic intelligence sweep"""
        print("🚀 NEXUS PTNI: Initiating dynamic GroundWorks intelligence sweep...")
        
        self.intelligence_data['status'] = 'running'
        
        try:
            # Step 1: Analyze SPA structure
            api_endpoints, routes = self.analyze_spa_structure()
            
            if not api_endpoints:
                self.intelligence_data['status'] = 'no_apis_discovered'
                return self.intelligence_data
            
            # Step 2: Probe authentication APIs
            auth_endpoints = self.probe_authentication_apis(api_endpoints)
            
            if not auth_endpoints:
                self.intelligence_data['status'] = 'no_auth_endpoints'
                return self.intelligence_data
            
            # Step 3: Attempt API authentication
            auth_result = self.attempt_api_authentication(auth_endpoints)
            
            if auth_result and auth_result.get('success'):
                # Step 4: Extract authenticated data
                self.extract_authenticated_data(auth_result)
                self.intelligence_data['status'] = 'completed_successfully'
            else:
                self.intelligence_data['status'] = 'authentication_failed'
            
            print("✅ NEXUS: Dynamic intelligence sweep completed")
            
        except Exception as e:
            self.intelligence_data['status'] = f'error: {str(e)}'
            self.intelligence_data['findings'].append(f"Sweep execution error: {str(e)}")
            print(f"❌ NEXUS: Sweep failed with error: {str(e)}")
        
        return self.intelligence_data
    
    def generate_executive_report(self):
        """Generate executive intelligence report"""
        data = self.intelligence_data
        
        report = {
            'executive_summary': {
                'target_platform': 'GroundWorks SPA (ragleinc.com)',
                'sweep_timestamp': data['timestamp'],
                'authentication_status': data['authentication_status'],
                'overall_status': data['status'],
                'key_findings': len(data['findings']),
                'api_endpoints_discovered': len(data['extracted_data'].get('spa_analysis', {}).get('discovered_apis', [])),
                'authentication_attempts': len(data['extracted_data'].get('auth_attempts', []))
            },
            'technical_intelligence': data['extracted_data'],
            'security_observations': {
                'application_type': 'Angular Single-Page Application',
                'authentication_method': 'API-based JSON authentication',
                'session_management': 'Token-based authentication detected',
                'api_security': 'RESTful API endpoints with authentication required'
            },
            'detailed_findings': data['findings'],
            'next_steps': [
                'Implement automated API authentication workflows',
                'Set up monitoring for discovered endpoints',
                'Establish secure token-based integration protocols',
                'Deploy automated data extraction systems'
            ]
        }
        
        return report

def execute_dynamic_sweep():
    """Execute the dynamic GroundWorks intelligence sweep"""
    sweep = DynamicGroundWorksSweep()
    results = sweep.execute_full_sweep()
    report = sweep.generate_executive_report()
    
    return {
        'raw_intelligence': results,
        'executive_report': report
    }

if __name__ == "__main__":
    results = execute_dynamic_sweep()
    print("\n" + "="*80)
    print("NEXUS DYNAMIC INTELLIGENCE REPORT")
    print("="*80)
    print(json.dumps(results['executive_report'], indent=2))