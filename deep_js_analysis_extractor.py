"""
Deep JavaScript Analysis Extractor
Advanced analysis of Angular bundles to extract embedded data and discover hidden endpoints
"""

import requests
import re
import json
import logging
import base64
from urllib.parse import urljoin, unquote
import ast

class DeepJSAnalysisExtractor:
    """Deep analysis of JavaScript bundles for data extraction"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'reports': [],
            'billing': [],
            'embedded_configurations': {},
            'discovered_data': []
        }
        
        # Enhanced headers for deep analysis
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
    
    def deep_bundle_analysis(self):
        """Perform deep analysis of all JavaScript bundles"""
        try:
            # Get main page to discover bundles
            main_response = self.session.get(self.base_url, timeout=30)
            bundle_urls = self.extract_bundle_urls(main_response.text)
            
            all_extracted_data = []
            
            for bundle_url in bundle_urls:
                try:
                    bundle_response = self.session.get(bundle_url, timeout=30)
                    bundle_content = bundle_response.text
                    
                    # Multiple analysis techniques
                    embedded_data = self.extract_embedded_data_structures(bundle_content)
                    if embedded_data:
                        all_extracted_data.extend(embedded_data)
                    
                    config_data = self.extract_configuration_objects(bundle_content)
                    if config_data:
                        self.extracted_data['embedded_configurations'].update(config_data)
                    
                    api_data = self.extract_api_response_templates(bundle_content)
                    if api_data:
                        all_extracted_data.extend(api_data)
                    
                    hardcoded_data = self.extract_hardcoded_data_arrays(bundle_content)
                    if hardcoded_data:
                        all_extracted_data.extend(hardcoded_data)
                    
                except Exception as e:
                    logging.debug(f"Bundle analysis failed for {bundle_url}: {e}")
                    continue
            
            # Categorize all extracted data
            self.categorize_extracted_data(all_extracted_data)
            
            return {
                'status': 'success',
                'data': self.extracted_data,
                'extraction_summary': {
                    'bundles_analyzed': len(bundle_urls),
                    'data_structures_found': len(all_extracted_data),
                    'projects_extracted': len(self.extracted_data['projects']),
                    'assets_extracted': len(self.extracted_data['assets']),
                    'personnel_extracted': len(self.extracted_data['personnel']),
                    'reports_extracted': len(self.extracted_data['reports']),
                    'billing_extracted': len(self.extracted_data['billing']),
                    'configurations_found': len(self.extracted_data['embedded_configurations']),
                    'extraction_method': 'deep_js_bundle_analysis'
                }
            }
            
        except Exception as e:
            logging.error(f"Deep bundle analysis failed: {e}")
            return {
                'status': 'error',
                'message': f'Deep JavaScript analysis failed: {str(e)}'
            }
    
    def extract_bundle_urls(self, html_content):
        """Extract all JavaScript bundle URLs"""
        bundle_urls = []
        
        # Find script tags with src attributes
        script_patterns = [
            r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']',
            r'src\s*:\s*["\']([^"\']*\.js[^"\']*)["\']'
        ]
        
        for pattern in script_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    bundle_url = urljoin(self.base_url, match)
                elif match.startswith('http'):
                    bundle_url = match
                else:
                    bundle_url = urljoin(self.base_url, match)
                
                if bundle_url not in bundle_urls:
                    bundle_urls.append(bundle_url)
        
        return bundle_urls
    
    def extract_embedded_data_structures(self, js_content):
        """Extract embedded data structures from JavaScript"""
        data_structures = []
        
        # Look for large object/array definitions that might contain data
        patterns = [
            # Array of objects with typical data fields
            r'(\[{[^}]*(?:id|name|title|project|asset|user|employee)[^}]*}[^]]*\])',
            # Object definitions with data-like structures
            r'({[^}]*(?:id|name|title|project|asset|user|employee)[^}]*})',
            # JSON-like strings
            r'["\']({[^}]*(?:id|name|title|project|asset|user|employee)[^}]*})["\']',
            # Data assignment patterns
            r'(?:data|items|records|list)\s*[=:]\s*(\[[^\]]*\])',
            r'(?:data|items|records|list)\s*[=:]\s*({[^}]*})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Clean up the matched string
                    cleaned_match = self.clean_js_object(match)
                    if len(cleaned_match) > 50:  # Only process substantial data
                        parsed_data = self.safe_json_parse(cleaned_match)
                        if parsed_data:
                            data_structures.append(parsed_data)
                except Exception:
                    continue
        
        return data_structures
    
    def extract_configuration_objects(self, js_content):
        """Extract configuration objects that might contain useful data"""
        config_data = {}
        
        # Configuration patterns
        config_patterns = [
            r'(?:config|settings|environment|constants)\s*[=:]\s*({[^}]+})',
            r'\.config\s*=\s*({[^}]+})',
            r'CONFIG\s*[=:]\s*({[^}]+})',
            r'SETTINGS\s*[=:]\s*({[^}]+})'
        ]
        
        for pattern in config_patterns:
            matches = re.findall(pattern, js_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    cleaned_config = self.clean_js_object(match)
                    parsed_config = self.safe_json_parse(cleaned_config)
                    if parsed_config and isinstance(parsed_config, dict):
                        config_data.update(parsed_config)
                except Exception:
                    continue
        
        return config_data
    
    def extract_api_response_templates(self, js_content):
        """Extract API response templates or mock data"""
        response_data = []
        
        # Look for API response patterns
        response_patterns = [
            r'(?:mockData|sampleData|testData|defaultData)\s*[=:]\s*(\[[^\]]*\])',
            r'(?:mockData|sampleData|testData|defaultData)\s*[=:]\s*({[^}]*})',
            r'\.respond\s*\(\s*(\[[^\]]*\])',
            r'\.respond\s*\(\s*({[^}]*})',
            r'response\s*[=:]\s*(\[[^\]]*\])',
            r'response\s*[=:]\s*({[^}]*})'
        ]
        
        for pattern in response_patterns:
            matches = re.findall(pattern, js_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    cleaned_response = self.clean_js_object(match)
                    parsed_response = self.safe_json_parse(cleaned_response)
                    if parsed_response:
                        response_data.append(parsed_response)
                except Exception:
                    continue
        
        return response_data
    
    def extract_hardcoded_data_arrays(self, js_content):
        """Extract hardcoded data arrays that might contain real data"""
        hardcoded_data = []
        
        # Look for hardcoded arrays with data-like structures
        array_patterns = [
            r'\[\s*{[^}]*(?:id|name|title|project|asset|equipment|job|user|employee|driver|vehicle)[^}]*}[^]]*\]',
            r'(?:projects|assets|jobs|employees|users|drivers|vehicles|equipment)\s*[=:]\s*(\[[^\]]*\])'
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, js_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        match = match[0] if match else ''
                    
                    cleaned_array = self.clean_js_object(match)
                    if len(cleaned_array) > 100:  # Only process substantial arrays
                        parsed_array = self.safe_json_parse(cleaned_array)
                        if parsed_array and isinstance(parsed_array, list) and len(parsed_array) > 0:
                            hardcoded_data.extend(parsed_array)
                except Exception:
                    continue
        
        return hardcoded_data
    
    def clean_js_object(self, js_string):
        """Clean JavaScript object/array string for JSON parsing"""
        if not js_string:
            return ''
        
        # Remove JavaScript-specific syntax
        cleaned = js_string.strip()
        
        # Fix common JavaScript to JSON issues
        cleaned = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', cleaned)  # Quote unquoted keys
        cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)  # Replace single quotes with double quotes
        cleaned = re.sub(r'undefined', 'null', cleaned)  # Replace undefined with null
        cleaned = re.sub(r'new Date\([^)]*\)', '"date"', cleaned)  # Replace Date objects
        cleaned = re.sub(r'function[^}]*}', '"function"', cleaned)  # Replace functions
        cleaned = re.sub(r'//.*?\n', '', cleaned)  # Remove single-line comments
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # Remove multi-line comments
        
        return cleaned
    
    def safe_json_parse(self, json_string):
        """Safely parse JSON string with error handling"""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            try:
                # Try with ast.literal_eval for Python literals
                return ast.literal_eval(json_string)
            except (ValueError, SyntaxError):
                return None
    
    def categorize_extracted_data(self, all_data):
        """Categorize extracted data into appropriate sections"""
        for item in all_data:
            if isinstance(item, dict):
                self.categorize_single_item(item)
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, dict):
                        self.categorize_single_item(sub_item)
    
    def categorize_single_item(self, item):
        """Categorize a single data item"""
        if not isinstance(item, dict):
            return
        
        # Convert keys to lowercase for comparison
        item_keys = [key.lower() for key in item.keys()]
        item_str = str(item).lower()
        
        # Project/Job categorization
        if any(keyword in item_keys or keyword in item_str for keyword in [
            'project', 'job', 'jobid', 'project_id', 'job_number', 'contract',
            'site', 'location', 'work', 'construction'
        ]):
            self.extracted_data['projects'].append(item)
        
        # Asset/Equipment categorization
        elif any(keyword in item_keys or keyword in item_str for keyword in [
            'asset', 'equipment', 'vehicle', 'truck', 'machine', 'tool',
            'asset_id', 'equipment_id', 'vin', 'serial', 'make', 'model'
        ]):
            self.extracted_data['assets'].append(item)
        
        # Personnel categorization
        elif any(keyword in item_keys or keyword in item_str for keyword in [
            'employee', 'user', 'driver', 'worker', 'personnel', 'staff',
            'name', 'email', 'phone', 'employee_id', 'driver_id'
        ]):
            self.extracted_data['personnel'].append(item)
        
        # Report categorization
        elif any(keyword in item_keys or keyword in item_str for keyword in [
            'report', 'summary', 'analytics', 'dashboard', 'metric',
            'performance', 'utilization', 'efficiency'
        ]):
            self.extracted_data['reports'].append(item)
        
        # Billing categorization
        elif any(keyword in item_keys or keyword in item_str for keyword in [
            'billing', 'invoice', 'cost', 'expense', 'payment', 'revenue',
            'amount', 'price', 'rate', 'charge'
        ]):
            self.extracted_data['billing'].append(item)
        
        # General discovered data
        else:
            self.extracted_data['discovered_data'].append(item)

def execute_deep_js_analysis(username, password):
    """Execute deep JavaScript analysis extraction"""
    extractor = DeepJSAnalysisExtractor(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    return extractor.deep_bundle_analysis()