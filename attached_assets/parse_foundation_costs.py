
import pandas as pd

def parse_foundation_wo(file_path):
    df = pd.read_excel(file_path, sheet_name=0)
    df = df.rename(columns={
        'equipment_no': 'asset_id',
        'transaction_date': 'date',
        'service_code': 'service',
        'unit_cost': 'unit_cost',
        'extended_cost': 'total_cost'
    })
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df[['asset_id', 'date', 'service', 'unit_cost', 'total_cost']].dropna()

def parse_profit_report(file_path):
    df = pd.read_excel(file_path, sheet_name=0)
    return df[['equipment_no', 'usage_hours', 'billing_dollars', 'service_labor', 'service_other']]

def parse_uvc_analysis(file_path):
    df = pd.read_excel(file_path, sheet_name=0)
    return df[['equipment_no', 'usage_hours', 'service_labor', 'service_other', 'other_overhead']]
