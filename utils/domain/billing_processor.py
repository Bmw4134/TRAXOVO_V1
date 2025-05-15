"""
Billing Processor

This module processes equipment billing files, extracting asset rates, charges, 
and calculating monthly billing allocations.
"""
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def process_billing(processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process billing data from the file processor result
    
    Args:
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Processed billing data
    """
    result = {
        'success': True,
        'message': 'Billing data processed successfully',
        'assets': [],
        'rates': {},
        'charges': {},
        'period': processor_result.get('extracted_data', {}).get('period', ''),
        'year': processor_result.get('extracted_data', {}).get('year', ''),
        'total_billed': processor_result.get('extracted_data', {}).get('total_billed', 0),
        'districts': processor_result.get('extracted_data', {}).get('districts', []),
        'billing_summary': {}
    }
    
    try:
        # Extract assets
        result['assets'] = processor_result.get('extracted_data', {}).get('assets', [])
        
        # Extract rates and charges
        result['rates'] = processor_result.get('extracted_data', {}).get('rates', {})
        result['charges'] = processor_result.get('extracted_data', {}).get('charges', {})
        
        # Calculate billing summary
        sheets_data = processor_result.get('sheets', {})
        for sheet_name, sheet_data in sheets_data.items():
            # Look for columns that indicate charge or amount
            charge_columns = []
            for col, col_info in sheet_data.get('column_types', {}).items():
                if ('charge' in col.lower() or 'amount' in col.lower() or 'bill' in col.lower()) and col_info.get('is_numeric', False):
                    charge_columns.append(col)
            
            # Calculate totals for each charge type
            for col in charge_columns:
                if col in sheet_data.get('column_summaries', {}):
                    summary = sheet_data['column_summaries'][col]
                    result['billing_summary'][col] = {
                        'sum': summary.get('sum', 0),
                        'mean': summary.get('mean', 0),
                        'median': summary.get('median', 0),
                        'min': summary.get('min', 0),
                        'max': summary.get('max', 0)
                    }
        
        # Calculate district allocations
        district_allocations = {}
        for district in result['districts']:
            district_allocations[district] = {
                'count': 0,
                'total': 0
            }
        
        for sheet_name, sheet_data in sheets_data.items():
            # Look for district and amount columns
            district_col = None
            amount_cols = []
            
            for col, col_info in sheet_data.get('column_types', {}).items():
                if 'district' in col.lower():
                    district_col = col
                if ('amount' in col.lower() or 'total' in col.lower()) and col_info.get('is_numeric', False):
                    amount_cols.append(col)
            
            # If we have both district and amount columns, calculate district allocations
            if district_col and amount_cols:
                # Get district frequencies
                district_freqs = sheet_data.get('value_frequencies', {}).get(district_col, {})
                
                # Update district allocations
                for district, count in district_freqs.items():
                    if district and district != 'nan' and district != 'total' and district != 'Total':
                        if district in district_allocations:
                            district_allocations[district]['count'] += int(count)
        
        result['district_allocations'] = district_allocations
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing billing data: {e}")
        return {
            'success': False,
            'message': f'Error processing billing data: {str(e)}'
        }