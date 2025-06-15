"""
Enhanced Ground Works Data Extractor
Extracts data from authenticated browser session
"""

import requests
import re
import json
import time
from datetime import datetime
import os

class EnhancedGroundWorksExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://groundworks.ragleinc.com"
        self.extracted_data = {
            'projects': [],
            'raw_html_data': {},
            'extracted_tables': [],
            'forms_data': [],
            'scripts_data': [],
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'source': 'authenticated_session'
            }
        }
        
    def extract_projects_page(self):
        """Extract all data from the projects page"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            if response.status_code == 200:
                html_content = response.text
                
                # Store raw HTML for analysis
                self.extracted_data['raw_html_data']['projects_page'] = html_content
                
                # Extract all tables
                tables = self.extract_all_tables(html_content)
                self.extracted_data['extracted_tables'].extend(tables)
                
                # Extract all forms
                forms = self.extract_all_forms(html_content)
                self.extracted_data['forms_data'].extend(forms)
                
                # Extract JavaScript data
                scripts = self.extract_script_data(html_content)
                self.extracted_data['scripts_data'].extend(scripts)
                
                # Extract project-specific patterns
                projects = self.extract_project_patterns(html_content)
                self.extracted_data['projects'].extend(projects)
                
                print(f"Projects page extracted: {len(tables)} tables, {len(forms)} forms, {len(scripts)} scripts")
                return True
                
        except Exception as e:
            print(f"Error extracting projects page: {e}")
            
        return False
    
    def extract_all_tables(self, html_content):
        """Extract all table data from HTML"""
        tables = []
        table_matches = re.findall(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
        
        for i, table_html in enumerate(table_matches):
            table_data = {
                'table_id': f"table_{i}",
                'headers': [],
                'rows': [],
                'raw_html': table_html[:500]  # First 500 chars for reference
            }
            
            # Extract headers
            header_matches = re.findall(r'<th[^>]*>(.*?)</th>', table_html, re.DOTALL | re.IGNORECASE)
            for header in header_matches:
                clean_header = re.sub(r'<[^>]+>', '', header).strip()
                if clean_header:
                    table_data['headers'].append(clean_header)
            
            # Extract rows
            row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            for row_html in row_matches:
                cell_matches = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL | re.IGNORECASE)
                row_data = []
                for cell in cell_matches:
                    clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                    row_data.append(clean_cell)
                if row_data:
                    table_data['rows'].append(row_data)
            
            if table_data['headers'] or table_data['rows']:
                tables.append(table_data)
        
        return tables
    
    def extract_all_forms(self, html_content):
        """Extract all form data from HTML"""
        forms = []
        form_matches = re.findall(r'<form[^>]*>(.*?)</form>', html_content, re.DOTALL | re.IGNORECASE)
        
        for i, form_html in enumerate(form_matches):
            form_data = {
                'form_id': f"form_{i}",
                'action': '',
                'method': '',
                'inputs': [],
                'selects': [],
                'textareas': []
            }
            
            # Extract form attributes
            action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
            if action_match:
                form_data['action'] = action_match.group(1)
            
            method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
            if method_match:
                form_data['method'] = method_match.group(1)
            
            # Extract inputs
            input_matches = re.findall(r'<input[^>]*>', form_html, re.IGNORECASE)
            for input_html in input_matches:
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
            
            forms.append(form_data)
        
        return forms
    
    def extract_script_data(self, html_content):
        """Extract JavaScript data and variables"""
        scripts = []
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
        
        for i, script_content in enumerate(script_matches):
            script_data = {
                'script_id': f"script_{i}",
                'variables': [],
                'json_objects': [],
                'api_calls': []
            }
            
            # Extract variable declarations
            var_matches = re.findall(r'(?:var|let|const)\s+(\w+)\s*=\s*([^;]+);', script_content)
            for var_name, var_value in var_matches:
                script_data['variables'].append({'name': var_name, 'value': var_value.strip()})
            
            # Extract JSON objects
            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_content)
            for json_str in json_matches:
                try:
                    parsed_json = json.loads(json_str)
                    script_data['json_objects'].append(parsed_json)
                except:
                    # Store as string if not valid JSON
                    if len(json_str) < 200:  # Only store short strings
                        script_data['json_objects'].append(json_str)
            
            # Extract API calls
            api_matches = re.findall(r'(?:fetch|axios|ajax)\s*\(\s*["\']([^"\']*)["\']', script_content, re.IGNORECASE)
            for api_url in api_matches:
                script_data['api_calls'].append(api_url)
            
            if script_data['variables'] or script_data['json_objects'] or script_data['api_calls']:
                scripts.append(script_data)
        
        return scripts
    
    def extract_project_patterns(self, html_content):
        """Extract project-specific data patterns"""
        projects = []
        
        # Look for common project data patterns
        project_patterns = [
            r'project["\']?\s*:\s*["\']([^"\']*)["\']',
            r'name["\']?\s*:\s*["\']([^"\']*)["\']',
            r'id["\']?\s*:\s*["\']?(\d+)["\']?',
            r'status["\']?\s*:\s*["\']([^"\']*)["\']'
        ]
        
        # Extract data attributes
        data_attrs = re.findall(r'data-[\w-]+=["\']([^"\']*)["\']', html_content)
        
        # Extract any structured data in spans, divs with specific classes
        structured_matches = re.findall(r'<(?:span|div)[^>]*class=["\'][^"\']*(?:project|name|id|status)[^"\']*["\'][^>]*>([^<]*)</(?:span|div)>', html_content, re.IGNORECASE)
        
        # Combine all extracted data
        all_extracted = data_attrs + structured_matches
        
        # Group data into potential projects
        for i in range(0, len(all_extracted), 3):  # Group by 3s
            if i + 2 < len(all_extracted):
                project = {
                    'extracted_id': f"extracted_{i//3}",
                    'field_1': all_extracted[i],
                    'field_2': all_extracted[i+1],
                    'field_3': all_extracted[i+2],
                    'source': 'pattern_extraction'
                }
                projects.append(project)
        
        return projects
    
    def scan_additional_pages(self):
        """Scan additional pages for data"""
        additional_pages = [
            '/dashboard',
            '/reports',
            '/admin',
            '/users',
            '/settings',
            '/assets',
            '/equipment',
            '/billing'
        ]
        
        for page in additional_pages:
            try:
                response = self.session.get(f"{self.base_url}{page}")
                if response.status_code == 200:
                    # Store page content
                    page_name = page.strip('/').replace('/', '_') or 'dashboard'
                    self.extracted_data['raw_html_data'][f"{page_name}_page"] = response.text
                    
                    # Extract tables from this page
                    tables = self.extract_all_tables(response.text)
                    for table in tables:
                        table['source_page'] = page
                    self.extracted_data['extracted_tables'].extend(tables)
                    
                    print(f"Scanned {page}: {len(tables)} tables found")
                    
            except Exception as e:
                print(f"Error scanning {page}: {e}")
    
    def save_all_data(self):
        """Save all extracted data"""
        try:
            # Create backup directory
            backup_dir = "ground_works_complete_backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Save complete extraction
            with open(f"{backup_dir}/complete_extraction.json", 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Save individual components
            for key, data in self.extracted_data.items():
                if data and key != 'raw_html_data':
                    with open(f"{backup_dir}/{key}.json", 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Save raw HTML separately
            html_dir = f"{backup_dir}/raw_html"
            os.makedirs(html_dir, exist_ok=True)
            
            for page_name, html_content in self.extracted_data['raw_html_data'].items():
                with open(f"{html_dir}/{page_name}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            print(f"All data saved to {backup_dir}/")
            return backup_dir
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return None
    
    def execute_complete_extraction(self):
        """Execute complete data extraction"""
        print("Starting enhanced Ground Works data extraction...")
        
        # Extract main projects page
        if not self.extract_projects_page():
            print("Failed to extract projects page")
            return None
        
        # Scan additional pages
        self.scan_additional_pages()
        
        # Save all data
        backup_path = self.save_all_data()
        
        # Generate summary
        summary = {
            'total_tables': len(self.extracted_data['extracted_tables']),
            'total_forms': len(self.extracted_data['forms_data']),
            'total_scripts': len(self.extracted_data['scripts_data']),
            'total_projects': len(self.extracted_data['projects']),
            'pages_scanned': len(self.extracted_data['raw_html_data']),
            'backup_location': backup_path
        }
        
        print(f"Extraction complete: {summary}")
        return summary

def main():
    extractor = EnhancedGroundWorksExtractor()
    return extractor.execute_complete_extraction()

if __name__ == "__main__":
    result = main()
    if result:
        print(json.dumps(result, indent=2))