#!/usr/bin/env python3
"""
Quick GPS debugging script to test why no drivers are matching job sites
"""

import pandas as pd
import math
import json

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in meters"""
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    # Haversine formula
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# Load job sites
with open('data/traxora_jobsite_catalog_v2.json', 'r') as f:
    job_sites = json.load(f)

print("Job Sites Loaded:")
for site in job_sites:
    print(f"  {site['job_number']}: {site['latitude']}, {site['longitude']} (radius: {site['radius']}m)")

# Load MTD data and check first driver
mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)

print(f"\nColumns in MTD file: {df.columns.tolist()}")

# Filter out rows with empty GPS data first
gps_rows = df.dropna(subset=['Latitude', 'Longitude'])
print(f"Total rows with GPS data: {len(gps_rows)}")

# Get first driver with actual GPS data
first_driver_data = gps_rows[gps_rows['Textbox53'].str.contains('AMMAR', na=False)].head(5)

print(f"\nFirst 5 GPS records for AMMAR:")
for _, record in first_driver_data.iterrows():
    lat = record.get('Latitude')
    lon = record.get('Longitude')
    location = record.get('Location', 'Unknown')
    
    print(f"  GPS: {lat}, {lon} - {location}")
    
    if lat and lon and not pd.isna(lat) and not pd.isna(lon):
        # Check distance to each job site
        for site in job_sites:
            distance = calculate_distance(lat, lon, site['latitude'], site['longitude'])
            within_radius = distance <= site['radius']
            print(f"    Distance to {site['job_number']}: {distance:.0f}m (within radius: {within_radius})")