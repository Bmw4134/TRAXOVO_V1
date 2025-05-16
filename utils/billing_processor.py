"""
Billing Processor Utility

This module contains functions for processing PM billing allocation files,
comparing versions, and generating regional export files.
"""
import os
import re
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define colors for highlighting changes
HIGHLIGHT_ADDED = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Light green
HIGHLIGHT_REMOVED = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Light red
HIGHLIGHT_CHANGED = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Light yellow

# Define border styles
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

HEADER_FONT = Font(bold=True, size=12)
NORMAL_FONT = Font(size=11)

def clean_column_names(df):
    """
    Standardize column names in the dataframe.
    
    Args:
        df (DataFrame): The DataFrame to clean
        
    Returns:
        DataFrame: DataFrame with standardized column names
    """
    # Convert all column names to uppercase and replace spaces with underscores
    df.columns = [str(col).strip().upper().replace(' ', '_') for col in df.columns]
    
    # Map common variations to standardized names
    column_mapping = {
        'DIV.': 'DIV',
        'DIVISION': 'DIV',
        'JOB_CODE': 'JOB',
        'JOB_NUMBER': 'JOB',
        'EQUIP._ID': 'ASSET_ID',
        'EQUIPMENT_ID': 'ASSET_ID',
        'EQUIPMENT': 'EQUIPMENT_DESCRIPTION',
        'EQUIP._DESCRIPTION': 'EQUIPMENT_DESCRIPTION',
        'ASSET_DESCRIPTION': 'EQUIPMENT_DESCRIPTION',
        'OPERATOR': 'DRIVER',
        'EMPLOYEE': 'DRIVER',
        'ALLOCATION': 'UNIT_ALLOCATION',
        'UNITS': 'UNIT_ALLOCATION',
        'UNIT_ALLOC.': 'UNIT_ALLOCATION',
        'COST_CENTER': 'COST_CODE',
        'CC': 'COST_CODE',
        'UNIT_PRICE': 'RATE',
        'PRICE': 'RATE',
        'EXTENDED': 'UNIT_ALLOCATION_AMOUNT',
        'TOTAL': 'UNIT_ALLOCATION_AMOUNT',
        'AMOUNT': 'UNIT_ALLOCATION_AMOUNT',
        'REVISIONS': 'REVISION',
        'ADJUSTMENT': 'REVISION',
        'NOTES': 'COMMENTS',
        'COMMENT': 'COMMENTS'
    }
    
    # Replace column names if they exist in the mapping
    df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
    
    return df

def preprocess_pm_data(df):
    """
    Preprocess PM allocation data.
    
    Args:
        df (DataFrame): The DataFrame to preprocess
        
    Returns:
        DataFrame: Preprocessed DataFrame
    """
    # Clean up column names
    df = clean_column_names(df)
    
    # Required columns
    required_cols = ['DIV', 'JOB', 'ASSET_ID', 'EQUIPMENT_DESCRIPTION', 'UNIT_ALLOCATION', 'RATE']
    
    # Check if required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Convert numeric columns
    numeric_cols = ['UNIT_ALLOCATION', 'RATE']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate unit allocation amount if not present
    if 'UNIT_ALLOCATION_AMOUNT' not in df.columns:
        df['UNIT_ALLOCATION_AMOUNT'] = df['UNIT_ALLOCATION'] * df['RATE']
    
    # Ensure REVISION column exists
    if 'REVISION' not in df.columns:
        df['REVISION'] = 0
    else:
        df['REVISION'] = pd.to_numeric(df['REVISION'], errors='coerce').fillna(0)
    
    # Ensure COMMENTS column exists
    if 'COMMENTS' not in df.columns:
        df['COMMENTS'] = ''
    
    # Fill NaN values
    df = df.fillna('')
    
    # Ensure asset ID is string for consistent comparison
    df['ASSET_ID'] = df['ASSET_ID'].astype(str)
    df['JOB'] = df['JOB'].astype(str)
    
    return df

def identify_regions(df):
    """
    Identify regions based on division codes.
    
    Args:
        df (DataFrame): The DataFrame to analyze
        
    Returns:
        dict: Dictionary mapping division codes to regions
    """
    region_map = {}
    
    # Define region patterns
    dfw_pattern = r'^(D|DF)'  # Dallas/Fort Worth starts with D or DF
    hou_pattern = r'^(H|HO)'  # Houston starts with H or HO
    wtx_pattern = r'^(W|WT)'  # West Texas starts with W or WT
    
    # Map divisions to regions
    for div in df['DIV'].unique():
        if pd.isna(div) or div == '':
            continue
            
        div_str = str(div).upper()
        
        if re.match(dfw_pattern, div_str):
            region_map[div_str] = 'DFW'
        elif re.match(hou_pattern, div_str):
            region_map[div_str] = 'HOU'
        elif re.match(wtx_pattern, div_str):
            region_map[div_str] = 'WTX'
        else:
            region_map[div_str] = 'OTHER'
    
    return region_map

def compare_pm_files(original_df, pm_df, region=None):
    """
    Compare original and PM-edited files to find differences.
    
    Args:
        original_df (DataFrame): Original allocation data
        pm_df (DataFrame): PM-edited allocation data
        region (str, optional): Region to filter on (DFW, HOU, WTX, or ALL)
        
    Returns:
        dict: Dictionary containing changes, added and removed rows
    """
    # Preprocess dataframes
    original_df = preprocess_pm_data(original_df)
    pm_df = preprocess_pm_data(pm_df)
    
    # Add region column based on DIV
    region_map = identify_regions(pd.concat([original_df, pm_df]))
    original_df['REGION'] = original_df['DIV'].map(region_map)
    pm_df['REGION'] = pm_df['DIV'].map(region_map)
    
    # Filter by region if specified
    if region and region.upper() != 'ALL':
        original_df = original_df[original_df['REGION'] == region.upper()]
        pm_df = pm_df[pm_df['REGION'] == region.upper()]
    
    # Create unique identifier for each row (DIV-JOB-ASSET_ID)
    original_df['ROW_ID'] = original_df['DIV'] + '-' + original_df['JOB'] + '-' + original_df['ASSET_ID']
    pm_df['ROW_ID'] = pm_df['DIV'] + '-' + pm_df['JOB'] + '-' + pm_df['ASSET_ID']
    
    # Find rows that exist in both dataframes
    common_rows = pd.merge(
        original_df, pm_df, on='ROW_ID', suffixes=('_ORIG', '_PM')
    )
    
    # Find added and removed rows
    added_rows = pm_df[~pm_df['ROW_ID'].isin(original_df['ROW_ID'])]
    removed_rows = original_df[~original_df['ROW_ID'].isin(pm_df['ROW_ID'])]
    
    # Check for changes in common rows
    changes = []
    for _, row in common_rows.iterrows():
        row_changes = []
        
        # Fields to compare
        fields_to_compare = [
            ('UNIT_ALLOCATION', 'Unit Allocation'),
            ('RATE', 'Rate'),
            ('UNIT_ALLOCATION_AMOUNT', 'Unit Allocation Amount'),
            ('REVISION', 'Revision'),
            ('COMMENTS', 'Comments')
        ]
        
        for field, field_name in fields_to_compare:
            orig_value = row[f'{field}_ORIG']
            pm_value = row[f'{field}_PM']
            
            # Special handling for numeric fields
            if field in ['UNIT_ALLOCATION', 'RATE', 'UNIT_ALLOCATION_AMOUNT', 'REVISION']:
                # Convert to float for comparison
                try:
                    orig_value = float(orig_value) if orig_value != '' else 0
                    pm_value = float(pm_value) if pm_value != '' else 0
                    
                    # Check if values are different (beyond rounding error)
                    if abs(orig_value - pm_value) > 0.01:
                        row_changes.append({
                            'DIV': row['DIV_ORIG'],
                            'JOB': row['JOB_ORIG'],
                            'ASSET_ID': row['ASSET_ID_ORIG'],
                            'EQUIPMENT_DESCRIPTION': row['EQUIPMENT_DESCRIPTION_ORIG'],
                            'CHANGED_FIELD': field_name,
                            'ORIGINAL_VALUE': str(orig_value),
                            'UPDATED_VALUE': str(pm_value)
                        })
                except (ValueError, TypeError):
                    # If conversion fails, compare as strings
                    if str(orig_value) != str(pm_value):
                        row_changes.append({
                            'DIV': row['DIV_ORIG'],
                            'JOB': row['JOB_ORIG'],
                            'ASSET_ID': row['ASSET_ID_ORIG'],
                            'EQUIPMENT_DESCRIPTION': row['EQUIPMENT_DESCRIPTION_ORIG'],
                            'CHANGED_FIELD': field_name,
                            'ORIGINAL_VALUE': str(orig_value),
                            'UPDATED_VALUE': str(pm_value)
                        })
            else:
                # Compare string fields
                if str(orig_value) != str(pm_value):
                    row_changes.append({
                        'DIV': row['DIV_ORIG'],
                        'JOB': row['JOB_ORIG'],
                        'ASSET_ID': row['ASSET_ID_ORIG'],
                        'EQUIPMENT_DESCRIPTION': row['EQUIPMENT_DESCRIPTION_ORIG'],
                        'CHANGED_FIELD': field_name,
                        'ORIGINAL_VALUE': str(orig_value),
                        'UPDATED_VALUE': str(pm_value)
                    })
        
        changes.extend(row_changes)
    
    # Create DataFrames from the results
    changes_df = pd.DataFrame(changes) if changes else pd.DataFrame()
    
    # Return the comparison results
    return {
        'changes': changes_df,
        'added': added_rows,
        'removed': removed_rows,
        'region_map': region_map
    }

def generate_comparison_file(comparison, month, output_dir='exports'):
    """
    Generate Excel file with comparison results.
    
    Args:
        comparison (dict): Comparison results from compare_pm_files
        month (str): Month of the data (e.g., "APRIL 2025")
        output_dir (str): Directory to save the output file
        
    Returns:
        str: Path to the generated file
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Count changes
    num_changes = len(comparison.get('changes', []))
    num_added = len(comparison.get('added', []))
    num_removed = len(comparison.get('removed', []))
    total_changes = num_changes + num_added + num_removed
    
    # Create filename with timestamp and change count
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(
        output_dir, 
        f"PM_ALLOCATION_COMPARISON_{month.replace(' ', '_')}_{total_changes}_CHANGES_{timestamp}.xlsx"
    )
    
    # Create Excel workbook
    wb = Workbook()
    
    # Summary sheet
    summary_sheet = wb.active
    summary_sheet.title = "Summary"
    
    # Add summary information
    summary_sheet['A1'] = f"PM ALLOCATION COMPARISON - {month}"
    summary_sheet['A1'].font = Font(bold=True, size=14)
    summary_sheet.merge_cells('A1:F1')
    
    summary_sheet['A3'] = "Generated On:"
    summary_sheet['B3'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    summary_sheet['A4'] = "Total Changes:"
    summary_sheet['B4'] = total_changes
    
    summary_sheet['A5'] = "Changed Fields:"
    summary_sheet['B5'] = num_changes
    
    summary_sheet['A6'] = "Added Rows:"
    summary_sheet['B6'] = num_added
    
    summary_sheet['A7'] = "Removed Rows:"
    summary_sheet['B7'] = num_removed
    
    # Apply styling
    for cell in ['A3', 'A4', 'A5', 'A6', 'A7']:
        summary_sheet[cell].font = Font(bold=True)
    
    # Changes sheet
    if not comparison.get('changes').empty:
        changes_df = comparison.get('changes')
        changes_sheet = wb.create_sheet("Changes")
        
        # Write headers
        headers = ['DIV', 'JOB', 'ASSET ID', 'EQUIPMENT DESCRIPTION', 'CHANGED FIELD', 'ORIGINAL VALUE', 'UPDATED VALUE']
        for col_num, header in enumerate(headers, 1):
            cell = changes_sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = HEADER_FONT
            cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = THIN_BORDER
        
        # Write data
        for row_num, row in enumerate(changes_df.itertuples(), 2):
            # DIV
            cell = changes_sheet.cell(row=row_num, column=1)
            cell.value = getattr(row, 'DIV', '')
            cell.border = THIN_BORDER
            
            # JOB
            cell = changes_sheet.cell(row=row_num, column=2)
            cell.value = getattr(row, 'JOB', '')
            cell.border = THIN_BORDER
            
            # ASSET ID
            cell = changes_sheet.cell(row=row_num, column=3)
            cell.value = getattr(row, 'ASSET_ID', '')
            cell.border = THIN_BORDER
            
            # EQUIPMENT DESCRIPTION
            cell = changes_sheet.cell(row=row_num, column=4)
            cell.value = getattr(row, 'EQUIPMENT_DESCRIPTION', '')
            cell.border = THIN_BORDER
            
            # CHANGED FIELD
            cell = changes_sheet.cell(row=row_num, column=5)
            cell.value = getattr(row, 'CHANGED_FIELD', '')
            cell.font = Font(bold=True)
            cell.border = THIN_BORDER
            
            # ORIGINAL VALUE
            cell = changes_sheet.cell(row=row_num, column=6)
            cell.value = getattr(row, 'ORIGINAL_VALUE', '')
            cell.fill = HIGHLIGHT_REMOVED
            cell.border = THIN_BORDER
            
            # UPDATED VALUE
            cell = changes_sheet.cell(row=row_num, column=7)
            cell.value = getattr(row, 'UPDATED_VALUE', '')
            cell.fill = HIGHLIGHT_ADDED
            cell.border = THIN_BORDER
        
        # Auto-adjust column widths
        for col in changes_sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            
            adjusted_width = (max_length + 2) * 1.2
            changes_sheet.column_dimensions[column].width = adjusted_width
    
    # Added rows sheet
    if not comparison.get('added').empty:
        added_df = comparison.get('added')
        added_sheet = wb.create_sheet("Added")
        
        # Get columns to include
        columns_to_include = ['DIV', 'JOB', 'ASSET_ID', 'EQUIPMENT_DESCRIPTION', 'DRIVER', 
                              'UNIT_ALLOCATION', 'RATE', 'UNIT_ALLOCATION_AMOUNT', 'COST_CODE', 
                              'REVISION', 'COMMENTS']
        
        # Filter columns that exist in the dataframe
        display_columns = [col for col in columns_to_include if col in added_df.columns]
        
        # Write headers
        headers = [col.replace('_', ' ').title() for col in display_columns]
        for col_num, header in enumerate(headers, 1):
            cell = added_sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = HEADER_FONT
            cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = THIN_BORDER
        
        # Write data
        for row_num, row in enumerate(added_df.itertuples(), 2):
            for col_num, col in enumerate(display_columns, 1):
                cell = added_sheet.cell(row=row_num, column=col_num)
                cell.value = getattr(row, col, '')
                cell.fill = HIGHLIGHT_ADDED
                cell.border = THIN_BORDER
        
        # Auto-adjust column widths
        for col in added_sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            
            adjusted_width = (max_length + 2) * 1.2
            added_sheet.column_dimensions[column].width = adjusted_width
    
    # Removed rows sheet
    if not comparison.get('removed').empty:
        removed_df = comparison.get('removed')
        removed_sheet = wb.create_sheet("Removed")
        
        # Get columns to include
        columns_to_include = ['DIV', 'JOB', 'ASSET_ID', 'EQUIPMENT_DESCRIPTION', 'DRIVER', 
                              'UNIT_ALLOCATION', 'RATE', 'UNIT_ALLOCATION_AMOUNT', 'COST_CODE', 
                              'REVISION', 'COMMENTS']
        
        # Filter columns that exist in the dataframe
        display_columns = [col for col in columns_to_include if col in removed_df.columns]
        
        # Write headers
        headers = [col.replace('_', ' ').title() for col in display_columns]
        for col_num, header in enumerate(headers, 1):
            cell = removed_sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = HEADER_FONT
            cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = THIN_BORDER
        
        # Write data
        for row_num, row in enumerate(removed_df.itertuples(), 2):
            for col_num, col in enumerate(display_columns, 1):
                cell = removed_sheet.cell(row=row_num, column=col_num)
                cell.value = getattr(row, col, '')
                cell.fill = HIGHLIGHT_REMOVED
                cell.border = THIN_BORDER
        
        # Auto-adjust column widths
        for col in removed_sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            
            adjusted_width = (max_length + 2) * 1.2
            removed_sheet.column_dimensions[column].width = adjusted_width
    
    # Save the file
    wb.save(output_file)
    
    return output_file

def generate_region_exports(comparison, pm_df, month, export_dir='exports', fsi_format=False):
    """
    Generate region-specific export files.
    
    Args:
        comparison (dict): Comparison results from compare_pm_files
        pm_df (DataFrame): PM-edited allocation data
        month (str): Month of the data (e.g., "APRIL 2025")
        export_dir (str): Directory to save the output files
        fsi_format (bool): Whether to include FSI import format export
        
    Returns:
        dict: Dictionary with export file paths
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Preprocess PM dataframe if not already done
    pm_df = preprocess_pm_data(pm_df)
    
    # Get region map from comparison or generate new one
    if comparison and 'region_map' in comparison:
        region_map = comparison['region_map']
    else:
        region_map = identify_regions(pm_df)
    
    # Add region column based on DIV
    pm_df['REGION'] = pm_df['DIV'].map(region_map)
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Dictionary to store export file paths
    export_files = {}
    
    # Process for each region
    for region in ['DFW', 'HOU', 'WTX']:
        # Filter by region
        region_df = pm_df[pm_df['REGION'] == region].copy()
        
        if region_df.empty:
            logger.info(f"No data for region {region}")
            continue
        
        # Standard export format
        export_file = os.path.join(
            export_dir, 
            f"{region}_{month.replace(' ', '_')}_{timestamp}.csv"
        )
        
        # Select and reorder columns
        export_columns = [
            'DIV', 'JOB', 'ASSET_ID', 'EQUIPMENT_DESCRIPTION', 'DRIVER', 
            'UNIT_ALLOCATION', 'RATE', 'UNIT_ALLOCATION_AMOUNT', 'COST_CODE', 
            'REVISION', 'COMMENTS'
        ]
        
        # Filter columns that exist
        export_columns = [col for col in export_columns if col in region_df.columns]
        
        # Export standard format
        region_df[export_columns].to_csv(export_file, index=False)
        export_files[f"{region}_standard"] = export_file
        
        # FSI import format if requested
        if fsi_format:
            fsi_file = os.path.join(
                export_dir, 
                f"{region}_{month.replace(' ', '_')}_FSI_IMPORT_{timestamp}.csv"
            )
            
            # Create FSI format
            fsi_df = region_df.copy()
            
            # FSI format requires specific columns with specific names
            fsi_columns = {
                'DIV': 'Division',
                'JOB': 'Job',
                'COST_CODE': 'Cost Code',
                'UNIT_ALLOCATION_AMOUNT': 'Amount'
            }
            
            # Create the FSI format dataframe
            fsi_export_df = pd.DataFrame()
            
            for fsi_col, original_col in fsi_columns.items():
                if fsi_col in fsi_df.columns:
                    fsi_export_df[original_col] = fsi_df[fsi_col]
                else:
                    fsi_export_df[original_col] = ''
            
            # Add description field (Asset ID + Equipment Description)
            fsi_export_df['Description'] = fsi_df['ASSET_ID'] + ' - ' + fsi_df['EQUIPMENT_DESCRIPTION']
            
            # Export FSI format
            fsi_export_df.to_csv(fsi_file, index=False)
            export_files[f"{region}_fsi"] = fsi_file
    
    return {
        'success': True,
        'export_files': export_files
    }

def process_pm_allocation(original_file, pm_file, region='all', month='', fsi_format=False):
    """
    Process PM allocation files and generate comparison and exports.
    
    Args:
        original_file (str): Path to original allocation file
        pm_file (str): Path to PM-edited allocation file
        region (str): Region to filter (DFW, HOU, WTX, ALL)
        month (str): Month of the data (e.g., "APRIL 2025")
        fsi_format (bool): Whether to include FSI import format export
        
    Returns:
        dict: Dictionary with results and file paths
    """
    try:
        logger.info(f"Processing PM allocation files: Original: {original_file}, PM: {pm_file}")
        logger.info(f"Parameters - Region: {region}, Month: {month}, FSI Format: {fsi_format}")
        
        # Load Excel files
        try:
            original_df = pd.read_excel(original_file)
            pm_df = pd.read_excel(pm_file)
            
            logger.info(f"Files loaded successfully. Original shape: {original_df.shape}, PM shape: {pm_df.shape}")
            logger.info(f"Original columns: {list(original_df.columns)}")
            logger.info(f"PM columns: {list(pm_df.columns)}")
        except Exception as e:
            logger.error(f"Error loading Excel files: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Error loading files: {str(e)}"
            }
        
        # Extract month from filename if not provided
        if not month:
            month_pattern = r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{4}'
            match = re.search(month_pattern, os.path.basename(pm_file), re.IGNORECASE)
            if match:
                month = match.group(0).upper()
            else:
                # Default to current month
                month = datetime.now().strftime('%B %Y').upper()
            
            logger.info(f"Month determined from filename: {month}")
        
        # Compare files
        try:
            comparison = compare_pm_files(original_df, pm_df, region)
            logger.info("Files compared successfully")
        except Exception as e:
            logger.error(f"Error comparing files: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Error comparing files: {str(e)}"
            }
        
        # Generate comparison file
        try:
            comparison_file = generate_comparison_file(comparison, month)
            logger.info(f"Comparison file generated: {comparison_file}")
        except Exception as e:
            logger.error(f"Error generating comparison file: {str(e)}", exc_info=True)
            comparison_file = ""
        
        # Generate region exports
        try:
            export_results = generate_region_exports(pm_df, month=month, fsi_format=fsi_format)
            logger.info(f"Export files generated: {list(export_results.get('export_files', {}).keys())}")
        except Exception as e:
            logger.error(f"Error generating export files: {str(e)}", exc_info=True)
            export_results = {'export_files': {}}
        
        # Count changes
        num_changes = len(comparison.get('changes', []))
        num_added = len(comparison.get('added', []))
        num_removed = len(comparison.get('removed', []))
        total_changes = num_changes + num_added + num_removed
        
        # Format comparison data for template display
        formatted_comparison = {
            'changed_rows': [],
            'added_rows': [],
            'removed_rows': []
        }
        
        # Format changed rows
        if not comparison.get('changes').empty:
            changes_df = comparison.get('changes')
            
            # Group changes by asset to combine multiple field changes for the same asset
            grouped_changes = {}
            for _, row in changes_df.iterrows():
                key = f"{row.get('DIV', '')}-{row.get('JOB', '')}-{row.get('ASSET_ID', '')}"
                
                if key not in grouped_changes:
                    grouped_changes[key] = {
                        'div': row.get('DIV', ''),
                        'job': row.get('JOB', ''),
                        'asset_id': row.get('ASSET_ID', ''),
                        'equipment': row.get('EQUIPMENT_DESCRIPTION', ''),
                        'changes': []
                    }
                
                # Add this field change
                grouped_changes[key]['changes'].append({
                    'field': row.get('CHANGED_FIELD', ''),
                    'original': row.get('ORIGINAL_VALUE', ''),
                    'updated': row.get('UPDATED_VALUE', '')
                })
            
            # Convert to list
            formatted_comparison['changed_rows'] = list(grouped_changes.values())
            
        # Format added rows
        if not comparison.get('added').empty:
            added_df = comparison.get('added')
            for _, row in added_df.iterrows():
                formatted_comparison['added_rows'].append({
                    'div': row.get('DIV', ''),
                    'job': row.get('JOB', ''),
                    'asset_id': row.get('ASSET_ID', ''),
                    'equipment': row.get('EQUIPMENT_DESCRIPTION', ''),
                    'driver': row.get('DRIVER', ''),
                    'allocation': row.get('UNIT_ALLOCATION', 0),
                    'cost_code': row.get('COST_CODE', ''),
                    'revision_amount': row.get('REVISION', 0)
                })
        
        # Format removed rows
        if not comparison.get('removed').empty:
            removed_df = comparison.get('removed')
            for _, row in removed_df.iterrows():
                formatted_comparison['removed_rows'].append({
                    'div': row.get('DIV', ''),
                    'job': row.get('JOB', ''),
                    'asset_id': row.get('ASSET_ID', ''),
                    'equipment': row.get('EQUIPMENT_DESCRIPTION', ''),
                    'driver': row.get('DRIVER', ''),
                    'allocation': row.get('UNIT_ALLOCATION', 0),
                    'cost_code': row.get('COST_CODE', ''),
                    'allocation_amount': row.get('UNIT_ALLOCATION_AMOUNT', 0)
                })
        
        logger.info(f"Comparison results: {total_changes} total changes")
        logger.info(f"Changed fields: {num_changes}, Added rows: {num_added}, Removed rows: {num_removed}")
        
        return {
            'success': True,
            'comparison_file': comparison_file,
            'export_files': export_results.get('export_files', {}),
            'comparison': formatted_comparison,
            'message': f"Successfully processed PM allocation files for {month}",
            'changes': {
                'total': total_changes,
                'changed_fields': num_changes,
                'added_rows': num_added,
                'removed_rows': num_removed
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing PM allocation files: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f"Error processing files: {str(e)}"
        }