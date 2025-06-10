#!/usr/bin/env python3
"""
NEXUS Quick Deployment Validator
Rapid validation of critical deployment readiness
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, timeout=10):
    """Test API endpoint functionality"""
    try:
        response = requests.get(url, timeout=timeout)
        return {
            "status": "success" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "response_size": len(response.content),
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)[:100]
        }

def run_nexus_validation():
    """Run comprehensive NEXUS validation"""
    print("================================================================================")
    print("🚀 NEXUS ∞ RAPID DEPLOYMENT VALIDATION")
    print("================================================================================")
    
    base_url = "http://localhost:5000"
    
    # Critical API endpoints to test
    endpoints = [
        "/api/comprehensive-data",
        "/api/asset-overview", 
        "/api/safety-overview",
        "/api/maintenance-status",
        "/api/fuel-energy",
        "/api/gauge-status",
        "/api/traxovo/automation-status",
        "/api/qnis-vector-data"
    ]
    
    total_endpoints = len(endpoints)
    successful_endpoints = 0
    
    print(f"Testing {total_endpoints} critical API endpoints...")
    print()
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...", end=" ")
        result = test_api_endpoint(f"{base_url}{endpoint}")
        
        if result["status"] == "success":
            successful_endpoints += 1
            size_kb = result["response_size"] / 1024
            print(f"✅ SUCCESS ({size_kb:.1f}KB, {result['response_time']:.2f}s)")
        else:
            print(f"❌ FAILED - {result.get('error', 'Unknown error')}")
    
    # Calculate success rate
    success_rate = (successful_endpoints / total_endpoints) * 100
    
    print()
    print("================================================================================")
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("================================================================================")
    print(f"API Endpoints: {successful_endpoints}/{total_endpoints} ({success_rate:.1f}%)")
    
    # Determine deployment status
    if success_rate >= 90:
        status = "🟢 READY FOR DEPLOYMENT"
        recommendation = "System is production-ready"
    elif success_rate >= 75:
        status = "🟡 NEEDS MINOR FIXES"
        recommendation = "Minor optimizations needed"
    else:
        status = "🔴 REQUIRES ATTENTION"
        recommendation = "Critical issues must be resolved"
    
    print(f"Status: {status}")
    print(f"Recommendation: {recommendation}")
    print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test dashboard accessibility
    print("Testing dashboard accessibility...")
    dashboard_result = test_api_endpoint(f"{base_url}/dashboard")
    if dashboard_result["status"] == "success":
        print("✅ Dashboard accessible")
    else:
        print("❌ Dashboard issues detected")
    
    print("================================================================================")
    print("🎯 NEXUS VALIDATION COMPLETE")
    print("================================================================================")
    
    return {
        "success_rate": success_rate,
        "successful_endpoints": successful_endpoints,
        "total_endpoints": total_endpoints,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    run_nexus_validation()