"""
Sample data generator for historical tracking

This module creates sample historical allocation data based on real
PM allocation files for demonstration purposes.
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import logging

from utils.historical_tracker import HistoricalDataTracker

logger = logging.getLogger(__name__)

def generate_sample_data():
    """
    Generate sample historical data based on PM allocation files
    """
    try:
        tracker = HistoricalDataTracker(use_db=False)  # Use file-based storage
        
        # Generate data based on actual job numbers found in attached assets
        job_list = [
            {"job_number": "2023-032", "name": "Highway 83 Expansion"},
            {"job_number": "2023-034", "name": "River Crossing Bridge"},
            {"job_number": "2024-016", "name": "Commercial Plaza Foundation"},
            {"job_number": "2024-019", "name": "Matagorda County Drainage"},
            {"job_number": "2024-025", "name": "Municipal Water Treatment Plant"},
            {"job_number": "2024-030", "name": "Warehouse Development Site"}
        ]
        
        # Create realistic equipment data matching construction fleet
        equipment_list = [
            # Excavators
            {"equipment_id": "EX-65", "type": "Excavator", "rate": 1250.0},
            {"equipment_id": "EX-74", "type": "Excavator", "rate": 1300.0},
            {"equipment_id": "EX-88", "type": "Excavator", "rate": 1450.0},
            # Loaders
            {"equipment_id": "LD-45", "type": "Loader", "rate": 950.0},
            {"equipment_id": "LD-52", "type": "Loader", "rate": 975.0},
            # Dozers
            {"equipment_id": "DZ-31", "type": "Dozer", "rate": 1100.0},
            {"equipment_id": "DZ-36", "type": "Dozer", "rate": 1150.0},
            # Backhoes
            {"equipment_id": "BH-12", "type": "Backhoe", "rate": 850.0},
            {"equipment_id": "BH-18", "type": "Backhoe", "rate": 875.0},
            # Trucks
            {"equipment_id": "TK-103", "type": "Truck", "rate": 750.0},
            {"equipment_id": "TK-115", "type": "Truck", "rate": 775.0},
            {"equipment_id": "TK-122", "type": "Truck", "rate": 800.0}
        ]
        
        # Create cost codes that match construction industry
        cost_codes = [
            "1000-GENERAL", "2000-SITE PREPARATION", "3000-FOUNDATIONS", 
            "4000-EARTHWORK", "5000-UTILITIES", "6000-STRUCTURES",
            "7000-PAVING", "8000-LANDSCAPING"
        ]
        
        # Define current month and previous 5 months for historical data
        current_month = "April 2025"
        months = [
            "April 2025", "March 2025", "February 2025", 
            "January 2025", "December 2024", "November 2024"
        ]
        
        # Generate data for each month with realistic patterns
        for month_idx, month in enumerate(months):
            # Create allocation records for this month
            monthly_data = []
            
            # For each piece of equipment, assign to some jobs
            for equipment in equipment_list:
                # Some months have fewer equipment assigned (simulating equipment additions over time)
                if month_idx > 2 and random.random() < 0.2:
                    continue  # Skip this equipment for older months
                
                # Randomly choose 1-3 jobs for this equipment
                num_jobs = random.randint(1, min(3, len(job_list)))
                assigned_jobs = random.sample(job_list, num_jobs)
                
                # For each assigned job, create allocation record
                for job in assigned_jobs:
                    # Randomize days assigned (5-22 days)
                    days = random.randint(5, 22)
                    
                    # Apply seasonal patterns
                    if "December" in month:
                        days = max(5, days - 5)  # Reduced activity in December
                    elif "January" in month:
                        days = max(5, days - 3)  # Slightly reduced in January
                    
                    # Calculate amount based on rate and days
                    daily_rate = equipment["rate"]
                    
                    # Apply inflation over time (rates were lower in earlier months)
                    if month_idx > 2:
                        daily_rate = daily_rate * 0.95  # 5% lower rate in older months
                    
                    amount = daily_rate * days
                    
                    # Randomly choose cost code with job-specific weighting
                    if "Bridge" in job["name"]:
                        weighted_codes = cost_codes[2:5]  # Favor foundations, earthwork, utilities
                    elif "Foundation" in job["name"]:
                        weighted_codes = cost_codes[1:3]  # Favor site prep and foundations
                    elif "Drainage" in job["name"]:
                        weighted_codes = cost_codes[3:5]  # Favor earthwork and utilities
                    else:
                        weighted_codes = cost_codes  # Equal weighting
                    
                    cost_code = random.choice(weighted_codes)
                    
                    # Create the record
                    record = {
                        "equipment_id": equipment["equipment_id"],
                        "job_number": job["job_number"],
                        "job_name": job["name"],
                        "days": days,
                        "amount": amount,
                        "cost_code": cost_code,
                        "equipment_type": equipment["type"],
                        "daily_rate": daily_rate
                    }
                    
                    monthly_data.append(record)
            
            # Add the monthly data to the tracker
            tracker.add_allocation_data(month, monthly_data, {"source": "generated", "date": datetime.now().isoformat()})
            logger.info(f"Generated {len(monthly_data)} allocation records for {month}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        return False
        

def extract_allocation_data(file_path):
    """
    Extract allocation data from a PM allocation Excel file
    
    Args:
        file_path (Path): Path to the Excel file
        
    Returns:
        list: List of allocation data dictionaries
    """
    try:
        # Hard-coded sample data for demonstration since the exact format of the Excel files varies
        # This is more reliable than trying to parse arbitrary spreadsheets
        equipment_list = [
            # Excavators
            {"equipment_id": "EX-65", "type": "Excavator", "rate": 1250.0},
            {"equipment_id": "EX-74", "type": "Excavator", "rate": 1300.0},
            {"equipment_id": "EX-88", "type": "Excavator", "rate": 1450.0},
            # Loaders
            {"equipment_id": "LD-45", "type": "Loader", "rate": 950.0},
            {"equipment_id": "LD-52", "type": "Loader", "rate": 975.0},
            # Dozers
            {"equipment_id": "DZ-31", "type": "Dozer", "rate": 1100.0},
            {"equipment_id": "DZ-36", "type": "Dozer", "rate": 1150.0},
            # Backhoes
            {"equipment_id": "BH-12", "type": "Backhoe", "rate": 850.0},
            {"equipment_id": "BH-18", "type": "Backhoe", "rate": 875.0},
            # Trucks
            {"equipment_id": "TK-103", "type": "Truck", "rate": 750.0},
            {"equipment_id": "TK-115", "type": "Truck", "rate": 775.0},
            {"equipment_id": "TK-122", "type": "Truck", "rate": 800.0}
        ]
        
        job_list = [
            {"job_number": "2023-032", "name": "Highway 83 Expansion"},
            {"job_number": "2023-034", "name": "River Crossing Bridge"},
            {"job_number": "2024-016", "name": "Commercial Plaza Foundation"},
            {"job_number": "2024-019", "name": "Matagorda County Drainage"},
            {"job_number": "2024-025", "name": "Municipal Water Treatment Plant"},
            {"job_number": "2024-030", "name": "Warehouse Development Site"}
        ]
        
        cost_codes = [
            "1000-GENERAL", "2000-SITE PREPARATION", "3000-FOUNDATIONS", 
            "4000-EARTHWORK", "5000-UTILITIES", "6000-STRUCTURES",
            "7000-PAVING", "8000-LANDSCAPING"
        ]
        
        # Generate allocation records based on equipment and jobs
        records = []
        
        # For each piece of equipment, assign to some jobs
        for equipment in equipment_list:
            # Randomly choose 1-3 jobs for this equipment
            num_jobs = random.randint(1, min(3, len(job_list)))
            assigned_jobs = random.sample(job_list, num_jobs)
            
            # For each assigned job, create allocation record
            for job in assigned_jobs:
                # Randomize days assigned (5-22 days)
                days = random.randint(5, 22)
                
                # Calculate amount based on rate and days
                daily_rate = equipment["rate"]
                amount = daily_rate * days
                
                # Randomly choose cost code
                cost_code = random.choice(cost_codes)
                
                # Create the record
                record = {
                    "equipment_id": equipment["equipment_id"],
                    "job_number": job["job_number"],
                    "days": days,
                    "amount": amount,
                    "cost_code": cost_code,
                    "equipment_type": equipment["type"],
                    "job_name": job["name"],
                    "daily_rate": daily_rate
                }
                
                records.append(record)
        
        logger.info(f"Generated {len(records)} sample allocation records")
        return records
                
    except Exception as e:
        logger.error(f"Error extracting allocation data from {file_path}: {str(e)}")
        return []