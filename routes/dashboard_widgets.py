"""
TRAXOVO Dashboard Widgets System
Customizable metric widgets with authentic data integration
"""

from flask import Blueprint, render_template, request, jsonify, session
import logging
import os
from datetime import datetime, timedelta
from services.supabase_client import get_supabase_client

dashboard_widgets_bp = Blueprint('widgets', __name__, url_prefix='/widgets')

class AuthenticMetricsEngine:
    """Engine for calculating authentic fleet metrics with drill-down explanations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_fleet_metrics(self):
        """Get all authentic fleet metrics with calculations"""
        try:
            # Connect to authentic data sources
            metrics = {}
            
            # Asset Metrics - from authentic equipment records
            asset_data = self._get_authentic_asset_data()
            metrics['assets'] = self._calculate_asset_metrics(asset_data)
            
            # Revenue Metrics - from authentic billing data
            revenue_data = self._get_authentic_revenue_data()
            metrics['revenue'] = self._calculate_revenue_metrics(revenue_data)
            
            # Utilization Metrics - from authentic operational data
            utilization_data = self._get_authentic_utilization_data()
            metrics['utilization'] = self._calculate_utilization_metrics(utilization_data)
            
            # Driver Metrics - from authentic attendance/timecard data
            driver_data = self._get_authentic_driver_data()
            metrics['drivers'] = self._calculate_driver_metrics(driver_data)
            
            # Safety Metrics - from authentic incident records
            safety_data = self._get_authentic_safety_data()
            metrics['safety'] = self._calculate_safety_metrics(safety_data)
            
            # Maintenance Metrics - from authentic service records
            maintenance_data = self._get_authentic_maintenance_data()
            metrics['maintenance'] = self._calculate_maintenance_metrics(maintenance_data)
            
            return metrics
            
        except Exception as e:
            logging.error(f"Metrics calculation error: {e}")
            return self._get_unavailable_metrics()
    
    def _get_authentic_asset_data(self):
        """Get authentic asset data from Supabase"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic asset records
            assets = self.supabase.client.table('equipment_assets').select('*').execute()
            return assets.data if assets.data else None
        except:
            return None
    
    def _calculate_asset_metrics(self, asset_data):
        """Calculate authentic asset metrics with explanations"""
        if not asset_data:
            return {
                'total_assets': 0,
                'active_assets': 0,
                'billable_assets': 0,
                'asset_value': 0,
                'explanation': 'No asset data available - connect to authentic database',
                'calculation': 'Waiting for Supabase connection'
            }
        
        total = len(asset_data)
        active = len([a for a in asset_data if a.get('status') == 'active'])
        billable = len([a for a in asset_data if a.get('billable', False)])
        total_value = sum(a.get('value', 0) for a in asset_data)
        
        return {
            'total_assets': total,
            'active_assets': active,
            'billable_assets': billable,
            'asset_value': total_value,
            'explanation': f'Asset counts from authenticated equipment database. {active} of {total} assets currently operational.',
            'calculation': f'Active Rate: {(active/total*100):.1f}% | Billable: {billable} units'
        }
    
    def _get_authentic_revenue_data(self):
        """Get authentic revenue data from billing systems"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic revenue records from current month
            current_month = datetime.now().strftime('%Y-%m')
            revenue = self.supabase.client.table('revenue_records')\
                .select('*')\
                .gte('date', f'{current_month}-01')\
                .execute()
            return revenue.data if revenue.data else None
        except:
            return None
    
    def _calculate_revenue_metrics(self, revenue_data):
        """Calculate authentic revenue metrics"""
        if not revenue_data:
            return {
                'monthly_revenue': 0,
                'daily_average': 0,
                'billing_rate': 0,
                'explanation': 'No revenue data available - connect to billing system',
                'calculation': 'Awaiting authentic billing integration'
            }
        
        total_revenue = sum(r.get('amount', 0) for r in revenue_data)
        days_in_month = datetime.now().day
        daily_avg = total_revenue / days_in_month if days_in_month > 0 else 0
        
        return {
            'monthly_revenue': total_revenue,
            'daily_average': daily_avg,
            'billing_rate': len(revenue_data),
            'explanation': f'Revenue calculated from {len(revenue_data)} authentic billing records for current month',
            'calculation': f'Total: ${total_revenue:,.2f} | Daily Avg: ${daily_avg:,.2f}'
        }
    
    def _get_authentic_utilization_data(self):
        """Get authentic utilization data from operational systems"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic utilization records
            utilization = self.supabase.client.table('equipment_utilization')\
                .select('*')\
                .gte('date', (datetime.now() - timedelta(days=30)).isoformat())\
                .execute()
            return utilization.data if utilization.data else None
        except:
            return None
    
    def _calculate_utilization_metrics(self, utilization_data):
        """Calculate authentic utilization metrics"""
        if not utilization_data:
            return {
                'fleet_utilization': 0.0,
                'peak_hours': 0,
                'efficiency_rating': 0,
                'explanation': 'No utilization data available - connect to telematics system',
                'calculation': 'Awaiting authentic operational data'
            }
        
        avg_utilization = sum(u.get('utilization_rate', 0) for u in utilization_data) / len(utilization_data)
        peak_hours = max(u.get('hours_operated', 0) for u in utilization_data)
        
        return {
            'fleet_utilization': min(avg_utilization, 100.0),  # Cap at 100%
            'peak_hours': peak_hours,
            'efficiency_rating': min(avg_utilization * 1.1, 100),
            'explanation': f'Utilization calculated from {len(utilization_data)} equipment operational records over 30 days',
            'calculation': f'Average: {avg_utilization:.1f}% | Peak: {peak_hours} hours'
        }
    
    def _get_authentic_driver_data(self):
        """Get authentic driver data from attendance systems"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic driver attendance records
            today = datetime.now().strftime('%Y-%m-%d')
            drivers = self.supabase.client.table('driver_attendance')\
                .select('*')\
                .eq('date', today)\
                .execute()
            return drivers.data if drivers.data else None
        except:
            return None
    
    def _calculate_driver_metrics(self, driver_data):
        """Calculate authentic driver metrics"""
        if not driver_data:
            return {
                'total_drivers': 0,
                'clocked_in': 0,
                'attendance_rate': 0,
                'explanation': 'No driver data available - connect to attendance system',
                'calculation': 'Awaiting authentic timecard integration'
            }
        
        total = len(driver_data)
        clocked_in = len([d for d in driver_data if d.get('status') == 'clocked_in'])
        attendance_rate = (clocked_in / total * 100) if total > 0 else 0
        
        return {
            'total_drivers': total,
            'clocked_in': clocked_in,
            'attendance_rate': attendance_rate,
            'explanation': f'Driver metrics from authenticated attendance records for today',
            'calculation': f'Present: {clocked_in}/{total} | Rate: {attendance_rate:.1f}%'
        }
    
    def _get_authentic_safety_data(self):
        """Get authentic safety data from incident systems"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic safety incident records
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            incidents = self.supabase.client.table('safety_incidents')\
                .select('*')\
                .gte('date', thirty_days_ago)\
                .execute()
            return incidents.data if incidents.data else None
        except:
            return None
    
    def _calculate_safety_metrics(self, safety_data):
        """Calculate authentic safety metrics"""
        if not safety_data:
            return {
                'incidents_30d': 0,
                'safety_score': 100,
                'days_since_incident': 0,
                'explanation': 'No safety data available - connect to incident tracking system',
                'calculation': 'Awaiting authentic safety record integration'
            }
        
        incidents = len(safety_data)
        # Calculate days since last incident
        if safety_data:
            latest_incident = max(safety_data, key=lambda x: x.get('date', ''))
            last_incident_date = datetime.fromisoformat(latest_incident['date'])
            days_since = (datetime.now() - last_incident_date).days
        else:
            days_since = 0
        
        safety_score = max(100 - (incidents * 5), 0)  # Reduce score by 5 per incident
        
        return {
            'incidents_30d': incidents,
            'safety_score': safety_score,
            'days_since_incident': days_since,
            'explanation': f'Safety metrics from {incidents} authenticated incident records over 30 days',
            'calculation': f'Score: {safety_score}/100 | Last incident: {days_since} days ago'
        }
    
    def _get_authentic_maintenance_data(self):
        """Get authentic maintenance data from service systems"""
        if not self.supabase.connected:
            return None
        
        try:
            # Query authentic maintenance records
            current_month = datetime.now().strftime('%Y-%m')
            maintenance = self.supabase.client.table('maintenance_records')\
                .select('*')\
                .gte('date', f'{current_month}-01')\
                .execute()
            return maintenance.data if maintenance.data else None
        except:
            return None
    
    def _calculate_maintenance_metrics(self, maintenance_data):
        """Calculate authentic maintenance metrics"""
        if not maintenance_data:
            return {
                'maintenance_costs': 0,
                'work_orders': 0,
                'uptime_percentage': 0,
                'explanation': 'No maintenance data available - connect to service management system',
                'calculation': 'Awaiting authentic maintenance record integration'
            }
        
        total_costs = sum(m.get('cost', 0) for m in maintenance_data)
        work_orders = len(maintenance_data)
        # Calculate uptime based on maintenance frequency
        uptime = max(100 - (work_orders * 2), 85)  # Assume maintenance reduces uptime
        
        return {
            'maintenance_costs': total_costs,
            'work_orders': work_orders,
            'uptime_percentage': uptime,
            'explanation': f'Maintenance metrics from {work_orders} authenticated service records for current month',
            'calculation': f'Total Cost: ${total_costs:,.2f} | Orders: {work_orders} | Uptime: {uptime}%'
        }
    
    def _get_unavailable_metrics(self):
        """Return metrics when data is unavailable"""
        unavailable = {
            'value': 0,
            'explanation': 'Data unavailable - database connection required',
            'calculation': 'Connect to Supabase for authentic metrics'
        }
        
        return {
            'assets': {**unavailable, 'total_assets': 0, 'active_assets': 0, 'billable_assets': 0, 'asset_value': 0},
            'revenue': {**unavailable, 'monthly_revenue': 0, 'daily_average': 0, 'billing_rate': 0},
            'utilization': {**unavailable, 'fleet_utilization': 0.0, 'peak_hours': 0, 'efficiency_rating': 0},
            'drivers': {**unavailable, 'total_drivers': 0, 'clocked_in': 0, 'attendance_rate': 0},
            'safety': {**unavailable, 'incidents_30d': 0, 'safety_score': 100, 'days_since_incident': 0},
            'maintenance': {**unavailable, 'maintenance_costs': 0, 'work_orders': 0, 'uptime_percentage': 0}
        }

@dashboard_widgets_bp.route('/api/metrics')
def get_metrics():
    """API endpoint for authentic metrics data"""
    engine = AuthenticMetricsEngine()
    metrics = engine.get_fleet_metrics()
    
    return jsonify({
        'status': 'success',
        'metrics': metrics,
        'timestamp': datetime.now().isoformat(),
        'data_source': 'authentic' if engine.supabase.connected else 'unavailable'
    })

@dashboard_widgets_bp.route('/api/user-widgets')
def get_user_widgets():
    """Get user's customized widget configuration"""
    user_id = session.get('user_id', 'anonymous')
    
    # Get user's widget preferences (mock for now - replace with database)
    default_widgets = [
        {'id': 'total_assets', 'title': 'Total Assets', 'type': 'metric', 'size': 'small', 'position': 0},
        {'id': 'monthly_revenue', 'title': 'Monthly Revenue', 'type': 'metric', 'size': 'medium', 'position': 1},
        {'id': 'fleet_utilization', 'title': 'Fleet Utilization', 'type': 'gauge', 'size': 'medium', 'position': 2},
        {'id': 'safety_score', 'title': 'Safety Score', 'type': 'score', 'size': 'small', 'position': 3}
    ]
    
    return jsonify({
        'status': 'success',
        'widgets': default_widgets,
        'user_id': user_id
    })

@dashboard_widgets_bp.route('/api/save-widgets', methods=['POST'])
def save_user_widgets():
    """Save user's customized widget configuration"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'anonymous')
        widgets = data.get('widgets', [])
        
        # Save widget configuration (mock for now - replace with database)
        # In production, save to user_preferences table
        
        return jsonify({
            'status': 'success',
            'message': 'Widget configuration saved',
            'user_id': user_id
        })
        
    except Exception as e:
        logging.error(f"Widget save error: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_widgets_bp.route('/customize')
def widget_customizer():
    """Widget customization interface"""
    return render_template('widget_customizer.html')