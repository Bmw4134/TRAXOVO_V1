"""
TRAXOVO Smart Equipment Lookup System
Natural language search across all fleet data sources
"""
import pandas as pd
import json
import re
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime

smart_lookup_bp = Blueprint('smart_lookup', __name__, url_prefix='/smart-lookup')

class SmartEquipmentSearch:
    def __init__(self):
        self.data_sources = {
            'billing_files': [
                'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
                'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
            ],
            'api_data': 'GAUGE API PULL 1045AM_05.15.2025.json'
        }
        
    def smart_search(self, query):
        """
        Intelligent equipment search using natural language
        Example queries: "375 air compressors", "Sullair equipment", "excavators", "AC-22"
        """
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'found_equipment': [],
            'total_matches': 0,
            'search_summary': ''
        }
        
        # Parse the query for equipment types and identifiers
        query_lower = query.lower()
        search_terms = self._extract_search_terms(query_lower)
        
        # Search billing files
        billing_results = self._search_billing_files(search_terms)
        results['found_equipment'].extend(billing_results)
        
        # Search API data
        api_results = self._search_api_data(search_terms)
        results['found_equipment'].extend(api_results)
        
        # Remove duplicates and summarize
        results['found_equipment'] = self._deduplicate_results(results['found_equipment'])
        results['total_matches'] = len(results['found_equipment'])
        results['search_summary'] = self._generate_summary(query, results['found_equipment'])
        
        return results
    
    def _extract_search_terms(self, query):
        """Extract meaningful search terms from natural language query"""
        terms = {
            'equipment_types': [],
            'models': [],
            'makes': [],
            'identifiers': [],
            'specifications': []
        }
        
        # Equipment type patterns
        if any(term in query for term in ['air compressor', 'compressor']):
            terms['equipment_types'].append('compressor')
        if any(term in query for term in ['excavator', 'excavation']):
            terms['equipment_types'].append('excavator')
        if any(term in query for term in ['dozer', 'bulldozer']):
            terms['equipment_types'].append('dozer')
        if any(term in query for term in ['loader', 'wheel loader']):
            terms['equipment_types'].append('loader')
            
        # Extract model numbers
        model_pattern = r'\b\d{3,4}\b'
        models = re.findall(model_pattern, query)
        terms['models'].extend(models)
        
        # Extract asset identifiers
        id_pattern = r'\b[A-Z]{2,3}-\d+\b'
        identifiers = re.findall(id_pattern, query.upper())
        terms['identifiers'].extend(identifiers)
        
        # Extract makes
        if 'sullair' in query:
            terms['makes'].append('sullair')
        if any(make in query for make in ['caterpillar', 'cat', 'john deere', 'jd']):
            terms['makes'].extend(['caterpillar', 'cat', 'john deere', 'jd'])
            
        # Extract specifications
        if 'cfm' in query:
            terms['specifications'].append('cfm')
        if 'psi' in query:
            terms['specifications'].append('psi')
            
        return terms
    
    def _search_billing_files(self, search_terms):
        """Search through equipment billing files"""
        results = []
        
        for file_path in self.data_sources['billing_files']:
            try:
                sheets = pd.read_excel(file_path, sheet_name=None)
                
                for sheet_name, df in sheets.items():
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            for idx, value in enumerate(df[col]):
                                if pd.notna(value):
                                    text = str(value).strip()
                                    if self._matches_search_terms(text, search_terms):
                                        results.append({
                                            'source': f'{file_path} - {sheet_name}',
                                            'description': text,
                                            'type': 'billing_record',
                                            'row': idx + 1,
                                            'column': col
                                        })
                                        
            except Exception as e:
                continue
                
        return results
    
    def _search_api_data(self, search_terms):
        """Search through Gauge API data"""
        results = []
        
        try:
            with open(self.data_sources['api_data'], 'r') as f:
                api_data = json.load(f)
            
            for item in api_data:
                if isinstance(item, dict):
                    # Combine all relevant fields for search
                    searchable_text = ' '.join([
                        str(item.get('Label', '')),
                        str(item.get('AssetModel', '')),
                        str(item.get('AssetMake', '')),
                        str(item.get('AssetCategory', '')),
                        str(item.get('AssetIdentifier', ''))
                    ])
                    
                    if self._matches_search_terms(searchable_text, search_terms):
                        results.append({
                            'source': 'Gauge API',
                            'description': item.get('Label', 'No Label'),
                            'type': 'live_asset',
                            'asset_id': item.get('AssetIdentifier', 'Unknown'),
                            'make': item.get('AssetMake', ''),
                            'model': item.get('AssetModel', ''),
                            'category': item.get('AssetCategory', ''),
                            'location': item.get('Location', ''),
                            'status': 'Active' if item.get('Active') else 'Inactive'
                        })
                        
        except Exception as e:
            pass
            
        return results
    
    def _matches_search_terms(self, text, search_terms):
        """Check if text matches the extracted search terms"""
        text_lower = text.lower()
        
        # Check equipment types
        for eq_type in search_terms['equipment_types']:
            if eq_type in text_lower:
                # Additional checks for specific models if provided
                if search_terms['models']:
                    for model in search_terms['models']:
                        if model in text:
                            return True
                else:
                    return True
        
        # Check for specific identifiers
        for identifier in search_terms['identifiers']:
            if identifier in text.upper():
                return True
        
        # Check for makes
        for make in search_terms['makes']:
            if make in text_lower:
                if search_terms['models']:
                    for model in search_terms['models']:
                        if model in text:
                            return True
                else:
                    return True
        
        return False
    
    def _deduplicate_results(self, results):
        """Remove duplicate entries"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = result['description'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                
        return unique_results
    
    def _generate_summary(self, query, results):
        """Generate a human-readable summary of search results"""
        if not results:
            return f"No equipment found matching '{query}'"
        
        count = len(results)
        equipment_types = set()
        
        for result in results:
            desc = result['description'].lower()
            if 'compressor' in desc:
                equipment_types.add('air compressors')
            elif 'excavator' in desc:
                equipment_types.add('excavators')
            elif 'dozer' in desc:
                equipment_types.add('dozers')
            elif 'loader' in desc:
                equipment_types.add('loaders')
                
        types_str = ', '.join(equipment_types) if equipment_types else 'equipment units'
        return f"Found {count} {types_str} matching '{query}'"

# Initialize the search engine
search_engine = SmartEquipmentSearch()

@smart_lookup_bp.route('/')
def index():
    """Smart lookup dashboard"""
    return render_template('smart_lookup/dashboard.html')

@smart_lookup_bp.route('/search', methods=['POST'])
def search_equipment():
    """API endpoint for smart equipment search"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    results = search_engine.smart_search(query)
    return jsonify(results)

@smart_lookup_bp.route('/quick-search/<query>')
def quick_search(query):
    """Quick search endpoint for URL-based queries"""
    results = search_engine.smart_search(query)
    return jsonify(results)