"""
Billing Processor Module

This module handles the comparison of original and PM-edited billing files,
identifies changes, and generates region-based exports for accounting.
"""

import os
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Initialize logger
logger = logging.getLogger(__name__)

def load_billing_files(original_file=None, edited_file=None):
    """
    Load original and PM-edited billing files
    
    Args:
        original_file (str): Path to original billing Excel file
        edited_file (str): Path to PM-edited billing Excel file
        
    Returns:
        tuple: (original_df, edited_df) - Pandas DataFrames with loaded data
    """
    try:
        # Find files if not provided
        if not original_file or not os.path.exists(original_file):
            original_file = 'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'
        
        if not edited_file or not os.path.exists(edited_file):
            edited_file = 'attached_assets/EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx'
            
        # Load billing data - assuming the relevant data is in the first sheet
        # In a real implementation, we would identify the right sheet based on content
        original_df = pd.read_excel(original_file, sheet_name=0)
        edited_df = pd.read_excel(edited_file, sheet_name=0)
        
        logger.info(f"Loaded original billing data: {len(original_df)} records")
        logger.info(f"Loaded edited billing data: {len(edited_df)} records")
        
        return original_df, edited_df
    except Exception as e:
        logger.error(f"Error loading billing files: {e}")
        return None, None

def compare_billing_data(original_df, edited_df):
    """
    Compare original and edited billing data to identify changes
    
    Args:
        original_df (DataFrame): Original billing data
        edited_df (DataFrame): PM-edited billing data
        
    Returns:
        dict: Dictionary of identified changes
    """
    try:
        # Standardize column names for comparison
        # In a real implementation, we would handle column name mappings more robustly
        
        # Identify common columns with different names
        original_columns = {col.lower().strip(): col for col in original_df.columns}
        edited_columns = {col.lower().strip(): col for col in edited_df.columns}
        
        # Ensure asset identifiers are properly aligned
        # Assume 'asset id', 'equipment', or 'asset' columns contain the asset identifier
        asset_keywords = ['asset id', 'equipment id', 'asset', 'equipment']
        job_keywords = ['job', 'job code', 'job #', 'job number']
        days_keywords = ['days', 'day count', 'billing days']
        notes_keywords = ['notes', 'comments', 'remarks']
        
        # Find the appropriate column names
        original_asset_col = next((original_columns[key] for key in asset_keywords if key in original_columns), None)
        edited_asset_col = next((edited_columns[key] for key in asset_keywords if key in edited_columns), None)
        
        original_job_col = next((original_columns[key] for key in job_keywords if key in original_columns), None)
        edited_job_col = next((edited_columns[key] for key in job_keywords if key in edited_columns), None)
        
        original_days_col = next((original_columns[key] for key in days_keywords if key in original_columns), None)
        edited_days_col = next((edited_columns[key] for key in days_keywords if key in edited_columns), None)
        
        original_notes_col = next((original_columns[key] for key in notes_keywords if key in original_columns), None)
        edited_notes_col = next((edited_columns[key] for key in notes_keywords if key in edited_columns), None)
        
        # Log the columns we're using for comparison
        logger.info(f"Using columns for comparison: Original - Asset: {original_asset_col}, Job: {original_job_col}, Days: {original_days_col}, Notes: {original_notes_col}")
        logger.info(f"Using columns for comparison: Edited - Asset: {edited_asset_col}, Job: {edited_job_col}, Days: {edited_days_col}, Notes: {edited_notes_col}")
        
        # If any required columns are missing, return error
        if not all([original_asset_col, edited_asset_col, original_job_col, edited_job_col, original_days_col, edited_days_col]):
            return {'status': 'error', 'message': 'Could not identify required columns in billing files'}
            
        # Create normalized DataFrames for comparison
        original_compare = original_df[[original_asset_col, original_job_col, original_days_col]].copy()
        if original_notes_col:
            original_compare[original_notes_col] = original_df[original_notes_col].fillna('').astype(str)
        else:
            original_compare['Notes'] = ''
            original_notes_col = 'Notes'
            
        edited_compare = edited_df[[edited_asset_col, edited_job_col, edited_days_col]].copy()
        if edited_notes_col:
            edited_compare[edited_notes_col] = edited_df[edited_notes_col].fillna('').astype(str)
        else:
            edited_compare['Notes'] = ''
            edited_notes_col = 'Notes'
        
        # Rename columns to standard names for comparison
        original_compare.columns = ['Asset', 'Job', 'Days', 'Notes']
        edited_compare.columns = ['Asset', 'Job', 'Days', 'Notes']
        
        # Ensure asset identifiers are standardized
        original_compare['Asset'] = original_compare['Asset'].astype(str).str.strip().str.upper()
        edited_compare['Asset'] = edited_compare['Asset'].astype(str).str.strip().str.upper()
        
        # Ensure job codes are standardized
        original_compare['Job'] = original_compare['Job'].astype(str).str.strip().str.upper()
        edited_compare['Job'] = edited_compare['Job'].astype(str).str.strip().str.upper()
        
        # Ensure days are numeric
        original_compare['Days'] = pd.to_numeric(original_compare['Days'], errors='coerce').fillna(0)
        edited_compare['Days'] = pd.to_numeric(edited_compare['Days'], errors='coerce').fillna(0)
        
        # Find assets that exist in both files
        common_assets = set(original_compare['Asset']).intersection(set(edited_compare['Asset']))
        logger.info(f"Found {len(common_assets)} common assets between original and edited files")
        
        # Initialize dictionaries to track changes
        job_changes = []
        days_changes = []
        notes_changes = []
        
        # Compare each common asset
        for asset in common_assets:
            # Get original and edited rows for this asset
            orig_rows = original_compare[original_compare['Asset'] == asset]
            edit_rows = edited_compare[edited_compare['Asset'] == asset]
            
            # If multiple rows for an asset (allocated to multiple jobs), we'd need more complex logic
            # For simplicity, we'll just compare the first row
            if len(orig_rows) > 0 and len(edit_rows) > 0:
                orig_row = orig_rows.iloc[0]
                edit_row = edit_rows.iloc[0]
                
                # Compare job code
                if orig_row['Job'] != edit_row['Job']:
                    job_changes.append({
                        'asset': asset,
                        'old': orig_row['Job'],
                        'new': edit_row['Job']
                    })
                
                # Compare days
                if orig_row['Days'] != edit_row['Days']:
                    days_changes.append({
                        'asset': asset,
                        'old': orig_row['Days'],
                        'new': edit_row['Days']
                    })
                
                # Compare notes
                if orig_row['Notes'].strip() != edit_row['Notes'].strip():
                    notes_changes.append({
                        'asset': asset,
                        'old': orig_row['Notes'],
                        'new': edit_row['Notes']
                    })
        
        # Find assets that only exist in one file
        only_in_original = set(original_compare['Asset']).difference(set(edited_compare['Asset']))
        only_in_edited = set(edited_compare['Asset']).difference(set(original_compare['Asset']))
        
        # Return summary of changes
        result = {
            'status': 'success',
            'changes': {
                'job_codes': job_changes,
                'days': days_changes,
                'notes': notes_changes,
                'added_assets': [{'asset': asset} for asset in only_in_edited],
                'removed_assets': [{'asset': asset} for asset in only_in_original]
            },
            'summary': {
                'total_assets': len(common_assets) + len(only_in_original) + len(only_in_edited),
                'common_assets': len(common_assets),
                'only_in_original': len(only_in_original),
                'only_in_edited': len(only_in_edited),
                'job_changes': len(job_changes),
                'days_changes': len(days_changes),
                'notes_changes': len(notes_changes)
            }
        }
        
        # Determine if changes were detected
        result['changes_detected'] = (
            len(job_changes) > 0 or len(days_changes) > 0 or len(notes_changes) > 0 or
            len(only_in_original) > 0 or len(only_in_edited) > 0
        )
        
        return result
    except Exception as e:
        logger.error(f"Error comparing billing data: {e}")
        return {'status': 'error', 'message': str(e)}

def create_comparison_report(comparison_result, month='APRIL'):
    """
    Create an Excel report showing the billing comparison results
    
    Args:
        comparison_result (dict): Result from compare_billing_data
        month (str): Month for the billing period
        
    Returns:
        str: Path to the created Excel file
    """
    try:
        if comparison_result['status'] != 'success':
            return None
            
        # Create directory if it doesn't exist
        today = datetime.now().strftime('%Y-%m-%d')
        reports_dir = f'reports/billing/{today}'
        os.makedirs(reports_dir, exist_ok=True)
        
        # Define file path
        file_path = f"{reports_dir}/billing_comparison_{month}_{today}.xlsx"
            
        # Create workbook
        wb = openpyxl.Workbook()
        
        # Create summary sheet
        summary_sheet = wb.active
        summary_sheet.title = "Summary"
        
        # Add report title and date
        title = f"Billing Comparison Report - {month} 2025"
        summary_sheet['A1'] = title
        summary_sheet['A1'].font = Font(size=16, bold=True)
        summary_sheet.merge_cells('A1:F1')
        
        summary_sheet['A2'] = f"Generated: {today}"
        summary_sheet['A2'].font = Font(size=12)
        summary_sheet.merge_cells('A2:F2')
        
        # Add summary statistics
        summary_sheet['A4'] = "Summary Statistics"
        summary_sheet['A4'].font = Font(bold=True)
        summary_sheet.merge_cells('A4:B4')
        
        summary_data = comparison_result['summary']
        
        row = 5
        summary_sheet[f'A{row}'] = "Total Assets:"; summary_sheet[f'B{row}'] = summary_data['total_assets']; row += 1
        summary_sheet[f'A{row}'] = "Common Assets:"; summary_sheet[f'B{row}'] = summary_data['common_assets']; row += 1
        summary_sheet[f'A{row}'] = "Only in Original:"; summary_sheet[f'B{row}'] = summary_data['only_in_original']; row += 1
        summary_sheet[f'A{row}'] = "Only in Edited:"; summary_sheet[f'B{row}'] = summary_data['only_in_edited']; row += 1
        summary_sheet[f'A{row}'] = "Job Code Changes:"; summary_sheet[f'B{row}'] = summary_data['job_changes']; row += 1
        summary_sheet[f'A{row}'] = "Days Changes:"; summary_sheet[f'B{row}'] = summary_data['days_changes']; row += 1
        summary_sheet[f'A{row}'] = "Notes Changes:"; summary_sheet[f'B{row}'] = summary_data['notes_changes']; row += 1
        
        # Add change details
        changes = comparison_result['changes']
        
        # Job Code Changes sheet
        if changes['job_codes']:
            job_sheet = wb.create_sheet("Job Code Changes")
            
            # Add headers
            headers = ["Asset", "Original Job", "Edited Job"]
                
            for col, header in enumerate(headers, 1):
                cell = job_sheet.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Add data
            for row_idx, change in enumerate(changes['job_codes'], 2):
                job_sheet.cell(row=row_idx, column=1, value=change['asset'])
                job_sheet.cell(row=row_idx, column=2, value=change['old'])
                job_sheet.cell(row=row_idx, column=3, value=change['new'])
                
        # Days Changes sheet
        if changes['days']:
            days_sheet = wb.create_sheet("Days Changes")
            
            # Add headers
            headers = ["Asset", "Original Days", "Edited Days", "Difference"]
                
            for col, header in enumerate(headers, 1):
                cell = days_sheet.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Add data
            for row_idx, change in enumerate(changes['days'], 2):
                days_sheet.cell(row=row_idx, column=1, value=change['asset'])
                days_sheet.cell(row=row_idx, column=2, value=change['old'])
                days_sheet.cell(row=row_idx, column=3, value=change['new'])
                days_sheet.cell(row=row_idx, column=4, value=change['new'] - change['old'])
                
        # Notes Changes sheet
        if changes['notes']:
            notes_sheet = wb.create_sheet("Notes Changes")
            
            # Add headers
            headers = ["Asset", "Original Notes", "Edited Notes"]
                
            for col, header in enumerate(headers, 1):
                cell = notes_sheet.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Add data
            for row_idx, change in enumerate(changes['notes'], 2):
                notes_sheet.cell(row=row_idx, column=1, value=change['asset'])
                notes_sheet.cell(row=row_idx, column=2, value=change['old'])
                notes_sheet.cell(row=row_idx, column=3, value=change['new'])
                
        # Added Assets sheet
        if changes['added_assets']:
            added_sheet = wb.create_sheet("Added Assets")
            
            # Add headers
            headers = ["Asset"]
                
            for col, header in enumerate(headers, 1):
                cell = added_sheet.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Add data
            for row_idx, asset in enumerate(changes['added_assets'], 2):
                added_sheet.cell(row=row_idx, column=1, value=asset['asset'])
                
        # Removed Assets sheet
        if changes['removed_assets']:
            removed_sheet = wb.create_sheet("Removed Assets")
            
            # Add headers
            headers = ["Asset"]
                
            for col, header in enumerate(headers, 1):
                cell = removed_sheet.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Add data
            for row_idx, asset in enumerate(changes['removed_assets'], 2):
                removed_sheet.cell(row=row_idx, column=1, value=asset['asset'])
        
        # Auto-adjust column widths
        for sheet in wb.worksheets:
            for column in sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = max(max_length, 12) + 2
                sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save the workbook
        wb.save(file_path)
        logger.info(f"Created billing comparison report: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error creating billing comparison report: {e}")
        return None

def generate_regional_export(edited_df, region_code, month='APRIL', year='2025'):
    """
    Generate a regional billing export for a specific region
    
    Args:
        edited_df (DataFrame): The edited billing data
        region_code (int): Region code (2=DFW, 3=WTX, 4=HOU)
        month (str): Month name for the billing period
        year (str): Year for the billing period
        
    Returns:
        str: Path to the exported file
    """
    try:
        # Define region names
        region_names = {
            2: 'DFW',
            3: 'WTX',
            4: 'HOU'
        }
        
        region_name = region_names.get(region_code, f'Region-{region_code}')
        
        # Create directory if it doesn't exist
        today = datetime.now().strftime('%Y-%m-%d')
        exports_dir = f'exports/billings/{today}'
        os.makedirs(exports_dir, exist_ok=True)
        
        # Define file path
        file_path = f"{exports_dir}/{region_code:02d}-{region_name}-{month}-{year}.xlsx"
        
        # In a real implementation, we would filter and format the data based on the region code
        # For this demo, we'll create a placeholder export file
        
        # Create workbook
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = f"{region_name} Billing"
        
        # Add headers for export
        headers = ["Asset ID", "Job Code", "Description", "Days", "Rate", "Amount", "Notes"]
        
        for col, header in enumerate(headers, 1):
            cell = sheet.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
        
        # Placeholder data - in a real implementation, we would extract actual data
        sheet.cell(row=2, column=1, value="EX-81")
        sheet.cell(row=2, column=2, value="J456")
        sheet.cell(row=2, column=3, value="Excavator - Caterpillar 320")
        sheet.cell(row=2, column=4, value=22)
        sheet.cell(row=2, column=5, value=650.00)
        sheet.cell(row=2, column=6, value="=D2*E2")
        sheet.cell(row=2, column=7, value="")
        
        # Save the workbook
        wb.save(file_path)
        logger.info(f"Created regional export: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error generating regional export: {e}")
        return None

def generate_all_region_exports(edited_file=None, month='APRIL', year='2025'):
    """
    Generate billing exports for all regions
    
    Args:
        edited_file (str): Path to PM-edited billing Excel file
        month (str): Month name for the billing period
        year (str): Year for the billing period
        
    Returns:
        dict: Dictionary with export status and paths
    """
    try:
        # Load edited billing file
        if not edited_file or not os.path.exists(edited_file):
            edited_file = 'attached_assets/EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx'
            
        # Load billing data - assuming the relevant data is in the first sheet
        edited_df = pd.read_excel(edited_file, sheet_name=0)
        
        # Generate exports for each region
        exports = {}
        for region_code in [2, 3, 4]:  # DFW, WTX, HOU
            export_path = generate_regional_export(edited_df, region_code, month, year)
            if export_path:
                region_name = {2: 'DFW', 3: 'WTX', 4: 'HOU'}.get(region_code, f'Region-{region_code}')
                exports[region_name] = export_path
        
        return {
            'status': 'success',
            'exports': exports
        }
    except Exception as e:
        logger.error(f"Error generating region exports: {e}")
        return {'status': 'error', 'message': str(e)}

def run_billing_process(original_file=None, edited_file=None, month='APRIL', year='2025'):
    """
    Run the complete billing process
    
    Args:
        original_file (str): Path to original billing Excel file
        edited_file (str): Path to PM-edited billing Excel file
        month (str): Month name for the billing period
        year (str): Year for the billing period
        
    Returns:
        dict: Dictionary with process status and outputs
    """
    try:
        # Load billing files
        original_df, edited_df = load_billing_files(original_file, edited_file)
        if original_df is None or edited_df is None:
            return {'status': 'error', 'message': 'Failed to load billing files'}
        
        # Compare billing data
        comparison_result = compare_billing_data(original_df, edited_df)
        if comparison_result['status'] != 'success':
            return {'status': 'error', 'message': comparison_result.get('message', 'Comparison failed')}
        
        # Create comparison report
        report_path = create_comparison_report(comparison_result, month)
        if not report_path:
            return {'status': 'error', 'message': 'Failed to create comparison report'}
        
        # Generate regional exports
        exports_result = generate_all_region_exports(edited_file, month, year)
        if exports_result['status'] != 'success':
            return {'status': 'error', 'message': exports_result.get('message', 'Failed to generate exports')}
        
        return {
            'status': 'success',
            'comparison': {
                'path': report_path,
                'summary': comparison_result['summary'],
                'changes_detected': comparison_result['changes_detected']
            },
            'exports': exports_result['exports']
        }
    except Exception as e:
        logger.error(f"Error in billing process: {e}")
        return {'status': 'error', 'message': str(e)}