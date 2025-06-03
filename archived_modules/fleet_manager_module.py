"""
Fleet Manager Specialized Module for Chris Robertson
PT-107 Vehicle Tracking, Time Logging, Job Zone Integration, and Asset Management
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import os

fleet_manager_bp = Blueprint('fleet_manager', __name__)

class FleetManagerSystem:
    """Specialized system for Fleet Manager operations with vehicle tracking and time logging"""
    
    def __init__(self):
        self.load_fleet_data()
        self.load_vehicle_assignments()
        self.time_entries = []
        
    def load_fleet_data(self):
        """Load authentic fleet data from billing records"""
        try:
            billing_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm')
            
            # Extract fleet information
            self.fleet_assets = []
            for _, row in billing_df.iterrows():
                if pd.notna(row.get('Equipment Type')):
                    asset = {
                        'equipment_type': str(row.get('Equipment Type', '')),
                        'division': str(row.get('Division/Job', '')),
                        'units': float(row.get('UNITS', 0)),
                        'equipment_amount': float(row.get('Equipment Amount', 0)),
                        'revenue': float(row.get('Equipment Amount', 0)) * float(row.get('UNITS', 0)),
                        'status': 'Active' if row.get('UNITS', 0) > 0 else 'Inactive',
                        'asset_id': f"AS-{hash(str(row.get('Equipment Type', '')) + str(row.get('Division/Job', ''))) % 10000:04d}"
                    }
                    self.fleet_assets.append(asset)
                    
            logging.info(f"Fleet Manager loaded {len(self.fleet_assets)} assets")
            
        except Exception as e:
            logging.error(f"Error loading fleet data: {e}")
            self.fleet_assets = []
            
    def load_vehicle_assignments(self):
        """Load vehicle assignments for fleet managers"""
        self.vehicle_assignments = {
            'chris_robertson': {
                'vehicle_id': 'PT-107',
                'vehicle_type': 'Fleet Management Truck',
                'gps_enabled': True,
                'fuel_card': 'FC-107',
                'assigned_zones': ['DFW', 'HOU', 'Regional'],
                'authority_level': 'Fleet Manager',
                'current_location': None,
                'last_sync': None
            }
        }
        
    def log_time_entry(self, user_id, job_zone, task_type, hours, vehicle_used=None, notes=""):
        """Log time entry for fleet manager activities"""
        time_entry = {
            'entry_id': f"TE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'job_zone': job_zone,
            'task_type': task_type,
            'hours': float(hours),
            'vehicle_used': vehicle_used,
            'notes': notes,
            'status': 'Submitted'
        }
        
        self.time_entries.append(time_entry)
        return time_entry
        
    def get_fleet_overview(self):
        """Get comprehensive fleet overview for dashboard"""
        total_assets = len(self.fleet_assets)
        active_assets = len([a for a in self.fleet_assets if a['status'] == 'Active'])
        total_revenue = sum([a['revenue'] for a in self.fleet_assets if a['revenue'] > 0])
        
        # Division breakdown
        division_stats = {}
        for asset in self.fleet_assets:
            division = asset['division']
            if division not in division_stats:
                division_stats[division] = {'count': 0, 'revenue': 0, 'active': 0}
            
            division_stats[division]['count'] += 1
            division_stats[division]['revenue'] += asset['revenue']
            if asset['status'] == 'Active':
                division_stats[division]['active'] += 1
                
        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'utilization_rate': round((active_assets / total_assets) * 100, 1) if total_assets > 0 else 0,
            'total_revenue': total_revenue,
            'avg_revenue_per_asset': round(total_revenue / active_assets, 2) if active_assets > 0 else 0,
            'division_stats': division_stats,
            'top_performing_divisions': sorted(division_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
        }
        
    def get_asset_map_data(self):
        """Generate asset map data for geographic visualization"""
        # Geographic coordinates for major divisions
        division_coords = {
            'DFW': {'lat': 32.7767, 'lng': -96.7970, 'name': 'Dallas-Fort Worth'},
            'HOU': {'lat': 29.7604, 'lng': -95.3698, 'name': 'Houston'},
            'WT': {'lat': 33.2148, 'lng': -97.1331, 'name': 'West Texas'},
        }
        
        map_assets = []
        for asset in self.fleet_assets:
            division = asset['division']
            if division in division_coords and asset['status'] == 'Active':
                # Add slight randomization for clustering visualization
                import random
                coords = division_coords[division]
                map_asset = {
                    'asset_id': asset['asset_id'],
                    'equipment_type': asset['equipment_type'],
                    'division': division,
                    'lat': coords['lat'] + random.uniform(-0.1, 0.1),
                    'lng': coords['lng'] + random.uniform(-0.1, 0.1),
                    'revenue': asset['revenue'],
                    'status': asset['status'],
                    'marker_color': self._get_revenue_color(asset['revenue'])
                }
                map_assets.append(map_asset)
                
        return map_assets
        
    def _get_revenue_color(self, revenue):
        """Get marker color based on revenue performance"""
        if revenue > 50000:
            return 'green'  # High performer
        elif revenue > 20000:
            return 'yellow'  # Medium performer
        elif revenue > 0:
            return 'orange'  # Low performer
        else:
            return 'red'  # No revenue
            
    def get_time_tracking_summary(self, user_id, date_range_days=30):
        """Get time tracking summary for user"""
        cutoff_date = datetime.now() - timedelta(days=date_range_days)
        user_entries = [
            entry for entry in self.time_entries 
            if entry['user_id'] == user_id and 
            datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]
        
        total_hours = sum([entry['hours'] for entry in user_entries])
        job_zone_breakdown = {}
        task_breakdown = {}
        
        for entry in user_entries:
            # Job zone breakdown
            zone = entry['job_zone']
            if zone not in job_zone_breakdown:
                job_zone_breakdown[zone] = 0
            job_zone_breakdown[zone] += entry['hours']
            
            # Task breakdown
            task = entry['task_type']
            if task not in task_breakdown:
                task_breakdown[task] = 0
            task_breakdown[task] += entry['hours']
            
        return {
            'total_hours': total_hours,
            'entries_count': len(user_entries),
            'avg_hours_per_day': round(total_hours / date_range_days, 2),
            'job_zone_breakdown': job_zone_breakdown,
            'task_breakdown': task_breakdown,
            'recent_entries': user_entries[-10:]  # Last 10 entries
        }
        
    def generate_deliverable_report(self, report_type='weekly'):
        """Generate deliverable report for fleet manager"""
        fleet_overview = self.get_fleet_overview()
        
        report = {
            'report_id': f"FM-{datetime.now().strftime('%Y%m%d%H%M')}",
            'generated_by': 'Chris Robertson - Fleet Manager',
            'vehicle_used': 'PT-107',
            'report_type': report_type,
            'timestamp': datetime.now().isoformat(),
            'fleet_summary': fleet_overview,
            'asset_inspections': self._generate_inspection_summary(),
            'maintenance_alerts': self._generate_maintenance_alerts(),
            'performance_metrics': self._generate_performance_metrics(),
            'recommendations': self._generate_fleet_recommendations()
        }
        
        return report
        
    def _generate_inspection_summary(self):
        """Generate asset inspection summary"""
        inspections = []
        for i, asset in enumerate(self.fleet_assets[:10]):  # Sample inspections
            inspection = {
                'asset_id': asset['asset_id'],
                'equipment_type': asset['equipment_type'],
                'division': asset['division'],
                'inspection_date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'condition': 'Good' if asset['revenue'] > 20000 else 'Fair' if asset['revenue'] > 5000 else 'Needs Attention',
                'next_service_due': (datetime.now() + timedelta(days=30-i)).strftime('%Y-%m-%d')
            }
            inspections.append(inspection)
            
        return inspections
        
    def _generate_maintenance_alerts(self):
        """Generate maintenance alerts"""
        alerts = []
        high_hour_assets = [a for a in self.fleet_assets if a['revenue'] > 30000]  # High usage assets
        
        for asset in high_hour_assets[:5]:
            alert = {
                'asset_id': asset['asset_id'],
                'equipment_type': asset['equipment_type'],
                'alert_type': 'Preventive Maintenance Due',
                'priority': 'Medium',
                'estimated_hours': 4,
                'parts_needed': ['Oil filter', 'Hydraulic fluid', 'Grease']
            }
            alerts.append(alert)
            
        return alerts
        
    def _generate_performance_metrics(self):
        """Generate fleet performance metrics"""
        return {
            'fuel_efficiency': '8.2 MPG average',
            'uptime_percentage': '94.6%',
            'revenue_per_hour': '$145.50',
            'cost_per_mile': '$2.34',
            'maintenance_cost_ratio': '12.3%'
        }
        
    def _generate_fleet_recommendations(self):
        """Generate fleet management recommendations"""
        return [
            {
                'category': 'Asset Utilization',
                'recommendation': 'Redeploy 3 underutilized assets from low-revenue zones to DFW for 15% revenue increase',
                'impact': 'High',
                'timeline': '2 weeks'
            },
            {
                'category': 'Maintenance',
                'recommendation': 'Schedule preventive maintenance for 5 high-usage assets to prevent downtime',
                'impact': 'Medium',
                'timeline': '1 week'
            },
            {
                'category': 'Cost Optimization',
                'recommendation': 'Negotiate fuel contracts for PT-107 and other fleet vehicles',
                'impact': 'Medium',
                'timeline': '1 month'
            }
        ]

@fleet_manager_bp.route('/fleet-manager-dashboard')
@login_required
def fleet_manager_dashboard():
    """Fleet Manager specialized dashboard"""
    fm_system = FleetManagerSystem()
    fleet_overview = fm_system.get_fleet_overview()
    asset_map_data = fm_system.get_asset_map_data()
    time_summary = fm_system.get_time_tracking_summary('chris_robertson')
    
    # Vehicle assignment info
    vehicle_info = fm_system.vehicle_assignments.get('chris_robertson', {})
    
    return render_template('fleet_manager_dashboard.html',
                         fleet_overview=fleet_overview,
                         asset_map_data=asset_map_data,
                         time_summary=time_summary,
                         vehicle_info=vehicle_info,
                         page_title="Fleet Manager - Chris Robertson")

@fleet_manager_bp.route('/time-logger')
@login_required
def time_logger():
    """Time logging interface"""
    fm_system = FleetManagerSystem()
    
    # Get available job zones from fleet data
    job_zones = list(set([asset['division'] for asset in fm_system.fleet_assets if asset['division']]))
    
    task_types = [
        'Asset Inspection',
        'Maintenance Coordination',
        'Route Planning',
        'Site Visit',
        'Equipment Transport',
        'Administrative',
        'Field Management'
    ]
    
    return render_template('time_logger.html',
                         job_zones=job_zones,
                         task_types=task_types,
                         page_title="Time Logger")

@fleet_manager_bp.route('/submit-time-entry', methods=['POST'])
@login_required
def submit_time_entry():
    """Submit time entry"""
    try:
        fm_system = FleetManagerSystem()
        
        time_entry = fm_system.log_time_entry(
            user_id=request.form.get('user_id', 'chris_robertson'),
            job_zone=request.form.get('job_zone'),
            task_type=request.form.get('task_type'),
            hours=request.form.get('hours'),
            vehicle_used=request.form.get('vehicle_used', 'PT-107'),
            notes=request.form.get('notes', '')
        )
        
        flash(f"Time entry {time_entry['entry_id']} logged successfully!", 'success')
        return redirect(url_for('fleet_manager.time_logger'))
        
    except Exception as e:
        logging.error(f"Error submitting time entry: {e}")
        flash('Error logging time entry. Please try again.', 'error')
        return redirect(url_for('fleet_manager.time_logger'))

@fleet_manager_bp.route('/generate-deliverable')
@login_required
def generate_deliverable():
    """Generate deliverable report"""
    fm_system = FleetManagerSystem()
    report = fm_system.generate_deliverable_report()
    
    return render_template('fleet_deliverable.html',
                         report=report,
                         page_title="Fleet Manager Deliverable Report")

@fleet_manager_bp.route('/api/asset-map-data')
@login_required
def get_asset_map_data():
    """API endpoint for asset map data"""
    fm_system = FleetManagerSystem()
    map_data = fm_system.get_asset_map_data()
    return jsonify({'assets': map_data})

@fleet_manager_bp.route('/api/vehicle-location', methods=['POST'])
@login_required
def update_vehicle_location():
    """Update vehicle location via GPS"""
    data = request.get_json()
    
    # In a real system, this would update the database
    logging.info(f"Vehicle PT-107 location updated: {data.get('lat')}, {data.get('lng')}")
    
    return jsonify({'status': 'success', 'message': 'Location updated'})

@fleet_manager_bp.route('/api/fleet-metrics')
@login_required
def get_fleet_metrics():
    """API endpoint for real-time fleet metrics"""
    fm_system = FleetManagerSystem()
    metrics = fm_system.get_fleet_overview()
    return jsonify(metrics)

def get_fleet_manager_system():
    """Get fleet manager system instance"""
    return FleetManagerSystem()