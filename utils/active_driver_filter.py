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
    """Validate and clean the consolidated employee list using ONLY recent timecard activity"""
    if not consolidated_employees:
        return []
    
    active_employees = []
    terminated_count = 0
    
    for emp in consolidated_employees:
        emp_no = emp.get('Employee No', 0)
        
        # STRICT FILTER: Only include if they have recent timecard activity
        if active_timecard_ids and emp_no in active_timecard_ids:
            active_employees.append(emp)
        else:
            terminated_count += 1
    
    print(f"Driver Filter Results: {len(active_employees)} active (timecard validated), {terminated_count} filtered out")
    return active_employees