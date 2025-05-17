"""
Cost Code Processor

This module handles complex cost code splitting logic for PM allocation sheets
"""

import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)

def _process_special_asset_splits(df):
    """
    Process special asset splits for Matagorda jobs and other complex patterns
    
    Args:
        df (pandas.DataFrame): DataFrame with potential special splits
        
    Returns:
        pandas.DataFrame: Processed DataFrame with splits handled
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
        
    # Find our equipment and job columns
    equipment_col = 'equipment_id'
    job_col = 'job_number'
    cost_code_col = 'cost_code'
    note_col = 'notes'
    
    # Look for alternative column names if standards not found
    for col in df.columns:
        if 'equip' in str(col).lower() and 'id' in str(col).lower():
            equipment_col = col
        elif 'job' in str(col).lower() and ('id' in str(col).lower() or 'number' in str(col).lower()):
            job_col = col
        elif 'cost' in str(col).lower() and 'code' in str(col).lower():
            cost_code_col = col
        elif 'note' in str(col).lower() or 'comment' in str(col).lower():
            note_col = col
            
    # Create the notes column if it doesn't exist
    if note_col not in df.columns:
        df[note_col] = None
            
    # Process the data row by row to identify special cases
    processed_rows = []
    
    for _, row in df.iterrows():
        # Get key fields
        asset_id = str(row.get(equipment_col, '')).upper()
        job_number = str(row.get(job_col, ''))
        cost_code = str(row.get(cost_code_col, ''))
        
        # Check for Matagorda patterns
        is_matagorda = ('MATAGORDA' in job_number.upper() or 
                       '0496' in cost_code or
                       '496' in cost_code)
                       
        # Special handling for EX-65 at Matagorda (triple split)
        if asset_id == 'EX-65' and is_matagorda:
            # Special triple split for EX-65 at Matagorda
            processed_rows.extend(_create_triple_split(row, cost_code_col, note_col))
            
        # Special handling for excavators at Matagorda (double split)
        elif asset_id.startswith('EX-') and is_matagorda:
            # Double split for other excavators at Matagorda
            processed_rows.extend(_create_double_split(row, cost_code_col, note_col))
            
        else:
            # Keep original row for non-special cases
            processed_rows.append(row)
            
    # Create new DataFrame with all processed rows
    result_df = pd.DataFrame(processed_rows)
    
    # Preserve original column order
    result_df = result_df[df.columns]
    
    return result_df
    
def _create_triple_split(row, cost_code_col, note_col):
    """Create a triple split for special assets like EX-65 at Matagorda"""
    splits = []
    
    # Find amount column if it exists
    amount_col = None
    for col in row.index:
        if 'amount' in str(col).lower() or 'rate' in str(col).lower():
            amount_col = col
            break
    
    # Create split 1: Default split for general equipment (50%)
    row1 = row.copy()
    row1[cost_code_col] = '0496 6012B'  # Standard cost code
    row1['unit_allocation'] = 0.5  # 50% allocation
    if amount_col and amount_col in row1 and not pd.isna(row1[amount_col]):
        row1[amount_col] = row1[amount_col] * 0.5
    if note_col in row1 and not pd.isna(row1[note_col]):
        row1[note_col] += " | Split 1/3: General equipment"
    else:
        row1[note_col] = "Split 1/3: General equipment"
    splits.append(row1)
    
    # Create split 2: Pipeline-specific cost (30%)
    row2 = row.copy()
    row2[cost_code_col] = '0496 6012C'  # Pipeline cost code 
    row2['unit_allocation'] = 0.3  # 30% allocation
    if amount_col and amount_col in row2 and not pd.isna(row2[amount_col]):
        row2[amount_col] = row2[amount_col] * 0.3
    if note_col in row2 and not pd.isna(row2[note_col]):
        row2[note_col] += " | Split 2/3: Pipeline-specific"
    else:
        row2[note_col] = "Split 2/3: Pipeline-specific"
    splits.append(row2)
    
    # Create split 3: Foundation-specific cost (20%)
    row3 = row.copy()
    row3[cost_code_col] = '0496 6012F'  # Foundation cost code
    row3['unit_allocation'] = 0.2  # 20% allocation
    if amount_col and amount_col in row3 and not pd.isna(row3[amount_col]):
        row3[amount_col] = row3[amount_col] * 0.2
    if note_col in row3 and not pd.isna(row3[note_col]):
        row3[note_col] += " | Split 3/3: Foundation-specific"
    else:
        row3[note_col] = "Split 3/3: Foundation-specific"
    splits.append(row3)
    
    return splits
    
def _create_double_split(row, cost_code_col, note_col):
    """Create a double split for excavators at Matagorda"""
    splits = []
    
    # Find amount column if it exists
    amount_col = None
    for col in row.index:
        if 'amount' in str(col).lower() or 'rate' in str(col).lower():
            amount_col = col
            break
    
    # Create split 1: General equipment (60%)
    row1 = row.copy()
    row1[cost_code_col] = '0496 6012B'  # Standard cost code
    row1['unit_allocation'] = 0.6  # 60% allocation
    if amount_col and amount_col in row1 and not pd.isna(row1[amount_col]):
        row1[amount_col] = row1[amount_col] * 0.6
    if note_col in row1 and not pd.isna(row1[note_col]):
        row1[note_col] += " | Split 1/2: General equipment"
    else:
        row1[note_col] = "Split 1/2: General equipment"
    splits.append(row1)
    
    # Create split 2: Pipeline-specific cost (40%)
    row2 = row.copy()
    row2[cost_code_col] = '0496 6012C'  # Pipeline cost code 
    row2['unit_allocation'] = 0.4  # 40% allocation
    if amount_col and amount_col in row2 and not pd.isna(row2[amount_col]):
        row2[amount_col] = row2[amount_col] * 0.4
    if note_col in row2 and not pd.isna(row2[note_col]):
        row2[note_col] += " | Split 2/2: Pipeline-specific"
    else:
        row2[note_col] = "Split 2/2: Pipeline-specific"
    splits.append(row2)
    
    return splits

def process_cost_code_splits(df):
    """
    Process cost code splits for a DataFrame
    
    Args:
        df (DataFrame): Input data with potential cost code splits
        
    Returns:
        DataFrame: Processed data with cost code splits handled
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
        
    # Process special asset split cases first (before general cost code splitting)
    try:
        df = _process_special_asset_splits(df.copy())
    except Exception as e:
        logger.error(f"Error in special asset splits: {str(e)}")
        # Continue with original data if there's an error
        
    # Preserve original columns to ensure we don't lose any
    original_columns = df.columns.tolist()
        
    # Check if we have necessary columns
    necessary_cols = ['cost_code', 'job_number', 'asset_id', 'unit_allocation']
    
    # Create columns if they don't exist
    for col in necessary_cols:
        if col not in df.columns:
            if col == 'unit_allocation':
                df[col] = 1.0
            else:
                df[col] = None
    
    # Process rows with potential splits
    processed_rows = []
    cost_code_splits = 0
    
    # Find column with cost codes
    cost_code_col = None
    for col in df.columns:
        if 'cost' in str(col).lower() and 'code' in str(col).lower():
            cost_code_col = col
            break
    
    # Find column with notes 
    note_col = None
    for col in df.columns:
        if 'note' in str(col).lower() or 'detail' in str(col).lower() or 'comment' in str(col).lower():
            note_col = col
            break
            
    # Fallback if columns not found
    if not cost_code_col:
        cost_code_col = 'cost_code'
    if not note_col:
        note_col = 'note'
    
    # Make sure columns exist
    if cost_code_col not in df.columns:
        df[cost_code_col] = None
    if note_col not in df.columns:
        df[note_col] = None
    
    # Process each row
    for _, row in df.iterrows():
        # Get cost code and note
        cost_code = row.get(cost_code_col, '')
        note = row.get(note_col, '')
        
        # Skip if no cost code or no split indicated
        if pd.isna(cost_code) or ('/' not in str(cost_code) and 'CC NEEDED' not in str(cost_code)):
            processed_rows.append(row)
            continue
            
        # Handle CC NEEDED marker
        if 'CC NEEDED' in str(cost_code):
            # Extract the base cost code if available
            parts = str(cost_code).split('/')
            base_code = parts[0].strip() if len(parts) > 0 else '9000 100F'
            
            # Replace with the base code
            row_copy = row.copy()
            row_copy[cost_code_col] = base_code
            if not pd.isna(note):
                row_copy[note_col] = f"{note} (Cost code updated from {cost_code})"
            else:
                row_copy[note_col] = f"Cost code updated from {cost_code}"
                
            processed_rows.append(row_copy)
            continue
            
        # Process splits with slashes
        if '/' in str(cost_code):
            # Parse the split codes
            split_codes = [c.strip() for c in str(cost_code).split('/')]
            
            # Default to equal distribution
            split_ratio = 1.0 / len(split_codes)
            split_ratios = [split_ratio] * len(split_codes)
            
            # Check for split instructions
            if not pd.isna(note) and 'split' in str(note).lower():
                # Look for patterns like "Split 0.25 EA" or "Split 25% EA"
                values = re.findall(r'(\d+\.\d+|\d+)(%)?', str(note))
                if values:
                    try:
                        # Get the first numeric value
                        value_str, is_percent = values[0]
                        value = float(value_str)
                        
                        # Convert percentage to decimal if needed
                        if is_percent:
                            value = value / 100.0
                            
                        if value > 0:
                            # Handle special case for Matagorda job - multiple different cost codes
                            job_number = row.get('job_number', '')
                            asset_id = row.get('equipment_id', '')
                            
                            # Match patterns for Matagorda or similar complex splits
                            is_complex_split = (
                                'matagorda' in str(job_number).lower() or 
                                '496' in str(cost_code) or
                                'ex-65' in str(asset_id).lower() or
                                (len(split_codes) > 3 and any('eq' in code.lower() for code in split_codes))
                            )
                            
                            if is_complex_split:
                                # Special processing for complex Matagorda split
                                # Keep the cost codes but distribute them evenly
                                split_ratios = [1.0 / len(split_codes)] * len(split_codes)
                            else:
                                # Standard case - each split gets this ratio
                                split_ratios = [value] * len(split_codes)
                            
                            # Normalize if needed
                            total = sum(split_ratios)
                            if total != 1.0:
                                split_ratios = [r / total for r in split_ratios]
                    except ValueError:
                        # Fall back to equal distribution
                        logger.warning(f"Failed to parse split ratio from note: {note}")
            
            # Get allocation amount
            allocation = row.get('unit_allocation', 1.0)
            if pd.isna(allocation):
                allocation = 1.0
                
            # Get financial amount if available
            amount_col = None
            for col in df.columns:
                if 'amount' in str(col).lower() or 'rate' in str(col).lower():
                    amount_col = col
                    break
                    
            # Create a row for each split code
            for i, code in enumerate(split_codes):
                # Handle empty codes or EQ shorthand
                if not code or code.strip() == '' or code.upper() == 'EQ':
                    code = '9000 100M'  # Default equipment code
                
                # Special handling for Matagorda jobs - preserve original cost code format
                if '496' in str(code):
                    # Ensure proper cost code format for Matagorda
                    if ' ' not in code and len(code) >= 4:
                        # Format as "0496 6012X" pattern if needed
                        prefix = code[:4]
                        suffix = code[4:]
                        
                        # Add leading zero if needed (049 -> 0496)
                        if len(prefix) == 3 and prefix.isdigit():
                            prefix = "0" + prefix
                            
                        code = f"{prefix} {suffix}"
                        
                    # Add project identifier if missing
                    if not code.upper().endswith(('A', 'B', 'C', 'D', 'E', 'F')) and len(code) > 6:
                        code = code + "B"  # Default to B if not specified
                
                split_row = row.copy()
                split_row[cost_code_col] = code
                
                # Apply the split ratio to allocation
                if i < len(split_ratios):
                    this_ratio = split_ratios[i]
                    split_row['unit_allocation'] = allocation * this_ratio
                    
                    # Apply to amount if available
                    if amount_col and amount_col in split_row and not pd.isna(split_row[amount_col]):
                        split_row[amount_col] = split_row[amount_col] * this_ratio
                
                # Add note about the split
                if pd.isna(note) or not note:
                    split_row[note_col] = f"Cost code split {i+1}/{len(split_codes)}"
                else:
                    split_row[note_col] = f"{note} (Split {i+1}/{len(split_codes)})"
                    
                processed_rows.append(split_row)
                
            cost_code_splits += len(split_codes) - 1
            continue
            
        # No split needed
        processed_rows.append(row)
        
    # Create result DataFrame with proper column structure
    result_df = pd.DataFrame(processed_rows)
    
    # Ensure all original columns are preserved (especially status field)
    for col in original_columns:
        if col not in result_df.columns:
            result_df[col] = None
    
    # Reorder columns to match original
    result_df = result_df[original_columns]
    
    logger.info(f"Processed {cost_code_splits} cost code splits")
    return result_df