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
        tracker = HistoricalDataTracker()
        
        # Get a list of PM allocation Excel files from attached_assets directory
        asset_dir = Path('attached_assets')
        pm_files = list(asset_dir.glob('*EQMO*APRIL*.xlsx'))
        
        if not pm_files:
            logger.warning("No PM allocation files found in attached_assets directory")
            return False
        
        # Use the primary April 2025 file as the basis for our April dataset
        april_file = None
        for file in pm_files:
            if "TR-FINAL REVISIONS" in file.name:
                april_file = file
                break
        
        if not april_file:
            april_file = pm_files[0]  # Fallback to first file if no "FINAL" found
            
        logger.info(f"Using {april_file.name} as base for April 2025 data")
        
        # Create sample data for the current month (April 2025)
        april_data = extract_allocation_data(april_file)
        current_month = "April 2025"
        
        # Add the data to the historical tracker
        tracker.add_allocation_data(current_month, april_data, {"source_file": april_file.name})
        
        # Create data for previous months based on April data but with variations
        for month_offset in range(1, 6):
            # Calculate the previous month's date
            current_date = datetime.strptime(f"April 2025", "%B %Y")
            prev_date = current_date - timedelta(days=30 * month_offset)
            prev_month = prev_date.strftime("%B %Y")
            
            # Generate variation of the April data for the previous month
            prev_data = []
            for item in april_data:
                # Create a copy with some random variations
                variation = random.uniform(0.85, 1.15)  # 15% variation up or down
                
                # Some equipment might not be present in earlier months
                if random.random() > 0.9:
                    continue
                    
                # Copy the item with variations
                new_item = item.copy()
                new_item['amount'] = item['amount'] * variation
                new_item['days'] = max(1, round(item['days'] * variation))
                
                # Occasionally change job assignments for more realistic data
                if random.random() > 0.7:
                    # Choose another job from the dataset if possible
                    job_numbers = set(i['job_number'] for i in april_data if 'job_number' in i)
                    if len(job_numbers) > 1 and 'job_number' in new_item:
                        current_job = new_item['job_number']
                        alternate_jobs = list(job_numbers - {current_job})
                        new_item['job_number'] = random.choice(alternate_jobs)
                
                prev_data.append(new_item)
                
            # Add the historical data
            tracker.add_allocation_data(prev_month, prev_data, {"generated": True})
            logger.info(f"Generated historical data for {prev_month}")
        
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