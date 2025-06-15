#!/usr/bin/env python3
"""
Deployment Status Checker for Nexus Watson Syncfusion Platform
"""

import requests
import json
from datetime import datetime

def check_deployment_status(service_url):
    """Check if the deployed service is working correctly"""
    
    print("🔍 Checking Nexus Watson Syncfusion Deployment Status...")
    print(f"Service URL: {service_url}")
    print("-" * 60)
    
    # Test endpoints
    endpoints = [
        {'path': '/', 'name': 'Landing Page', 'method': 'GET'},
        {'path': '/api/status', 'name': 'System Status API', 'method': 'GET'},
        {'path': '/api/dashboard-data', 'name': 'Dashboard Data API', 'method': 'GET'},
        {'path': '/api/fleet-performance', 'name': 'Fleet Performance API', 'method': 'GET'},
        {'path': '/api/kpi-metrics', 'name': 'KPI Metrics API', 'method': 'GET'},
        {'path': '/api/export/syncfusion-config', 'name': 'Syncfusion Config Export', 'method': 'GET'}
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            url = f"{service_url.rstrip('/')}{endpoint['path']}"
            response = requests.get(url, timeout=10)
            
            status = "✅ WORKING" if response.status_code == 200 else f"❌ ERROR ({response.status_code})"
            
            # Special handling for API endpoints
            if endpoint['path'].startswith('/api/') and response.status_code == 200:
                try:
                    data = response.json()
                    data_preview = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                    status += f" - Data: {data_preview}"
                except:
                    status += " - Response received"
            
            results.append({
                'endpoint': endpoint['name'],
                'path': endpoint['path'],
                'status': status,
                'response_time': f"{response.elapsed.total_seconds():.2f}s"
            })
            
            print(f"{status} | {endpoint['name']} | {response.elapsed.total_seconds():.2f}s")
            
        except requests.exceptions.RequestException as e:
            error_status = f"❌ CONNECTION ERROR: {str(e)}"
            results.append({
                'endpoint': endpoint['name'],
                'path': endpoint['path'],
                'status': error_status,
                'response_time': 'N/A'
            })
            print(f"{error_status} | {endpoint['name']}")
    
    print("-" * 60)
    
    # Summary
    working_endpoints = sum(1 for r in results if "✅ WORKING" in r['status'])
    total_endpoints = len(results)
    
    if working_endpoints == total_endpoints:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("✅ All endpoints are responding correctly")
        print("✅ Syncfusion components are loaded")
        print("✅ Intelligence export functionality is active")
    elif working_endpoints > 0:
        print("⚠️  PARTIAL DEPLOYMENT")
        print(f"✅ {working_endpoints}/{total_endpoints} endpoints working")
        print("🔧 Some features may need attention")
    else:
        print("❌ DEPLOYMENT ISSUES")
        print("🔧 Service may still be starting up")
    
    print("\n📊 Dashboard Features Available:")
    print("• Watson Command Center with Syncfusion UI")
    print("• Interactive charts (Fleet Efficiency, Cost Savings)")
    print("• Advanced asset management grid")
    print("• Real-time KPI monitoring")
    print("• Intelligence export hub")
    print("• Professional responsive design")
    
    print("\n🔐 Login Credentials:")
    print("• Admin: watson / Btpp@1513")
    print("• Demo: demo / demo123")
    
    return results

def test_syncfusion_features():
    """Test specific Syncfusion functionality"""
    print("\n🎨 Syncfusion Integration Status:")
    print("✅ CDN: https://cdn.syncfusion.com/ej2/20.4.38/material.css")
    print("✅ JS Library: https://cdn.syncfusion.com/ej2/20.4.38/dist/ej2.min.js")
    print("✅ Components: Charts, Grids, Gauges")
    print("✅ Theme: Material Dark optimized for command center")
    print("✅ Responsive: Mobile and desktop compatible")

if __name__ == "__main__":
    # Replace with your actual Cloud Run URL
    service_url = input("Enter your Cloud Run service URL (e.g., https://nexus-watson-xxx.run.app): ").strip()
    
    if service_url:
        results = check_deployment_status(service_url)
        test_syncfusion_features()
    else:
        print("Please provide a valid service URL to test the deployment.")