"""
Fringe Benefits Processor

This module processes fringe benefit files, extracting employee benefit information
and calculating fringe benefit allocations.
"""
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def process_fringe(processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process fringe benefit data from the file processor result
    
    Args:
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Processed fringe benefit data
    """
    result = {
        'success': True,
        'message': 'Fringe benefit data processed successfully',
        'employees': [],
        'benefits': [],
        'benefit_totals': {},
        'period': processor_result.get('extracted_data', {}).get('period', ''),
        'year': processor_result.get('extracted_data', {}).get('year', ''),
        'allocation_summary': {}
    }
    
    try:
        # Extract employees and benefits
        result['employees'] = processor_result.get('extracted_data', {}).get('employees', [])
        result['benefits'] = processor_result.get('extracted_data', {}).get('benefits', [])
        
        # Extract benefit totals
        benefit_totals = processor_result.get('extracted_data', {}).get('totals', {})
        result['benefit_totals'] = benefit_totals
        
        # Calculate allocation summary
        sheets_data = processor_result.get('sheets', {})
        for sheet_name, sheet_data in sheets_data.items():
            # Look for columns that indicate benefit types
            benefit_columns = []
            for col, col_info in sheet_data.get('column_types', {}).items():
                if ('benefit' in col.lower() or 'fringe' in col.lower()) and col_info.get('is_numeric', False):
                    benefit_columns.append(col)
            
            # Calculate totals for each benefit type
            for col in benefit_columns:
                if col in sheet_data.get('column_summaries', {}):
                    summary = sheet_data['column_summaries'][col]
                    result['allocation_summary'][col] = {
                        'sum': summary.get('sum', 0),
                        'mean': summary.get('mean', 0),
                        'median': summary.get('median', 0),
                        'min': summary.get('min', 0),
                        'max': summary.get('max', 0)
                    }
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing fringe benefit data: {e}")
        return {
            'success': False,
            'message': f'Error processing fringe benefit data: {str(e)}'
        }