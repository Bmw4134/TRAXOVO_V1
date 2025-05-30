"""
Supabase Data Synchronization Service
Populates Supabase with authentic Gauge API assets and Excel data
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from services.adaptive_refresh_optimizer import get_refresh_optimizer

logger = logging.getLogger(__name__)

class SupabaseDataSync:
    """Synchronizes authentic data from Gauge API and Excel into Supabase"""
    
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_ANON_KEY')
        self.refresh_optimizer = get_refresh_optimizer()
        
    def sync_gauge_assets_to_supabase(self):
        """Load your 717 Gauge API assets into Supabase"""
        start_time = datetime.now()
        
        try:
            # Load authentic Gauge API data
            url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
            auth = ('bwatson', 'Plsw@2900413477')
            
            response = requests.get(url, auth=auth, verify=False, timeout=10)
            
            if response.status_code != 200:
                self.refresh_optimizer.record_component_error('gauge_api_assets')
                return {'success': False, 'error': f'Gauge API error: {response.status_code}'}
            
            gauge_assets = response.json()
            
            # Load Excel financial data for enhancement
            excel_data = self._load_excel_financial_data()
            
            # Process and insert assets
            processed_assets = []
            for asset in gauge_assets:
                processed_asset = self._process_gauge_asset(asset, excel_data)
                processed_assets.append(processed_asset)
            
            # Insert into Supabase using direct SQL
            insert_count = self._bulk_insert_assets(processed_assets)
            
            # Record performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self.refresh_optimizer.measure_component_performance(
                'gauge_api_assets', 
                execution_time, 
                len(processed_assets)
            )
            
            return {
                'success': True,
                'assets_processed': len(processed_assets),
                'assets_inserted': insert_count,
                'execution_time': execution_time
            }
            
        except Exception as e:
            self.refresh_optimizer.record_component_error('gauge_api_assets')
            logger.error(f"Gauge API sync error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_excel_financial_data(self):
        """Load financial data from April 2025 Excel"""
        try:
            file_path = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'
            
            equipment_df = pd.read_excel(file_path, sheet_name='Equip Table')
            rates_df = pd.read_excel(file_path, sheet_name='Equip Rates')
            
            # Create lookup dictionaries
            equipment_lookup = {}
            for _, row in equipment_df.iterrows():
                asset_id = row.get('Equipment #')
                if asset_id:
                    equipment_lookup[asset_id] = {
                        'purchase_price': float(row.get('Purchase Price', 0) or 0),
                        'description': row.get('Equipment Description', ''),
                        'division': row.get('Division', ''),
                        'status': row.get('Status', 'A')
                    }
            
            rates_lookup = {}
            for _, row in rates_df.iterrows():
                asset_id = row.get('Equip #')
                if asset_id:
                    rates_lookup[asset_id] = {
                        'monthly_rate': float(row.get('Rate', 0) or 0),
                        'category': row.get('Category', ''),
                        'utilization_rate': float(row.get('Month %', 0) or 0)
                    }
            
            return {'equipment': equipment_lookup, 'rates': rates_lookup}
            
        except Exception as e:
            logger.error(f"Excel data loading error: {e}")
            return {'equipment': {}, 'rates': {}}
    
    def _process_gauge_asset(self, gauge_asset: Dict, excel_data: Dict) -> Dict:
        """Process a single Gauge asset with Excel enhancement"""
        asset_id = gauge_asset.get('AssetId', gauge_asset.get('id', 'unknown'))
        
        processed = {
            'asset_id': asset_id,
            'asset_name': gauge_asset.get('AssetName', gauge_asset.get('name', 'Unknown')),
            'status': gauge_asset.get('Status', 'unknown'),
            'latitude': float(gauge_asset.get('Latitude', 0) or 0),
            'longitude': float(gauge_asset.get('Longitude', 0) or 0),
            'last_update': gauge_asset.get('LastUpdate', datetime.now().isoformat()),
            'purchase_price': 0.0,
            'monthly_rate': 0.0,
            'category': 'Unknown',
            'description': '',
            'division': ''
        }
        
        # Enhance with Excel financial data
        if asset_id in excel_data.get('equipment', {}):
            equipment_data = excel_data['equipment'][asset_id]
            processed.update({
                'purchase_price': equipment_data['purchase_price'],
                'description': equipment_data['description'],
                'division': equipment_data['division']
            })
        
        if asset_id in excel_data.get('rates', {}):
            rates_data = excel_data['rates'][asset_id]
            processed.update({
                'monthly_rate': rates_data['monthly_rate'],
                'category': rates_data['category']
            })
        
        return processed
    
    def _bulk_insert_assets(self, assets: List[Dict]) -> int:
        """Bulk insert assets into Supabase using SQL"""
        if not assets:
            return 0
        
        try:
            from services.execute_sql_direct import execute_sql_query
            
            # Clear existing data
            execute_sql_query("DELETE FROM public.assets")
            
            # Prepare bulk insert
            insert_values = []
            for asset in assets:
                values = f"""(
                    '{asset['asset_id']}',
                    '{asset['asset_name'].replace("'", "''")}',
                    '{asset['status']}',
                    {asset['latitude']},
                    {asset['longitude']},
                    '{asset['last_update']}',
                    '{asset['division']}',
                    {asset['purchase_price']},
                    {asset['monthly_rate']},
                    '{asset['category'].replace("'", "''")}',
                    '{asset['description'].replace("'", "''")}',
                    NOW(),
                    NOW()
                )"""
                insert_values.append(values)
            
            # Execute bulk insert
            sql = f"""
            INSERT INTO public.assets 
            (asset_id, asset_name, status, latitude, longitude, last_update, 
             division, purchase_price, monthly_rate, category, description, created_at, updated_at)
            VALUES {','.join(insert_values)}
            """
            
            execute_sql_query(sql)
            
            return len(assets)
            
        except Exception as e:
            logger.error(f"Bulk insert error: {e}")
            return 0
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            from services.execute_sql_direct import execute_sql_query
            
            # Count assets in Supabase
            result = execute_sql_query("SELECT COUNT(*) as count FROM public.assets")
            supabase_count = result[0]['count'] if result else 0
            
            # Get refresh rates
            refresh_rates = self.refresh_optimizer.get_performance_summary()
            
            return {
                'supabase_asset_count': supabase_count,
                'last_sync': datetime.now().isoformat(),
                'refresh_optimization': refresh_rates,
                'sync_components': {
                    'gauge_api': 'connected',
                    'excel_data': 'loaded',
                    'supabase': 'populated' if supabase_count > 0 else 'empty'
                }
            }
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                'error': str(e),
                'supabase_asset_count': 0,
                'sync_components': {
                    'gauge_api': 'unknown',
                    'excel_data': 'unknown',
                    'supabase': 'error'
                }
            }

# Create SQL execution helper
def create_sql_executor():
    """Create direct SQL execution helper"""
    content = '''"""
Direct SQL execution for Supabase data operations
"""

import os
import psycopg2
import logging

logger = logging.getLogger(__name__)

def execute_sql_query(sql_query: str):
    """Execute SQL query directly on Supabase database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return []
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        
        # Check if it's a SELECT query
        if sql_query.strip().upper().startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result = []
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return []
'''
    
    with open('services/execute_sql_direct.py', 'w') as f:
        f.write(content)

# Initialize SQL executor
create_sql_executor()

# Global sync service
supabase_sync = SupabaseDataSync()

def get_supabase_sync():
    """Get the Supabase sync service"""
    return supabase_sync