"""
Cookie Extraction Guide for Ground Works Data Extraction
Instructions for extracting session cookies from authenticated browser
"""

def generate_cookie_extraction_instructions():
    """Generate step-by-step instructions for cookie extraction"""
    
    instructions = """
    GROUND WORKS DATA EXTRACTION - COOKIE AUTHENTICATION GUIDE
    ==========================================================
    
    Since you have admin access to Ground Works, we need to extract your session cookies
    to authenticate the data extraction tools properly.
    
    STEP 1: Extract Cookies from Edge Browser
    -----------------------------------------
    
    In your Edge browser while logged into Ground Works:
    
    1. Press F12 to open Developer Tools
    2. Go to the "Application" tab (or "Storage" in some versions)
    3. In the left sidebar, expand "Cookies"
    4. Click on "https://groundworks.ragleinc.com"
    5. You'll see a list of cookies - copy ALL of them
    
    Look for cookies with names like:
    - session_id
    - auth_token
    - .ASPXAUTH
    - JSESSIONID
    - connect.sid
    - laravel_session
    - Any cookie with "auth", "session", or "token" in the name
    
    STEP 2: Format Cookie String
    ----------------------------
    
    Copy each cookie in this format:
    cookie_name=cookie_value; cookie_name2=cookie_value2; 
    
    Example:
    session_id=abc123def456; auth_token=xyz789; .ASPXAUTH=long_encrypted_string;
    
    STEP 3: Alternative Method - Copy as cURL
    ----------------------------------------
    
    1. In Ground Works, right-click on any page
    2. Select "Inspect" or press F12
    3. Go to "Network" tab
    4. Refresh the page or navigate to /projects
    5. Find any request to groundworks.ragleinc.com
    6. Right-click the request → Copy → Copy as cURL
    7. Look for the -H 'Cookie: ...' line in the cURL command
    
    STEP 4: Use Cookies for Data Extraction
    ---------------------------------------
    
    Once you have the cookie string, run:
    
    python extract_with_cookies.py "your_cookie_string_here"
    
    This will authenticate and extract:
    - All project data with real contract values
    - Complete asset inventory with 737+ items
    - Personnel records and assignments  
    - Billing data and invoice history
    - Schedule and calendar information
    - Reports and analytics data
    
    CRITICAL: Extract NOW While Access Active
    ========================================
    
    Since your access may be revoked soon, extract the cookies immediately
    while you're still authenticated to Ground Works.
    
    The extraction will capture:
    - Project details (E Long Avenue, Pleasant Run, etc.)
    - Real contract amounts and completion percentages
    - Actual asset IDs (PT-107, SS-09, AB-011, etc.)
    - Personnel assignments and contact information
    - Billing history and payment status
    - Complete operational data
    
    """
    
    return instructions

def create_cookie_based_extractor():
    """Create the cookie-based extraction script"""
    
    extractor_code = '''
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
    
    print(f"\\nAuthenticated extraction complete!")
    print(f"Successfully extracted from {successful_extractions} endpoints")
    print(f"Data saved to: {filename}")
    
    return extracted_data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_with_cookies.py \\"cookie_string\\"")
        sys.exit(1)
    
    cookie_string = sys.argv[1]
    extract_with_cookies(cookie_string)
'''
    
    with open('extract_with_cookies.py', 'w') as f:
        f.write(extractor_code)
    
    print("Created extract_with_cookies.py")

if __name__ == "__main__":
    print(generate_cookie_extraction_instructions())
    create_cookie_based_extractor()