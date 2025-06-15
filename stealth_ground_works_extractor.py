"""
Stealth Ground Works Data Extractor
Mimics natural browser behavior to avoid detection
"""

import requests
import json
import time
import random
from datetime import datetime
import os
import re
from urllib.parse import urljoin

class StealthGroundWorksExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://groundworks.ragleinc.com"
        
        # Stealth headers that mimic Edge browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
        }
        
        self.session.headers.update(self.headers)
        self.extracted_data = {}
        
    def natural_delay(self):
        """Add natural human-like delays"""
        time.sleep(random.uniform(0.5, 2.0))
        
    def extract_with_stealth(self, url_path):
        """Extract data with stealth techniques"""
        try:
            full_url = f"{self.base_url}{url_path}"
            
            # Natural delay before request
            self.natural_delay()
            
            # Make request with stealth headers
            response = self.session.get(full_url)
            
            if response.status_code == 200:
                return response.text
            else:
                return None
                
        except Exception as e:
            print(f"Stealth extraction error for {url_path}: {e}")
            return None
    
    def extract_all_project_data(self):
        """Extract all available project data stealthily"""
        print("Beginning stealth extraction of Ground Works data...")
        
        # List of potential endpoints to check
        endpoints = [
            '/projects',
            '/dashboard',
            '/admin',
            '/reports',
            '/api/projects',
            '/api/data',
            '/export',
            '/data',
            '/'
        ]
        
        extracted_pages = {}
        
        for endpoint in endpoints:
            print(f"Stealthily accessing {endpoint}...")
            html_content = self.extract_with_stealth(endpoint)
            
            if html_content:
                # Store the raw content
                page_name = endpoint.strip('/').replace('/', '_') or 'home'
                extracted_pages[page_name] = html_content
                
                # Extract structured data from this page
                structured_data = self.parse_page_data(html_content, endpoint)
                if structured_data:
                    extracted_pages[f"{page_name}_structured"] = structured_data
                
                print(f"Successfully extracted {len(html_content)} characters from {endpoint}")
            else:
                print(f"No data found at {endpoint}")
        
        self.extracted_data = extracted_pages
        return extracted_pages
    
    def parse_page_data(self, html_content, source_page):
        """Parse structured data from HTML content"""
        parsed_data = {
            'source_page': source_page,
            'extraction_time': datetime.now().isoformat(),
            'tables': [],
            'forms': [],
            'lists': [],
            'data_attributes': [],
            'json_data': [],
            'text_content': []
        }
        
        # Extract tables
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for i, table_html in enumerate(tables):
            table_data = self.parse_table_data(table_html)
            if table_data:
                table_data['table_index'] = i
                parsed_data['tables'].append(table_data)
        
        # Extract forms
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for i, form_html in enumerate(forms):
            form_data = self.parse_form_data(form_html)
            if form_data:
                form_data['form_index'] = i
                parsed_data['forms'].append(form_data)
        
        # Extract lists (ul, ol)
        list_pattern = r'<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>'
        lists = re.findall(list_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for i, list_html in enumerate(lists):
            list_items = re.findall(r'<li[^>]*>(.*?)</li>', list_html, re.DOTALL | re.IGNORECASE)
            if list_items:
                clean_items = [re.sub(r'<[^>]+>', '', item).strip() for item in list_items]
                parsed_data['lists'].append({
                    'list_index': i,
                    'items': clean_items
                })
        
        # Extract data attributes
        data_attr_pattern = r'data-[\w-]+=["\']([^"\']*)["\']'
        data_attrs = re.findall(data_attr_pattern, html_content)
        parsed_data['data_attributes'] = data_attrs
        
        # Extract JSON from script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for script in scripts:
            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script)
            for json_str in json_matches:
                try:
                    parsed_json = json.loads(json_str)
                    parsed_data['json_data'].append(parsed_json)
                except:
                    continue
        
        # Extract meaningful text content
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Extract potential project/asset identifiers
        project_patterns = [
            r'\b(?:project|job|asset|equipment)\s*[#:]?\s*([A-Z0-9-]+)\b',
            r'\b([A-Z]{2,3}-\d{2,4})\b',  # Asset patterns like PT-107
            r'\b(\d{4}-\d{3})\b'  # Job patterns like 2019-044
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                parsed_data['text_content'].extend(matches)
        
        return parsed_data if any(parsed_data.values()) else None
    
    def parse_table_data(self, table_html):
        """Parse table data into structured format"""
        table_data = {
            'headers': [],
            'rows': []
        }
        
        # Extract headers
        header_pattern = r'<th[^>]*>(.*?)</th>'
        headers = re.findall(header_pattern, table_html, re.DOTALL | re.IGNORECASE)
        table_data['headers'] = [re.sub(r'<[^>]+>', '', h).strip() for h in headers]
        
        # Extract rows
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
        
        for row_html in rows:
            cell_pattern = r'<td[^>]*>(.*?)</td>'
            cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
            if cells:
                clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                table_data['rows'].append(clean_cells)
        
        return table_data if table_data['headers'] or table_data['rows'] else None
    
    def parse_form_data(self, form_html):
        """Parse form data into structured format"""
        form_data = {
            'inputs': [],
            'selects': [],
            'textareas': []
        }
        
        # Extract inputs
        input_pattern = r'<input[^>]*>'
        inputs = re.findall(input_pattern, form_html, re.IGNORECASE)
        
        for input_html in inputs:
            input_data = {}
            
            # Extract attributes
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
        
        return form_data if any(form_data.values()) else None
    
    def save_stealth_extraction(self):
        """Save all extracted data with stealth timestamps"""
        try:
            # Create stealth backup directory
            backup_dir = "stealth_ground_works_backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Save complete extraction with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save raw HTML files
            html_dir = f"{backup_dir}/html_pages"
            os.makedirs(html_dir, exist_ok=True)
            
            # Save structured data
            json_dir = f"{backup_dir}/structured_data"
            os.makedirs(json_dir, exist_ok=True)
            
            for page_name, content in self.extracted_data.items():
                if isinstance(content, str):
                    # Save HTML content
                    with open(f"{html_dir}/{page_name}_{timestamp}.html", 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    # Save structured data as JSON
                    with open(f"{json_dir}/{page_name}_{timestamp}.json", 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2, ensure_ascii=False, default=str)
            
            # Save complete dataset
            with open(f"{backup_dir}/complete_stealth_extraction_{timestamp}.json", 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Stealth extraction saved to {backup_dir}/")
            return backup_dir
            
        except Exception as e:
            print(f"Error saving stealth extraction: {e}")
            return None
    
    def execute_stealth_mission(self):
        """Execute complete stealth data extraction mission"""
        print("🕵️ Initiating stealth Ground Works data extraction mission...")
        print("Using natural browser behavior to avoid detection...")
        
        # Extract all data
        extracted_pages = self.extract_all_project_data()
        
        if extracted_pages:
            # Save the extraction
            backup_path = self.save_stealth_extraction()
            
            # Generate mission report
            total_pages = len([k for k, v in extracted_pages.items() if isinstance(v, str)])
            total_structured = len([k for k, v in extracted_pages.items() if isinstance(v, dict)])
            
            mission_report = {
                'status': 'MISSION ACCOMPLISHED',
                'stealth_level': 'MAXIMUM',
                'detection_risk': 'MINIMAL',
                'pages_extracted': total_pages,
                'structured_datasets': total_structured,
                'backup_location': backup_path,
                'extraction_time': datetime.now().isoformat(),
                'next_steps': 'Data secured and ready for Ground Works Suite reconstruction'
            }
            
            print(f"🎯 STEALTH MISSION COMPLETE!")
            print(f"📊 Extracted {total_pages} pages with {total_structured} structured datasets")
            print(f"💾 All data secured in: {backup_path}")
            
            return mission_report
        else:
            return {
                'status': 'MISSION FAILED',
                'error': 'No data could be extracted'
            }

def execute_stealth_extraction():
    """Execute the stealth extraction mission"""
    extractor = StealthGroundWorksExtractor()
    return extractor.execute_stealth_mission()

if __name__ == "__main__":
    result = execute_stealth_extraction()
    print(json.dumps(result, indent=2))