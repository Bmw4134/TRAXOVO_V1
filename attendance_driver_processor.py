#!/usr/bin/env python3
"""
Attendance Matrix & Driver Reporting Processor
Processes authentic fleet data for attendance tracking and driver performance
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import re

class AttendanceDriverProcessor:
    def __init__(self):
        self.data_files = {
            'activity': 'attached_assets/ActivityDetail (4)_1749454854416.csv',
            'usage': 'attached_assets/DailyUsage_1749454857635.csv',
            'driving_history': 'attached_assets/DrivingHistory (2)_1749454860929.csv'
        }
        self.processed_data = {}
    
    def process_attendance_matrix(self):
        """Process attendance patterns from activity data"""
        attendance_data = {
            'daily_attendance': [],
            'driver_utilization': {},
            'equipment_hours': {},
            'attendance_summary': {}
        }
        
        try:
            # Process Activity Detail with robust parsing
            activity_df = self.safe_csv_read(self.data_files['activity'])
            if not activity_df.empty:
                attendance_data['total_activity_records'] = len(activity_df)
                
                # Extract attendance patterns
                for index, row in activity_df.head(100).iterrows():
                    record = {}
                    for col, value in row.items():
                        if pd.notna(value):
                            record[str(col).strip()] = str(value).strip()
                    
                    if record:
                        attendance_data['daily_attendance'].append({
                            'record_id': index + 1,
                            'data': record
                        })
                
                # Calculate utilization metrics
                if 'Equipment' in activity_df.columns or 'Asset' in activity_df.columns:
                    equipment_col = 'Equipment' if 'Equipment' in activity_df.columns else 'Asset'
                    equipment_counts = activity_df[equipment_col].value_counts()
                    attendance_data['equipment_hours'] = equipment_counts.head(10).to_dict()
                
        except Exception as e:
            attendance_data['error'] = f"Activity processing: {str(e)}"
        
        return attendance_data
    
    def process_driver_reporting(self):
        """Process driver performance and reporting metrics"""
        driver_data = {
            'driver_performance': [],
            'daily_usage_patterns': [],
            'driving_metrics': {},
            'performance_summary': {}
        }
        
        try:
            # Process Daily Usage data
            usage_df = self.safe_csv_read(self.data_files['usage'])
            if not usage_df.empty:
                driver_data['total_usage_records'] = len(usage_df)
                
                for index, row in usage_df.head(50).iterrows():
                    usage_record = {}
                    for col, value in row.items():
                        if pd.notna(value):
                            usage_record[str(col).strip()] = str(value).strip()
                    
                    if usage_record:
                        driver_data['daily_usage_patterns'].append({
                            'day_id': index + 1,
                            'metrics': usage_record
                        })
                
                # Calculate usage statistics
                numeric_columns = usage_df.select_dtypes(include=['number']).columns
                if len(numeric_columns) > 0:
                    driver_data['usage_statistics'] = {
                        'avg_daily_hours': usage_df[numeric_columns[0]].mean() if len(numeric_columns) > 0 else 0,
                        'total_entries': len(usage_df),
                        'active_days': usage_df[numeric_columns[0]].count() if len(numeric_columns) > 0 else 0
                    }
        
        except Exception as e:
            driver_data['usage_error'] = f"Usage processing: {str(e)}"
        
        try:
            # Process Driving History with enhanced parsing
            driving_df = self.safe_csv_read(self.data_files['driving_history'])
            if not driving_df.empty:
                driver_data['total_driving_records'] = len(driving_df)
                
                # Extract driver performance metrics
                for index, row in driving_df.head(25).iterrows():
                    driver_record = {}
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            driver_record[str(col).strip()] = str(value).strip()
                    
                    if driver_record:
                        driver_data['driver_performance'].append({
                            'driver_id': index + 1,
                            'performance': driver_record
                        })
        
        except Exception as e:
            driver_data['driving_error'] = f"Driving history processing: {str(e)}"
        
        return driver_data
    
    def process_equipment_billing(self):
        """Process equipment billing and cost tracking"""
        billing_data = {
            'equipment_costs': [],
            'billing_summary': {},
            'cost_analytics': {},
            'revenue_tracking': {}
        }
        
        try:
            # Look for billing-related data in activity records
            activity_df = self.safe_csv_read(self.data_files['activity'])
            if not activity_df.empty:
                # Extract cost-related fields
                cost_fields = [col for col in activity_df.columns if any(keyword in str(col).lower() 
                              for keyword in ['cost', 'rate', 'bill', 'hour', 'revenue', 'charge'])]
                
                if cost_fields:
                    billing_data['available_cost_fields'] = cost_fields
                    
                    for index, row in activity_df.head(20).iterrows():
                        cost_record = {}
                        for field in cost_fields:
                            if pd.notna(row[field]):
                                cost_record[field] = str(row[field])
                        
                        if cost_record:
                            billing_data['equipment_costs'].append({
                                'equipment_id': index + 1,
                                'billing_data': cost_record
                            })
                
                # Calculate billing summary
                numeric_cost_fields = [col for col in cost_fields if activity_df[col].dtype in ['int64', 'float64']]
                if numeric_cost_fields:
                    billing_data['billing_summary'] = {
                        'total_cost_entries': len(activity_df),
                        'cost_field_averages': {field: activity_df[field].mean() for field in numeric_cost_fields[:3]}
                    }
        
        except Exception as e:
            billing_data['billing_error'] = f"Billing processing: {str(e)}"
        
        return billing_data
    
    def safe_csv_read(self, file_path):
        """Safely read CSV files with multiple encoding attempts"""
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t', '|']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False, 
                                   on_bad_lines='skip', engine='python')
                    if not df.empty and len(df.columns) > 1:
                        return df
                except:
                    continue
        
        return pd.DataFrame()
    
    def generate_comprehensive_report(self):
        """Generate comprehensive attendance and driver reporting"""
        print("Processing Attendance Matrix & Driver Reporting...")
        
        # Process all modules
        attendance_matrix = self.process_attendance_matrix()
        driver_reporting = self.process_driver_reporting()
        equipment_billing = self.process_equipment_billing()
        
        comprehensive_report = {
            'attendance_matrix': attendance_matrix,
            'driver_reporting': driver_reporting,
            'equipment_billing': equipment_billing,
            'processing_timestamp': datetime.now().isoformat(),
            'data_sources': list(self.data_files.keys())
        }
        
        return comprehensive_report

def main():
    """Run attendance and driver reporting processor"""
    processor = AttendanceDriverProcessor()
    report = processor.generate_comprehensive_report()
    
    print("\n" + "="*60)
    print("ATTENDANCE MATRIX & DRIVER REPORTING SUMMARY")
    print("="*60)
    
    # Display Attendance Matrix
    attendance = report['attendance_matrix']
    print(f"\n📊 ATTENDANCE MATRIX:")
    print(f"   Total Activity Records: {attendance.get('total_activity_records', 0):,}")
    print(f"   Daily Attendance Entries: {len(attendance.get('daily_attendance', []))}")
    
    if attendance.get('equipment_hours'):
        print(f"   Top Equipment Usage:")
        for equipment, hours in list(attendance['equipment_hours'].items())[:5]:
            print(f"     {equipment}: {hours} entries")
    
    # Display Driver Reporting
    driver = report['driver_reporting']
    print(f"\n🚛 DRIVER REPORTING:")
    print(f"   Total Usage Records: {driver.get('total_usage_records', 0):,}")
    print(f"   Driver Performance Entries: {len(driver.get('driver_performance', []))}")
    print(f"   Daily Usage Patterns: {len(driver.get('daily_usage_patterns', []))}")
    
    if driver.get('usage_statistics'):
        stats = driver['usage_statistics']
        print(f"   Usage Statistics:")
        print(f"     Active Days: {stats.get('active_days', 0)}")
        print(f"     Total Entries: {stats.get('total_entries', 0)}")
    
    # Display Equipment Billing
    billing = report['equipment_billing']
    print(f"\n💰 EQUIPMENT BILLING:")
    print(f"   Equipment Cost Entries: {len(billing.get('equipment_costs', []))}")
    
    if billing.get('available_cost_fields'):
        print(f"   Available Cost Fields: {billing['available_cost_fields'][:5]}")
    
    if billing.get('billing_summary'):
        print(f"   Billing Summary: {billing['billing_summary'].get('total_cost_entries', 0)} entries")
    
    # Save detailed report
    with open('attendance_driver_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: attendance_driver_report.json")
    print(f"🕒 Processing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return report

if __name__ == "__main__":
    main()