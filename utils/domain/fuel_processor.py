"""
Fuel Processor

This module processes fuel transaction files, extracting card usage, transaction details,
and calculating fuel consumption metrics.
"""
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def process_fuel(processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process fuel data from the file processor result
    
    Args:
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Processed fuel data
    """
    result = {
        'success': True,
        'message': 'Fuel data processed successfully',
        'assets': [],
        'cards': [],
        'merchants': [],
        'period': '',
        'year': '',
        'total_gallons': 0,
        'total_amount': 0,
        'fuel_types': {},
        'card_usage': {},
        'merchant_usage': {},
        'asset_usage': {}
    }
    
    try:
        # Try to determine period from filename
        filename = processor_result.get('metadata', {}).get('file_info', {}).get('filename', '')
        
        # Extract month/period
        month_match = False
        for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                     'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 
                     'september', 'october', 'november', 'december']:
            if month in filename.lower():
                month_match = True
                if month in ['jan', 'january']:
                    result['period'] = 'January'
                elif month in ['feb', 'february']:
                    result['period'] = 'February'
                elif month in ['mar', 'march']:
                    result['period'] = 'March'
                elif month in ['apr', 'april']:
                    result['period'] = 'April'
                elif month == 'may':
                    result['period'] = 'May'
                elif month in ['jun', 'june']:
                    result['period'] = 'June'
                elif month in ['jul', 'july']:
                    result['period'] = 'July'
                elif month in ['aug', 'august']:
                    result['period'] = 'August'
                elif month in ['sep', 'september']:
                    result['period'] = 'September'
                elif month in ['oct', 'october']:
                    result['period'] = 'October'
                elif month in ['nov', 'november']:
                    result['period'] = 'November'
                elif month in ['dec', 'december']:
                    result['period'] = 'December'
                break
        
        # Extract year if present
        year_match = False
        for year in range(2020, 2031):
            if str(year) in filename:
                result['year'] = str(year)
                year_match = True
                break
        
        # Process sheets to extract fuel data
        sheets_data = processor_result.get('sheets', {})
        for sheet_name, sheet_data in sheets_data.items():
            # Look for card, asset, merchant, and amount columns
            card_col = None
            asset_col = None
            merchant_col = None
            amount_cols = []
            gallons_cols = []
            fuel_type_col = None
            
            # Identify columns
            for col, col_info in sheet_data.get('column_types', {}).items():
                col_lower = col.lower()
                
                # Card column
                if 'card' in col_lower or 'wex' in col_lower or 'account' in col_lower:
                    card_col = col
                
                # Asset column
                elif col_info.get('purpose') == 'asset' or 'unit' in col_lower or 'vehicle' in col_lower:
                    asset_col = col
                
                # Merchant column
                elif 'merchant' in col_lower or 'vendor' in col_lower or 'store' in col_lower:
                    merchant_col = col
                
                # Amount column
                elif ('amount' in col_lower or 'cost' in col_lower or 'price' in col_lower) and col_info.get('is_numeric', False):
                    amount_cols.append(col)
                
                # Gallons column
                elif ('gallon' in col_lower or 'volume' in col_lower or 'quantity' in col_lower) and col_info.get('is_numeric', False):
                    gallons_cols.append(col)
                
                # Fuel type column
                elif 'fuel' in col_lower and 'type' in col_lower:
                    fuel_type_col = col
            
            # Extract cards
            if card_col and card_col in sheet_data.get('value_frequencies', {}):
                cards = sheet_data['value_frequencies'][card_col]
                for card, count in cards.items():
                    if card and card.lower() != 'nan' and card.lower() != 'total' and card.lower() != 'card':
                        if card not in result['cards']:
                            result['cards'].append(card)
                        
                        # Initialize card usage
                        if card not in result['card_usage']:
                            result['card_usage'][card] = {
                                'total_amount': 0,
                                'total_gallons': 0,
                                'transaction_count': int(count),
                                'assets': []
                            }
                        else:
                            result['card_usage'][card]['transaction_count'] += int(count)
            
            # Extract assets
            if asset_col and asset_col in sheet_data.get('value_frequencies', {}):
                assets = sheet_data['value_frequencies'][asset_col]
                for asset, count in assets.items():
                    if asset and asset.lower() != 'nan' and asset.lower() != 'total' and asset.lower() != 'asset':
                        if asset not in result['assets']:
                            result['assets'].append(asset)
                        
                        # Initialize asset usage
                        if asset not in result['asset_usage']:
                            result['asset_usage'][asset] = {
                                'total_amount': 0,
                                'total_gallons': 0,
                                'transaction_count': int(count)
                            }
                        else:
                            result['asset_usage'][asset]['transaction_count'] += int(count)
            
            # Extract merchants
            if merchant_col and merchant_col in sheet_data.get('value_frequencies', {}):
                merchants = sheet_data['value_frequencies'][merchant_col]
                for merchant, count in merchants.items():
                    if merchant and merchant.lower() != 'nan' and merchant.lower() != 'total' and merchant.lower() != 'merchant':
                        if merchant not in result['merchants']:
                            result['merchants'].append(merchant)
                        
                        # Initialize merchant usage
                        if merchant not in result['merchant_usage']:
                            result['merchant_usage'][merchant] = {
                                'total_amount': 0,
                                'total_gallons': 0,
                                'transaction_count': int(count)
                            }
                        else:
                            result['merchant_usage'][merchant]['transaction_count'] += int(count)
            
            # Extract fuel types
            if fuel_type_col and fuel_type_col in sheet_data.get('value_frequencies', {}):
                fuel_types = sheet_data['value_frequencies'][fuel_type_col]
                for fuel_type, count in fuel_types.items():
                    if fuel_type and fuel_type.lower() != 'nan' and fuel_type.lower() != 'total':
                        if fuel_type not in result['fuel_types']:
                            result['fuel_types'][fuel_type] = {
                                'total_amount': 0,
                                'total_gallons': 0,
                                'transaction_count': int(count)
                            }
                        else:
                            result['fuel_types'][fuel_type]['transaction_count'] += int(count)
            
            # Extract amount totals
            for col in amount_cols:
                if col in sheet_data.get('column_summaries', {}):
                    summary = sheet_data['column_summaries'][col]
                    if 'sum' in summary:
                        result['total_amount'] += summary['sum']
            
            # Extract gallons totals
            for col in gallons_cols:
                if col in sheet_data.get('column_summaries', {}):
                    summary = sheet_data['column_summaries'][col]
                    if 'sum' in summary:
                        result['total_gallons'] += summary['sum']
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing fuel data: {e}")
        return {
            'success': False,
            'message': f'Error processing fuel data: {str(e)}'
        }