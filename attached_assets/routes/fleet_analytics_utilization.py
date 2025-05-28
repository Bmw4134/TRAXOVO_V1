
import pandas as pd

def parse_fleet_utilization(filepath):
    xls = pd.ExcelFile(filepath)
    data = xls.parse(xls.sheet_names[1])
    data.columns = data.iloc[1]
    data = data.drop(index=[0,1]).reset_index(drop=True)
    data = data.rename(columns={'Asset': 'asset_id'})
    return data[['asset_id', 'Make', 'Model', 'Jan-25', 'Feb-25', 'Mar-25', 'Apr-25', 'May-25']]
