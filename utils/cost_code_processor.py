"""
Cost Code Processor

This module handles special cost code splitting rules for specific projects and assets.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)

# Matagorda job pattern constants
MATAGORDA_JOB_CODE = "0496"
MATAGORDA_COST_CODES = {
    "PRIMARY": "6012B",   # Primary cost code (50% for EX-65, 60% for others)
    "SECONDARY": "6012C", # Secondary cost code (30% for EX-65, 40% for others)
    "TERTIARY": "6012F"   # Tertiary cost code (20% for EX-65 only)
}

SPECIAL_ASSETS = {
    "EX-65": {
        "split_type": "triple",
        "percentages": [0.5, 0.3, 0.2]  # 50/30/20 split
    }
}

# Default split for excavators in Matagorda
DEFAULT_EXCAVATOR_SPLIT = {
    "split_type": "double",
    "percentages": [0.6, 0.4]  # 60/40 split
}


def is_matagorda_job(job_number):
    """
    Check if a job number is a Matagorda job (starts with 0496)
    
    Args:
        job_number (str): Job number to check
        
    Returns:
        bool: True if it's a Matagorda job
    """
    return str(job_number).startswith(MATAGORDA_JOB_CODE)


def is_excavator(equipment_id):
    """
    Check if an equipment ID is for an excavator (starts with EX)
    
    Args:
        equipment_id (str): Equipment ID to check
        
    Returns:
        bool: True if it's an excavator
    """
    return str(equipment_id).upper().startswith("EX")


def get_split_pattern(equipment_id):
    """
    Get the split pattern for an equipment ID
    
    Args:
        equipment_id (str): Equipment ID to get split pattern for
        
    Returns:
        dict: Split pattern info including type and percentages
    """
    equipment_id = str(equipment_id).upper()
    
    # Check for special assets with specific rules
    if equipment_id in SPECIAL_ASSETS:
        return SPECIAL_ASSETS[equipment_id]
        
    # For excavators, use the default excavator split
    if is_excavator(equipment_id):
        return DEFAULT_EXCAVATOR_SPLIT
        
    # All other equipment types get no split
    return {
        "split_type": "none",
        "percentages": [1.0]  # 100% to primary cost code
    }


def apply_cost_code_splitting(df, equipment_id_col="equipment_id", job_number_col="job_number", 
                             cost_code_col="cost_code", amount_col="amount", 
                             rate_col="rate", days_col="days"):
    """
    Apply cost code splitting rules to matching rows in a DataFrame
    
    Args:
        df (DataFrame): DataFrame with billing data
        equipment_id_col (str): Column name for equipment ID
        job_number_col (str): Column name for job number
        cost_code_col (str): Column name for cost code
        amount_col (str): Column name for amount
        rate_col (str): Column name for rate
        days_col (str): Column name for days
        
    Returns:
        DataFrame: DataFrame with split rows where applicable
    """
    result_df = pd.DataFrame()
    
    # Process each row
    for _, row in df.iterrows():
        job_number = str(row.get(job_number_col, ""))
        equipment_id = str(row.get(equipment_id_col, ""))
        cost_code = str(row.get(cost_code_col, ""))
        
        # If it's a Matagorda job and has a special split pattern
        if is_matagorda_job(job_number):
            split_pattern = get_split_pattern(equipment_id)
            
            # Skip if there's no special handling needed
            if split_pattern["split_type"] == "none":
                result_df = pd.concat([result_df, pd.DataFrame([row])], ignore_index=True)
                continue
                
            # Create split rows
            split_rows = []
            percentages = split_pattern["percentages"]
            
            # Primary cost code
            primary_row = row.copy()
            primary_row[cost_code_col] = MATAGORDA_COST_CODES["PRIMARY"]
            primary_row[amount_col] = row[amount_col] * percentages[0] if amount_col in row and pd.notna(row[amount_col]) else None
            primary_row[days_col] = row[days_col] * percentages[0] if days_col in row and pd.notna(row[days_col]) else None
            primary_row["split_note"] = f"{int(percentages[0] * 100)}% allocation"
            split_rows.append(primary_row)
            
            # Secondary cost code
            if len(percentages) > 1 and percentages[1] > 0:
                secondary_row = row.copy()
                secondary_row[cost_code_col] = MATAGORDA_COST_CODES["SECONDARY"]
                secondary_row[amount_col] = row[amount_col] * percentages[1] if amount_col in row and pd.notna(row[amount_col]) else None
                secondary_row[days_col] = row[days_col] * percentages[1] if days_col in row and pd.notna(row[days_col]) else None
                secondary_row["split_note"] = f"{int(percentages[1] * 100)}% allocation"
                split_rows.append(secondary_row)
            
            # Tertiary cost code (for triple split like EX-65)
            if len(percentages) > 2 and percentages[2] > 0:
                tertiary_row = row.copy()
                tertiary_row[cost_code_col] = MATAGORDA_COST_CODES["TERTIARY"]
                tertiary_row[amount_col] = row[amount_col] * percentages[2] if amount_col in row and pd.notna(row[amount_col]) else None
                tertiary_row[days_col] = row[days_col] * percentages[2] if days_col in row and pd.notna(row[days_col]) else None
                tertiary_row["split_note"] = f"{int(percentages[2] * 100)}% allocation"
                split_rows.append(tertiary_row)
                
            # Add split rows to result
            split_df = pd.DataFrame(split_rows)
            result_df = pd.concat([result_df, split_df], ignore_index=True)
            
        else:
            # No special handling needed, just add the row as is
            result_df = pd.concat([result_df, pd.DataFrame([row])], ignore_index=True)
    
    return result_df


def summarize_splits(df, job_number_col="job_number", equipment_id_col="equipment_id", amount_col="amount"):
    """
    Generate a summary of cost code splits in the data
    
    Args:
        df (DataFrame): DataFrame with billing data
        job_number_col (str): Column name for job number
        equipment_id_col (str): Column name for equipment ID 
        amount_col (str): Column name for amount
        
    Returns:
        dict: Summary of split allocations
    """
    matagorda_rows = df[df[job_number_col].astype(str).str.startswith(MATAGORDA_JOB_CODE)]
    
    if matagorda_rows.empty:
        return {
            "has_splits": False,
            "total_split_rows": 0,
            "total_split_amount": 0
        }
    
    # Group by equipment to find splits
    equipment_groups = matagorda_rows.groupby(equipment_id_col)
    
    split_summary = {
        "has_splits": False,
        "total_split_rows": 0,
        "total_split_amount": 0,
        "equipment_splits": []
    }
    
    for equipment_id, group in equipment_groups:
        # Check if this equipment has a split
        split_pattern = get_split_pattern(equipment_id)
        
        if split_pattern["split_type"] != "none":
            split_summary["has_splits"] = True
            split_summary["total_split_rows"] += len(group)
            
            if amount_col in group.columns:
                split_summary["total_split_amount"] += group[amount_col].sum()
            
            # Add equipment-specific summary
            split_summary["equipment_splits"].append({
                "equipment_id": equipment_id,
                "split_type": split_pattern["split_type"],
                "percentages": split_pattern["percentages"],
                "row_count": len(group)
            })
    
    return split_summary