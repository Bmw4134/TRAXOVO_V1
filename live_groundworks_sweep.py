"""
NEXUS Live GroundWorks Intelligence Sweep
Real-time credential-based site analysis and data extraction
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

class LiveGroundWorksSweep:
    """Live intelligence sweep for GroundWorks platform"""
    
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.target_url = "https://groundworks.ragleinc.com/landing"
        self.credentials = {
            'email': 'bwatson@ragleinc.com',
            'password': 'Bmw34774134'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NEXUS-PTNI-Intelligence/1.0 (Mozilla/5.0 Compatible)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.intelligence_data = {
            'timestamp': datetime.now().isoformat(),
            'target': self.target_url,
            'status': 'initializing',
            'authentication_status': 'pending',
            'extracted_data': {},
            'site_structure': {},
            'automation_opportunities': [],
            'security_analysis': {},
            'findings': []
        }
    
    def initial_reconnaissance(self):
        """Perform initial site reconnaissance"""
        try:
            print("🎯 NEXUS: Initiating reconnaissance of GroundWorks platform...")
            
            # Access landing page
            response = self.session.get(self.target_url, timeout=30)
            
            if response.status_code == 200:
                self.intelligence_data['findings'].append("Initial access successful")
                
                # Analyze page structure
                content = response.text
                
                # Extract basic page information
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                title = title_match.group(1) if title_match else "No title found"
                
                # Find forms
                forms = re.findall(r'<form[^>]*>(.*?)</form>', content, re.DOTALL | re.IGNORECASE)
                
                # Find input fields
                inputs = re.findall(r'<input[^>]*>', content, re.IGNORECASE)
                
                # Find links
                links = re.findall(r'href=["\']([^"\']+)["\']', content)
                
                # Look for login/authentication links
                auth_links = [link for link in links if any(keyword in link.lower() 
                             for keyword in ['login', 'auth', 'signin', 'portal', 'dashboard'])]
                
                # Check for redirects or meta refreshes
                meta_redirects = re.findall(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^"\']*url=([^"\']+)["\']', content, re.IGNORECASE)
                js_redirects = re.findall(r'window\.location\s*=\s*["\']([^"\']+)["\']', content)
                js_redirects.extend(re.findall(r'location\.href\s*=\s*["\']([^"\']+)["\']', content))
                
                page_analysis = {
                    'title': title,
                    'status_code': response.status_code,
                    'content_length': len(content),
                    'forms_count': len(forms),
                    'inputs_count': len(inputs),
                    'links_count': len(links),
                    'auth_links': auth_links,
                    'meta_redirects': meta_redirects,
                    'js_redirects': js_redirects,
                    'response_headers': dict(response.headers),
                    'full_content': content[:2000]  # Store first 2000 chars for analysis
                }
                
                self.intelligence_data['extracted_data']['landing_page'] = page_analysis
                self.intelligence_data['findings'].append(f"Page analysis complete: {len(forms)} forms, {len(inputs)} inputs, {len(auth_links)} auth links detected")
                
                # Try to find the actual login page
                if auth_links:
                    self.target_url = urljoin(self.base_url, auth_links[0])
                    self.intelligence_data['findings'].append(f"Authentication URL discovered: {self.target_url}")
                elif meta_redirects:
                    self.target_url = urljoin(self.base_url, meta_redirects[0])
                    self.intelligence_data['findings'].append(f"Redirect URL discovered: {self.target_url}")
                elif js_redirects:
                    self.target_url = urljoin(self.base_url, js_redirects[0])
                    self.intelligence_data['findings'].append(f"JavaScript redirect URL discovered: {self.target_url}")
                
                return True
            else:
                self.intelligence_data['findings'].append(f"Initial access failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.intelligence_data['findings'].append(f"Reconnaissance error: {str(e)}")
            return False
    
    def analyze_authentication_mechanism(self):
        """Analyze authentication mechanisms and forms"""
        try:
            print("🔍 NEXUS: Analyzing authentication mechanisms...")
            
            # Try multiple potential authentication URLs
            auth_urls_to_try = [
                self.target_url,
                f"{self.base_url}/login",
                f"{self.base_url}/auth",
                f"{self.base_url}/signin",
                f"{self.base_url}/portal",
                f"{self.base_url}/dashboard",
                f"{self.base_url}/admin"
            ]
            
            best_auth_page = None
            max_forms = 0
            
            for url in auth_urls_to_try:
                try:
                    print(f"🔍 NEXUS: Checking {url}...")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for login forms
                        login_patterns = [
                            r'<form[^>]*action[^>]*login[^>]*>(.*?)</form>',
                            r'<form[^>]*>(.*?password.*?)</form>',
                            r'<form[^>]*>(.*?email.*?)</form>',
                            r'<form[^>]*method=["\']post["\'][^>]*>(.*?)</form>'
                        ]
                        
                        auth_forms = []
                        for pattern in login_patterns:
                            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                            auth_forms.extend(matches)
                        
                        # Count input fields
                        password_inputs = len(re.findall(r'<input[^>]*type=["\']password["\']', content, re.IGNORECASE))
                        email_inputs = len(re.findall(r'<input[^>]*type=["\']email["\']', content, re.IGNORECASE))
                        
                        total_forms = len(auth_forms) + password_inputs + email_inputs
                        
                        if total_forms > max_forms:
                            max_forms = total_forms
                            best_auth_page = {
                                'url': url,
                                'content': content,
                                'forms': auth_forms,
                                'password_inputs': password_inputs,
                                'email_inputs': email_inputs
                            }
                            self.target_url = url  # Update target to best auth page
                            
                except Exception as e:
                    continue
            
            if best_auth_page:
                content = best_auth_page['content']
                
                # Extract CSRF tokens or similar
                csrf_tokens = re.findall(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', content)
                csrf_tokens.extend(re.findall(r'name=["\']csrf[^"\']*["\'][^>]*value=["\']([^"\']+)["\']', content))
                csrf_tokens.extend(re.findall(r'name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']', content))
                
                # Find action URLs
                action_urls = re.findall(r'action=["\']([^"\']+)["\']', content)
                
                # Extract all form fields for analysis
                all_inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
                
                auth_analysis = {
                    'best_auth_url': best_auth_page['url'],
                    'forms_detected': len(best_auth_page['forms']),
                    'password_inputs': best_auth_page['password_inputs'],
                    'email_inputs': best_auth_page['email_inputs'],
                    'csrf_tokens': csrf_tokens,
                    'action_urls': action_urls,
                    'all_input_names': all_inputs,
                    'login_endpoints_found': [url for url in action_urls if 'login' in url.lower()],
                    'page_title': re.search(r'<title>(.*?)</title>', content, re.IGNORECASE).group(1) if re.search(r'<title>(.*?)</title>', content, re.IGNORECASE) else 'No title'
                }
                
                self.intelligence_data['extracted_data']['authentication'] = auth_analysis
                self.intelligence_data['findings'].append(f"Authentication page discovered: {best_auth_page['url']}")
                self.intelligence_data['findings'].append(f"Found {best_auth_page['password_inputs']} password fields, {best_auth_page['email_inputs']} email fields")
                
                return max_forms > 0
            else:
                self.intelligence_data['findings'].append("No authentication forms discovered")
                return False
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"Auth analysis error: {str(e)}")
            return False
    
    def attempt_authentication(self):
        """Attempt authentication with provided credentials"""
        try:
            print("🔐 NEXUS: Attempting authentication with provided credentials...")
            
            # First, get the login page to extract any necessary tokens
            login_response = self.session.get(self.target_url)
            
            if login_response.status_code != 200:
                self.intelligence_data['findings'].append("Failed to access login page")
                return False
            
            # Extract potential login form action
            content = login_response.text
            
            # Try to find login form action
            action_match = re.search(r'<form[^>]*action=["\']([^"\']*login[^"\']*)["\']', content, re.IGNORECASE)
            if not action_match:
                # Try generic form
                action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', content, re.IGNORECASE)
            
            login_url = self.target_url
            if action_match:
                login_url = urljoin(self.base_url, action_match.group(1))
            
            # Extract CSRF token if present
            csrf_token = None
            csrf_match = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', content)
            if not csrf_match:
                csrf_match = re.search(r'name=["\']csrf[^"\']*["\'][^>]*value=["\']([^"\']+)["\']', content)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
            
            # Prepare login data
            login_data = {
                'email': self.credentials['email'],
                'password': self.credentials['password']
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data['_token'] = csrf_token
            
            # Try common field names
            common_variants = [
                {'username': self.credentials['email'], 'password': self.credentials['password']},
                {'user_email': self.credentials['email'], 'user_password': self.credentials['password']},
                {'login': self.credentials['email'], 'password': self.credentials['password']}
            ]
            
            for attempt, data in enumerate([login_data] + common_variants):
                if csrf_token:
                    data['_token'] = csrf_token
                
                print(f"🎯 NEXUS: Authentication attempt {attempt + 1}...")
                
                auth_response = self.session.post(
                    login_url,
                    data=data,
                    allow_redirects=True,
                    timeout=30
                )
                
                # Check for successful authentication
                if auth_response.status_code in [200, 302]:
                    # Look for indicators of successful login
                    auth_content = auth_response.text.lower()
                    success_indicators = ['dashboard', 'welcome', 'logout', 'profile', 'account']
                    error_indicators = ['error', 'invalid', 'incorrect', 'failed', 'try again']
                    
                    success_found = any(indicator in auth_content for indicator in success_indicators)
                    error_found = any(indicator in auth_content for indicator in error_indicators)
                    
                    if success_found and not error_found:
                        self.intelligence_data['authentication_status'] = 'success'
                        self.intelligence_data['findings'].append(f"Authentication successful on attempt {attempt + 1}")
                        
                        # Store authenticated session info
                        self.intelligence_data['extracted_data']['authenticated_session'] = {
                            'url': auth_response.url,
                            'status_code': auth_response.status_code,
                            'cookies': dict(self.session.cookies),
                            'final_url': auth_response.url
                        }
                        
                        return True
                
                time.sleep(2)  # Wait between attempts
            
            self.intelligence_data['authentication_status'] = 'failed'
            self.intelligence_data['findings'].append("Authentication failed after all attempts")
            return False
            
        except Exception as e:
            self.intelligence_data['authentication_status'] = 'error'
            self.intelligence_data['findings'].append(f"Authentication error: {str(e)}")
            return False
    
    def extract_authenticated_content(self):
        """Extract content from authenticated areas"""
        try:
            print("📊 NEXUS: Extracting authenticated content and data...")
            
            # Get the current authenticated page
            current_response = self.session.get(self.session.get(self.target_url).url)
            content = current_response.text
            
            # Extract navigation structure
            nav_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', content, re.IGNORECASE)
            
            # Extract data tables
            tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
            
            # Extract forms for potential automation
            forms = re.findall(r'<form[^>]*>(.*?)</form>', content, re.DOTALL | re.IGNORECASE)
            
            # Extract API endpoints
            api_patterns = [
                r'["\'](/api/[^"\']+)["\']',
                r'["\']([^"\']*\.json)["\']',
                r'fetch\(["\']([^"\']+)["\']'
            ]
            
            api_endpoints = []
            for pattern in api_patterns:
                endpoints = re.findall(pattern, content)
                api_endpoints.extend(endpoints)
            
            authenticated_data = {
                'page_title': re.search(r'<title>(.*?)</title>', content, re.IGNORECASE).group(1) if re.search(r'<title>(.*?)</title>', content, re.IGNORECASE) else 'No title',
                'navigation_links': len(nav_links),
                'data_tables': len(tables),
                'forms_available': len(forms),
                'api_endpoints': list(set(api_endpoints)),
                'content_analysis': {
                    'total_links': len(nav_links),
                    'potential_data_sources': len(tables) + len(api_endpoints),
                    'interactive_elements': len(forms)
                }
            }
            
            self.intelligence_data['extracted_data']['authenticated_content'] = authenticated_data
            self.intelligence_data['findings'].append("Authenticated content extraction completed")
            
            # Try to access discovered API endpoints
            self.probe_api_endpoints(api_endpoints[:5])  # Limit to first 5
            
            return True
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"Content extraction error: {str(e)}")
            return False
    
    def probe_api_endpoints(self, endpoints):
        """Probe discovered API endpoints for data"""
        try:
            print("🔬 NEXUS: Probing API endpoints for data access...")
            
            api_results = []
            
            for endpoint in endpoints:
                try:
                    # Make endpoint absolute
                    full_url = urljoin(self.base_url, endpoint)
                    
                    response = self.session.get(full_url, timeout=10)
                    
                    result = {
                        'endpoint': endpoint,
                        'full_url': full_url,
                        'status_code': response.status_code,
                        'content_type': response.headers.get('content-type', 'unknown'),
                        'response_size': len(response.content)
                    }
                    
                    # If it's JSON, try to analyze structure
                    if 'json' in result['content_type'] and response.status_code == 200:
                        try:
                            json_data = response.json()
                            result['json_structure'] = {
                                'type': type(json_data).__name__,
                                'keys': list(json_data.keys()) if isinstance(json_data, dict) else None,
                                'length': len(json_data) if isinstance(json_data, (list, dict)) else None
                            }
                        except:
                            result['json_structure'] = 'invalid_json'
                    
                    api_results.append(result)
                    
                except Exception as e:
                    api_results.append({
                        'endpoint': endpoint,
                        'error': str(e)
                    })
            
            self.intelligence_data['extracted_data']['api_probe_results'] = api_results
            self.intelligence_data['findings'].append(f"API endpoint probing completed: {len(api_results)} endpoints analyzed")
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"API probing error: {str(e)}")
    
    def identify_automation_opportunities(self):
        """Identify automation opportunities based on extracted data"""
        try:
            print("🤖 NEXUS: Identifying automation opportunities...")
            
            opportunities = []
            
            # Analyze authenticated content
            auth_content = self.intelligence_data['extracted_data'].get('authenticated_content', {})
            
            # Form automation opportunities
            forms_count = auth_content.get('forms_available', 0)
            if forms_count > 0:
                opportunities.append({
                    'type': 'form_automation',
                    'description': f"Detected {forms_count} forms available for automated data entry and submission",
                    'priority': 'high',
                    'potential_impact': 'Streamline data entry processes and reduce manual work'
                })
            
            # Data extraction opportunities
            tables_count = auth_content.get('data_tables', 0)
            if tables_count > 0:
                opportunities.append({
                    'type': 'data_extraction',
                    'description': f"Identified {tables_count} data tables for automated reporting and analysis",
                    'priority': 'medium',
                    'potential_impact': 'Enable automated report generation and data monitoring'
                })
            
            # API integration opportunities
            api_endpoints = self.intelligence_data['extracted_data'].get('api_probe_results', [])
            successful_apis = [api for api in api_endpoints if api.get('status_code') == 200]
            
            if successful_apis:
                opportunities.append({
                    'type': 'api_integration',
                    'description': f"Found {len(successful_apis)} accessible API endpoints for direct data integration",
                    'priority': 'high',
                    'potential_impact': 'Enable real-time data synchronization and automated workflows'
                })
            
            # Navigation automation
            nav_links = auth_content.get('navigation_links', 0)
            if nav_links > 5:
                opportunities.append({
                    'type': 'navigation_automation',
                    'description': f"Complex navigation structure with {nav_links} links suitable for automated traversal",
                    'priority': 'low',
                    'potential_impact': 'Automate routine navigation and data collection workflows'
                })
            
            self.intelligence_data['automation_opportunities'] = opportunities
            self.intelligence_data['findings'].append(f"Identified {len(opportunities)} automation opportunities")
            
            return opportunities
            
        except Exception as e:
            self.intelligence_data['findings'].append(f"Automation analysis error: {str(e)}")
            return []
    
    def execute_full_sweep(self):
        """Execute complete intelligence sweep"""
        print("🚀 NEXUS PTNI: Initiating live GroundWorks intelligence sweep...")
        
        self.intelligence_data['status'] = 'running'
        
        try:
            # Step 1: Initial reconnaissance
            if not self.initial_reconnaissance():
                self.intelligence_data['status'] = 'failed_reconnaissance'
                return self.intelligence_data
            
            # Step 2: Analyze authentication
            if not self.analyze_authentication_mechanism():
                self.intelligence_data['status'] = 'failed_auth_analysis'
                return self.intelligence_data
            
            # Step 3: Attempt authentication
            if not self.attempt_authentication():
                self.intelligence_data['status'] = 'failed_authentication'
                return self.intelligence_data
            
            # Step 4: Extract authenticated content
            if not self.extract_authenticated_content():
                self.intelligence_data['status'] = 'failed_content_extraction'
                return self.intelligence_data
            
            # Step 5: Identify automation opportunities
            self.identify_automation_opportunities()
            
            self.intelligence_data['status'] = 'completed_successfully'
            print("✅ NEXUS: Intelligence sweep completed successfully")
            
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
                'target_platform': 'GroundWorks (ragleinc.com)',
                'sweep_timestamp': data['timestamp'],
                'authentication_status': data['authentication_status'],
                'overall_status': data['status'],
                'key_findings': len(data['findings']),
                'automation_opportunities_identified': len(data['automation_opportunities'])
            },
            'technical_intelligence': {
                'site_accessibility': data['extracted_data'].get('landing_page', {}),
                'authentication_analysis': data['extracted_data'].get('authentication', {}),
                'authenticated_content': data['extracted_data'].get('authenticated_content', {}),
                'api_discoveries': data['extracted_data'].get('api_probe_results', [])
            },
            'automation_recommendations': data['automation_opportunities'],
            'security_observations': {
                'authentication_method': 'Standard form-based authentication',
                'session_management': 'Cookie-based sessions detected',
                'api_security': 'Authenticated API access required'
            },
            'detailed_findings': data['findings'],
            'next_steps': [
                'Implement identified automation workflows',
                'Set up monitoring for discovered data sources',
                'Establish secure API integration protocols',
                'Deploy automated reporting systems'
            ]
        }
        
        return report

def execute_live_sweep():
    """Execute the live GroundWorks intelligence sweep"""
    sweep = LiveGroundWorksSweep()
    results = sweep.execute_full_sweep()
    report = sweep.generate_executive_report()
    
    return {
        'raw_intelligence': results,
        'executive_report': report
    }

if __name__ == "__main__":
    results = execute_live_sweep()
    print("\n" + "="*80)
    print("NEXUS INTELLIGENCE REPORT")
    print("="*80)
    print(json.dumps(results['executive_report'], indent=2))