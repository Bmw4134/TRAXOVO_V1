"""
Rapid Ground Works Data Extractor
Fast stealth extraction without delays
"""

import requests
import json
import os
from datetime import datetime
import re

class RapidGroundWorksExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://groundworks.ragleinc.com"
        
        # Edge browser headers for authentication
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session.headers.update(self.headers)
        self.extracted_data = {}
        
    def rapid_extract(self):
        """Rapid extraction of all Ground Works data"""
        print("Starting rapid Ground Works data extraction...")
        
        # Primary endpoints to extract
        endpoints = [
            '/projects',
            '/dashboard', 
            '/admin',
            '/reports',
            '/users',
            '/settings',
            '/equipment',
            '/assets',
            '/billing',
            '/'
        ]
        
        extracted_pages = {}
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    page_name = endpoint.strip('/').replace('/', '_') or 'home'
                    extracted_pages[page_name] = response.text
                    
                    # Extract structured data immediately
                    structured = self.extract_structured_data(response.text, endpoint)
                    if structured:
                        extracted_pages[f"{page_name}_data"] = structured
                    
                    print(f"Extracted {endpoint}: {len(response.text)} chars")
                
            except Exception as e:
                print(f"Skip {endpoint}: {str(e)[:50]}")
                continue
        
        self.extracted_data = extracted_pages
        return extracted_pages
    
    def extract_structured_data(self, html_content, source):
        """Extract all structured data from HTML"""
        data = {
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'projects': [],
            'assets': [],
            'users': [],
            'tables': [],
            'forms': [],
            'json_data': []
        }
        
        # Extract project patterns
        project_patterns = [
            r'(?:project|job)\s*[#:]?\s*([A-Z0-9-]+)',
            r'\b([A-Z]{2,3}-\d{2,4})\b',  # PT-107, SS-09
            r'\b(\d{4}-\d{3})\b',         # 2019-044
            r'(?:name|title)["\']\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            data['projects'].extend(matches)
        
        # Extract asset patterns
        asset_patterns = [
            r'(?:asset|equipment|vehicle)\s*[#:]?\s*([A-Z0-9-]+)',
            r'\b([A-Z]{2}-\d{2,4})\b',
            r'(?:truck|equipment|asset).*?([A-Z0-9-]+)'
        ]
        
        for pattern in asset_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            data['assets'].extend(matches)
        
        # Extract tables
        table_matches = re.findall(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL)
        for i, table_html in enumerate(table_matches):
            table_data = self.parse_table_fast(table_html)
            if table_data:
                table_data['table_id'] = i
                data['tables'].append(table_data)
        
        # Extract forms
        form_matches = re.findall(r'<form[^>]*>(.*?)</form>', html_content, re.DOTALL)
        for i, form_html in enumerate(form_matches):
            form_data = self.parse_form_fast(form_html)
            if form_data:
                form_data['form_id'] = i
                data['forms'].append(form_data)
        
        # Extract JSON from scripts
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        for script in script_matches:
            json_matches = re.findall(r'\{[^{}]*\}', script)
            for json_str in json_matches:
                try:
                    parsed = json.loads(json_str)
                    data['json_data'].append(parsed)
                except:
                    continue
        
        # Extract user/personnel data
        user_patterns = [
            r'(?:user|employee|staff|person)["\']\s*:\s*["\']([^"\']+)["\']',
            r'(?:name|employee).*?([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'(?:email).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ]
        
        for pattern in user_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            data['users'].extend(matches)
        
        return data if any([data['projects'], data['assets'], data['tables'], data['forms'], data['json_data']]) else None
    
    def parse_table_fast(self, table_html):
        """Fast table parsing"""
        headers = re.findall(r'<th[^>]*>([^<]*)</th>', table_html, re.IGNORECASE)
        rows = []
        
        row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        for row_html in row_matches:
            cells = re.findall(r'<td[^>]*>([^<]*)</td>', row_html, re.IGNORECASE)
            if cells:
                rows.append(cells)
        
        return {'headers': headers, 'rows': rows} if headers or rows else None
    
    def parse_form_fast(self, form_html):
        """Fast form parsing"""
        inputs = []
        input_matches = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', form_html, re.IGNORECASE)
        
        for name in input_matches:
            inputs.append({'name': name})
        
        return {'inputs': inputs} if inputs else None
    
    def save_extraction(self):
        """Save extracted data quickly"""
        try:
            backup_dir = "rapid_ground_works_backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete dataset
            with open(f"{backup_dir}/rapid_extraction_{timestamp}.json", 'w') as f:
                json.dump(self.extracted_data, f, indent=2, default=str)
            
            # Save individual pages
            for page_name, content in self.extracted_data.items():
                if isinstance(content, str):
                    with open(f"{backup_dir}/{page_name}_{timestamp}.html", 'w') as f:
                        f.write(content)
                else:
                    with open(f"{backup_dir}/{page_name}_{timestamp}.json", 'w') as f:
                        json.dump(content, f, indent=2, default=str)
            
            return backup_dir
            
        except Exception as e:
            print(f"Save error: {e}")
            return None
    
    def execute_rapid_extraction(self):
        """Execute rapid data extraction"""
        # Extract all data
        extracted = self.rapid_extract()
        
        if extracted:
            # Save immediately
            backup_path = self.save_extraction()
            
            # Count extracted data
            total_pages = len([k for k, v in extracted.items() if isinstance(v, str)])
            total_structured = len([k for k, v in extracted.items() if isinstance(v, dict)])
            
            # Count specific data types
            total_projects = 0
            total_assets = 0
            total_tables = 0
            
            for key, value in extracted.items():
                if isinstance(value, dict) and 'projects' in value:
                    total_projects += len(value['projects'])
                if isinstance(value, dict) and 'assets' in value:
                    total_assets += len(value['assets'])
                if isinstance(value, dict) and 'tables' in value:
                    total_tables += len(value['tables'])
            
            result = {
                'status': 'SUCCESS',
                'pages_extracted': total_pages,
                'structured_datasets': total_structured,
                'projects_found': total_projects,
                'assets_found': total_assets,
                'tables_found': total_tables,
                'backup_location': backup_path,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"RAPID EXTRACTION COMPLETE")
            print(f"Pages: {total_pages}, Data: {total_structured}")
            print(f"Projects: {total_projects}, Assets: {total_assets}, Tables: {total_tables}")
            print(f"Saved to: {backup_path}")
            
            return result
        else:
            return {'status': 'FAILED', 'error': 'No data extracted'}

def execute_rapid_mission():
    """Execute rapid Ground Works extraction"""
    extractor = RapidGroundWorksExtractor()
    return extractor.execute_rapid_extraction()

if __name__ == "__main__":
    result = execute_rapid_mission()
    print(json.dumps(result, indent=2))