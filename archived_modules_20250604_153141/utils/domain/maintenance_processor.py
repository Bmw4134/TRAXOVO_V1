"""
Maintenance Processor

This module processes maintenance and work order files, extracting repair costs, 
service types, and calculating maintenance metrics.
"""
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def process_maintenance(processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process maintenance data from the file processor result
    
    Args:
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Processed maintenance data
    """
    result = {
        'success': True,
        'message': 'Maintenance data processed successfully',
        'work_orders': [],
        'assets': [],
        'service_types': [],
        'costs': {},
        'date_range': processor_result.get('extracted_data', {}).get('date_range', {}),
        'year': processor_result.get('extracted_data', {}).get('year', ''),
        'districts': processor_result.get('extracted_data', {}).get('districts', []),
        'wo_summary': {},
        'cost_summary': {},
        'asset_maintenance': {}
    }
    
    try:
        # Extract work orders, assets, and service types
        result['work_orders'] = processor_result.get('extracted_data', {}).get('work_orders', [])
        result['assets'] = processor_result.get('extracted_data', {}).get('assets', [])
        result['service_types'] = processor_result.get('extracted_data', {}).get('service_types', [])
        
        # Extract costs
        result['costs'] = processor_result.get('extracted_data', {}).get('costs', {})
        
        # Calculate work order summary
        wo_summary = {
            'total_count': len(result['work_orders']),
            'by_service_type': {},
            'by_district': {}
        }
        
        # Calculate cost summary
        cost_summary = {
            'total_cost': 0,
            'by_service_type': {},
            'by_district': {}
        }
        
        # Initialize service type counts
        for service_type in result['service_types']:
            wo_summary['by_service_type'][service_type] = {
                'count': 0,
                'percentage': 0
            }
            cost_summary['by_service_type'][service_type] = {
                'cost': 0,
                'percentage': 0
            }
        
        # Initialize district counts
        for district in result['districts']:
            wo_summary['by_district'][district] = {
                'count': 0,
                'percentage': 0
            }
            cost_summary['by_district'][district] = {
                'cost': 0,
                'percentage': 0
            }
        
        # Initialize asset maintenance data
        asset_maintenance = {}
        for asset in result['assets']:
            asset_maintenance[asset] = {
                'wo_count': 0,
                'total_cost': 0,
                'service_types': {}
            }
        
        # Analyze cost data
        sheets_data = processor_result.get('sheets', {})
        for sheet_name, sheet_data in sheets_data.items():
            # Look for cost columns
            cost_columns = []
            for col, col_info in sheet_data.get('column_types', {}).items():
                if col_info.get('purpose') == 'cost':
                    cost_columns.append(col)
            
            # Calculate totals for each cost column
            for col in cost_columns:
                if col in sheet_data.get('column_summaries', {}):
                    summary = sheet_data['column_summaries'][col]
                    cost_summary['total_cost'] += summary.get('sum', 0)
        
        # Update result with calculated metrics
        result['wo_summary'] = wo_summary
        result['cost_summary'] = cost_summary
        result['asset_maintenance'] = asset_maintenance
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing maintenance data: {e}")
        return {
            'success': False,
            'message': f'Error processing maintenance data: {str(e)}'
        }