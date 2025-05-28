"""
Active Driver Filter Module
Removes terminated, inactive, or invalid drivers from all datasets
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

def filter_active_timecards(timecard_data):
    """Apply active filter to timecard records"""
    active_records = []
    for record in timecard_data:
        # Check various status field names
        status_fields = ['Status', 'Employee Status', 'Active', 'Employment Status']
        is_active = True
        
        for field in status_fields:
            if field in record:
                status = str(record[field]).lower()
                if status in {"terminated", "inactive", "resigned", "deceased", "temp term"}:
                    is_active = False
                    break
        
        if is_active:
            active_records.append(record)
    
    return active_records

def validate_driver_status(consolidated_employees, active_timecard_ids=None):
    """Validate using AssetListExport contact assignments and timecard activity"""
    import pandas as pd
    
    try:
        # Load AssetListExport for real driver assignments
        asset_df = pd.read_excel('AssetsListExport.xlsx')
        
        # Extract employee IDs from Contact field
        asset_driver_ids = set()
        for contact in asset_df['Contact'].dropna():
            contact_str = str(contact)
            # Extract numbers in parentheses like "(210003)"
            import re
            matches = re.findall(r'\((\d+)\)', contact_str)
            for match in matches:
                asset_driver_ids.add(int(match))
        
        # Also check Secondary Asset Identifier
        for secondary in asset_df['Secondary Asset Identifier'].dropna():
            secondary_str = str(secondary)
            matches = re.findall(r'^(\d+)', secondary_str)
            for match in matches:
                asset_driver_ids.add(int(match))
        
        active_employees = []
        
        for emp in consolidated_employees:
            emp_no = emp.get('Employee No', 0)
            
            # Include if they have BOTH asset assignment AND timecard activity
            if (emp_no in asset_driver_ids and 
                active_timecard_ids and emp_no in active_timecard_ids):
                active_employees.append(emp)
        
        print(f"Driver Filter Results: {len(active_employees)} active drivers (asset + timecard validated)")
        return active_employees
        
    except Exception as e:
        print(f"Error loading asset data: {e}")
        return []