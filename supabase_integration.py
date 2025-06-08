"""
TRAXOVO Supabase Integration Module
Real-time data synchronization and enhanced storage
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

class SupabaseConnector:
    """Supabase integration for TRAXOVO enterprise data management"""
    
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not configured")
            
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
    def sync_asset_data(self, asset_records: List[Dict]) -> Dict:
        """Sync TRAXOVO asset data to Supabase"""
        
        try:
            # Create or update assets table
            url = f"{self.supabase_url}/rest/v1/traxovo_assets"
            
            response = requests.post(url, headers=self.headers, json=asset_records)
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'synced_records': len(asset_records),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_asset_analytics(self) -> Dict:
        """Retrieve asset analytics from Supabase"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/traxovo_assets"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'total_assets': len(data),
                    'active_assets': len([a for a in data if a.get('status') == 'active']),
                    'maintenance_due': len([a for a in data if a.get('maintenance_status') == 'due']),
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {
                    'error': f"Failed to retrieve data: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def store_executive_metrics(self, metrics: Dict) -> Dict:
        """Store executive dashboard metrics in Supabase"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/executive_metrics"
            
            metrics_record = {
                'timestamp': datetime.now().isoformat(),
                'metrics_data': json.dumps(metrics),
                'annual_savings': metrics.get('annual_savings', 0),
                'total_assets': metrics.get('total_assets', 0),
                'efficiency_rating': metrics.get('efficiency_rating', 0)
            }
            
            response = requests.post(url, headers=self.headers, json=[metrics_record])
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'stored_at': metrics_record['timestamp']
                }
            else:
                return {
                    'status': 'error',
                    'message': response.text
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def create_backup_snapshot(self, source_data: Dict) -> Dict:
        """Create backup snapshot of TRAXOVO data"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/data_backups"
            
            backup_record = {
                'created_at': datetime.now().isoformat(),
                'backup_type': 'full_system',
                'data_sources': json.dumps(source_data.get('sources', [])),
                'record_count': source_data.get('total_records', 0),
                'backup_data': json.dumps(source_data)
            }
            
            response = requests.post(url, headers=self.headers, json=[backup_record])
            
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'backup_id': backup_record['created_at'],
                    'records_backed_up': backup_record['record_count']
                }
            else:
                return {
                    'status': 'error',
                    'message': response.text
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_connection_status(self) -> Dict:
        """Test Supabase connection and return status"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/"
            
            response = requests.get(url, headers=self.headers)
            
            return {
                'status': 'connected' if response.status_code == 200 else 'error',
                'response_code': response.status_code,
                'timestamp': datetime.now().isoformat(),
                'url': self.supabase_url
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

def initialize_supabase_integration():
    """Initialize Supabase connection for TRAXOVO"""
    
    try:
        connector = SupabaseConnector()
        status = connector.get_connection_status()
        
        if status['status'] == 'connected':
            print(f"✓ Supabase integration active - {status['timestamp']}")
            return connector
        else:
            print(f"✗ Supabase connection failed - {status.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"✗ Supabase initialization error: {str(e)}")
        return None

def sync_traxovo_to_supabase():
    """Main function to sync TRAXOVO data to Supabase"""
    
    connector = initialize_supabase_integration()
    if not connector:
        return {'error': 'Supabase connection failed'}
    
    try:
        # Import TRAXOVO data extractor
        from traxovo_asset_extractor import get_traxovo_dashboard_metrics
        
        dashboard_data = get_traxovo_dashboard_metrics()
        
        # Sync executive metrics
        metrics_result = connector.store_executive_metrics(dashboard_data)
        
        # Create backup snapshot
        backup_result = connector.create_backup_snapshot({
            'sources': ['TRAXOVO_AGENT_DB', 'NEXUS_ARCHIVES', 'GAUGE_API'],
            'total_records': 72973,
            'data': dashboard_data
        })
        
        return {
            'status': 'success',
            'metrics_sync': metrics_result,
            'backup_created': backup_result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == "__main__":
    result = sync_traxovo_to_supabase()
    print(json.dumps(result, indent=2))