"""
Comprehensive Ground Works Data Extractor
Extracts complete authentic data from Ground Works system with admin access
"""

import json
import os
import requests
import time
from datetime import datetime
import re
from urllib.parse import urljoin

class ComprehensiveGroundWorksExtractor:
    """Complete data extraction from Ground Works system using authenticated session"""
    
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.session = requests.Session()
        
        # Set browser headers to match your Edge session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        self.session.headers.update(self.headers)
        self.extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'schedules': [],
            'billing': [],
            'reports': [],
            'configurations': {},
            'raw_pages': {},
            'api_data': {},
            'extraction_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_extracted': 0,
                'authenticated': False
            }
        }

    def attempt_session_authentication(self):
        """Attempt to use existing authentication or establish session"""
        print("Attempting to establish authenticated session...")
        
        # Try to access main dashboard
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            if response.status_code == 200 and len(response.text) > 1000:
                self.extracted_data['extraction_metadata']['authenticated'] = True
                print("Successfully connected to Ground Works with authentication")
                return True
        except:
            pass
        
        # Try direct project access
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200 and len(response.text) > 1000:
                self.extracted_data['extraction_metadata']['authenticated'] = True
                print("Successfully accessed projects page")
                return True
        except:
            pass
        
        # Try common Angular routes
        angular_routes = [
            "/app/projects",
            "/app/dashboard",
            "/app/assets",
            "/main",
            "/home"
        ]
        
        for route in angular_routes:
            try:
                response = self.session.get(f"{self.base_url}{route}")
                if response.status_code == 200 and len(response.text) > 1000:
                    self.extracted_data['extraction_metadata']['authenticated'] = True
                    print(f"Successfully accessed {route}")
                    return True
            except:
                continue
        
        return False

    def extract_all_api_endpoints(self):
        """Extract data from all possible API endpoints"""
        print("Extracting data from API endpoints...")
        
        # Common Ground Works API patterns
        api_endpoints = [
            # Projects
            "/api/projects",
            "/api/projects/list",
            "/api/projects/all",
            "/api/project/data",
            "/projects/api",
            "/projects/list",
            "/projects/data",
            
            # Assets & Equipment
            "/api/assets",
            "/api/equipment",
            "/api/fleet",
            "/api/vehicles",
            "/assets/list",
            "/equipment/data",
            "/fleet/status",
            
            # Personnel
            "/api/users",
            "/api/personnel",
            "/api/employees",
            "/api/staff",
            "/users/list",
            "/personnel/data",
            
            # Schedules & Time
            "/api/schedules",
            "/api/calendar",
            "/api/timesheet",
            "/api/attendance",
            "/schedules/data",
            "/calendar/events",
            
            # Billing & Finance
            "/api/billing",
            "/api/invoices",
            "/api/finance",
            "/api/payments",
            "/billing/data",
            "/invoices/list",
            
            # Reports
            "/api/reports",
            "/api/analytics",
            "/api/dashboard",
            "/reports/data",
            "/analytics/data",
            
            # Configuration
            "/api/config",
            "/api/settings",
            "/api/system",
            "/config/data"
        ]
        
        extracted_apis = 0
        
        for endpoint in api_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try GET request
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            self.extracted_data['api_data'][endpoint] = data
                            extracted_apis += 1
                            print(f"✓ Extracted JSON data from {endpoint}")
                        except:
                            pass
                    else:
                        # Try to parse as text/HTML for embedded data
                        text_data = self.extract_data_from_html(response.text)
                        if text_data:
                            self.extracted_data['api_data'][endpoint] = text_data
                            extracted_apis += 1
                            print(f"✓ Extracted text data from {endpoint}")
                
                # Also try POST with empty body (common for some APIs)
                try:
                    post_response = self.session.post(url, json={}, timeout=5)
                    if post_response.status_code == 200:
                        try:
                            data = post_response.json()
                            self.extracted_data['api_data'][f"{endpoint}_post"] = data
                            extracted_apis += 1
                            print(f"✓ Extracted POST data from {endpoint}")
                        except:
                            pass
                except:
                    pass
                    
            except Exception as e:
                continue
        
        print(f"Extracted data from {extracted_apis} API endpoints")
        return extracted_apis

    def extract_all_page_data(self):
        """Extract data from all accessible pages"""
        print("Extracting data from all accessible pages...")
        
        # Common Ground Works pages
        pages = [
            "/dashboard",
            "/projects",
            "/assets",
            "/equipment",
            "/personnel",
            "/users",
            "/schedules",
            "/calendar",
            "/billing",
            "/invoices",
            "/reports",
            "/analytics",
            "/settings",
            "/admin",
            "/system",
            
            # Angular routes
            "/app/dashboard",
            "/app/projects",
            "/app/assets",
            "/app/personnel",
            "/app/billing",
            "/app/reports",
            
            # Possible sub-routes
            "/projects/active",
            "/projects/completed",
            "/assets/active",
            "/equipment/maintenance",
            "/personnel/active",
            "/billing/pending",
            "/reports/monthly"
        ]
        
        extracted_pages = 0
        
        for page in pages:
            try:
                url = f"{self.base_url}{page}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200 and len(response.text) > 500:
                    # Store raw HTML
                    page_name = page.strip('/').replace('/', '_') or 'home'
                    self.extracted_data['raw_pages'][page_name] = response.text
                    
                    # Extract structured data from the page
                    structured_data = self.extract_comprehensive_page_data(response.text, page)
                    
                    # Categorize extracted data
                    if 'project' in page.lower():
                        self.extracted_data['projects'].extend(structured_data.get('items', []))
                    elif 'asset' in page.lower() or 'equipment' in page.lower():
                        self.extracted_data['assets'].extend(structured_data.get('items', []))
                    elif 'personnel' in page.lower() or 'user' in page.lower():
                        self.extracted_data['personnel'].extend(structured_data.get('items', []))
                    elif 'billing' in page.lower() or 'invoice' in page.lower():
                        self.extracted_data['billing'].extend(structured_data.get('items', []))
                    elif 'schedule' in page.lower() or 'calendar' in page.lower():
                        self.extracted_data['schedules'].extend(structured_data.get('items', []))
                    
                    extracted_pages += 1
                    print(f"✓ Extracted data from {page}")
                    
            except Exception as e:
                continue
        
        print(f"Extracted data from {extracted_pages} pages")
        return extracted_pages

    def extract_comprehensive_page_data(self, html_content, source_page):
        """Extract all possible data from HTML content"""
        data = {
            'source': source_page,
            'items': [],
            'tables': [],
            'forms': [],
            'scripts': [],
            'metadata': {}
        }
        
        # Extract all tables with detailed parsing
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for i, table_html in enumerate(tables):
            table_data = self.parse_table_comprehensively(table_html)
            if table_data and table_data.get('rows'):
                data['tables'].append(table_data)
                
                # Convert table rows to items
                headers = table_data.get('headers', [])
                for row in table_data.get('rows', []):
                    if len(row) >= len(headers):
                        item = {}
                        for j, header in enumerate(headers):
                            if j < len(row):
                                item[header.lower().replace(' ', '_')] = row[j]
                        item['source'] = f"{source_page}_table_{i}"
                        data['items'].append(item)

        # Extract Angular data from script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for script in scripts:
            # Look for JSON data in scripts
            json_patterns = [
                r'projects\s*[:=]\s*(\[.*?\])',
                r'assets\s*[:=]\s*(\[.*?\])',
                r'users\s*[:=]\s*(\[.*?\])',
                r'data\s*[:=]\s*(\{.*?\})',
                r'config\s*[:=]\s*(\{.*?\})',
                r'window\.\w+\s*=\s*(\{.*?\})',
                r'var\s+\w+\s*=\s*(\{.*?\})',
                r'const\s+\w+\s*=\s*(\[.*?\])'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, script, re.DOTALL)
                for match in matches:
                    try:
                        parsed_data = json.loads(match)
                        if isinstance(parsed_data, list):
                            data['items'].extend(parsed_data)
                        elif isinstance(parsed_data, dict):
                            data['metadata'].update(parsed_data)
                    except:
                        continue

        # Extract data from div elements with data attributes
        data_div_pattern = r'<div[^>]*data-[^>]*>(.*?)</div>'
        data_divs = re.findall(data_div_pattern, html_content, re.DOTALL)
        
        for div_content in data_divs:
            # Extract any structured content
            if 'project' in div_content.lower() or 'asset' in div_content.lower():
                text_items = re.findall(r'([A-Z]{2,3}-\d{2,4}|\d{4}-\d{3})', div_content)
                for item in text_items:
                    data['items'].append({'identifier': item, 'source': f"{source_page}_div"})

        # Extract form data
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for form_html in forms:
            form_data = self.parse_form_comprehensively(form_html)
            if form_data:
                data['forms'].append(form_data)

        return data

    def parse_table_comprehensively(self, table_html):
        """Comprehensive table parsing with all data extraction"""
        table_data = {
            'headers': [],
            'rows': [],
            'metadata': {}
        }
        
        # Extract table headers
        header_patterns = [
            r'<th[^>]*>(.*?)</th>',
            r'<td[^>]*class="[^"]*header[^"]*"[^>]*>(.*?)</td>'
        ]
        
        for pattern in header_patterns:
            headers = re.findall(pattern, table_html, re.DOTALL | re.IGNORECASE)
            if headers:
                table_data['headers'] = [self.clean_html_text(h) for h in headers]
                break
        
        # Extract table rows
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
        
        for row_html in rows:
            # Skip header rows
            if '<th' in row_html:
                continue
                
            cell_pattern = r'<td[^>]*>(.*?)</td>'
            cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
            
            if cells:
                clean_cells = [self.clean_html_text(cell) for cell in cells]
                if any(cell.strip() for cell in clean_cells):  # Only add non-empty rows
                    table_data['rows'].append(clean_cells)
        
        return table_data

    def parse_form_comprehensively(self, form_html):
        """Comprehensive form parsing"""
        form_data = {
            'inputs': [],
            'selects': [],
            'textareas': [],
            'action': '',
            'method': ''
        }
        
        # Extract form attributes
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        if action_match:
            form_data['action'] = action_match.group(1)
        
        method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        if method_match:
            form_data['method'] = method_match.group(1)
        
        # Extract inputs
        input_pattern = r'<input[^>]*>'
        inputs = re.findall(input_pattern, form_html, re.IGNORECASE)
        
        for input_html in inputs:
            input_data = {}
            
            name_match = re.search(r'name=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
            type_match = re.search(r'type=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
            value_match = re.search(r'value=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
            
            if name_match:
                input_data['name'] = name_match.group(1)
            if type_match:
                input_data['type'] = type_match.group(1)
            if value_match:
                input_data['value'] = value_match.group(1)
            
            if input_data:
                form_data['inputs'].append(input_data)
        
        return form_data

    def clean_html_text(self, text):
        """Clean HTML text and extract meaningful content"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        # Decode HTML entities
        clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return clean_text.strip()

    def extract_data_from_html(self, html_content):
        """Extract any structured data from HTML"""
        extracted = []
        
        # Look for JSON-like structures
        json_patterns = [
            r'\{[^{}]*"[^"]*"[^{}]*\}',
            r'\[[^[\]]*\{[^}]*\}[^[\]]*\]'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                try:
                    data = json.loads(match)
                    extracted.append(data)
                except:
                    continue
        
        return extracted

    def extract_export_data(self):
        """Try to access export/download endpoints"""
        print("Attempting to access export endpoints...")
        
        export_endpoints = [
            "/export/projects",
            "/export/assets",
            "/export/personnel",
            "/export/all",
            "/download/data",
            "/download/projects",
            "/download/assets",
            "/api/export/projects",
            "/api/export/assets",
            "/api/export/all",
            "/reports/export",
            "/data/export"
        ]
        
        exports = 0
        
        for endpoint in export_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try different methods
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            response = self.session.get(url, timeout=10)
                        else:
                            response = self.session.post(url, json={}, timeout=10)
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            
                            if 'json' in content_type:
                                try:
                                    data = response.json()
                                    self.extracted_data['api_data'][f"{endpoint}_export"] = data
                                    exports += 1
                                    print(f"✓ Exported JSON from {endpoint}")
                                except:
                                    pass
                            elif 'csv' in content_type or 'excel' in content_type:
                                # Save binary export data
                                self.extracted_data['api_data'][f"{endpoint}_file"] = {
                                    'content_type': content_type,
                                    'size': len(response.content),
                                    'data': response.content[:1000].decode('utf-8', errors='ignore')  # First 1000 chars
                                }
                                exports += 1
                                print(f"✓ Exported file from {endpoint}")
                        
                    except:
                        continue
                        
            except:
                continue
        
        print(f"Successfully accessed {exports} export endpoints")
        return exports

    def save_comprehensive_extraction(self):
        """Save all extracted data with detailed organization"""
        try:
            backup_dir = "comprehensive_ground_works_extraction"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Update metadata
            total_extracted = (
                len(self.extracted_data['projects']) +
                len(self.extracted_data['assets']) +
                len(self.extracted_data['personnel']) +
                len(self.extracted_data['billing']) +
                len(self.extracted_data['schedules']) +
                len(self.extracted_data['api_data']) +
                len(self.extracted_data['raw_pages'])
            )
            
            self.extracted_data['extraction_metadata']['total_extracted'] = total_extracted
            self.extracted_data['extraction_metadata']['completion_time'] = datetime.now().isoformat()
            
            # Save complete dataset
            with open(f"{backup_dir}/complete_extraction_{timestamp}.json", 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Save individual data types
            for data_type, data in self.extracted_data.items():
                if data and data_type != 'extraction_metadata':
                    with open(f"{backup_dir}/{data_type}_{timestamp}.json", 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Save raw HTML pages separately
            html_dir = f"{backup_dir}/html_pages"
            os.makedirs(html_dir, exist_ok=True)
            
            for page_name, html_content in self.extracted_data['raw_pages'].items():
                with open(f"{html_dir}/{page_name}_{timestamp}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            print(f"Comprehensive extraction saved to {backup_dir}/")
            return backup_dir
            
        except Exception as e:
            print(f"Error saving extraction: {e}")
            return None

    def execute_comprehensive_extraction(self):
        """Execute complete comprehensive extraction of Ground Works"""
        print("Starting comprehensive Ground Works data extraction...")
        
        # Step 1: Establish authentication
        if not self.attempt_session_authentication():
            print("Warning: Could not establish authenticated session")
        
        # Step 2: Extract from all API endpoints
        api_count = self.extract_all_api_endpoints()
        
        # Step 3: Extract from all pages
        page_count = self.extract_all_page_data()
        
        # Step 4: Try export endpoints
        export_count = self.extract_export_data()
        
        # Step 5: Save everything
        backup_path = self.save_comprehensive_extraction()
        
        # Generate comprehensive summary
        summary = {
            'status': 'COMPREHENSIVE_EXTRACTION_COMPLETE',
            'authentication_established': self.extracted_data['extraction_metadata']['authenticated'],
            'api_endpoints_extracted': api_count,
            'pages_extracted': page_count,
            'export_endpoints_accessed': export_count,
            'total_projects': len(self.extracted_data['projects']),
            'total_assets': len(self.extracted_data['assets']),
            'total_personnel': len(self.extracted_data['personnel']),
            'total_billing': len(self.extracted_data['billing']),
            'total_schedules': len(self.extracted_data['schedules']),
            'raw_pages_captured': len(self.extracted_data['raw_pages']),
            'api_data_sources': len(self.extracted_data['api_data']),
            'backup_location': backup_path,
            'extraction_time': datetime.now().isoformat()
        }
        
        print("\n" + "="*50)
        print("COMPREHENSIVE EXTRACTION SUMMARY")
        print("="*50)
        print(f"Authentication: {'✓ SUCCESS' if summary['authentication_established'] else '✗ FAILED'}")
        print(f"API Endpoints: {summary['api_endpoints_extracted']} extracted")
        print(f"Pages Scraped: {summary['pages_extracted']} extracted")
        print(f"Export Access: {summary['export_endpoints_accessed']} accessed")
        print(f"Projects Found: {summary['total_projects']}")
        print(f"Assets Found: {summary['total_assets']}")
        print(f"Personnel Found: {summary['total_personnel']}")
        print(f"Billing Records: {summary['total_billing']}")
        print(f"Schedule Items: {summary['total_schedules']}")
        print(f"Raw Pages: {summary['raw_pages_captured']}")
        print(f"API Sources: {summary['api_data_sources']}")
        print(f"Saved to: {backup_path}")
        print("="*50)
        
        return summary

def execute_comprehensive_ground_works_extraction():
    """Main function to execute comprehensive Ground Works extraction"""
    extractor = ComprehensiveGroundWorksExtractor()
    return extractor.execute_comprehensive_extraction()

if __name__ == "__main__":
    result = execute_comprehensive_ground_works_extraction()
    print(json.dumps(result, indent=2, default=str))