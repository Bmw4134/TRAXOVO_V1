"""
TRAXOVO Consolidated Billing Intelligence
Unified billing processing with all authentic data mappings preserved
"""

import os
import pandas as pd
from collections import defaultdict
import difflib
from flask import Blueprint, render_template, jsonify, request

billing_bp = Blueprint('billing_consolidated', __name__)

def get_authentic_billing_files():
    """Load authentic RAGLE billing files from uploads"""
    billing_files = []
    
    # Your authentic Foundation billing files (preserved mapping)
    authentic_files = [
        'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
        'attached_assets/RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm',
        'attached_assets/EQUIPMENT USAGE DETAIL 010125-053125.xlsx',
        'attached_assets/Equipment Detail History Report_01.01.2020-05.31.2025.xlsx'
    ]
    
    for file_path in authentic_files:
        if os.path.exists(file_path):
            billing_files.append({
                'path': file_path,
                'name': os.path.basename(file_path),
                'type': 'authentic_ragle_data'
            })
    
    return billing_files

def detect_intelligent_duplicates(consolidated_data):
    """Enhanced duplicate detection preserving all logic from development sessions"""
    if not consolidated_data:
        return [], {'duplicate_count': 0, 'equipment_groups': 0, 'clean_records': 0}
    
    equipment_groups = defaultdict(list)
    intelligent_duplicates = []
    
    # Fuzzy matching logic for equipment identification
    for record in consolidated_data:
        equipment_id = record['equipment_id'].upper().strip()
        matched = False
        
        for existing_id in equipment_groups.keys():
            similarity = difflib.SequenceMatcher(None, equipment_id, existing_id).ratio()
            if similarity > 0.85:  # Preserved threshold from development
                equipment_groups[existing_id].append(record)
                matched = True
                break
        
        if not matched:
            equipment_groups[equipment_id].append(record)
    
    # Amount-based duplicate detection
    for group_id, records in equipment_groups.items():
        if len(records) > 1:
            amount_groups = defaultdict(list)
            for record in records:
                rounded_amount = round(record['abs_amount'])
                amount_groups[rounded_amount].append(record)
            
            for amount, amount_records in amount_groups.items():
                if len(amount_records) > 1:
                    intelligent_duplicates.extend(amount_records[1:])
    
    return intelligent_duplicates, {
        'duplicate_count': len(intelligent_duplicates),
        'equipment_groups': len(equipment_groups),
        'clean_records': len(consolidated_data) - len(intelligent_duplicates)
    }

@billing_bp.route('/billing-consolidated')
def billing_dashboard():
    """Unified billing dashboard with all authentic data"""
    
    billing_files = get_authentic_billing_files()
    
    # Process authentic RAGLE data
    total_revenue = 0
    billing_summary = {
        'files_processed': len(billing_files),
        'total_revenue': 0,
        'monthly_breakdown': {}
    }
    
    for file_info in billing_files:
        try:
            df = pd.read_excel(file_info['path'], engine='openpyxl')
            
            # Extract revenue using preserved column mappings
            amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'total' in col.lower()]
            if amount_cols:
                monthly_total = df[amount_cols[0]].sum()
                total_revenue += monthly_total
                
                # Preserve month identification logic
                month = "April 2025" if "APRIL" in file_info['name'] else "March 2025"
                billing_summary['monthly_breakdown'][month] = monthly_total
                
        except Exception as e:
            print(f"Error processing {file_info['name']}: {e}")
    
    billing_summary['total_revenue'] = total_revenue
    
    return render_template('billing_consolidated.html', 
                         billing_summary=billing_summary,
                         billing_files=billing_files)
