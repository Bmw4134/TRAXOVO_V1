"""
TRAXOVO Unified Kernel
Centralized state management and module coordination
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from dataclasses import dataclass
from typing import Dict, List, Any

unified_kernel = Blueprint('unified_kernel', __name__)

@dataclass
class TRAXOVOState:
    """Centralized state management for TRAXOVO"""
    fleet_metrics: Dict[str, Any]
    attendance_data: Dict[str, Any]
    billing_data: Dict[str, Any]
    map_state: Dict[str, Any]
    user_preferences: Dict[str, Any]
    active_module: str
    last_updated: str

class TRAXOVOKernel:
    def __init__(self):
        self.state = TRAXOVOState(
            fleet_metrics={
                'total_assets': 717,
                'active_assets': 614,
                'utilization_rate': 91.7,
                'monthly_revenue': 847200,
                'total_drivers': 92,
                'active_drivers': 68
            },
            attendance_data={
                'pm_division': [],
                'ej_division': [],
                'asset_assignments': {}
            },
            billing_data={
                'monthly_summary': {},
                'project_profitability': {}
            },
            map_state={
                'center_lat': 32.7767,
                'center_lng': -96.7970,
                'zoom_level': 11,
                'active_markers': [],
                'selected_asset': None
            },
            user_preferences={
                'dashboard_layout': 'default',
                'theme': 'light',
                'refresh_interval': 30
            },
            active_module='dashboard',
            last_updated=datetime.now().isoformat()
        )
        self.module_registry = {}
        self.integration_points = {}
        
    def register_module(self, module_name: str, config: Dict[str, Any]):
        """Register a module with the kernel"""
        self.module_registry[module_name] = {
            'config': config,
            'state': {},
            'last_accessed': datetime.now().isoformat(),
            'integration_points': config.get('integration_points', [])
        }
        logging.info(f"Registered module: {module_name}")
    
    def update_state(self, module_name: str, state_update: Dict[str, Any]):
        """Update state for a specific module"""
        if module_name in self.module_registry:
            self.module_registry[module_name]['state'].update(state_update)
            self.module_registry[module_name]['last_accessed'] = datetime.now().isoformat()
        
        # Update global state if needed
        if module_name == 'fleet_dashboard':
            self.state.fleet_metrics.update(state_update.get('metrics', {}))
        elif module_name == 'attendance_matrix':
            self.state.attendance_data.update(state_update.get('attendance', {}))
        elif module_name == 'billing_system':
            self.state.billing_data.update(state_update.get('billing', {}))
        elif module_name == 'fleet_map':
            self.state.map_state.update(state_update.get('map', {}))
            
        self.state.last_updated = datetime.now().isoformat()
    
    def get_unified_context(self, active_module: str) -> Dict[str, Any]:
        """Get unified context for template rendering"""
        self.state.active_module = active_module
        
        return {
            'traxovo_state': {
                'fleet_metrics': self.state.fleet_metrics,
                'attendance_summary': {
                    'total_drivers': len(self.state.attendance_data.get('pm_division', [])) + 
                                   len(self.state.attendance_data.get('ej_division', [])),
                    'pm_drivers': len(self.state.attendance_data.get('pm_division', [])),
                    'ej_drivers': len(self.state.attendance_data.get('ej_division', []))
                },
                'billing_summary': {
                    'monthly_revenue': self.state.billing_data.get('monthly_summary', {}).get('april_2025', {}).get('total_revenue', 847200),
                    'ytd_revenue': self.state.billing_data.get('monthly_summary', {}).get('ytd_performance', {}).get('total_revenue', 2890400)
                },
                'map_state': self.state.map_state,
                'active_module': active_module,
                'last_updated': self.state.last_updated
            },
            'navigation_state': {
                'breadcrumb': self.generate_breadcrumb(active_module),
                'quick_actions': self.get_module_actions(active_module),
                'integration_points': self.get_integration_points(active_module)
            },
            'ui_state': {
                'theme': self.state.user_preferences.get('theme', 'light'),
                'layout': self.state.user_preferences.get('dashboard_layout', 'default'),
                'refresh_interval': self.state.user_preferences.get('refresh_interval', 30)
            }
        }
    
    def generate_breadcrumb(self, active_module: str) -> List[Dict[str, str]]:
        """Generate breadcrumb navigation"""
        breadcrumbs = [{'name': 'TRAXOVO', 'url': '/dashboard'}]
        
        module_map = {
            'dashboard': {'name': 'Executive Dashboard', 'url': '/dashboard'},
            'attendance_matrix': {'name': 'Attendance Matrix', 'url': '/attendance-matrix'},
            'fleet_map': {'name': 'Fleet Map', 'url': '/fleet-map'},
            'billing': {'name': 'Billing Intelligence', 'url': '/billing-consolidated'},
            'executive_reports': {'name': 'Executive Reports', 'url': '/executive-reports'},
            'asset_manager': {'name': 'Asset Manager', 'url': '/asset-manager'},
            'driver_management': {'name': 'Driver Management', 'url': '/driver-management'}
        }
        
        if active_module in module_map:
            breadcrumbs.append(module_map[active_module])
        
        return breadcrumbs
    
    def get_module_actions(self, active_module: str) -> List[Dict[str, str]]:
        """Get quick actions for current module"""
        actions_map = {
            'dashboard': [
                {'name': 'Refresh Data', 'action': 'refreshData()', 'icon': 'fas fa-sync-alt'},
                {'name': 'Customize Layout', 'action': 'toggleEditMode()', 'icon': 'fas fa-edit'}
            ],
            'attendance_matrix': [
                {'name': 'Export Report', 'action': 'exportAttendanceReport()', 'icon': 'fas fa-file-excel'},
                {'name': 'Bulk Assignment', 'action': 'bulkAssignAssets()', 'icon': 'fas fa-users-cog'}
            ],
            'fleet_map': [
                {'name': 'Center Map', 'action': 'centerMap()', 'icon': 'fas fa-crosshairs'},
                {'name': 'Track All', 'action': 'trackAllAssets()', 'icon': 'fas fa-broadcast-tower'}
            ],
            'billing': [
                {'name': 'Generate Invoice', 'action': 'generateInvoice()', 'icon': 'fas fa-file-invoice'},
                {'name': 'Export Data', 'action': 'exportBilling()', 'icon': 'fas fa-download'}
            ]
        }
        
        return actions_map.get(active_module, [])
    
    def get_integration_points(self, active_module: str) -> List[Dict[str, str]]:
        """Get integration points between modules"""
        integration_map = {
            'attendance_matrix': [
                {'module': 'asset_manager', 'type': 'asset_lookup', 'description': 'Asset ID assignments'},
                {'module': 'billing', 'type': 'cost_tracking', 'description': 'Labor cost calculation'}
            ],
            'fleet_map': [
                {'module': 'attendance_matrix', 'type': 'driver_location', 'description': 'Driver-asset positioning'},
                {'module': 'billing', 'type': 'utilization_tracking', 'description': 'Real-time billing data'}
            ],
            'billing': [
                {'module': 'attendance_matrix', 'type': 'labor_hours', 'description': 'Driver hour tracking'},
                {'module': 'asset_manager', 'type': 'asset_rates', 'description': 'Equipment billing rates'}
            ]
        }
        
        return integration_map.get(active_module, [])
    
    def detect_module_status(self) -> Dict[str, str]:
        """Detect status of all registered modules"""
        status_report = {}
        
        for module_name, module_data in self.module_registry.items():
            last_accessed = datetime.fromisoformat(module_data['last_accessed'])
            time_diff = (datetime.now() - last_accessed).total_seconds()
            
            if time_diff < 60:
                status = 'active'
            elif time_diff < 300:
                status = 'idle'
            else:
                status = 'inactive'
            
            status_report[module_name] = {
                'status': status,
                'last_accessed': module_data['last_accessed'],
                'has_state': bool(module_data['state']),
                'integration_points': len(module_data['integration_points'])
            }
        
        return status_report

# Initialize global kernel
traxovo_kernel = TRAXOVOKernel()

# Register core modules
traxovo_kernel.register_module('fleet_dashboard', {
    'template': 'master_unified.html',
    'integration_points': ['attendance_matrix', 'billing', 'fleet_map']
})

traxovo_kernel.register_module('attendance_matrix', {
    'template': 'attendance_comprehensive.html',
    'integration_points': ['asset_manager', 'billing', 'driver_management']
})

traxovo_kernel.register_module('fleet_map', {
    'template': 'fleet_map.html',
    'integration_points': ['attendance_matrix', 'asset_manager']
})

traxovo_kernel.register_module('billing_system', {
    'template': 'billing_consolidated.html',
    'integration_points': ['attendance_matrix', 'asset_manager', 'executive_reports']
})

@unified_kernel.route('/api/kernel/status')
def get_kernel_status():
    """Get comprehensive kernel status"""
    try:
        status = traxovo_kernel.detect_module_status()
        unified_context = traxovo_kernel.get_unified_context('status')
        
        return jsonify({
            'kernel_status': 'operational',
            'modules': status,
            'state': unified_context['traxovo_state'],
            'integration_health': 'optimal',
            'last_updated': traxovo_kernel.state.last_updated
        })
    except Exception as e:
        logging.error(f"Kernel status error: {e}")
        return jsonify({'error': 'Kernel status unavailable'}), 500

@unified_kernel.route('/api/kernel/sync')
def sync_modules():
    """Force synchronization across all modules"""
    try:
        # Update all module states with current data
        traxovo_kernel.update_state('fleet_dashboard', {
            'metrics': traxovo_kernel.state.fleet_metrics
        })
        
        traxovo_kernel.update_state('attendance_matrix', {
            'attendance': traxovo_kernel.state.attendance_data
        })
        
        traxovo_kernel.update_state('billing_system', {
            'billing': traxovo_kernel.state.billing_data
        })
        
        traxovo_kernel.update_state('fleet_map', {
            'map': traxovo_kernel.state.map_state
        })
        
        return jsonify({
            'sync_status': 'completed',
            'modules_synced': len(traxovo_kernel.module_registry),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Module sync error: {e}")
        return jsonify({'error': 'Sync failed'}), 500

@unified_kernel.route('/api/kernel/integration-points')
def get_integration_points():
    """Get all integration points between modules"""
    try:
        all_integrations = {}
        
        for module_name in traxovo_kernel.module_registry.keys():
            all_integrations[module_name] = traxovo_kernel.get_integration_points(module_name)
        
        return jsonify({
            'integration_points': all_integrations,
            'total_integrations': sum(len(points) for points in all_integrations.values())
        })
    except Exception as e:
        logging.error(f"Integration points error: {e}")
        return jsonify({'error': 'Integration data unavailable'}), 500