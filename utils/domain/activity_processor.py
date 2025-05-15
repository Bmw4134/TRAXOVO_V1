"""
Activity Processor

This module processes equipment activity/usage files, extracting usage hours, 
employee-asset associations, and calculating efficiency metrics.
"""
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def process_activity(processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process activity data from the file processor result
    
    Args:
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Processed activity data
    """
    result = {
        'success': True,
        'message': 'Activity data processed successfully',
        'assets': [],
        'employees': [],
        'jobs': [],
        'period': processor_result.get('extracted_data', {}).get('period', ''),
        'year': processor_result.get('extracted_data', {}).get('year', ''),
        'hour_totals': processor_result.get('extracted_data', {}).get('hour_totals', {}),
        'efficiency_metrics': processor_result.get('extracted_data', {}).get('efficiency_metrics', {}),
        'asset_utilization': {},
        'job_allocations': {},
        'employee_allocations': {}
    }
    
    try:
        # Extract assets, employees, and jobs
        result['assets'] = processor_result.get('extracted_data', {}).get('assets', [])
        result['employees'] = processor_result.get('extracted_data', {}).get('employees', [])
        result['jobs'] = processor_result.get('extracted_data', {}).get('jobs', [])
        
        # Calculate asset utilization
        asset_utilization = {}
        for asset in result['assets']:
            asset_utilization[asset] = {
                'total_hours': 0,
                'active_days': 0,
                'efficiency': 0
            }
        
        # Calculate job allocations
        job_allocations = {}
        for job in result['jobs']:
            job_allocations[job] = {
                'total_hours': 0,
                'asset_count': 0,
                'employee_count': 0
            }
        
        # Calculate employee allocations
        employee_allocations = {}
        for employee in result['employees']:
            employee_allocations[employee] = {
                'total_hours': 0,
                'asset_count': 0,
                'job_count': 0
            }
        
        # Process sheets for detailed metrics
        sheets_data = processor_result.get('sheets', {})
        for sheet_name, sheet_data in sheets_data.items():
            # Look for asset, employee, job, and hour columns
            asset_col = None
            employee_col = None
            job_col = None
            hour_cols = []
            
            for col, col_info in sheet_data.get('column_types', {}).items():
                if col_info.get('purpose') == 'asset':
                    asset_col = col
                elif col_info.get('purpose') == 'employee':
                    employee_col = col
                elif col_info.get('purpose') == 'job':
                    job_col = col
                elif col_info.get('purpose') == 'time':
                    hour_cols.append(col)
            
            # Process column summaries
            for col, summary in sheet_data.get('column_summaries', {}).items():
                if col in hour_cols and 'sum' in summary:
                    # We found an hour column with a sum
                    # Update overall hour totals
                    result['hour_totals'][col] = summary.get('sum', 0)
            
            # Process efficiency metrics
            for col, col_info in sheet_data.get('column_types', {}).items():
                if 'effic' in col.lower() or 'util' in col.lower():
                    if col in sheet_data.get('column_summaries', {}):
                        summary = sheet_data['column_summaries'][col]
                        result['efficiency_metrics'][col] = {
                            'mean': summary.get('mean', 0),
                            'median': summary.get('median', 0),
                            'min': summary.get('min', 0),
                            'max': summary.get('max', 0)
                        }
        
        # Update result with calculated metrics
        result['asset_utilization'] = asset_utilization
        result['job_allocations'] = job_allocations
        result['employee_allocations'] = employee_allocations
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing activity data: {e}")
        return {
            'success': False,
            'message': f'Error processing activity data: {str(e)}'
        }