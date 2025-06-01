
#!/usr/bin/env python3
"""
Simple health check tool for TRAXOVO modules
Tests basic functionality without requiring Selenium
"""

import requests
import json
from datetime import datetime
import sys
import os

def test_endpoint(url, description, expected_status=200):
    """Test a single endpoint"""
    try:
        response = requests.get(url, timeout=10)
        success = response.status_code == expected_status
        return {
            'url': url,
            'description': description,
            'status_code': response.status_code,
            'success': success,
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            'url': url,
            'description': description,
            'status_code': 0,
            'success': False,
            'error': str(e),
            'response_time': 0
        }

def main():
    print("🔍 TRAXOVO Simple Health Check")
    print("=" * 50)
    
    # Base URL - adjust if running on different port
    base_url = "http://0.0.0.0:5000"
    
    # Test endpoints
    endpoints = [
        (f"{base_url}/", "Main Dashboard"),
        (f"{base_url}/fleet_map", "Fleet Map"),
        (f"{base_url}/driver_attendance", "Driver Attendance"),
        (f"{base_url}/asset_manager", "Asset Manager"),
        (f"{base_url}/billing_intelligence", "Billing Intelligence"),
        (f"{base_url}/equipment_billing", "Equipment Billing"),
        (f"{base_url}/ai_assistant", "AI Assistant"),
        (f"{base_url}/admin", "Admin Panel"),
    ]
    
    results = []
    success_count = 0
    
    for url, description in endpoints:
        print(f"Testing {description}...", end=" ")
        result = test_endpoint(url, description)
        results.append(result)
        
        if result['success']:
            print(f"✅ OK ({result['response_time']:.2f}s)")
            success_count += 1
        else:
            print(f"❌ FAILED - {result.get('error', f'Status: {result[\"status_code\"]}')}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {success_count}/{len(endpoints)} endpoints working")
    print(f"Success Rate: {(success_count/len(endpoints)*100):.1f}%")
    
    # Save detailed results
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(endpoints),
        'successful_tests': success_count,
        'success_rate': success_count/len(endpoints)*100,
        'results': results
    }
    
    with open('health_check_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed results saved to: health_check_results.json")
    
    # Exit with error code if any tests failed
    if success_count < len(endpoints):
        sys.exit(1)

if __name__ == "__main__":
    main()
