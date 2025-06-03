
import pandas as pd
import os
import json

# Assume files already exist in `raw/` folder
INPUT_DIR = "raw"
OUTPUT_DIR = "data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(INPUT_DIR, file))

        date_col = 'date' if 'date' in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        df_filtered = df[(df['driver_name'].notna()) | (df['EMP ID'].notna())]

        df_filtered = df_filtered.copy()
        df_filtered['status'] = df_filtered['status'].fillna("Not On Job")

        for date in df_filtered[date_col].dt.date.unique():
            df_day = df_filtered[df_filtered[date_col].dt.date == date]
            day_file = f"filtered_driving_data_{date}.json"
            with open(os.path.join(OUTPUT_DIR, day_file), 'w') as f:
                json.dump(df_day.to_dict(orient='records'), f, indent=2)

print("Driver filtering patch complete. New files in /data/.")
