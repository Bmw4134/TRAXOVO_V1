"""
Active Driver Filter Module
Purpose: Remove all terminated, inactive, or invalid drivers from incoming datasets.
"""

def filter_active_employees(employee_list):
    """
    INPUT (List[Dict]): [
        {"driver_id": "D123", "status": "Active"},
        {"driver_id": "D456", "status": "Terminated"},
        ...
    ]
    
    Logic:
    - Normalize 'status' field to lowercase
    - Exclude any status in:
      {"terminated", "inactive", "resigned", "deceased"}
    
    OUTPUT (List[Dict]): Only active drivers.
    """
    return [
        emp for emp in employee_list
        if emp.get("status", "").lower() not in {
            "terminated", "inactive", "resigned", "deceased"
        }
    ]

def filter_timecard_data(timecard_df):
    """
    Apply active filter to timecard DataFrame
    """
    import pandas as pd
    
    # Check for status column variations
    status_cols = [col for col in timecard_df.columns if 'status' in col.lower()]
    
    if status_cols:
        status_col = status_cols[0]
        active_mask = ~timecard_df[status_col].str.lower().isin({
            "terminated", "inactive", "resigned", "deceased"
        })
        return timecard_df[active_mask]
    
    # If no status column, return all (assume active)
    return timecard_df

def get_active_driver_count(file_path):
    """
    Get count of active drivers from your timecard files
    """
    import pandas as pd
    
    try:
        df = pd.read_excel(file_path)
        filtered_df = filter_timecard_data(df)
        
        # Find employee ID column
        emp_cols = [col for col in filtered_df.columns if any(word in col.lower() for word in ['employee', 'emp', 'driver'])]
        
        if emp_cols:
            return filtered_df[emp_cols[0]].nunique()
        else:
            return len(filtered_df)
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0