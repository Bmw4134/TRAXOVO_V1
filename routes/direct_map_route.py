"""
Direct Map Route

This module provides a direct route to the standalone map,
bypassing the normal template inheritance that might cause 500 errors.
"""

from flask import Blueprint, render_template, jsonify

direct_map = Blueprint('direct_map', __name__)

@direct_map.route('/direct-map')
def show_direct_map():
    """Render the direct map template"""
    return render_template('direct_map.html')

@direct_map.route('/api/mock-assets')
def mock_assets():
    """Return mock asset data for the direct map"""
    mockAssets = [
        {
            "asset_id": "RTC-02",
            "id": "RTC-02",
            "name": "RTC-02 TEREX RT665 Crane +",
            "make": "TEREX",
            "model": "RT665",
            "type": "Crane",
            "latitude": 32.7808342,
            "longitude": -96.78361,
            "location": "2023-032 SH 345 BRIDGE REHABILITATION",
            "last_update": "5/21/2025 2:40:55 PM CT",
            "status": "active",
            "driver": ""
        },
        {
            "asset_id": "BH-15",
            "id": "BH-15",
            "name": "BH-15 CAT 420F 2014 Backhoe +",
            "make": "CAT",
            "model": "420F",
            "type": "Backhoe",
            "latitude": 29.643177,
            "longitude": -95.34747,
            "location": "HOU YARD/SHOP",
            "last_update": "5/21/2025 3:29:05 PM CT",
            "status": "active",
            "driver": ""
        },
        {
            "asset_id": "EX-30",
            "id": "EX-30",
            "name": "EX-30 CAT 320D L 2011 Excavator +",
            "make": "CAT",
            "model": "320D L",
            "type": "Excavator",
            "latitude": 32.3848953,
            "longitude": -97.3316345,
            "location": "2024-019 (15) Tarrant VA Bridge Rehab",
            "last_update": "5/21/2025 4:59:18 PM CT",
            "status": "active",
            "driver": ""
        },
        {
            "asset_id": "R-09",
            "id": "R-09",
            "name": "R-09 CAT CP563 2006 Roller +",
            "make": "CAT",
            "model": "CP563",
            "type": "Roller",
            "latitude": 31.9183979,
            "longitude": -102.225624,
            "location": "2023-007 Ector BI 20E Rehab Roadway",
            "last_update": "5/21/2025 5:04:57 PM CT",
            "status": "active",
            "driver": ""
        },
        {
            "asset_id": "ML-03",
            "id": "ML-03",
            "name": "ML-03 GENIE S60X 2011 Man Lift +",
            "make": "GENIE",
            "model": "S60X",
            "type": "Man Lift",
            "latitude": 32.78879,
            "longitude": -96.79155,
            "location": "2023-032 SH 345 BRIDGE REHABILITATION",
            "last_update": "5/21/2025 8:55:41 AM CT",
            "status": "active",
            "driver": ""
        },
        {
            "asset_id": "DT-07",
            "id": "DT-07",
            "name": "DT-07 FORD F550 2012 Medium Truck +",
            "make": "FORD",
            "model": "F550",
            "type": "Medium Truck",
            "latitude": 32.61358,
            "longitude": -97.3076,
            "location": "DFW Yard",
            "last_update": "5/21/2025 9:46:51 AM CT",
            "status": "active",
            "driver": ""
        }
    ]
    return jsonify(mockAssets)

@direct_map.route('/api/mock-job-sites')
def mock_job_sites():
    """Return mock job site data for the direct map"""
    mockJobSites = [
        {
            "job_number": "2023-032",
            "name": "2023-032 SH 345 Bridge Rehabilitation",
            "latitude": 32.7807,
            "longitude": -96.7835,
            "radius": 1000,
            "color": "#33D4FF"
        },
        {
            "job_number": "DFW-YARD",
            "name": "DFW Yard",
            "latitude": 32.6138,
            "longitude": -97.3076,
            "radius": 800,
            "color": "#FF33A8"
        },
        {
            "job_number": "2023-007",
            "name": "2023-007 Ector BI 20E Rehab Roadway",
            "latitude": 31.9158,
            "longitude": -102.2303,
            "radius": 1500,
            "color": "#3357FF"
        },
        {
            "job_number": "HOU-YARD",
            "name": "HOU Yard/Shop",
            "latitude": 29.6433,
            "longitude": -95.3474,
            "radius": 800,
            "color": "#33FF57"
        },
        {
            "job_number": "2024-012",
            "name": "2024-012 Dal IH635 U-Turn Bridge",
            "latitude": 32.9241,
            "longitude": -96.9933,
            "radius": 1000,
            "color": "#FF5733"
        },
        {
            "job_number": "2024-019",
            "name": "2024-019 (15) Tarrant VA Bridge Rehab",
            "latitude": 32.3849,
            "longitude": -97.3316,
            "radius": 1200,
            "color": "#33A8FF"
        }
    ]
    return jsonify(mockJobSites)