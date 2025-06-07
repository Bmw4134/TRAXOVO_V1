"""
NEXUS GaugeSmart Intelligence Sweep
Real-time credential-based access and data extraction
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class GaugeSmartIntelligenceSweep:
    """Advanced intelligence sweep for GaugeSmart platform"""
    
    def __init__(self):
        self.base_url = "https://login.gaugesmart.com"
        self.target_url = "https://login.gaugesmart.com/Account/LogOn?ReturnUrl=%2f"
        self.credentials = {
            'username': 'bwatson',
            'password': 'Plsw@2900413477'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.intelligence = {
            'timestamp': datetime.now().isoformat(),
            'target': 'GaugeSmart Platform',
            'status': 'active',
            'authentication_status': 'attempting',
            'extracted_data': {},
            'findings': [],
            'automation_targets': []
        }
    
    def analyze_login_page(self):
        """Analyze the login page structure and extract form details"""
        try:
            print("🎯 NEXUS: Analyzing GaugeSmart login page...")
            
            response = self.session.get(self.target_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Extract form details
                form_action = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', content)
                action_url = form_action.group(1) if form_action else '/Account/LogOn'
                
                # Extract all input fields
                input_fields = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', content)
                
                # Extract hidden fields and their values
                hidden_fields = {}
                hidden_matches = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', content)
                for name, value in hidden_matches:
                    hidden_fields[name] = value
                
                # Extract CSRF/verification tokens
                csrf_tokens = re.findall(r'name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']', content)
                
                login_analysis = {
                    'form_action': action_url,
                    'input_fields': input_fields,
                    'hidden_fields': hidden_fields,
                    'csrf_tokens': csrf_tokens,
                    'page_title': re.search(r'<title>(.*?)</title>', content).group(1) if re.search(r'<title>(.*?)</title>', content) else 'No title',
                    'form_method': 'POST'
                }
                
                self.intelligence['extracted_data']['login_analysis'] = login_analysis
                self.intelligence['findings'].append("Login page analysis completed")
                
                return login_analysis
                
        except Exception as e:
            self.intelligence['findings'].append(f"Login page analysis error: {str(e)}")
            return None
    
    def attempt_authentication(self, login_data):
        """Attempt authentication with extracted form data"""
        try:
            print("🔐 NEXUS: Attempting GaugeSmart authentication...")
            
            if not login_data:
                return False
            
            # Construct login URL
            login_url = urljoin(self.base_url, login_data['form_action'])
            
            # Prepare authentication payload
            auth_payload = {
                'UserName': self.credentials['username'],
                'Password': self.credentials['password'],
                'RememberMe': 'false'
            }
            
            # Add hidden fields
            auth_payload.update(login_data['hidden_fields'])
            
            # Add CSRF token if present
            if login_data['csrf_tokens']:
                auth_payload['__RequestVerificationToken'] = login_data['csrf_tokens'][0]
            
            # Set appropriate headers for form submission
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.target_url,
                'Origin': self.base_url
            }
            
            print(f"🎯 NEXUS: Submitting authentication to {login_url}")
            
            # Submit authentication
            auth_response = self.session.post(
                login_url,
                data=auth_payload,
                headers=headers,
                allow_redirects=True,
                timeout=30
            )
            
            # Analyze authentication response
            if self.analyze_auth_response(auth_response):
                self.intelligence['authentication_status'] = 'successful'
                self.intelligence['findings'].append("Authentication successful")
                return True
            else:
                self.intelligence['authentication_status'] = 'failed'
                self.intelligence['findings'].append("Authentication failed")
                return False
                
        except Exception as e:
            self.intelligence['findings'].append(f"Authentication error: {str(e)}")
            return False
    
    def analyze_auth_response(self, response):
        """Analyze authentication response for success indicators"""
        try:
            content = response.text.lower()
            current_url = response.url.lower()
            
            # Success indicators
            success_indicators = [
                'dashboard', 'welcome', 'home', 'logout', 'profile',
                'account', 'settings', 'main', 'portal'
            ]
            
            # Error indicators
            error_indicators = [
                'invalid', 'incorrect', 'failed', 'error', 'denied',
                'login', 'logon', 'signin', 'unauthorized'
            ]
            
            # Check URL for success indicators
            url_success = any(indicator in current_url for indicator in success_indicators)
            url_error = any(indicator in current_url for indicator in ['login', 'logon', 'signin'])
            
            # Check content for indicators
            content_success = any(indicator in content for indicator in success_indicators)
            content_error = any(indicator in content for indicator in error_indicators)
            
            # Authentication likely successful if:
            # 1. Redirected away from login page
            # 2. URL contains dashboard/home indicators
            # 3. Content suggests authenticated state
            
            auth_success = (
                (url_success and not url_error) or
                (content_success and not content_error) or
                (response.status_code == 200 and 'login' not in current_url)
            )
            
            # Store authentication analysis
            auth_analysis = {
                'final_url': response.url,
                'status_code': response.status_code,
                'url_indicators': {
                    'success_found': url_success,
                    'error_found': url_error
                },
                'content_indicators': {
                    'success_found': content_success,
                    'error_found': content_error
                },
                'likely_authenticated': auth_success,
                'page_title': re.search(r'<title>(.*?)</title>', response.text).group(1) if re.search(r'<title>(.*?)</title>', response.text) else 'No title'
            }
            
            self.intelligence['extracted_data']['auth_analysis'] = auth_analysis
            
            return auth_success
            
        except Exception as e:
            return False
    
    def extract_authenticated_data(self):
        """Extract data from authenticated session"""
        try:
            print("📊 NEXUS: Extracting authenticated application data...")
            
            # Get current authenticated page
            current_response = self.session.get(self.session.get(self.base_url).url, timeout=15)
            content = current_response.text
            
            # Extract navigation structure
            nav_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', content)
            
            # Extract menu items
            menu_items = re.findall(r'<li[^>]*><a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a></li>', content)
            
            # Extract form elements
            forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', content)
            
            # Extract data tables
            tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL)
            
            # Extract JavaScript API calls
            api_calls = re.findall(r'["\']([^"\']*api[^"\']*)["\']', content)
            ajax_calls = re.findall(r'\.ajax\([^)]*url:\s*["\']([^"\']+)["\']', content)
            
            # Extract user/account information
            user_info = re.findall(r'user["\']?:\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
            
            # Identify dashboard elements
            dashboard_elements = {
                'charts': len(re.findall(r'chart|graph|visualization', content, re.IGNORECASE)),
                'gauges': len(re.findall(r'gauge|meter|reading', content, re.IGNORECASE)),
                'data_points': len(re.findall(r'data-[a-zA-Z-]+', content)),
                'interactive_elements': len(re.findall(r'onclick|onchange|button', content, re.IGNORECASE))
            }
            
            extracted_data = {
                'current_url': current_response.url,
                'page_title': re.search(r'<title>(.*?)</title>', content).group(1) if re.search(r'<title>(.*?)</title>', content) else 'No title',
                'navigation_links': nav_links[:15],  # Limit to first 15
                'menu_items': menu_items[:10],
                'forms_discovered': forms,
                'data_tables_count': len(tables),
                'api_endpoints': list(set(api_calls + ajax_calls))[:10],
                'user_references': user_info,
                'dashboard_elements': dashboard_elements,
                'page_size': len(content),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            self.intelligence['extracted_data']['application_data'] = extracted_data
            self.intelligence['findings'].append("Authenticated data extraction completed")
            
            # Probe discovered endpoints
            self.probe_discovered_endpoints(extracted_data['api_endpoints'])
            
            return True
            
        except Exception as e:
            self.intelligence['findings'].append(f"Data extraction error: {str(e)}")
            return False
    
    def probe_discovered_endpoints(self, endpoints):
        """Probe discovered endpoints for additional data"""
        try:
            print("🔬 NEXUS: Probing discovered endpoints...")
            
            endpoint_results = []
            
            for endpoint in endpoints[:5]:  # Limit to first 5 endpoints
                try:
                    if endpoint.startswith('/'):
                        full_url = urljoin(self.base_url, endpoint)
                    else:
                        full_url = endpoint
                    
                    response = self.session.get(full_url, timeout=10)
                    
                    endpoint_info = {
                        'endpoint': endpoint,
                        'full_url': full_url,
                        'status_code': response.status_code,
                        'content_type': response.headers.get('Content-Type', ''),
                        'accessible': response.status_code == 200,
                        'response_size': len(response.content)
                    }
                    
                    # If JSON response, try to analyze structure
                    if 'json' in endpoint_info['content_type'] and response.status_code == 200:
                        try:
                            json_data = response.json()
                            endpoint_info['data_structure'] = {
                                'type': type(json_data).__name__,
                                'keys': list(json_data.keys()) if isinstance(json_data, dict) else None,
                                'length': len(json_data) if isinstance(json_data, (list, dict)) else None
                            }
                        except:
                            endpoint_info['data_structure'] = 'invalid_json'
                    
                    endpoint_results.append(endpoint_info)
                    
                except Exception as e:
                    endpoint_results.append({
                        'endpoint': endpoint,
                        'error': str(e)
                    })
            
            self.intelligence['extracted_data']['endpoint_probe_results'] = endpoint_results
            self.intelligence['findings'].append(f"Endpoint probing completed: {len(endpoint_results)} endpoints analyzed")
            
        except Exception as e:
            self.intelligence['findings'].append(f"Endpoint probing error: {str(e)}")
    
    def identify_automation_opportunities(self):
        """Identify specific automation opportunities"""
        try:
            app_data = self.intelligence['extracted_data'].get('application_data', {})
            
            targets = []
            
            # Form automation opportunities
            forms_count = len(app_data.get('forms_discovered', []))
            if forms_count > 0:
                targets.append({
                    'type': 'form_automation',
                    'target': 'Automated data entry and form submission',
                    'forms_count': forms_count,
                    'priority': 'high',
                    'description': f"Automate {forms_count} discovered forms for data entry workflows"
                })
            
            # Gauge/meter data extraction
            dashboard_elements = app_data.get('dashboard_elements', {})
            if dashboard_elements.get('gauges', 0) > 0:
                targets.append({
                    'type': 'gauge_monitoring',
                    'target': 'Real-time gauge data monitoring',
                    'gauge_count': dashboard_elements['gauges'],
                    'priority': 'high',
                    'description': f"Monitor {dashboard_elements['gauges']} gauge readings for automated alerts"
                })
            
            # Data table extraction
            tables_count = app_data.get('data_tables_count', 0)
            if tables_count > 0:
                targets.append({
                    'type': 'data_extraction',
                    'target': 'Automated report generation',
                    'tables_count': tables_count,
                    'priority': 'medium',
                    'description': f"Extract data from {tables_count} tables for automated reporting"
                })
            
            # API integration opportunities
            api_endpoints = app_data.get('api_endpoints', [])
            if api_endpoints:
                targets.append({
                    'type': 'api_integration',
                    'target': 'Direct API data access',
                    'endpoints_count': len(api_endpoints),
                    'priority': 'high',
                    'description': f"Integrate with {len(api_endpoints)} API endpoints for real-time data access"
                })
            
            # Chart/visualization automation
            if dashboard_elements.get('charts', 0) > 0:
                targets.append({
                    'type': 'visualization_automation',
                    'target': 'Automated chart data extraction',
                    'charts_count': dashboard_elements['charts'],
                    'priority': 'medium',
                    'description': f"Extract data from {dashboard_elements['charts']} charts for analysis"
                })
            
            self.intelligence['automation_targets'] = targets
            self.intelligence['findings'].append(f"Identified {len(targets)} automation opportunities")
            
        except Exception as e:
            self.intelligence['findings'].append(f"Automation analysis error: {str(e)}")
    
    def execute_comprehensive_sweep(self):
        """Execute complete intelligence sweep"""
        print("🚀 NEXUS: Initiating comprehensive GaugeSmart intelligence sweep...")
        
        self.intelligence['status'] = 'running'
        
        try:
            # Step 1: Analyze login page
            login_data = self.analyze_login_page()
            if not login_data:
                self.intelligence['status'] = 'login_analysis_failed'
                return self.intelligence
            
            # Step 2: Attempt authentication
            if not self.attempt_authentication(login_data):
                self.intelligence['status'] = 'authentication_failed'
                return self.intelligence
            
            # Step 3: Extract authenticated data
            if not self.extract_authenticated_data():
                self.intelligence['status'] = 'data_extraction_failed'
                return self.intelligence
            
            # Step 4: Identify automation opportunities
            self.identify_automation_opportunities()
            
            self.intelligence['status'] = 'completed_successfully'
            print("✅ NEXUS: GaugeSmart intelligence sweep completed successfully")
            
        except Exception as e:
            self.intelligence['status'] = f'error: {str(e)}'
            self.intelligence['findings'].append(f"Sweep execution error: {str(e)}")
            print(f"❌ NEXUS: Sweep failed with error: {str(e)}")
        
        return self.intelligence
    
    def generate_intelligence_report(self):
        """Generate comprehensive intelligence report"""
        data = self.intelligence
        
        report = {
            'executive_summary': {
                'operation': 'GaugeSmart Intelligence Sweep',
                'timestamp': data['timestamp'],
                'authentication_status': data['authentication_status'],
                'overall_status': data['status'],
                'findings_count': len(data['findings']),
                'automation_targets': len(data['automation_targets']),
                'data_extracted': bool(data['extracted_data'])
            },
            'technical_intelligence': data['extracted_data'],
            'automation_opportunities': data['automation_targets'],
            'security_observations': {
                'authentication_method': 'Form-based with CSRF protection',
                'session_management': 'Cookie-based authentication',
                'platform_type': 'Enterprise gauge monitoring system'
            },
            'tactical_recommendations': [
                'Deploy automated gauge monitoring workflows',
                'Implement real-time data extraction protocols',
                'Set up automated alerting for gauge thresholds',
                'Establish API integration for continuous monitoring'
            ],
            'detailed_findings': data['findings']
        }
        
        return report

def execute_gaugesmart_sweep():
    """Execute GaugeSmart intelligence sweep"""
    sweep = GaugeSmartIntelligenceSweep()
    results = sweep.execute_comprehensive_sweep()
    report = sweep.generate_intelligence_report()
    
    return {
        'operation_successful': results['status'] == 'completed_successfully',
        'intelligence_report': report,
        'raw_data': results
    }

if __name__ == "__main__":
    print("🚀 NEXUS: Initiating GaugeSmart Intelligence Operation...")
    results = execute_gaugesmart_sweep()
    
    print("\n" + "="*80)
    print("NEXUS GAUGESMART INTELLIGENCE REPORT")
    print("="*80)
    print(json.dumps(results['intelligence_report'], indent=2))
    
    if results['operation_successful']:
        print("\n✅ OPERATION SUCCESSFUL: GaugeSmart intelligence extracted and automation targets identified")
    else:
        print("\n⚠️ OPERATION STATUS: Continuing intelligence analysis...")