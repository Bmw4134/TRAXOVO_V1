"""
QQ Route Validation System
Comprehensive testing of all TRAXOVO routes for deployment readiness
"""

import subprocess
import time
import json
import requests
from datetime import datetime

class TRAXOVORouteValidator:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = {}
        self.critical_routes = [
            "/",
            "/demo-direct", 
            "/quantum-dashboard",
            "/fleet-map",
            "/attendance-matrix",
            "/executive-dashboard",
            "/accessibility-dashboard",
            "/smart-po",
            "/dispatch-system",
            "/estimating-system"
        ]
        self.api_routes = [
            "/api/fort-worth-assets",
            "/api/attendance-data", 
            "/api/quantum-consciousness",
            "/api/accessibility-dashboard-data",
            "/health"
        ]
    
    def start_application(self):
        """Start TRAXOVO application for testing"""
        try:
            # Kill existing processes
            subprocess.run(["pkill", "-f", "gunicorn"], capture_output=True)
            time.sleep(2)
            
            # Start application in background
            self.process = subprocess.Popen([
                "python3", "app_qq_enhanced.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for startup
            time.sleep(8)
            return True
        except Exception as e:
            print(f"Failed to start application: {e}")
            return False
    
    def validate_all_routes(self):
        """Validate all critical routes"""
        print("Starting TRAXOVO application...")
        if not self.start_application():
            return {"error": "Failed to start application"}
        
        print("Testing critical routes...")
        for route in self.critical_routes:
            self.test_route(route, route_type="page")
        
        print("Testing API routes...")
        for route in self.api_routes:
            self.test_route(route, route_type="api")
        
        self.cleanup()
        return self.generate_report()
    
    def test_route(self, route, route_type="page"):
        """Test individual route"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{route}", timeout=10)
            response_time = time.time() - start_time
            
            self.results[route] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "content_length": len(response.content),
                "route_type": route_type,
                "success": 200 <= response.status_code < 400,
                "content_type": response.headers.get("content-type", "")
            }
            
            # Additional validation for API routes
            if route_type == "api" and response.status_code == 200:
                try:
                    json_data = response.json()
                    self.results[route]["valid_json"] = True
                    self.results[route]["has_data"] = bool(json_data)
                except:
                    self.results[route]["valid_json"] = False
            
            print(f"  {route}: {response.status_code} ({response_time:.2f}s)")
            
        except Exception as e:
            self.results[route] = {
                "error": str(e),
                "success": False,
                "route_type": route_type
            }
            print(f"  {route}: ERROR - {e}")
    
    def cleanup(self):
        """Cleanup application process"""
        try:
            if hasattr(self, 'process'):
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
        except:
            pass
    
    def generate_report(self):
        """Generate comprehensive route validation report"""
        successful_routes = [r for r, data in self.results.items() if data.get("success", False)]
        failed_routes = [r for r, data in self.results.items() if not data.get("success", False)]
        
        # Calculate statistics
        total_routes = len(self.results)
        success_rate = len(successful_routes) / total_routes * 100 if total_routes > 0 else 0
        
        avg_response_time = sum(
            data.get("response_time", 0) 
            for data in self.results.values() 
            if "response_time" in data
        ) / len([d for d in self.results.values() if "response_time" in d])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_routes": total_routes,
                "successful_routes": len(successful_routes),
                "failed_routes": len(failed_routes),
                "success_rate": round(success_rate, 1),
                "average_response_time": round(avg_response_time, 2)
            },
            "successful_routes": successful_routes,
            "failed_routes": failed_routes,
            "detailed_results": self.results,
            "deployment_status": "READY" if len(failed_routes) == 0 else "BLOCKED",
            "recommendation": "All routes operational" if len(failed_routes) == 0 else f"Fix {len(failed_routes)} failed routes"
        }
        
        return report

def main():
    print("🚀 QQ Route Validation System")
    print("=" * 50)
    
    validator = TRAXOVORouteValidator()
    report = validator.validate_all_routes()
    
    if "error" in report:
        print(f"Validation failed: {report['error']}")
        return
    
    print(f"\n📊 Route Validation Results:")
    print(f"  Total Routes: {report['summary']['total_routes']}")
    print(f"  Success Rate: {report['summary']['success_rate']}%")
    print(f"  Failed Routes: {report['summary']['failed_routes']}")
    print(f"  Avg Response Time: {report['summary']['average_response_time']}s")
    
    if report['failed_routes']:
        print(f"\n🚫 Failed Routes:")
        for route in report['failed_routes']:
            error_info = report['detailed_results'][route]
            if 'error' in error_info:
                print(f"  - {route}: {error_info['error']}")
            else:
                print(f"  - {route}: HTTP {error_info.get('status_code', 'Unknown')}")
    
    print(f"\n✅ Successful Routes:")
    for route in report['successful_routes']:
        route_data = report['detailed_results'][route]
        print(f"  - {route}: {route_data['status_code']} ({route_data.get('response_time', 0):.2f}s)")
    
    # Save report
    with open('qq_route_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Report saved: qq_route_validation_report.json")
    print(f"🎯 Status: {report['deployment_status']}")
    print(f"💡 Recommendation: {report['recommendation']}")
    print("=" * 50)

if __name__ == "__main__":
    main()