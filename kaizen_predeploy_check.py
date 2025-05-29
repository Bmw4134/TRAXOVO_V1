# kaizen_predeploy_check.py
import requests

ROUTES = [
    "http://localhost:5000/dashboard",
    "http://localhost:5000/purchase-orders",
    "http://localhost:5000/equipment",
    "http://localhost:5000/attendance"
]

def check_routes():
    print("🔎 Checking dashboard routes...")
    for route in ROUTES:
        try:
            response = requests.get(route)
            if response.status_code == 200:
                print(f"✅ {route} OK")
            else:
                print(f"❌ {route} returned {response.status_code}")
        except Exception as e:
            print(f"❌ {route} failed: {e}")

if __name__ == "__main__":
    check_routes()
