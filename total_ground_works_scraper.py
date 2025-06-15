"""
Total Ground Works Scraper
Comprehensive extraction of all possible data from Ground Works system
"""

import requests
import re
import json
import logging
from urllib.parse import urljoin, urlparse
# from bs4 import BeautifulSoup  # Will implement manual HTML parsing
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class TotalGroundWorksScraper:
    """Complete Ground Works data extraction system"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.extracted_data = {
            'site_structure': {},
            'javascript_bundles': {},
            'css_files': {},
            'api_endpoints': [],
            'embedded_data': {},
            'configuration_data': {},
            'authentication_patterns': {},
            'routing_information': {},
            'component_data': {},
            'business_logic': {},
            'database_schemas': {},
            'form_structures': {},
            'menu_structures': {},
            'user_permissions': {},
            'file_uploads': [],
            'external_resources': [],
            'security_patterns': {},
            'error_pages': {},
            'metadata': {}
        }
        
        # Enhanced headers for comprehensive scraping
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def execute_total_extraction(self):
        """Execute comprehensive Ground Works extraction"""
        try:
            logging.info("Starting total Ground Works extraction")
            
            # Phase 1: Site structure analysis
            self.analyze_site_structure()
            
            # Phase 2: JavaScript bundle deep analysis
            self.analyze_all_javascript_bundles()
            
            # Phase 3: CSS and style analysis
            self.analyze_css_files()
            
            # Phase 4: API endpoint discovery
            self.discover_api_endpoints()
            
            # Phase 5: Component and routing analysis
            self.analyze_angular_components()
            
            # Phase 6: Configuration extraction
            self.extract_configuration_data()
            
            # Phase 7: Business logic analysis
            self.analyze_business_logic()
            
            # Phase 8: Security pattern analysis
            self.analyze_security_patterns()
            
            # Phase 9: Menu and navigation analysis
            self.analyze_navigation_structures()
            
            # Phase 10: Comprehensive data categorization
            self.categorize_all_extracted_data()
            
            # Convert extracted data to the expected format for TRAXOVO dashboard
            converted_data = self.convert_to_traxovo_format()
            
            return {
                'status': 'success',
                'data': converted_data,
                'data_summary': {
                    'projects': len(converted_data.get('projects', [])),
                    'assets': len(converted_data.get('assets', [])),
                    'personnel': len(converted_data.get('personnel', [])),
                    'reports': len(converted_data.get('reports', [])),
                    'billing': len(converted_data.get('billing', [])),
                    'raw_extractions': len(self.extracted_data['embedded_data']),
                    'last_updated': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'extraction_method': 'total_comprehensive_scraping'
                },
                'total_extraction_summary': {
                    'site_structure_items': len(self.extracted_data['site_structure']),
                    'javascript_bundles': len(self.extracted_data['javascript_bundles']),
                    'css_files': len(self.extracted_data['css_files']),
                    'api_endpoints': len(self.extracted_data['api_endpoints']),
                    'embedded_data_structures': len(self.extracted_data['embedded_data']),
                    'configuration_items': len(self.extracted_data['configuration_data']),
                    'component_data': len(self.extracted_data['component_data']),
                    'business_logic_patterns': len(self.extracted_data['business_logic']),
                    'security_patterns': len(self.extracted_data['security_patterns']),
                    'extraction_method': 'total_comprehensive_scraping'
                },
                'raw_extracted_data': self.extracted_data
            }
            
        except Exception as e:
            logging.error(f"Total extraction failed: {e}")
            return {
                'status': 'error',
                'message': f'Total Ground Works extraction failed: {str(e)}'
            }
    
    def analyze_site_structure(self):
        """Analyze complete site structure using manual HTML parsing"""
        try:
            # Get main page
            response = self.session.get(self.base_url, timeout=30)
            html_content = response.text
            
            # Extract all links and references using regex
            self.extracted_data['site_structure']['links'] = []
            link_patterns = [
                r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>',
                r'<link[^>]*href=["\']([^"\']*)["\'][^>]*(?:rel=["\']([^"\']*)["\'])?'
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        self.extracted_data['site_structure']['links'].append({
                            'url': match[0],
                            'text': match[1] if len(match) > 1 else '',
                            'rel': match[2] if len(match) > 2 else ''
                        })
            
            # Extract all script references
            self.extracted_data['site_structure']['scripts'] = []
            script_patterns = [
                r'<script[^>]*src=["\']([^"\']*)["\'][^>]*>',
                r'<script[^>]*>(.*?)</script>'
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if match.endswith('.js') or '/' in match:
                        self.extracted_data['site_structure']['scripts'].append({
                            'src': match,
                            'type': 'external'
                        })
                    elif len(match) > 10:  # Inline script content
                        self.extracted_data['site_structure']['scripts'].append({
                            'inline_content': match[:1000],  # First 1000 chars
                            'type': 'inline'
                        })
            
            # Extract meta information
            self.extracted_data['site_structure']['meta'] = []
            meta_pattern = r'<meta[^>]*name=["\']([^"\']*)["\'][^>]*content=["\']([^"\']*)["\']'
            meta_matches = re.findall(meta_pattern, html_content, re.IGNORECASE)
            for name, content in meta_matches:
                self.extracted_data['site_structure']['meta'].append({
                    'name': name,
                    'content': content
                })
            
            # Extract all form structures
            self.extracted_data['form_structures'] = []
            form_pattern = r'<form[^>]*>(.*?)</form>'
            form_matches = re.findall(form_pattern, html_content, re.IGNORECASE | re.DOTALL)
            for form_content in form_matches:
                input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
                input_matches = re.findall(input_pattern, form_content, re.IGNORECASE)
                self.extracted_data['form_structures'].append({
                    'inputs': [{'name': name} for name in input_matches]
                })
            
        except Exception as e:
            logging.error(f"Site structure analysis failed: {e}")
    
    def analyze_all_javascript_bundles(self):
        """Deep analysis of all JavaScript bundles"""
        try:
            # Discover all JavaScript files
            js_files = self.discover_javascript_files()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_file = {
                    executor.submit(self.analyze_single_js_file, js_file): js_file 
                    for js_file in js_files
                }
                
                for future in as_completed(future_to_file):
                    js_file = future_to_file[future]
                    try:
                        analysis_result = future.result()
                        self.extracted_data['javascript_bundles'][js_file] = analysis_result
                    except Exception as e:
                        logging.error(f"JavaScript analysis failed for {js_file}: {e}")
                        
        except Exception as e:
            logging.error(f"JavaScript bundle analysis failed: {e}")
    
    def discover_javascript_files(self):
        """Discover all JavaScript files in the application"""
        js_files = []
        
        try:
            # Get main page
            response = self.session.get(self.base_url, timeout=30)
            
            # Extract script src attributes
            js_patterns = [
                r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']',
                r'src\s*:\s*["\']([^"\']*\.js[^"\']*)["\']',
                r'import\s+[^"\']*["\']([^"\']*\.js[^"\']*)["\']'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    if match.startswith('/'):
                        js_url = urljoin(self.base_url, match)
                    elif match.startswith('http'):
                        js_url = match
                    else:
                        js_url = urljoin(self.base_url, match)
                    
                    if js_url not in js_files:
                        js_files.append(js_url)
            
            # Common Angular file patterns
            common_files = [
                '/runtime.js', '/polyfills.js', '/vendor.js', '/main.js',
                '/scripts.js', '/app.js', '/chunk.js', '/bundle.js'
            ]
            
            for file_path in common_files:
                js_url = urljoin(self.base_url, file_path)
                if js_url not in js_files:
                    js_files.append(js_url)
                    
        except Exception as e:
            logging.error(f"JavaScript file discovery failed: {e}")
        
        return js_files
    
    def analyze_single_js_file(self, js_url):
        """Analyze a single JavaScript file comprehensively"""
        try:
            response = self.session.get(js_url, timeout=30)
            content = response.text
            
            analysis = {
                'size': len(content),
                'url': js_url,
                'embedded_data': self.extract_js_embedded_data(content),
                'api_patterns': self.extract_api_patterns(content),
                'routing_patterns': self.extract_routing_patterns(content),
                'component_patterns': self.extract_component_patterns(content),
                'configuration_patterns': self.extract_configuration_patterns(content),
                'business_data': self.extract_business_data_patterns(content),
                'authentication_patterns': self.extract_auth_patterns(content),
                'database_patterns': self.extract_database_patterns(content)
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"Single JS file analysis failed for {js_url}: {e}")
            return {'error': str(e)}
    
    def extract_js_embedded_data(self, content):
        """Extract embedded data from JavaScript content"""
        embedded_data = []
        
        patterns = [
            # RAGLE/Ground Works specific patterns
            r'(?:ragle|groundworks|project|asset|employee|job)(?:Data|List|Records|Config)\s*[=:]\s*(\[[^\]]*\])',
            r'(?:ragle|groundworks|project|asset|employee|job)(?:Data|List|Records|Config)\s*[=:]\s*({[^}]*})',
            
            # General business data patterns
            r'(?:projects|jobs|contracts|assets|equipment|personnel|employees|users|drivers)\s*[=:]\s*(\[[^\]]*\])',
            r'(?:billing|invoices|costs|revenue|financial)\s*[=:]\s*(\[[^\]]*\])',
            
            # Configuration and settings
            r'(?:config|settings|constants|environment)\s*[=:]\s*({[^{}]*})',
            
            # API response templates
            r'(?:template|mock|sample|default|response)(?:Data|Response)\s*[=:]\s*(\[[^\]]*\])',
            
            # Large object literals that might contain data
            r'(\{[^{}]*(?:"(?:id|name|title|number|code|reference|email|phone)"\s*:\s*"[^"]+")[^{}]*\})',
            
            # Array of objects with business identifiers
            r'(\[{[^}]*(?:"(?:id|name|title|project|asset|job|employee|driver|vehicle)"\s*:\s*"[^"]+")[^}]*}[^]]*\])'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse as JSON
                    if match.strip().startswith('[') or match.strip().startswith('{'):
                        # Clean up JavaScript-specific syntax
                        cleaned = self.clean_js_for_json(match)
                        if len(cleaned) > 50:  # Only substantial data
                            embedded_data.append({
                                'raw_content': match[:500],  # First 500 chars
                                'cleaned_content': cleaned[:500],
                                'size': len(match),
                                'type': 'array' if match.strip().startswith('[') else 'object'
                            })
                except Exception:
                    continue
        
        return embedded_data
    
    def extract_api_patterns(self, content):
        """Extract API endpoint patterns from JavaScript"""
        api_patterns = []
        
        patterns = [
            r'["\']([^"\']*(?:api|service|endpoint)[^"\']*)["\']',
            r'(?:url|endpoint|path)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'http(?:s)?://[^"\']*["\']',
            r'/api/[^"\']*',
            r'["\']/((?:login|auth|signin|logout|dashboard|admin|user|project|asset|report)[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and '/' in match:
                    api_patterns.append({
                        'endpoint': match,
                        'full_url': urljoin(self.base_url, match) if not match.startswith('http') else match
                    })
        
        return api_patterns
    
    def extract_routing_patterns(self, content):
        """Extract Angular routing patterns"""
        routing_patterns = []
        
        patterns = [
            r'(?:path|route)\s*:\s*["\']([^"\']+)["\']',
            r'(?:redirectTo|component)\s*:\s*["\']([^"\']+)["\']',
            r'RouterModule\.forRoot\s*\(\s*(\[.*?\])',
            r'Routes\s*=\s*(\[.*?\])'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                routing_patterns.append(match)
        
        return routing_patterns
    
    def extract_component_patterns(self, content):
        """Extract Angular component patterns"""
        component_patterns = []
        
        patterns = [
            r'@Component\s*\(\s*({[^}]*})',
            r'selector\s*:\s*["\']([^"\']+)["\']',
            r'templateUrl\s*:\s*["\']([^"\']+)["\']',
            r'styleUrls\s*:\s*(\[[^\]]*\])',
            r'class\s+(\w+Component)',
            r'ngOnInit\s*\(\s*\)\s*{([^}]*)}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                component_patterns.append(match)
        
        return component_patterns
    
    def extract_configuration_patterns(self, content):
        """Extract configuration and settings patterns"""
        config_patterns = []
        
        patterns = [
            r'(?:environment|config|settings|constants)\s*[=:]\s*({[^{}]*})',
            r'API_(?:URL|ENDPOINT|BASE)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:baseUrl|apiUrl|serviceUrl)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:production|development|staging)\s*:\s*(true|false)',
            r'(?:version|appVersion)\s*[=:]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                config_patterns.append(match)
        
        return config_patterns
    
    def extract_business_data_patterns(self, content):
        """Extract business-specific data patterns"""
        business_patterns = []
        
        # RAGLE INC specific patterns
        ragle_patterns = [
            r'ragle[^"\']*["\']([^"\']+)["\']',
            r'ground[_\s]*works[^"\']*["\']([^"\']+)["\']',
            r'dallas[^"\']*["\']([^"\']+)["\']',
            r'texas[^"\']*["\']([^"\']+)["\']',
            r'construction[^"\']*["\']([^"\']+)["\']',
            r'equipment[^"\']*["\']([^"\']+)["\']',
            r'project[^"\']*["\']([^"\']+)["\']'
        ]
        
        for pattern in ragle_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                business_patterns.append({
                    'type': 'ragle_specific',
                    'content': match
                })
        
        return business_patterns
    
    def extract_auth_patterns(self, content):
        """Extract authentication patterns"""
        auth_patterns = []
        
        patterns = [
            r'(?:login|signin|authenticate|auth)\s*\([^)]*\)',
            r'(?:token|jwt|session|cookie)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:username|email|password)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:authorization|bearer)\s*[=:]\s*["\']([^"\']+)["\']',
            r'localStorage\.(?:get|set)Item\s*\(\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                auth_patterns.append(match)
        
        return auth_patterns
    
    def extract_database_patterns(self, content):
        """Extract database and model patterns"""
        db_patterns = []
        
        patterns = [
            r'(?:model|schema|entity)\s+(\w+)\s*{',
            r'(?:table|collection)\s*[=:]\s*["\']([^"\']+)["\']',
            r'(?:select|insert|update|delete)\s+[^;]*;',
            r'(?:findBy|getBy|queryBy)(\w+)',
            r'(?:id|uuid|primary|foreign)(?:Key)?\s*[=:]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                db_patterns.append(match)
        
        return db_patterns
    
    def analyze_css_files(self):
        """Analyze CSS files for styling and layout information"""
        try:
            css_files = self.discover_css_files()
            
            for css_file in css_files:
                try:
                    response = self.session.get(css_file, timeout=30)
                    content = response.text
                    
                    self.extracted_data['css_files'][css_file] = {
                        'size': len(content),
                        'selectors': self.extract_css_selectors(content),
                        'variables': self.extract_css_variables(content),
                        'media_queries': self.extract_media_queries(content)
                    }
                    
                except Exception as e:
                    logging.error(f"CSS analysis failed for {css_file}: {e}")
                    
        except Exception as e:
            logging.error(f"CSS files analysis failed: {e}")
    
    def discover_css_files(self):
        """Discover CSS files"""
        css_files = []
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            
            css_patterns = [
                r'<link[^>]*href=["\']([^"\']*\.css[^"\']*)["\']',
                r'@import\s+["\']([^"\']*\.css[^"\']*)["\']'
            ]
            
            for pattern in css_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    css_url = urljoin(self.base_url, match)
                    if css_url not in css_files:
                        css_files.append(css_url)
                        
        except Exception as e:
            logging.error(f"CSS file discovery failed: {e}")
        
        return css_files
    
    def extract_css_selectors(self, content):
        """Extract CSS selectors"""
        selectors = re.findall(r'([.#]?[\w-]+(?:\s*[>+~]\s*[\w-]+)*)\s*{', content)
        return selectors[:100]  # Limit to first 100
    
    def extract_css_variables(self, content):
        """Extract CSS variables"""
        variables = re.findall(r'--[\w-]+\s*:\s*([^;]+);', content)
        return variables
    
    def extract_media_queries(self, content):
        """Extract media queries"""
        media_queries = re.findall(r'@media\s*([^{]+)', content)
        return media_queries
    
    def discover_api_endpoints(self):
        """Discover all possible API endpoints"""
        try:
            # Common API endpoint patterns for Ground Works
            common_endpoints = [
                '/api/auth/login', '/api/auth/logout', '/api/auth/verify',
                '/api/projects', '/api/projects/list', '/api/projects/details',
                '/api/assets', '/api/assets/list', '/api/assets/details',
                '/api/personnel', '/api/personnel/list', '/api/personnel/details',
                '/api/employees', '/api/employees/list', '/api/employees/details',
                '/api/drivers', '/api/drivers/list', '/api/drivers/details',
                '/api/vehicles', '/api/vehicles/list', '/api/vehicles/details',
                '/api/equipment', '/api/equipment/list', '/api/equipment/details',
                '/api/reports', '/api/reports/list', '/api/reports/generate',
                '/api/billing', '/api/billing/list', '/api/billing/details',
                '/api/invoices', '/api/invoices/list', '/api/invoices/details',
                '/api/dashboard', '/api/dashboard/data', '/api/dashboard/summary',
                '/api/config', '/api/settings', '/api/status',
                '/api/user', '/api/user/profile', '/api/user/preferences',
                '/api/admin', '/api/admin/users', '/api/admin/settings',
                '/login', '/dashboard', '/admin', '/reports', '/settings',
                '/projects', '/assets', '/personnel', '/billing'
            ]
            
            for endpoint in common_endpoints:
                endpoint_url = urljoin(self.base_url, endpoint)
                
                # Test different HTTP methods
                for method in ['GET', 'POST', 'PUT', 'DELETE']:
                    try:
                        if method == 'GET':
                            response = self.session.get(endpoint_url, timeout=10)
                        elif method == 'POST':
                            response = self.session.post(endpoint_url, timeout=10)
                        elif method == 'PUT':
                            response = self.session.put(endpoint_url, timeout=10)
                        else:
                            response = self.session.delete(endpoint_url, timeout=10)
                        
                        self.extracted_data['api_endpoints'].append({
                            'endpoint': endpoint,
                            'method': method,
                            'status_code': response.status_code,
                            'response_size': len(response.content),
                            'content_type': response.headers.get('content-type', ''),
                            'accessible': response.status_code not in [404, 405]
                        })
                        
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.error(f"API endpoint discovery failed: {e}")
    
    def analyze_angular_components(self):
        """Analyze Angular components and their data"""
        # This would be implemented based on the extracted component patterns
        pass
    
    def extract_configuration_data(self):
        """Extract all configuration data found"""
        # This would be implemented based on the extracted configuration patterns
        pass
    
    def analyze_business_logic(self):
        """Analyze business logic patterns"""
        # This would be implemented based on the extracted business patterns
        pass
    
    def analyze_security_patterns(self):
        """Analyze security patterns and authentication"""
        # This would be implemented based on the extracted auth patterns
        pass
    
    def analyze_navigation_structures(self):
        """Analyze navigation and menu structures"""
        # This would be implemented based on the extracted routing patterns
        pass
    
    def categorize_all_extracted_data(self):
        """Categorize all extracted data into business categories"""
        # This would implement comprehensive categorization
        pass
    
    def clean_js_for_json(self, js_string):
        """Clean JavaScript object/array string for JSON parsing"""
        if not js_string:
            return ''
        
        cleaned = js_string.strip()
        
        # Fix common JavaScript to JSON issues
        cleaned = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', cleaned)
        cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
        cleaned = re.sub(r'undefined', 'null', cleaned)
        cleaned = re.sub(r'new Date\([^)]*\)', '"date"', cleaned)
        cleaned = re.sub(r'function[^}]*}', '"function"', cleaned)
        cleaned = re.sub(r'//.*?\n', '', cleaned)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        
        return cleaned

def execute_total_ground_works_extraction(username, password):
    """Execute total Ground Works extraction"""
    scraper = TotalGroundWorksScraper(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return scraper.execute_total_extraction()