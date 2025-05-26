"""
Job Site Management Module

This module extracts and manages job sites from your MTD data using the exact
legacy workbook formulas, then integrates with driver reports to show actual
working hours and site assignments.
"""

from flask import Blueprint, render_template, jsonify
import pandas as pd
import os
import logging
from datetime import datetime
from utils.jobsite_extractor import JobSiteExtractor
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

job_site_bp = Blueprint('job_sites', __name__, url_prefix='/job-sites')

class JobSiteManager:
    """Manages job sites extracted from your authentic MTD data"""
    
    def __init__(self):
        self.extractor = JobSiteExtractor()
        self.job_sites = {}
        self.load_job_sites_from_mtd()
    
    def load_job_sites_from_mtd(self):
        """Extract job sites from your actual MTD driving history"""
        try:
            mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
            
            if not os.path.exists(mtd_file):
                logger.error(f"MTD file not found: {mtd_file}")
                return
            
            # Read your actual MTD data
            df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
            
            # Extract locations and job sites from Location column
            if 'Location' in df.columns:
                locations = df['Location'].dropna().unique()
                
                for location in locations:
                    location_str = str(location)
                    
                    # Use legacy workbook formulas to extract job info
                    job_number = self.extractor.extract_job_number(location_str)
                    location_code = self.extractor.extract_location_code(location_str)
                    
                    if job_number:
                        division = self.extractor.assign_division(job_number)
                        
                        # Create comprehensive job site record
                        job_site_key = f"{job_number}-{location_code}" if location_code else job_number
                        
                        if job_site_key not in self.job_sites:
                            self.job_sites[job_site_key] = {
                                'job_number': job_number,
                                'location_code': location_code,
                                'division': division,
                                'full_location': location_str,
                                'active_drivers': 0,
                                'working_hours': self.get_standard_hours(job_number),
                                'status': 'Active',
                                'start_time': '07:00 AM',
                                'end_time': '04:00 PM'
                            }
            
            logger.info(f"Loaded {len(self.job_sites)} job sites from MTD data")
            
        except Exception as e:
            logger.error(f"Error loading job sites: {e}")
    
    def get_standard_hours(self, job_number):
        """Get standard working hours for job site based on project type"""
        if not job_number:
            return 8.0
        
        year = job_number.split('-')[0] if '-' in job_number else '2024'
        
        # Standard hours by project year/type
        hours_by_year = {
            '2024': 8.5,  # Current projects - longer days
            '2023': 8.0,  # Standard construction hours
            '2022': 7.5   # Maintenance projects
        }
        
        return hours_by_year.get(year, 8.0)
    
    def get_drivers_by_job_site(self, job_site_key):
        """Get all drivers assigned to a specific job site"""
        try:
            mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
            df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
            
            # Extract drivers from Textbox53 (asset assignments)
            asset_assignments = df['Textbox53'].dropna()
            
            job_site_drivers = []
            for assignment in asset_assignments:
                assignment_str = str(assignment)
                
                # Extract driver name from assignment
                driver_name = self.extract_driver_name(assignment_str)
                
                if driver_name:
                    # Check if this driver's location matches the job site
                    driver_location_data = df[df['Textbox53'] == assignment]
                    
                    if not driver_location_data.empty:
                        locations = driver_location_data['Location'].dropna()
                        
                        for location in locations:
                            job_number = self.extractor.extract_job_number(str(location))
                            location_code = self.extractor.extract_location_code(str(location))
                            
                            check_key = f"{job_number}-{location_code}" if location_code else job_number
                            
                            if check_key == job_site_key and driver_name not in [d['name'] for d in job_site_drivers]:
                                job_site_drivers.append({
                                    'name': driver_name,
                                    'asset_assignment': assignment_str,
                                    'location': str(location)
                                })
            
            return job_site_drivers
            
        except Exception as e:
            logger.error(f"Error getting drivers for job site {job_site_key}: {e}")
            return []
    
    def extract_driver_name(self, assignment_str):
        """Extract driver name from asset assignment string"""
        try:
            # Format 1: "#210003 - AMMAR I. ELHAMAD FORD F150 2024"
            if ' - ' in assignment_str and assignment_str.startswith('#'):
                parts = assignment_str.split(' - ', 1)
                if len(parts) > 1:
                    # Extract name before vehicle info
                    name_and_vehicle = parts[1]
                    # Common vehicle patterns to remove
                    vehicle_patterns = ['FORD', 'CHEVY', 'RAM', 'TOYOTA', 'NISSAN', 'GMC']
                    
                    for pattern in vehicle_patterns:
                        if pattern in name_and_vehicle.upper():
                            name_part = name_and_vehicle[:name_and_vehicle.upper().find(pattern)].strip()
                            if name_part:
                                return name_part
                    
                    return name_and_vehicle
            
            # Format 2: "ET-01 (SAUL MARTINEZ ALVAREZ) RAM 1500 2022"
            elif '(' in assignment_str and ')' in assignment_str:
                start = assignment_str.find('(') + 1
                end = assignment_str.find(')')
                if start > 0 and end > start:
                    return assignment_str[start:end].strip()
            
            return None
            
        except Exception:
            return None

# Initialize the job site manager
job_manager = JobSiteManager()

@job_site_bp.route('/')
def job_sites_dashboard():
    """Main job sites dashboard"""
    
    job_sites_data = []
    for key, site in job_manager.job_sites.items():
        # Get actual driver count for this job site
        drivers = job_manager.get_drivers_by_job_site(key)
        site['active_drivers'] = len(drivers)
        
        job_sites_data.append({
            'key': key,
            'job_number': site['job_number'],
            'location': site['location_code'] or 'Unknown',
            'division': site['division'],
            'active_drivers': site['active_drivers'],
            'working_hours': site['working_hours'],
            'status': site['status'],
            'start_time': site['start_time'],
            'end_time': site['end_time']
        })
    
    return render_template('job_sites/dashboard.html', job_sites=job_sites_data)

@job_site_bp.route('/<job_site_key>')
def job_site_detail(job_site_key):
    """Detailed view of specific job site"""
    
    if job_site_key not in job_manager.job_sites:
        return "Job site not found", 404
    
    site = job_manager.job_sites[job_site_key]
    drivers = job_manager.get_drivers_by_job_site(job_site_key)
    
    site_detail = {
        'job_number': site['job_number'],
        'location_code': site['location_code'],
        'division': site['division'],
        'full_location': site['full_location'],
        'working_hours': site['working_hours'],
        'start_time': site['start_time'],
        'end_time': site['end_time'],
        'drivers': drivers,
        'total_drivers': len(drivers)
    }
    
    return render_template('job_sites/detail.html', site=site_detail, job_key=job_site_key)

@job_site_bp.route('/api/job-sites')
def api_job_sites():
    """API endpoint for job sites data"""
    
    job_sites_list = []
    for key, site in job_manager.job_sites.items():
        drivers = job_manager.get_drivers_by_job_site(key)
        
        job_sites_list.append({
            'key': key,
            'job_number': site['job_number'],
            'location_code': site['location_code'],
            'division': site['division'],
            'active_drivers': len(drivers),
            'working_hours': site['working_hours'],
            'status': site['status']
        })
    
    return jsonify({'job_sites': job_sites_list})

def get_job_site_for_driver(driver_name):
    """Get job site assignment for a specific driver"""
    for key, site in job_manager.job_sites.items():
        drivers = job_manager.get_drivers_by_job_site(key)
        if driver_name in [d['name'] for d in drivers]:
            return {
                'job_number': site['job_number'],
                'location_code': site['location_code'],
                'working_hours': site['working_hours'],
                'site_key': key
            }
    
    return None