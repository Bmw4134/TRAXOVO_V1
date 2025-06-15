#!/usr/bin/env python3
"""
Quantum NEXUS Dynamic System Verification Test
Tests all dynamic components and API endpoints
"""

import requests
import json
import time

def test_quantum_nexus_system():
    """Test complete quantum nexus dynamic system"""
    
    base_url = "http://localhost:5000"
    results = {}
    
    print("🔍 Testing Quantum NEXUS Dynamic System...")
    print("=" * 50)
    
    # Test main application
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        results['main_app'] = {
            'status': response.status_code,
            'accessible': response.status_code == 200,
            'response_time': response.elapsed.total_seconds()
        }
        print(f"✓ Main Application: HTTP {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
    except Exception as e:
        results['main_app'] = {'status': 'error', 'error': str(e)}
        print(f"✗ Main Application: {e}")
    
    # Test dynamic API endpoints
    endpoints = [
        '/api/fleet-metrics',
        '/api/dynamic-dashboard', 
        '/api/real-time-assets',
        '/api/external-connections',
        '/api/quantum-nexus-status'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
            results[endpoint] = {
                'status': response.status_code,
                'accessible': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]['has_data'] = 'data' in data
                    results[endpoint]['timestamp'] = data.get('timestamp', 'N/A')
                    print(f"✓ {endpoint}: HTTP {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                except:
                    print(f"⚠ {endpoint}: HTTP {response.status_code} (non-JSON response)")
            else:
                print(f"✗ {endpoint}: HTTP {response.status_code}")
                
        except Exception as e:
            results[endpoint] = {'status': 'error', 'error': str(e)}
            print(f"✗ {endpoint}: {e}")
    
    # Test dashboard page
    try:
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        results['dashboard'] = {
            'status': response.status_code,
            'accessible': response.status_code == 200,
            'response_time': response.elapsed.total_seconds()
        }
        print(f"✓ Dashboard: HTTP {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
    except Exception as e:
        results['dashboard'] = {'status': 'error', 'error': str(e)}
        print(f"✗ Dashboard: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r.get('accessible', False))
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Check for quantum nexus functionality
    if results.get('/api/quantum-nexus-status', {}).get('accessible'):
        print("✓ Quantum NEXUS Engine: OPERATIONAL")
    else:
        print("✗ Quantum NEXUS Engine: NOT ACCESSIBLE")
    
    if results.get('/api/fleet-metrics', {}).get('accessible'):
        print("✓ Dynamic Fleet Metrics: OPERATIONAL")
    else:
        print("✗ Dynamic Fleet Metrics: NOT ACCESSIBLE")
    
    if results.get('main_app', {}).get('accessible'):
        print("✓ Web Interface: OPERATIONAL")
    else:
        print("✗ Web Interface: NOT ACCESSIBLE")
    
    return results

if __name__ == "__main__":
    results = test_quantum_nexus_system()
    
    # Save results
    with open('quantum_nexus_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: quantum_nexus_test_results.json")