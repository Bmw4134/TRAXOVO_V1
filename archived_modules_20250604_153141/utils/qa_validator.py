import pandas as pd
import os
import json
from datetime import datetime

def validate_fleet_data(data, file_type="fleet_utilization"):
    """
    TRAXOVO QA Validator - Ensures data integrity for fleet analytics
    Only validates authentic data sources with complete traceability
    """
    
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'record_count': 0,
        'asset_count': 0
    }
    
    try:
        if data is None or data.empty:
            validation_results['valid'] = False
            validation_results['errors'].append("No data found in uploaded file")
            return validation_results
        
        # Record count validation
        validation_results['record_count'] = len(data)
        
        if file_type == "fleet_utilization":
            # Validate Fleet Utilization data structure
            required_columns = ['Asset']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required columns: {missing_columns}")
            else:
                # Asset validation
                asset_data = data[data['Asset'].notna() & (data['Asset'] != '')]
                validation_results['asset_count'] = len(asset_data)
                
                if validation_results['asset_count'] == 0:
                    validation_results['valid'] = False
                    validation_results['errors'].append("No valid asset records found")
        
        elif file_type == "foundation_costs":
            # Validate Foundation cost data
            if 'equipment_no' in data.columns or 'asset_id' in data.columns:
                validation_results['asset_count'] = len(data)
            else:
                validation_results['warnings'].append("No asset ID column found in Foundation data")
        
        # Log validation results
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'file_type': file_type,
            'validation_results': validation_results
        }
        
        # Save validation log
        os.makedirs('logs', exist_ok=True)
        with open('logs/qa_validation.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    except Exception as e:
        validation_results['valid'] = False
        validation_results['errors'].append(f"Validation error: {str(e)}")
    
    return validation_results