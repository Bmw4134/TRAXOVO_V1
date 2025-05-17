#!/usr/bin/env python3
"""
Simple PM Allocation File Processor

This script provides a simplified interface for processing PM allocation files.
It auto-detects files in the attached_assets directory and generates a reconciliation report.
"""

import os
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# Directory setup
ATTACHED_ASSETS_DIR = Path('./attached_assets')
REPORTS_DIR = Path('./reports')

# Ensure directory exists
REPORTS_DIR.mkdir(exist_ok=True)

def find_allocation_files():
    """Find allocation files in the attached_assets directory"""
    print("Looking for allocation files in:", ATTACHED_ASSETS_DIR)
    
    # Look for common patterns in filenames
    original_patterns = [
        r'EQMO.*BILLING.*(?<!REVISIONS)(?<!REVISED)(?<!FINAL)(?<!TR-FINAL).*\.(xlsx|xlsm)',
        r'EQ MONTHLY BILLINGS.*\.(xlsx|xlsm)',
        r'EQ.*PROFIT.*\.(xlsx|xlsm)',
        r'.*allocated.*\.(xlsx|xlsm)'  # Specific to your naming convention
    ]
    
    updated_patterns = [
        r'EQMO.*BILLING.*REVISIONS.*\.(xlsx|xlsm)',
        r'EQMO.*BILLING.*REVISED.*\.(xlsx|xlsm)',
        r'.*FINAL REVISIONS.*\.(xlsx|xlsm)',
        r'.*TR-FINAL.*\.(xlsx|xlsm)'  # Specific to your naming convention
    ]
    
    # List all Excel files
    all_files = []
    for extension in ['.xlsx', '.xlsm', '.xls']:
        all_files.extend(ATTACHED_ASSETS_DIR.glob(f'*{extension}'))
    
    # Sort by modification time (newest first)
    all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    print(f"Found {len(all_files)} Excel files in total")
    
    # Print all file names for debugging
    for i, file in enumerate(all_files):
        print(f"{i+1}. {file.name}")
    
    # Find updated file first
    updated_file = None
    for file in all_files:
        filename = file.name
        for pattern in updated_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                updated_file = file
                print(f"Found updated file: {file.name}")
                break
        if updated_file:
            break
    
    # Find original file
    original_file = None
    for file in all_files:
        if updated_file and file == updated_file:
            continue  # Skip the updated file
            
        filename = file.name
        for pattern in original_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                original_file = file
                print(f"Found original file: {file.name}")
                break
        if original_file:
            break
    
    # If we couldn't find by pattern, use the two most recent files
    if not updated_file and not original_file and len(all_files) >= 2:
        updated_file = all_files[0]  # Most recent
        original_file = all_files[1]  # Second most recent
        print(f"Using most recent files based on timestamps:")
        print(f"Updated file: {updated_file.name}")
        print(f"Original file: {original_file.name}")
    
    return original_file, updated_file

def process_allocation_files(original_file, updated_file):
    """Process PM allocation files and generate reconciliation report"""
    print("\nProcessing files:")
    print(f"Original: {original_file}")
    print(f"Updated: {updated_file}")
    
    # Generate output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = REPORTS_DIR / f"PM_Reconciliation_{timestamp}.csv"
    
    try:
        # Read the Excel files
        print("Reading original file...")
        original_df = pd.read_excel(original_file)
        
        print("Reading updated file...")
        updated_df = pd.read_excel(updated_file)
        
        # Clean column names
        original_df.columns = [str(col).strip().upper() for col in original_df.columns]
        updated_df.columns = [str(col).strip().upper() for col in updated_df.columns]
        
        # Print column names for debugging
        print("\nOriginal columns:", original_df.columns.tolist())
        print("Updated columns:", updated_df.columns.tolist())
        
        # Define patterns for identifying columns
        id_patterns = [r'EQ#', r'EQ #', r'EQUIPMENT #', r'EQUIP #', r'EQUIP', r'UNIT']
        desc_patterns = [r'DESCRIPTION', r'DESC', r'EQUIPMENT DESC']
        amount_patterns = [r'COST', r'AMOUNT', r'TOTAL', r'BILLING']
        
        # Find columns in original file
        orig_id_col = None
        orig_desc_col = None
        orig_amount_col = None
        
        for col in original_df.columns:
            if not orig_id_col and any(re.search(p, col, re.IGNORECASE) for p in id_patterns):
                orig_id_col = col
            elif not orig_desc_col and any(re.search(p, col, re.IGNORECASE) for p in desc_patterns):
                orig_desc_col = col
            elif not orig_amount_col and any(re.search(p, col, re.IGNORECASE) for p in amount_patterns):
                orig_amount_col = col
        
        # Find columns in updated file
        update_id_col = None
        update_desc_col = None
        update_amount_col = None
        
        for col in updated_df.columns:
            if not update_id_col and any(re.search(p, col, re.IGNORECASE) for p in id_patterns):
                update_id_col = col
            elif not update_desc_col and any(re.search(p, col, re.IGNORECASE) for p in desc_patterns):
                update_desc_col = col
            elif not update_amount_col and any(re.search(p, col, re.IGNORECASE) for p in amount_patterns):
                update_amount_col = col
        
        print(f"\nIdentified columns:")
        print(f"Original - ID: {orig_id_col}, Desc: {orig_desc_col}, Amount: {orig_amount_col}")
        print(f"Updated - ID: {update_id_col}, Desc: {update_desc_col}, Amount: {update_amount_col}")
        
        # Verify that we found all required columns
        if not all([orig_id_col, update_id_col, orig_amount_col, update_amount_col]):
            print("ERROR: Could not identify all required columns in the files.")
            return None
        
        # Prepare data structures for tracking changes
        changes = []
        
        # Get unique identifiers from both files
        original_ids = set(original_df[orig_id_col].astype(str))
        updated_ids = set(updated_df[update_id_col].astype(str))
        
        print(f"\nFound {len(original_ids)} unique IDs in original file")
        print(f"Found {len(updated_ids)} unique IDs in updated file")
        
        # Find additions (in updated but not in original)
        additions = updated_ids - original_ids
        print(f"Additions: {len(additions)}")
        
        for asset_id in additions:
            # Get the row for this asset
            row = updated_df[updated_df[update_id_col].astype(str) == asset_id].iloc[0]
            desc = row[update_desc_col] if update_desc_col else "N/A"
            amount = row[update_amount_col]
            
            # Convert amount to float if it's a string
            if isinstance(amount, str):
                try:
                    amount = float(amount.replace('$', '').replace(',', ''))
                except ValueError:
                    amount = 0
            
            changes.append({
                "Asset_ID": asset_id,
                "Description": desc,
                "Amount": amount,
                "Change_Type": "Added",
                "Original_Amount": 0,
                "Difference": amount
            })
        
        # Find deletions (in original but not in updated)
        deletions = original_ids - updated_ids
        print(f"Deletions: {len(deletions)}")
        
        for asset_id in deletions:
            # Get the row for this asset
            row = original_df[original_df[orig_id_col].astype(str) == asset_id].iloc[0]
            desc = row[orig_desc_col] if orig_desc_col else "N/A"
            amount = row[orig_amount_col]
            
            # Convert amount to float if it's a string
            if isinstance(amount, str):
                try:
                    amount = float(amount.replace('$', '').replace(',', ''))
                except ValueError:
                    amount = 0
            
            changes.append({
                "Asset_ID": asset_id,
                "Description": desc,
                "Amount": 0,
                "Change_Type": "Deleted",
                "Original_Amount": amount,
                "Difference": -amount
            })
        
        # Find modifications (same ID but different amount)
        common_ids = original_ids.intersection(updated_ids)
        print(f"Common IDs: {len(common_ids)}")
        
        modifications = 0
        
        for asset_id in common_ids:
            orig_row = original_df[original_df[orig_id_col].astype(str) == asset_id].iloc[0]
            update_row = updated_df[updated_df[update_id_col].astype(str) == asset_id].iloc[0]
            
            orig_amount = orig_row[orig_amount_col]
            update_amount = update_row[update_amount_col]
            
            # Handle NaN values
            if pd.isna(orig_amount):
                orig_amount = 0
            if pd.isna(update_amount):
                update_amount = 0
            
            # Convert amounts to float if they're strings
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
            
            # Check if amounts differ significantly
            if abs(orig_amount - update_amount) > 0.01:  # Allow for small floating point differences
                desc = update_row[update_desc_col] if update_desc_col else "N/A"
                
                changes.append({
                    "Asset_ID": asset_id,
                    "Description": desc,
                    "Amount": update_amount,
                    "Change_Type": "Modified",
                    "Original_Amount": orig_amount,
                    "Difference": update_amount - orig_amount
                })
                modifications += 1
        
        print(f"Modifications: {modifications}")
        print(f"Total changes: {len(changes)}")
        
        # Calculate summary totals
        total_original = sum(c["Original_Amount"] for c in changes)
        total_updated = sum(c["Amount"] for c in changes)
        total_difference = sum(c["Difference"] for c in changes)
        
        print(f"\nSummary:")
        print(f"Original Total: ${total_original:,.2f}")
        print(f"Updated Total: ${total_updated:,.2f}")
        print(f"Difference: ${total_difference:,.2f}")
        
        # Create output file
        if changes:
            output_df = pd.DataFrame(changes)
            output_df.to_csv(output_file, index=False)
            print(f"\nOutput saved to: {output_file}")
            
            return output_file
        else:
            print("\nNo changes detected between the files.")
            return None
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    """Main function"""
    print("=" * 60)
    print("PM ALLOCATION FILE PROCESSOR")
    print("=" * 60)
    
    original_file, updated_file = find_allocation_files()
    
    if not original_file or not updated_file:
        print("\nERROR: Could not find both original and updated allocation files.")
        print("Please ensure the files exist in the attached_assets directory.")
        return
    
    result = process_allocation_files(original_file, updated_file)
    
    if result:
        print("\nProcessing completed successfully!")
    else:
        print("\nProcessing failed. Please check the error messages above.")

if __name__ == "__main__":
    main()