#!/usr/bin/env python3
"""
Auto-detect and process PM allocation files

This standalone script will automatically find the original and updated 
PM allocation files in the attached_assets directory and process them.
"""

import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path

# Import PM processor utilities
from utils.pm_processor import find_allocation_files

# Configure paths
ATTACHED_ASSETS_DIR = Path('./attached_assets')
REPORTS_DIR = Path('./reports')

# Ensure reports directory exists
REPORTS_DIR.mkdir(exist_ok=True)

def compare_allocation_files(original_file, updated_file, output_path):
    """
    Compare the original and updated allocation files and output a reconciliation report
    
    Args:
        original_file (Path): Path to original allocation file
        updated_file (Path): Path to updated allocation file
        output_path (Path): Path to save the output report
        
    Returns:
        tuple: (output_file_path, summary_dict)
    """
    print(f"Processing files:\nOriginal: {original_file}\nUpdated: {updated_file}")
    
    # Load the Excel files
    original_df = pd.read_excel(original_file)
    updated_df = pd.read_excel(updated_file)
    
    # Clean column names (remove extra spaces, convert to uppercase)
    original_df.columns = [str(col).strip().upper() for col in original_df.columns]
    updated_df.columns = [str(col).strip().upper() for col in updated_df.columns]
    
    # Find ID and amount columns using regex patterns
    id_patterns = [r'EQ#', r'EQ #', r'EQUIPMENT #', r'EQUIP #', r'EQUIP. #', r'UNIT']
    amount_patterns = [r'COST', r'AMOUNT', r'TOTAL', r'BILLING']
    
    # Identify the ID column
    id_col_orig = None
    for col in original_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in id_patterns):
            id_col_orig = col
            break
    
    id_col_updated = None
    for col in updated_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in id_patterns):
            id_col_updated = col
            break
    
    # Identify the amount column
    amount_col_orig = None
    for col in original_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in amount_patterns):
            amount_col_orig = col
            break
    
    amount_col_updated = None
    for col in updated_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in amount_patterns):
            amount_col_updated = col
            break
    
    # Find description column
    desc_patterns = [r'DESCRIPTION', r'DESC', r'EQUIPMENT DESC']
    desc_col_orig = None
    for col in original_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in desc_patterns):
            desc_col_orig = col
            break
    
    desc_col_updated = None
    for col in updated_df.columns:
        if any(re.search(pattern, col, re.IGNORECASE) for pattern in desc_patterns):
            desc_col_updated = col
            break
    
    # Check if we found all needed columns
    if not all([id_col_orig, id_col_updated, amount_col_orig, amount_col_updated]):
        print("Error: Could not identify ID or amount columns in the files")
        return None, {"error": "Column identification failed"}
    
    # Prepare to track changes
    changes = []
    
    # Convert to sets for easy comparison
    original_ids = set(original_df[id_col_orig].astype(str))
    updated_ids = set(updated_df[id_col_updated].astype(str))
    
    # Find additions (in updated but not in original)
    additions = updated_ids - original_ids
    for asset_id in additions:
        row = updated_df[updated_df[id_col_updated].astype(str) == asset_id].iloc[0]
        description = row[desc_col_updated] if desc_col_updated else "N/A"
        amount = row[amount_col_updated]
        
        changes.append({
            "asset_id": asset_id,
            "description": description,
            "updated_value": amount,
            "original_value": None,
            "difference": amount,
            "status": "Added"
        })
    
    # Find deletions (in original but not in updated)
    deletions = original_ids - updated_ids
    for asset_id in deletions:
        row = original_df[original_df[id_col_orig].astype(str) == asset_id].iloc[0]
        description = row[desc_col_orig] if desc_col_orig else "N/A"
        amount = row[amount_col_orig]
        
        changes.append({
            "asset_id": asset_id,
            "description": description,
            "updated_value": None,
            "original_value": amount,
            "difference": -amount,
            "status": "Deleted"
        })
    
    # Find modifications (same ID but different amount)
    common_ids = original_ids.intersection(updated_ids)
    for asset_id in common_ids:
        orig_row = original_df[original_df[id_col_orig].astype(str) == asset_id].iloc[0]
        update_row = updated_df[updated_df[id_col_updated].astype(str) == asset_id].iloc[0]
        
        orig_amount = orig_row[amount_col_orig]
        update_amount = update_row[amount_col_updated]
        
        # Skip if amounts are the same (no change)
        if pd.isna(orig_amount) and pd.isna(update_amount):
            continue
        
        # Handle NaN values
        if pd.isna(orig_amount):
            orig_amount = 0
        if pd.isna(update_amount):
            update_amount = 0
            
        # Convert to numeric values if they're strings
        if isinstance(orig_amount, str):
            try:
                orig_amount = float(orig_amount.replace('$', '').replace(',', ''))
            except ValueError:
                orig_amount = 0
        
        if isinstance(update_amount, str):
            try:
                update_amount = float(update_amount.replace('$', '').replace(',', ''))
            except ValueError:
                update_amount = 0
            
        # Check if amount changed
        if abs(orig_amount - update_amount) > 0.01:  # Allow small floating point differences
            description = update_row[desc_col_updated] if desc_col_updated else "N/A"
            
            changes.append({
                "asset_id": asset_id,
                "description": description,
                "updated_value": update_amount,
                "original_value": orig_amount,
                "difference": update_amount - orig_amount,
                "status": "Modified"
            })
    
    # Calculate summary
    total_original = sum(change['original_value'] for change in changes if change['original_value'] is not None)
    total_updated = sum(change['updated_value'] for change in changes if change['updated_value'] is not None)
    total_difference = sum(change['difference'] for change in changes)
    
    summary = {
        "total_original": total_original,
        "total_updated": total_updated,
        "total_difference": total_difference,
        "total_changed_records": len(changes),
        "additions": len([c for c in changes if c['status'] == 'Added']),
        "deletions": len([c for c in changes if c['status'] == 'Deleted']),
        "modifications": len([c for c in changes if c['status'] == 'Modified'])
    }
    
    # Create output file with changes
    output_data = []
    for change in changes:
        output_data.append({
            "Asset_ID": change['asset_id'],
            "Description": change['description'],
            "Amount": change['updated_value'] if change['updated_value'] is not None else 0,
            "Change_Type": change['status'],
            "Original_Amount": change['original_value'] if change['original_value'] is not None else 0,
            "Difference": change['difference']
        })
    
    # Create output dataframe and save to CSV
    output_df = pd.DataFrame(output_data)
    output_df.to_csv(output_path, index=False)
    
    return output_path, summary

def main():
    """Main function to auto-detect and process PM allocation files"""
    print("Looking for PM allocation files in attached_assets directory...")
    
    # Find the allocation files
    original_file, updated_file = find_allocation_files()
    
    if not original_file or not updated_file:
        print("Could not find suitable allocation files. Please make sure the files exist in the attached_assets directory.")
        return
    
    print(f"Found files:\nOriginal: {original_file}\nUpdated: {updated_file}")
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"pm_reconciliation_{timestamp}.csv"
    
    # Process the files
    try:
        result_path, summary = compare_allocation_files(original_file, updated_file, output_path)
        
        if result_path:
            print("\nProcessing completed successfully!")
            print(f"Output saved to: {result_path}")
            print("\nSummary:")
            print(f"Original Total: ${summary['total_original']:,.2f}")
            print(f"Updated Total: ${summary['total_updated']:,.2f}")
            print(f"Difference: ${summary['total_difference']:,.2f}")
            print(f"Changed Records: {summary['total_changed_records']}")
            print(f"  - Additions: {summary['additions']}")
            print(f"  - Deletions: {summary['deletions']}")
            print(f"  - Modifications: {summary['modifications']}")
        else:
            print("Processing failed. Check the error messages above.")
    
    except Exception as e:
        print(f"Error processing files: {str(e)}")

if __name__ == "__main__":
    main()