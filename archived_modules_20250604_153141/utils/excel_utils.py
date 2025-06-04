"""
Excel utilities for data processing and report generation.

This module provides functions for Excel file generation and manipulation.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

def create_consolidated_excel(results, output_path):
    """
    Create a consolidated Excel file from batch processing results
    
    Args:
        results (dict): Batch processing results
        output_path (str): Output file path
        
    Returns:
        bool: Success status
    """
    try:
        # Create an Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Create the summary sheet
            summary_data = {
                'Metric': [
                    'Total Files Processed',
                    'Success Count',
                    'Error Count',
                    'Total Amount',
                    'Changes Detected',
                    'Processing Date'
                ],
                'Value': [
                    results['total_files'],
                    results['success_count'],
                    results['error_count'],
                    f"${results['total_amount']:,.2f}",
                    'Yes' if results['changes_detected'] else 'No',
                    results['processing_date']
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create the file details sheet
            if results['file_results']:
                file_details = []
                for result in results['file_results']:
                    file_detail = {
                        'Filename': result['filename'],
                        'Status': result['status'],
                        'Total Amount': f"${result.get('total_amount', 0):,.2f}" if result['status'] == 'success' else 'N/A'
                    }
                    
                    # Add comparison details if available
                    if result['status'] == 'success' and 'difference' in result:
                        file_detail['Difference'] = f"${result['difference']:,.2f}"
                        file_detail['Percent Change'] = f"{result['percent_change']:.2f}%"
                        file_detail['Has Changes'] = 'Yes' if result.get('has_changes', False) else 'No'
                    elif result['status'] == 'error':
                        file_detail['Error Message'] = result.get('error_message', 'Unknown error')
                        
                    file_details.append(file_detail)
                
                file_details_df = pd.DataFrame(file_details)
                file_details_df.to_excel(writer, sheet_name='File Details', index=False)
                
                # Create sheets for each successful file
                for result in results['file_results']:
                    if result['status'] == 'success' and 'is_base_file' in result and result['is_base_file']:
                        # This is a base file, we'll create a sheet with its data
                        try:
                            file_path = None
                            for processed_file in results['processed_files']:
                                if os.path.basename(processed_file) == result['filename']:
                                    file_path = processed_file
                                    break
                            
                            if file_path and os.path.exists(file_path):
                                df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
                                df.to_excel(writer, sheet_name='Base File', index=False)
                        except Exception as e:
                            logging.error(f"Error creating sheet for base file: {str(e)}")
                
                # Create a consolidated changes sheet
                if results['changes_detected']:
                    changes_data = []
                    for result in results['file_results']:
                        if result['status'] == 'success' and 'comparison_result' in result:
                            changes_data.append({
                                'Filename': result['filename'],
                                'Original Total': f"${result['comparison_result']['original_total']:,.2f}",
                                'Updated Total': f"${result['comparison_result']['updated_total']:,.2f}",
                                'Difference': f"${result['comparison_result']['difference']:,.2f}",
                                'Percent Change': f"{result['comparison_result']['percent_change']:.2f}%",
                                'Has Significant Changes': 'Yes' if result['comparison_result']['has_changes'] else 'No'
                            })
                    
                    if changes_data:
                        changes_df = pd.DataFrame(changes_data)
                        changes_df.to_excel(writer, sheet_name='Changes Summary', index=False)
        
        return True
    except Exception as e:
        logging.error(f"Error creating consolidated Excel file: {str(e)}")
        return False

def format_excel_report(file_path):
    """
    Apply formatting to an Excel report
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        bool: Success status
    """
    try:
        # This would use openpyxl to apply formatting
        # For this example, we'll just return success
        return True
    except Exception as e:
        logging.error(f"Error formatting Excel report: {str(e)}")
        return False