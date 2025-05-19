"""
Report Validator Module

This module validates attendance data reports to ensure data integrity
by checking for duplicate entries, proper counting, and logical consistency.
"""

import logging
import argparse
from datetime import datetime
from collections import Counter

# Import the attendance data generation function
# This will be the function whose output we validate
try:
    # Try different import paths based on how the function is defined
    try:
        from routes.driver_module import get_attendance_data
    except ImportError:
        try:
            from utils.attendance_processor import get_attendance_data
        except ImportError:
            from routes.driver_module_new import get_attendance_data
except ImportError:
    logging.error("Could not import get_attendance_data function. Make sure it exists in one of the expected modules.")
    # Define a stub function for testing if the real one isn't available
    def get_attendance_data(date=None):
        """Stub function for testing"""
        return {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'late_drivers': [],
            'early_end_drivers': [],
            'not_on_job_drivers': [],
            'exception_drivers': [],
            'summary': {'total_drivers': 0, 'total_issues': 0}
        }

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_report(report_data):
    """
    Validate attendance report data for integrity and consistency
    
    Args:
        report_data (dict): Report data from get_attendance_data function
        
    Returns:
        dict: Validation results containing any issues found
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    # Check if report has required keys
    required_keys = ['late_drivers', 'early_end_drivers', 'not_on_job_drivers', 
                    'exception_drivers', 'summary']
    
    for key in required_keys:
        if key not in report_data:
            validation_results['is_valid'] = False
            validation_results['errors'].append({
                'type': 'missing_key',
                'message': f"Report is missing required key: {key}"
            })
    
    # If missing essential keys, return early
    if not validation_results['is_valid']:
        return validation_results
    
    # Get the lists of drivers with issues
    late_drivers = report_data.get('late_drivers', [])
    early_end_drivers = report_data.get('early_end_drivers', [])
    not_on_job_drivers = report_data.get('not_on_job_drivers', [])
    exception_drivers = report_data.get('exception_drivers', [])
    
    # Extract all employee IDs for uniqueness checking
    all_employee_ids = []
    for driver_list in [late_drivers, early_end_drivers, not_on_job_drivers, exception_drivers]:
        for driver in driver_list:
            if 'employee_id' in driver:
                all_employee_ids.append(driver['employee_id'])
    
    # Count occurrences of each employee ID
    id_counts = Counter(all_employee_ids)
    
    # Check for duplicates across lists (same driver in multiple categories)
    duplicates = {emp_id: count for emp_id, count in id_counts.items() if count > 1}
    
    if duplicates:
        for emp_id, count in duplicates.items():
            # Find which lists contain this employee
            categories = []
            if any(d.get('employee_id') == emp_id for d in late_drivers):
                categories.append('late_drivers')
            if any(d.get('employee_id') == emp_id for d in early_end_drivers):
                categories.append('early_end_drivers')
            if any(d.get('employee_id') == emp_id for d in not_on_job_drivers):
                categories.append('not_on_job_drivers')
            if any(d.get('employee_id') == emp_id for d in exception_drivers):
                categories.append('exception_drivers')
            
            validation_results['warnings'].append({
                'type': 'duplicate_employee',
                'employee_id': emp_id,
                'count': count,
                'categories': categories,
                'message': f"Employee ID {emp_id} appears in multiple issue categories: {', '.join(categories)}"
            })
    
    # Check total issues count against actual sum
    actual_issue_count = len(late_drivers) + len(early_end_drivers) + len(not_on_job_drivers) + len(exception_drivers)
    reported_issue_count = report_data.get('summary', {}).get('total_issues', 0)
    
    if actual_issue_count != reported_issue_count:
        validation_results['is_valid'] = False
        validation_results['errors'].append({
            'type': 'count_mismatch',
            'expected': actual_issue_count,
            'actual': reported_issue_count,
            'message': f"Total issues count mismatch. Expected: {actual_issue_count}, Reported: {reported_issue_count}"
        })
    
    # Check for unique employee IDs within each list
    for list_name, driver_list in [
        ('late_drivers', late_drivers), 
        ('early_end_drivers', early_end_drivers),
        ('not_on_job_drivers', not_on_job_drivers), 
        ('exception_drivers', exception_drivers)
    ]:
        employee_ids = [d.get('employee_id') for d in driver_list if 'employee_id' in d]
        id_counts = Counter(employee_ids)
        duplicates = {emp_id: count for emp_id, count in id_counts.items() if count > 1}
        
        if duplicates:
            for emp_id, count in duplicates.items():
                validation_results['is_valid'] = False
                validation_results['errors'].append({
                    'type': 'duplicate_in_category',
                    'category': list_name,
                    'employee_id': emp_id,
                    'count': count,
                    'message': f"Employee ID {emp_id} appears {count} times in {list_name}"
                })
    
    # Gather statistics
    validation_results['statistics'] = {
        'late_drivers_count': len(late_drivers),
        'early_end_drivers_count': len(early_end_drivers),
        'not_on_job_drivers_count': len(not_on_job_drivers),
        'exception_drivers_count': len(exception_drivers),
        'total_actual_issues': actual_issue_count,
        'total_reported_issues': reported_issue_count,
        'unique_employees_with_issues': len(set(all_employee_ids))
    }
    
    return validation_results

def print_validation_results(results, detailed=True):
    """
    Print validation results in a readable format
    
    Args:
        results (dict): Validation results from validate_report
        detailed (bool): Whether to print detailed information
    """
    print("\n" + "="*80)
    print(f"REPORT VALIDATION RESULTS")
    print("="*80)
    
    if results['is_valid']:
        print("✅ Report is valid! No critical errors detected.")
    else:
        print("❌ Report has validation errors!")
    
    # Print statistics
    print("\nSTATISTICS:")
    for key, value in results['statistics'].items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    # Print errors
    if results['errors']:
        print("\nERRORS:")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error['message']}")
            if detailed:
                for k, v in error.items():
                    if k != 'message':
                        print(f"     - {k}: {v}")
    
    # Print warnings
    if results['warnings']:
        print("\nWARNINGS:")
        for i, warning in enumerate(results['warnings'], 1):
            print(f"  {i}. {warning['message']}")
            if detailed:
                for k, v in warning.items():
                    if k != 'message':
                        print(f"     - {k}: {v}")
    
    print("="*80)

def validate_attendance_report(date=None, detailed=True):
    """
    Validate attendance report for a specific date
    
    Args:
        date (str): Date in 'YYYY-MM-DD' format, or None for today
        detailed (bool): Whether to print detailed information
        
    Returns:
        dict: Validation results
    """
    # Parse date if provided
    if date:
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format: {date}. Using current date instead.")
            date = None
    
    # Get attendance data for the specified date
    try:
        report_data = get_attendance_data(date)
        print(f"Validating attendance report for date: {report_data.get('date', date or 'unknown')}")
    except Exception as e:
        logger.error(f"Error getting attendance data: {e}")
        print(f"❌ Error: Could not get attendance data for date {date}: {e}")
        return {'is_valid': False, 'errors': [{'message': f"Failed to get report data: {e}"}]}
    
    # Validate the report
    validation_results = validate_report(report_data)
    
    # Print results
    print_validation_results(validation_results, detailed=detailed)
    
    return validation_results

def main():
    """Main function when script is run directly"""
    parser = argparse.ArgumentParser(description='Validate attendance reports for data integrity.')
    parser.add_argument('-d', '--date', help='Date to validate in YYYY-MM-DD format (default: today)')
    parser.add_argument('--simple', action='store_true', help='Print simplified results')
    
    args = parser.parse_args()
    validate_attendance_report(args.date, detailed=not args.simple)

if __name__ == "__main__":
    main()