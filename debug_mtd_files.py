#!/usr/bin/env python3
"""
Debug MTD Files - Quick test to see what's in the uploaded files
"""

import pandas as pd
import os

def debug_mtd_files():
    """Debug the MTD files to see what data we have"""
    
    upload_dir = "uploads"
    
    print("=== DEBUGGING MTD FILES ===")
    
    # Look for driving history files
    for filename in os.listdir(upload_dir):
        if 'driving' in filename.lower() or 'history' in filename.lower():
            print(f"\n📁 Found DrivingHistory file: {filename}")
            
            try:
                # Read with flexible parsing to handle variable columns
                df = pd.read_csv(os.path.join(upload_dir, filename), skiprows=7, low_memory=False)
                print(f"   📊 Shape: {df.shape}")
                print(f"   🔹 Columns: {list(df.columns)}")
                
                # Look for records with actual data
                non_empty_rows = []
                for idx, row in df.iterrows():
                    if row.get('EventDateTime') and str(row.get('EventDateTime')).strip() != '':
                        non_empty_rows.append(row)
                        if len(non_empty_rows) >= 3:  # Just get first few
                            break
                
                print(f"   📈 Found {len(non_empty_rows)} records with EventDateTime")
                
                for i, row in enumerate(non_empty_rows[:3]):
                    contact = row.get('Contact', 'N/A')
                    event_time = row.get('EventDateTime', 'N/A')
                    msg_type = row.get('MsgType', 'N/A')
                    print(f"      {i+1}. {contact} | {event_time} | {msg_type}")
                    
                    # Try to extract date
                    if event_time and str(event_time) != 'N/A':
                        try:
                            parsed_date = pd.to_datetime(event_time)
                            date_str = parsed_date.strftime('%Y-%m-%d')
                            print(f"         → Date: {date_str}")
                        except Exception as e:
                            print(f"         → Date parse error: {e}")
                
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
    
    print("\n=== END DEBUG ===")

if __name__ == "__main__":
    debug_mtd_files()