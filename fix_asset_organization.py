"""
Fix Asset Organization Assignment Based on Asset ID Suffix System
- "U" suffix = Unified Specialties
- "S" suffix = Select Maintenance  
- No suffix = Ragle Inc
"""

import pandas as pd
import json
from datetime import datetime

def analyze_excel_asset_ids():
    """Analyze the Excel file to get correct asset organization counts"""
    
    try:
        # Read the Excel file
        df = pd.read_excel('attached_assets/AssetsListExport (2)_1749421195226.xlsx')
        
        print(f"Total rows in Excel: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Find asset ID column
        asset_id_col = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['asset', 'id', 'number']):
                asset_id_col = col
                break
        
        if not asset_id_col:
            print("No asset ID column found")
            return None
            
        print(f"Using asset ID column: {asset_id_col}")
        
        # Analyze asset ID patterns
        unified_count = 0
        select_count = 0
        ragle_count = 0
        
        for idx, row in df.iterrows():
            asset_id = str(row[asset_id_col]).strip()
            
            if asset_id.endswith('U'):
                unified_count += 1
            elif asset_id.endswith('S'):
                select_count += 1
            else:
                ragle_count += 1
        
        result = {
            'total_assets': len(df),
            'ragle_inc': ragle_count,
            'select_maintenance': select_count,
            'unified_specialties': unified_count,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        print("\nAsset Distribution Analysis:")
        print(f"Ragle Inc (no suffix): {ragle_count}")
        print(f"Select Maintenance (S suffix): {select_count}")
        print(f"Unified Specialties (U suffix): {unified_count}")
        print(f"Total: {ragle_count + select_count + unified_count}")
        
        # Save results
        with open('asset_organization_fix.json', 'w') as f:
            json.dump(result, f, indent=2)
            
        return result
        
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
        return None

if __name__ == "__main__":
    result = analyze_excel_asset_ids()
    if result:
        print("\nCorrect asset counts determined from authentic Excel data")
    else:
        print("Failed to analyze Excel file")