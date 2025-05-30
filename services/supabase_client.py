"""
Supabase Client Service
Connects to authentic TRAXOVO database
"""

import os
import logging
from typing import Optional, Dict, Any, List

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase client not available. Install with: pip install supabase")

class SupabaseClient:
    """Supabase database client for authentic data"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connected = False
        
        if SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with environment credentials"""
        try:
            url = os.environ.get('SUPABASE_URL')
            key = os.environ.get('SUPABASE_ANON_KEY')
            
            if not url or not key:
                logging.error("SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")
                return
            
            self.client = create_client(url, key)
            self.connected = True
            logging.info("Supabase client initialized successfully")
            
        except Exception as e:
            logging.error(f"Supabase initialization error: {e}")
            self.connected = False
    
    def get_authentic_metrics(self) -> Dict[str, Any]:
        """Get authentic fleet metrics from Supabase"""
        if not self.connected:
            return self._get_fallback_metrics()
        
        try:
            # Get asset counts
            assets_response = self.client.table('assets').select('id,active,billable').execute()
            assets = assets_response.data if assets_response.data else []
            
            total_assets = len(assets)
            active_assets = len([a for a in assets if a.get('active', False)])
            billable_assets = len([a for a in assets if a.get('billable', False)])
            
            # Get revenue data
            revenue_response = self.client.table('revenue_records').select('amount,date').execute()
            revenue_records = revenue_response.data if revenue_response.data else []
            
            current_month_revenue = sum(r.get('amount', 0) for r in revenue_records)
            
            # Get utilization data
            utilization_response = self.client.table('utilization_metrics').select('rate').execute()
            utilization_data = utilization_response.data if utilization_data else []
            
            avg_utilization = sum(u.get('rate', 0) for u in utilization_data) / len(utilization_data) if utilization_data else 0
            
            return {
                'total_assets': total_assets,
                'active_assets': min(active_assets, total_assets),  # Ensure active <= total
                'billable_assets': billable_assets,
                'monthly_revenue': current_month_revenue,
                'utilization_rate': min(avg_utilization, 100.0),  # Cap at 100%
                'data_source': 'supabase_authentic',
                'last_updated': 'real_time'
            }
            
        except Exception as e:
            logging.error(f"Supabase query error: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Fallback metrics when Supabase unavailable"""
        return {
            'total_assets': 0,
            'active_assets': 0,
            'billable_assets': 0,
            'monthly_revenue': 0,
            'utilization_rate': 0.0,
            'data_source': 'fallback_placeholder',
            'last_updated': 'unavailable'
        }
    
    def get_metric_drill_down(self, metric_type: str) -> Dict[str, Any]:
        """Get detailed breakdown of how a metric was calculated"""
        if not self.connected:
            return {'error': 'Database connection unavailable'}
        
        try:
            if metric_type == 'revenue':
                response = self.client.table('revenue_records').select('*').order('date', desc=True).limit(50).execute()
                records = response.data if response.data else []
                
                return {
                    'metric': 'Monthly Revenue',
                    'total': sum(r.get('amount', 0) for r in records),
                    'breakdown': records,
                    'calculation_method': 'Sum of all revenue records for current month',
                    'data_points': len(records)
                }
            
            elif metric_type == 'assets':
                response = self.client.table('assets').select('*').execute()
                assets = response.data if response.data else []
                
                return {
                    'metric': 'Asset Counts',
                    'total_assets': len(assets),
                    'active_assets': len([a for a in assets if a.get('active', False)]),
                    'billable_assets': len([a for a in assets if a.get('billable', False)]),
                    'breakdown': assets,
                    'calculation_method': 'Count of records in assets table by status',
                    'data_points': len(assets)
                }
            
            elif metric_type == 'utilization':
                response = self.client.table('utilization_metrics').select('*').order('date', desc=True).limit(30).execute()
                utilization_data = response.data if response.data else []
                
                avg_rate = sum(u.get('rate', 0) for u in utilization_data) / len(utilization_data) if utilization_data else 0
                
                return {
                    'metric': 'Fleet Utilization',
                    'average_rate': avg_rate,
                    'breakdown': utilization_data,
                    'calculation_method': 'Average of daily utilization rates over past 30 days',
                    'data_points': len(utilization_data)
                }
            
            else:
                return {'error': f'Unknown metric type: {metric_type}'}
                
        except Exception as e:
            logging.error(f"Drill-down query error: {e}")
            return {'error': str(e)}

# Global instance
_supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client