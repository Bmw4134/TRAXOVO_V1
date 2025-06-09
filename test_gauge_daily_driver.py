#!/usr/bin/env python3
"""
Test GAUGE Daily Driver Reporting Function
Connect to authentic gaugesmart.com with Watson credentials
"""

import requests
import json
from datetime import datetime
import sqlite3

def test_gauge_connection():
    """Test connection to actual GAUGE platform"""
    username = "bwatson"
    password = "Plsw@2900413477"
    base_url = "https://gaugesmart.com"
    
    session = requests.Session()
    
    # Try different authentication endpoints
    auth_endpoints = [
        "/login",
        "/api/login", 
        "/auth/login",
        "/user/login"
    ]
    
    print("Testing GAUGE platform connection...")
    print(f"Target: {base_url}")
    print(f"Username: {username}")
    
    for endpoint in auth_endpoints:
        try:
            print(f"\nTrying endpoint: {endpoint}")
            
            # Try form-based login
            login_url = f"{base_url}{endpoint}"
            login_data = {
                "username": username,
                "password": password,
                "email": username,
                "user": username
            }
            
            response = session.post(login_url, data=login_data, timeout=10)
            print(f"Response status: {response.status_code}")
            print(f"Response URL: {response.url}")
            
            if response.status_code == 200:
                # Check if we're successfully authenticated
                if "dashboard" in response.url.lower() or "welcome" in response.text.lower():
                    print("✓ Authentication successful!")
                    return session, True
                    
        except Exception as e:
            print(f"Error with {endpoint}: {str(e)}")
    
    return session, False

def test_daily_driver_report():
    """Test daily driver reporting function"""
    print("\nTesting Daily Driver Report Function...")
    
    try:
        import traxovo_agent_integration
        
        # Test data for daily driver report
        test_data = {
            "driver_id": "watson_001",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "hours_worked": 8.5,
            "miles_driven": 145,
            "equipment_used": "Ford F150 Fleet Vehicle",
            "route": "Fort Worth Zone 580-582"
        }
        
        result = traxovo_agent_integration.process_daily_driver_report(test_data)
        print("Daily driver report result:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"Error testing daily driver report: {str(e)}")
        return {"error": str(e)}

def check_database_records():
    """Check if authentic records exist in database"""
    databases = [
        "authentic_assets.db",
        "traxovo_agent.db", 
        "fleet_tracking.db"
    ]
    
    print("\nChecking database records...")
    
    for db_file in databases:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"\n{db_file}:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} records")
                
            conn.close()
            
        except Exception as e:
            print(f"  {db_file}: Not found or error - {str(e)}")

def main():
    print("GAUGE Authentication and Daily Driver Testing")
    print("=" * 50)
    
    # Test GAUGE connection
    session, authenticated = test_gauge_connection()
    
    # Test daily driver reporting
    driver_result = test_daily_driver_report()
    
    # Check database records
    check_database_records()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"GAUGE Authentication: {'SUCCESS' if authenticated else 'FAILED'}")
    print(f"Daily Driver Function: {'SUCCESS' if 'error' not in driver_result else 'FAILED'}")
    
    return {
        "gauge_authenticated": authenticated,
        "daily_driver_test": driver_result,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    result = main()
    
    with open('gauge_test_results.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\nTest results saved to gauge_test_results.json")