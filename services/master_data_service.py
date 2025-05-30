"""
Master Data Service - Consolidated authentic data management
"""

import os
import logging
import requests
from datetime import datetime
from services.execute_sql_direct import execute_sql_query

logger = logging.getLogger(__name__)

class MasterDataService:
    """Centralized service for all authentic data operations"""
    
    def __init__(self):
        self.gauge_api_url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
        self.gauge_auth = ('bwatson', 'Plsw@2900413477')
        
    def get_authentic_assets(self):
        """Get authentic assets from database"""
        try:
            assets = execute_sql_query("""
                SELECT asset_id, name, type, make, model, year, status, 
                       latitude, longitude, notes, division
                FROM public.assets 
                WHERE is_active = true
                ORDER BY asset_id
            """)
            return assets
        except Exception as e:
            logger.error(f"Database assets query error: {e}")
            return []
    
    def get_attendance_matrix_data(self, date_filter=None):
        """Get attendance matrix with authentic data"""
        try:
            where_clause = ""
            if date_filter:
                where_clause = f"WHERE date >= '{date_filter}'"
            
            attendance = execute_sql_query(f"""
                SELECT date, asset_id, employee_name, start_time, end_time,
                       total_hours, job_site, job_number, efficiency_score, status, source
                FROM public.attendance_matrix 
                {where_clause}
                ORDER BY date DESC, asset_id
            """)
            return attendance
        except Exception as e:
            logger.error(f"Attendance matrix query error: {e}")
            return []
    
    def get_po_system_data(self):
        """Get purchase order data"""
        try:
            pos = execute_sql_query("""
                SELECT po.*, COUNT(li.id) as line_items
                FROM public.purchase_orders po
                LEFT JOIN public.po_line_items li ON po.id = li.po_id
                GROUP BY po.id
                ORDER BY po.created_at DESC
            """)
            return pos
        except Exception as e:
            logger.error(f"PO system query error: {e}")
            return []
    
    def refresh_gauge_data(self):
        """Refresh data from Gauge API"""
        try:
            response = requests.get(self.gauge_api_url, auth=self.gauge_auth, verify=False, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Gauge API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Gauge API connection error: {e}")
            return []
    
    def get_dashboard_metrics(self):
        """Get comprehensive dashboard metrics"""
        try:
            # Asset counts
            asset_count = execute_sql_query("SELECT COUNT(*) as count FROM public.assets WHERE is_active = true")[0]['count']
            
            # Recent attendance
            recent_attendance = execute_sql_query("""
                SELECT COUNT(*) as count FROM public.attendance_matrix 
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            """)[0]['count']
            
            # PO metrics
            active_pos = execute_sql_query("""
                SELECT COUNT(*) as count FROM public.purchase_orders 
                WHERE status IN ('approved', 'pending')
            """)[0]['count']
            
            # Total PO value
            po_value = execute_sql_query("""
                SELECT COALESCE(SUM(total_amount), 0) as total 
                FROM public.purchase_orders WHERE status = 'approved'
            """)[0]['total']
            
            return {
                'total_assets': asset_count,
                'recent_attendance_records': recent_attendance,
                'active_purchase_orders': active_pos,
                'approved_po_value': float(po_value),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Dashboard metrics error: {e}")
            return {
                'total_assets': 0,
                'recent_attendance_records': 0,
                'active_purchase_orders': 0,
                'approved_po_value': 0.0,
                'last_updated': datetime.now().isoformat()
            }

# Global service instance
master_data_service = MasterDataService()

def get_master_data_service():
    """Get the master data service"""
    return master_data_service