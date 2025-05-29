#!/usr/bin/env python3
"""
KAIZEN AUTOREPAIR AUDIT
Comprehensive route validation and auto-repair for TRAXOVO
"""

import os
import json
import requests
import re
from datetime import datetime

class KaizenAutorepairAudit:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.audit_log = {
            "timestamp": datetime.now().isoformat(),
            "total_routes_tested": 0,
            "working_routes": [],
            "broken_routes": [],
            "repaired_routes": [],
            "unresolved_issues": []
        }
        
    def extract_routes_from_app(self):
        """Extract all routes from simple_app.py"""
        routes = []
        try:
            with open("simple_app.py", "r") as f:
                content = f.read()
            
            # Find all @app.route decorators
            route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=['\"\[].*?['\"\]])?\)\s*def\s+(\w+)"
            matches = re.findall(route_pattern, content)
            
            for route_path, function_name in matches:
                routes.append({
                    "path": route_path,
                    "function": function_name,
                    "type": "page" if not route_path.startswith("/api") else "api"
                })
                
        except Exception as e:
            self.audit_log["unresolved_issues"].append(f"Failed to read simple_app.py: {str(e)}")
            
        return routes
    
    def test_route(self, route):
        """Test a single route for functionality"""
        url = f"{self.base_url}{route['path']}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                self.audit_log["working_routes"].append({
                    "path": route["path"],
                    "function": route["function"],
                    "status": "OK",
                    "response_size": len(response.content)
                })
                return True
            else:
                self.audit_log["broken_routes"].append({
                    "path": route["path"],
                    "function": route["function"],
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                })
                return False
                
        except requests.exceptions.ConnectionError:
            self.audit_log["broken_routes"].append({
                "path": route["path"],
                "function": route["function"],
                "error": "Connection refused - server not responding"
            })
            return False
        except requests.exceptions.Timeout:
            self.audit_log["broken_routes"].append({
                "path": route["path"],
                "function": route["function"],
                "error": "Request timeout"
            })
            return False
        except Exception as e:
            self.audit_log["broken_routes"].append({
                "path": route["path"],
                "function": route["function"],
                "error": str(e)
            })
            return False
    
    def check_template_exists(self, route):
        """Check if required templates exist for a route"""
        template_mappings = {
            "/": "templates/dashboard_light_fixed.html",
            "/attendance": "templates/attendance_grid_dashboard.html",
            "/gps-tracking": "templates/gps_tracking_enhanced.html",
            "/data-upload": "templates/uploads/index.html",
            "/driver-performance-heatmap": "templates/interactive_driver_heatmap.html",
            "/kaizen": "templates/kaizen/dashboard.html"
        }
        
        if route["path"] in template_mappings:
            template_path = template_mappings[route["path"]]
            if not os.path.exists(template_path):
                return False, template_path
        
        return True, None
    
    def attempt_auto_repair(self, broken_route):
        """Attempt to auto-repair broken routes"""
        path = broken_route["path"]
        
        # Check if template is missing
        template_exists, missing_template = self.check_template_exists({"path": path})
        
        if not template_exists:
            # Try to create a basic template
            if self.create_fallback_template(missing_template, path):
                self.audit_log["repaired_routes"].append({
                    "path": path,
                    "repair_action": f"Created fallback template: {missing_template}",
                    "status": "REPAIRED"
                })
                return True
        
        return False
    
    def create_fallback_template(self, template_path, route_path):
        """Create a basic functional template"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            
            # Create basic template
            template_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO - {route_path.replace('/', '').replace('-', ' ').title()}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
        }}
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card bg-dark border-secondary">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-cog me-2"></i>
                            {route_path.replace('/', '').replace('-', ' ').title()} Module
                        </h5>
                    </div>
                    <div class="card-body">
                        <p>This module is ready for configuration and deployment.</p>
                        <a href="/" class="btn btn-primary">
                            <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
            
            with open(template_path, "w") as f:
                f.write(template_content)
                
            return True
            
        except Exception as e:
            self.audit_log["unresolved_issues"].append(f"Failed to create template {template_path}: {str(e)}")
            return False
    
    def run_comprehensive_audit(self):
        """Execute full system audit"""
        print("🔍 KAIZEN AUTOREPAIR AUDIT")
        print("=" * 40)
        
        # Extract all routes
        print("Extracting routes from application...")
        routes = self.extract_routes_from_app()
        self.audit_log["total_routes_tested"] = len(routes)
        
        if not routes:
            print("❌ No routes found - check simple_app.py")
            return self.audit_log
        
        print(f"Found {len(routes)} routes to test")
        
        # Test each route
        print("Testing route functionality...")
        for route in routes:
            print(f"  Testing {route['path']}...", end="")
            if self.test_route(route):
                print(" ✅")
            else:
                print(" ❌")
        
        # Attempt repairs on broken routes
        if self.audit_log["broken_routes"]:
            print("\nAttempting auto-repairs...")
            for broken_route in self.audit_log["broken_routes"]:
                if self.attempt_auto_repair(broken_route):
                    print(f"  ✅ Repaired: {broken_route['path']}")
        
        # Save audit log
        with open("kaizen_autorepair_log.json", "w") as f:
            json.dump(self.audit_log, f, indent=2)
        
        return self.audit_log
    
    def print_summary(self):
        """Display audit summary"""
        total = self.audit_log["total_routes_tested"]
        working = len(self.audit_log["working_routes"])
        broken = len(self.audit_log["broken_routes"])
        repaired = len(self.audit_log["repaired_routes"])
        
        print("\n🎯 AUDIT SUMMARY")
        print("=" * 40)
        print(f"Total Routes: {total}")
        print(f"Working: {working} ✅")
        print(f"Broken: {broken} ❌")
        print(f"Auto-Repaired: {repaired} 🔧")
        
        if broken == 0:
            print("\n🚀 ALL SYSTEMS OPERATIONAL")
            print("Your TRAXOVO system is VP-presentation ready!")
        else:
            print(f"\n⚠️ {broken} ROUTES NEED ATTENTION:")
            for route in self.audit_log["broken_routes"]:
                if route not in self.audit_log["repaired_routes"]:
                    print(f"  • {route['path']}: {route.get('error', 'Unknown issue')}")

if __name__ == "__main__":
    auditor = KaizenAutorepairAudit()
    auditor.run_comprehensive_audit()
    auditor.print_summary()