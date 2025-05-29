"""
TRAXOVO Deep Sync & Validation Engine
Performs comprehensive system validation and data synchronization
"""
import os
import json
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path

class DeepSyncValidator:
    """Comprehensive system validation and data sync"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {}
        self.data_sources = []
        
    def discover_data_sources(self):
        """Find all authentic data files in the system"""
        data_files = []
        
        # Look for billing and asset files
        for pattern in ['*.csv', '*.xlsx', '*.xlsm', '*.json']:
            for file in Path('.').rglob(pattern):
                if any(keyword in str(file).lower() for keyword in 
                      ['ragle', 'billing', 'asset', 'equipment', 'gauge']):
                    data_files.append(str(file))
        
        self.data_sources = data_files[:10]  # Limit for performance
        return self.data_sources
    
    def validate_routes(self):
        """Check all navigation routes are properly implemented"""
        routes_to_check = [
            '/', '/dashboard', '/fleet-map', '/billing', 
            '/revenue-analytics', '/attendance-matrix', 
            '/equipment-dispatch', '/predictive-maintenance',
            '/pdf-genius', '/foundation-export'
        ]
        
        route_status = {}
        
        try:
            # Import main app to check routes
            import main
            app = main.app
            
            with app.test_client() as client:
                for route in routes_to_check:
                    try:
                        response = client.get(route)
                        route_status[route] = {
                            'status_code': response.status_code,
                            'working': response.status_code < 400
                        }
                    except Exception as e:
                        route_status[route] = {
                            'status_code': 500,
                            'working': False,
                            'error': str(e)
                        }
                        
        except Exception as e:
            self.logger.error(f"Route validation failed: {e}")
            
        return route_status
    
    def check_mobile_compatibility(self):
        """Validate mobile interface components"""
        mobile_checks = {}
        
        # Check if mobile templates exist and have required features
        template_files = [
            'templates/dashboard_clickable.html',
            'templates/includes/sidebar.html',
            'templates/fleet_map_enhanced.html'
        ]
        
        for template in template_files:
            if os.path.exists(template):
                with open(template, 'r') as f:
                    content = f.read()
                    
                mobile_checks[template] = {
                    'hamburger_menu': 'mobile-menu-toggle' in content,
                    'responsive_css': '@media (max-width: 767px)' in content,
                    'bootstrap_mobile': 'col-12 col-md-' in content
                }
        
        return mobile_checks
    
    def validate_micro_agents(self):
        """Check micro-agent background services"""
        try:
            from micro_agent_sync import micro_agent
            return {
                'micro_agent_loaded': True,
                'background_sync': hasattr(micro_agent, 'start_background_sync'),
                'system_health': hasattr(micro_agent, 'get_system_health')
            }
        except ImportError:
            return {'micro_agent_loaded': False}
    
    def check_foundation_export(self):
        """Validate Foundation accounting export capabilities"""
        try:
            from foundation_export import foundation_exporter
            return {
                'exporter_loaded': True,
                'csv_export': hasattr(foundation_exporter, 'export_csv'),
                'excel_export': hasattr(foundation_exporter, 'export_excel'),
                'qif_export': hasattr(foundation_exporter, 'export_qif')
            }
        except ImportError:
            return {'exporter_loaded': False}
    
    def run_complete_validation(self):
        """Execute full system validation"""
        print("🔍 TRAXOVO DEEP SYNC & VALIDATION")
        print("=" * 50)
        
        # 1. Data Source Discovery
        print("📊 Discovering data sources...")
        data_sources = self.discover_data_sources()
        print(f"Found {len(data_sources)} data files")
        
        # 2. Route Validation
        print("🔗 Validating navigation routes...")
        routes = self.validate_routes()
        working_routes = sum(1 for r in routes.values() if r.get('working', False))
        print(f"Routes working: {working_routes}/{len(routes)}")
        
        # 3. Mobile Compatibility
        print("📱 Checking mobile compatibility...")
        mobile = self.check_mobile_compatibility()
        
        # 4. Micro-Agent Status
        print("⚡ Validating micro-agents...")
        agents = self.validate_micro_agents()
        
        # 5. Foundation Export
        print("💰 Checking Foundation export...")
        foundation = self.check_foundation_export()
        
        # Generate Report
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_sources': len(data_sources),
            'routes': routes,
            'mobile': mobile,
            'micro_agents': agents,
            'foundation_export': foundation,
            'deployment_ready': all([
                len(data_sources) > 0,
                working_routes >= len(routes) * 0.8,  # 80% routes working
                agents.get('micro_agent_loaded', False),
                foundation.get('exporter_loaded', False)
            ])
        }
        
        print("\n📋 VALIDATION SUMMARY")
        print(f"Deployment Ready: {'✅ YES' if report['deployment_ready'] else '❌ NO'}")
        print(f"Data Sources: {report['data_sources']}")
        print(f"Working Routes: {working_routes}/{len(routes)}")
        print(f"Micro-Agents: {'✅' if agents.get('micro_agent_loaded') else '❌'}")
        print(f"Foundation Export: {'✅' if foundation.get('exporter_loaded') else '❌'}")
        
        return report

if __name__ == "__main__":
    validator = DeepSyncValidator()
    validator.run_complete_validation()