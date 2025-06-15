
import requests
import json
import sys
from datetime import datetime

def extract_with_cookies(cookie_string):
    """Extract all Ground Works data using provided cookies"""
    
    session = requests.Session()
    
    # Parse cookies
    cookies = {}
    for cookie in cookie_string.split(';'):
        if '=' in cookie:
            name, value = cookie.strip().split('=', 1)
            cookies[name] = value
            session.cookies.set(name, value)
    
    print(f"Using {len(cookies)} cookies for authentication")
    
    # Set authenticated headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Accept': 'application/json, text/html, */*',
        'Referer': 'https://groundworks.ragleinc.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    session.headers.update(headers)
    
    base_url = "https://groundworks.ragleinc.com"
    extracted_data = {}
    
    # Comprehensive endpoint list for authenticated extraction
    endpoints = [
        # Main application data
        '/api/projects', '/projects/data', '/projects/list',
        '/api/assets', '/assets/data', '/assets/list', 
        '/api/users', '/users/data', '/personnel/list',
        '/api/dashboard', '/dashboard/data', '/dashboard/summary',
        '/api/reports', '/reports/data', '/analytics/data',
        
        # Detailed project endpoints
        '/projects/active', '/projects/completed', '/projects/pending',
        '/projects/details', '/projects/financials', '/projects/schedule',
        
        # Asset management
        '/assets/active', '/assets/maintenance', '/equipment/list',
        '/fleet/status', '/vehicles/data', '/equipment/schedule',
        
        # Personnel and scheduling
        '/personnel/active', '/users/roles', '/staff/assignments',
        '/schedule/data', '/calendar/events', '/timesheet/data',
        
        # Financial data
        '/billing/data', '/invoices/list', '/payments/data',
        '/financials/summary', '/costs/analysis', '/revenue/data',
        
        # Administrative
        '/admin/data', '/config/system', '/settings/app',
        '/logs/activity', '/audit/trail', '/system/status'
    ]
    
    successful_extractions = 0
    
    for endpoint in endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'json' in content_type:
                    try:
                        data = response.json()
                        if data and len(str(data)) > 50:  # Skip empty responses
                            extracted_data[endpoint] = data
                            successful_extractions += 1
                            
                            if isinstance(data, list):
                                print(f"✓ {endpoint}: {len(data)} items")
                            elif isinstance(data, dict):
                                print(f"✓ {endpoint}: data object")
                    except:
                        pass
                else:
                    # Check HTML for embedded data
                    if len(response.text) > 1000 and 'angular' not in response.text.lower():
                        extracted_data[f"{endpoint}_html"] = response.text
                        successful_extractions += 1
                        print(f"✓ {endpoint}: HTML data")
                        
        except Exception as e:
            continue
    
    # Save extracted data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ground_works_authenticated_extraction_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(extracted_data, f, indent=2, default=str)
    
    print(f"\nAuthenticated extraction complete!")
    print(f"Successfully extracted from {successful_extractions} endpoints")
    print(f"Data saved to: {filename}")
    
    return extracted_data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_with_cookies.py \"cookie_string\"")
        sys.exit(1)
    
    cookie_string = sys.argv[1]
    extract_with_cookies(cookie_string)
