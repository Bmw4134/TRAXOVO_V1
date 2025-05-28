
# Export KPI Data to Excel for Daily Metrics
import pandas as pd

def export_kpi_to_excel(driver_data, filepath):
    df = pd.DataFrame(driver_data)
    filtered = df[["driver_id", "early_ends", "gps_issues", "total_hours", "zone"]]
    filtered.to_excel(filepath, index=False)
