import pandas as pd
import json

# Extract real driver count from your authentic fleet data
def get_authentic_driver_count():
    try:
        # Load your FLEET sheet to get real driver data
        fleet_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                sheet_name='FLEET')
        
        # Count unique drivers from Employee column
        driver_columns = ['Employee', 'Emp ID', 'EMP ID2']
        
        unique_drivers = set()
        
        for col in driver_columns:
            if col in fleet_df.columns:
                drivers = fleet_df[col].dropna()
                for driver in drivers:
                    if driver and str(driver).strip() and str(driver).strip() != '0':
                        unique_drivers.add(str(driver).strip())
        
        print(f"Found {len(unique_drivers)} unique drivers in fleet data")
        print("Sample drivers:", list(unique_drivers)[:5])
        
        return len(unique_drivers)
        
    except Exception as e:
        print(f"Error extracting driver count: {e}")
        return 0

if __name__ == "__main__":
    driver_count = get_authentic_driver_count()
    print(f"Authentic driver count: {driver_count}")