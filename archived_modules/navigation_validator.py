"""
TRAXOVO Navigation System Validator
Ensures all routes work and mobile interface functions properly
"""
import os
import requests
from datetime import datetime

class NavigationValidator:
    """Validates all navigation routes and mobile functionality"""
    
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.routes = [
            '/', '/dashboard', '/fleet-map', '/billing',
            '/revenue-analytics', '/attendance-matrix', 
            '/equipment-dispatch', '/predictive-maintenance'
        ]
        
    def check_route(self, route):
        """Test if a route responds correctly"""
        try:
            response = requests.get(f"{self.base_url}{route}", timeout=10)
            return {
                'route': route,
                'status_code': response.status_code,
                'working': response.status_code < 400,
                'has_content': len(response.text) > 100
            }
        except Exception as e:
            return {
                'route': route,
                'status_code': 0,
                'working': False,
                'error': str(e)
            }
    
    def validate_all_routes(self):
        """Check all navigation routes"""
        print("🔗 Validating TRAXOVO Navigation Routes")
        print("-" * 40)
        
        results = []
        for route in self.routes:
            result = self.check_route(route)
            status = "✅" if result['working'] else "❌"
            print(f"{status} {route} - Status: {result['status_code']}")
            results.append(result)
            
        working_count = sum(1 for r in results if r['working'])
        print(f"\nNavigation Health: {working_count}/{len(results)} routes working")
        
        return results

    def check_mobile_features(self):
        """Validate mobile interface components"""
        print("\n📱 Mobile Interface Validation")
        print("-" * 40)
        
        mobile_files = [
            'templates/dashboard_clickable.html',
            'templates/includes/sidebar.html'
        ]
        
        mobile_status = {}
        for file_path in mobile_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                checks = {
                    'hamburger_menu': 'mobile-menu-toggle' in content,
                    'responsive_breakpoints': '@media (max-width: 767px)' in content,
                    'bootstrap_grid': 'col-12 col-md-' in content,
                    'sidebar_toggle': 'toggleSidebar' in content
                }
                
                mobile_status[file_path] = checks
                
                print(f"📄 {file_path}")
                for feature, present in checks.items():
                    status = "✅" if present else "❌"
                    print(f"  {status} {feature}")
        
        return mobile_status

if __name__ == "__main__":
    validator = NavigationValidator()
    
    # Wait for server to start
    import time
    time.sleep(3)
    
    # Run validation
    routes = validator.validate_all_routes()
    mobile = validator.check_mobile_features()
    
    print(f"\n📊 Validation completed at {datetime.now().strftime('%H:%M:%S')}")