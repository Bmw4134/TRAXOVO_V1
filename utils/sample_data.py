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
        # Read the Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Clean column names (remove whitespace, lowercase)
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Look for key columns that might exist in the file
        equipment_cols = [col for col in df.columns if 'equip' in str(col).lower()]
        job_cols = [col for col in df.columns if 'job' in str(col).lower()]
        amount_cols = [col for col in df.columns if 'amount' in str(col).lower()]
        days_cols = [col for col in df.columns if 'day' in str(col).lower()]
        cost_code_cols = [col for col in df.columns if 'code' in str(col).lower()]
        
        # Map columns to standard names
        column_mapping = {}
        
        if equipment_cols:
            column_mapping['equipment_id'] = equipment_cols[0]
        if job_cols:
            column_mapping['job_number'] = job_cols[0]
        if amount_cols:
            column_mapping['amount'] = amount_cols[0]
        if days_cols:
            column_mapping['days'] = days_cols[0]
        if cost_code_cols:
            column_mapping['cost_code'] = cost_code_cols[0]
            
        # If we don't have key columns, data is not usable
        if 'equipment_id' not in column_mapping or 'amount' not in column_mapping:
            logger.warning(f"Could not find key columns in {file_path}")
            return []
            
        # Rename columns for consistent processing
        df = df.rename(columns=column_mapping)
        
        # Filter out rows with no equipment ID or amount
        df = df.dropna(subset=['equipment_id'])
        
        # Convert to list of dictionaries
        records = []
        for _, row in df.iterrows():
            record = {}
            for key in ['equipment_id', 'job_number', 'amount', 'days', 'cost_code']:
                if key in df.columns:
                    # Clean and convert the value
                    value = row[key]
                    if key in ['amount', 'days']:
                        # Ensure numeric values are properly converted
                        try:
                            if key == 'amount':
                                value = float(value) if pd.notna(value) else 0.0
                            else:  # days
                                value = int(float(value)) if pd.notna(value) else 0
                        except (ValueError, TypeError):
                            value = 0
                    elif key in ['equipment_id', 'job_number', 'cost_code']:
                        # Ensure string values are properly converted
                        value = str(value).strip() if pd.notna(value) else ''
                        
                    record[key] = value
            
            # Only add records with valid equipment ID and amount
            if record.get('equipment_id') and record.get('amount', 0) > 0:
                records.append(record)
        
        return records
                
    except Exception as e:
        logger.error(f"Error extracting allocation data from {file_path}: {str(e)}")
        return []