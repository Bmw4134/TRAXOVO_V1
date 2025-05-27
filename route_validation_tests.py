"""
TRAXORA Route Validation Tests
Comprehensive testing suite for all registered routes
"""

import requests
import json
import os
from datetime import datetime

class TRAXORARouteValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = {}
        
    def test_route(self, route, method="GET", data=None, files=None):
        """Test a single route and return results"""
        try:
            url = f"{self.base_url}{route}"
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, data=data, files=files, timeout=10)
            
            return {
                "route": route,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "route": route,
                "status_code": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_core_routes(self):
        """Test core navigation routes"""
        print("🔍 Testing Core Routes...")
        
        core_routes = [
            "/",
            "/health",
        ]
        
        results = []
        for route in core_routes:
            result = self.test_route(route)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {route} - {result.get('status_code', 'ERROR')}")
        
        return results
    
    def validate_may_reporting_routes(self):
        """Test May reporting specific routes"""
        print("\n📊 Testing May Reporting Routes...")
        
        may_routes = [
            "/upload-may-week-data",
            "/view-may-reports",
        ]
        
        results = []
        for route in may_routes:
            result = self.test_route(route)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {route} - {result.get('status_code', 'ERROR')}")
        
        return results
    
    def validate_administrative_routes(self):
        """Test administrative routes"""
        print("\n⚙️ Testing Administrative Routes...")
        
        admin_routes = [
            "/kaizen",
            "/system-health",
            "/system-admin",
            "/job-module",
        ]
        
        results = []
        for route in admin_routes:
            result = self.test_route(route)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {route} - {result.get('status_code', 'ERROR')}")
        
        return results
    
    def validate_driver_attendance_routes(self):
        """Test driver attendance routes"""
        print("\n👥 Testing Driver Attendance Routes...")
        
        attendance_routes = [
            "/driver-attendance",
            "/driver-attendance/upload",
        ]
        
        results = []
        for route in attendance_routes:
            result = self.test_route(route)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {route} - {result.get('status_code', 'ERROR')}")
        
        return results
    
    def validate_reporting_routes(self):
        """Test reporting dashboard routes"""
        print("\n📈 Testing Reporting Routes...")
        
        report_routes = [
            "/reports-dashboard",
            "/enhanced-weekly-report/",
            "/reports/",
        ]
        
        results = []
        for route in report_routes:
            result = self.test_route(route)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {route} - {result.get('status_code', 'ERROR')}")
        
        return results
    
    def simulate_may_data_upload(self):
        """Simulate uploading May week data"""
        print("\n📤 Simulating May Data Upload...")
        
        # Create test CSV data for May 23-27
        test_csv_content = """Date,Driver,Job Site,Start Time,End Time,Status
2025-05-23,John Smith,2024-016,07:00,16:00,On Time
2025-05-24,Jane Doe,2023-032,07:15,16:00,Late Start
2025-05-25,Mike Johnson,2024-019,07:00,15:30,Early End
2025-05-26,Sarah Wilson,2024-025,07:00,16:00,On Time
2025-05-27,Tom Brown,2022-008,--,--,Not On Job"""
        
        try:
            # Test the upload endpoint
            files = {'files': ('may_test_data.csv', test_csv_content, 'text/csv')}
            data = {'date_range': 'may-23-27'}
            
            result = self.test_route('/process-may-files', method='POST', data=data, files=files)
            status = "✅" if result["success"] else "❌"
            print(f"{status} May Data Upload Test - {result.get('status_code', 'ERROR')}")
            
            return result
        except Exception as e:
            print(f"❌ May Data Upload Test - ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_system_health_api(self):
        """Test system health API endpoint"""
        print("\n🏥 Testing System Health API...")
        
        result = self.test_route('/api/system-metrics')
        status = "✅" if result["success"] else "❌"
        print(f"{status} System Health API - {result.get('status_code', 'ERROR')}")
        
        return result
    
    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🚀 TRAXORA Route Validation Starting...")
        print("=" * 50)
        
        all_results = {
            "core_routes": self.validate_core_routes(),
            "may_reporting": self.validate_may_reporting_routes(),
            "administrative": self.validate_administrative_routes(),
            "driver_attendance": self.validate_driver_attendance_routes(),
            "reporting": self.validate_reporting_routes(),
            "may_upload_simulation": self.simulate_may_data_upload(),
            "system_health_api": self.test_system_health_api()
        }
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 VALIDATION SUMMARY:")
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, list):
                category_passed = sum(1 for r in results if r.get("success", False))
                category_total = len(results)
                total_tests += category_total
                passed_tests += category_passed
                print(f"📁 {category}: {category_passed}/{category_total} passed")
            elif isinstance(results, dict):
                total_tests += 1
                if results.get("success", False):
                    passed_tests += 1
                    print(f"📁 {category}: ✅ passed")
                else:
                    print(f"📁 {category}: ❌ failed")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"validation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {results_file}")
        
        return all_results

if __name__ == "__main__":
    validator = TRAXORARouteValidator()
    validator.run_comprehensive_validation()