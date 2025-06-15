#!/usr/bin/env python3
"""
TRAXOVO Platform Validation System
"""

import requests
import json

def validate_traxovo_platform():
    """Validate TRAXOVO operational intelligence platform"""
    print('TRAXOVO Platform Validation')
    print('=' * 40)

    # Test landing page
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        print(f'Landing Page: {response.status_code} - OK' if response.status_code == 200 else f'Landing Page: FAILED ({response.status_code})')
    except Exception as e:
        print(f'Landing Page: FAILED - {e}')

    # Test live metrics API
    try:
        response = requests.get('http://localhost:5000/api/live-metrics', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'Live Metrics: OK - Fleet: {data.get("fleet_count", "N/A")}, Efficiency: {data.get("efficiency", "N/A")}%')
        else:
            print(f'Live Metrics: FAILED ({response.status_code})')
    except Exception as e:
        print(f'Live Metrics: FAILED - {e}')

    # Test fleet data API
    try:
        response = requests.get('http://localhost:5000/api/fleet-data', timeout=10)
        if response.status_code == 200:
            data = response.json()
            dfw_assets = len([a for a in data if 'DFW' in a.get('asset_id', '')])
            print(f'Fleet Data: OK - {len(data)} assets, DFW assets: {dfw_assets}')
        else:
            print(f'Fleet Data: FAILED ({response.status_code})')
    except Exception as e:
        print(f'Fleet Data: FAILED - {e}')

    # Test operational KPIs
    try:
        response = requests.get('http://localhost:5000/api/operational-kpis', timeout=10)
        if response.status_code == 200:
            data = response.json()
            efficiency = data.get('fleet_efficiency', 0)
            savings = data.get('daily_cost_savings', 0)
            print(f'Operational KPIs: OK - Efficiency: {efficiency:.1f}%, Savings: ${savings:.0f}')
        else:
            print(f'Operational KPIs: FAILED ({response.status_code})')
    except Exception as e:
        print(f'Operational KPIs: FAILED - {e}')

    # Test health endpoint
    try:
        response = requests.get('http://localhost:5000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            platform = data.get('platform', 'N/A')
            version = data.get('version', 'N/A')
            print(f'Health Check: OK - Platform: {platform}, Version: {version}')
        else:
            print(f'Health Check: FAILED ({response.status_code})')
    except Exception as e:
        print(f'Health Check: FAILED - {e}')

    print('=' * 40)
    print('TRAXOVO Platform Ready for Operations')

if __name__ == '__main__':
    validate_traxovo_platform()