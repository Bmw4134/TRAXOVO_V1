"""
TRAXOVO Data Consolidation and Deduplication Engine
Consolidates all authentic data sources with deduplication logic
"""
import pandas as pd
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class TRAXOVODataConsolidator:
    """Master data consolidation engine for authentic TRAXOVO data"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url) if self.database_url else None
        self.consolidated_data = {}
        
    def consolidate_all_data(self) -> Dict:
        """Master consolidation of all authentic data sources"""
        logger.info("Starting comprehensive data consolidation")
        
        # 1. Consolidate Equipment/Asset Data
        self.consolidated_data['assets'] = self._consolidate_asset_data()
        
        # 2. Consolidate Attendance Data
        self.consolidated_data['attendance'] = self._consolidate_attendance_data()
        
        # 3. Consolidate Payroll Data
        self.consolidated_data['payroll'] = self._consolidate_payroll_data()
        
        # 4. Consolidate Usage/Utilization Data
        self.consolidated_data['usage'] = self._consolidate_usage_data()
        
        # 5. Consolidate Billing/Cost Data
        self.consolidated_data['billing'] = self._consolidate_billing_data()
        
        # 6. Consolidate Geofencing Data
        self.consolidated_data['geofencing'] = self._consolidate_geofencing_data()
        
        return self.consolidated_data
    
    def _consolidate_asset_data(self) -> pd.DataFrame:
        """Consolidate and deduplicate asset/equipment data"""
        asset_files = [
            'attached_assets/EQ LIST ALL DETAILS SELECTED 052925.xlsx',
            'attached_assets/Equipment Detail History Report_01.01.2020-05.31.2025.xlsx',
            'attached_assets/CURRENT EQ SERVICE-EXPENSE CODE LIST 052925.xlsx'
        ]
        
        consolidated_assets = []
        
        for file_path in asset_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    
                    # Standardize column names
                    df.columns = df.columns.str.lower().str.replace(' ', '_')
                    
                    # Extract key fields with fallback mapping
                    asset_data = {
                        'asset_id': df.get('equipment_id', df.get('equipment_no', df.get('asset_id'))),
                        'description': df.get('description', df.get('equipment_description')),
                        'category': df.get('category', df.get('equipment_category')),
                        'make_model': df.get('make/model', df.get('make_model', df.get('manufacturer'))),
                        'year': df.get('year', df.get('model_year')),
                        'status': df.get('status', 'Active'),
                        'location': df.get('location', df.get('current_location')),
                        'cost_center': df.get('cost_center', df.get('department')),
                        'source_file': os.path.basename(file_path)
                    }
                    
                    # Convert to DataFrame and clean
                    asset_df = pd.DataFrame(asset_data)
                    asset_df = asset_df.dropna(subset=['asset_id'])
                    asset_df['asset_id'] = asset_df['asset_id'].astype(str).str.strip()
                    
                    consolidated_assets.append(asset_df)
                    
                except Exception as e:
                    logger.error(f"Error processing asset file {file_path}: {e}")
        
        if consolidated_assets:
            # Combine all asset data
            combined_df = pd.concat(consolidated_assets, ignore_index=True)
            
            # Deduplication logic: prioritize most recent/complete records
            combined_df['completeness_score'] = combined_df.count(axis=1)
            deduplicated = combined_df.loc[combined_df.groupby('asset_id')['completeness_score'].idxmax()]
            
            logger.info(f"Consolidated {len(combined_df)} asset records into {len(deduplicated)} unique assets")
            return deduplicated.drop('completeness_score', axis=1)
        
        return pd.DataFrame()
    
    def _consolidate_attendance_data(self) -> pd.DataFrame:
        """Consolidate attendance from CSV files and usage journals"""
        attendance_files = []
        
        # Find attendance CSV files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'attendance' in file.lower() and file.endswith('.csv'):
                    attendance_files.append(os.path.join(root, file))
        
        # Also check usage journals for operator data
        usage_files = [f for f in os.listdir('attached_assets') if 'USAGE JOURNAL' in f.upper()]
        
        consolidated_attendance = []
        
        # Process CSV attendance files
        for file_path in attendance_files:
            try:
                df = pd.read_csv(file_path)
                df.columns = df.columns.str.lower().str.replace(' ', '_')
                
                attendance_data = {
                    'employee_id': df.get('employee_id', df.get('operator_id', df.get('driver_id'))),
                    'employee_name': df.get('employee_name', df.get('operator', df.get('driver_name'))),
                    'date': pd.to_datetime(df.get('date', df.get('work_date')), errors='coerce'),
                    'clock_in': df.get('clock_in', df.get('start_time')),
                    'clock_out': df.get('clock_out', df.get('end_time')),
                    'hours_worked': df.get('hours_worked', df.get('total_hours')),
                    'location': df.get('location', df.get('job_site')),
                    'source_file': os.path.basename(file_path)
                }
                
                att_df = pd.DataFrame(attendance_data)
                consolidated_attendance.append(att_df)
                
            except Exception as e:
                logger.error(f"Error processing attendance file {file_path}: {e}")
        
        # Process usage journals for operator tracking
        for file in usage_files:
            file_path = f'attached_assets/{file}'
            if file.endswith('.xlsx'):
                try:
                    df = pd.read_excel(file_path)
                    
                    # Extract operator attendance from usage data
                    if 'operator' in df.columns or 'Operator' in df.columns:
                        operator_col = 'operator' if 'operator' in df.columns else 'Operator'
                        
                        usage_attendance = {
                            'employee_name': df[operator_col],
                            'date': pd.to_datetime(df.get('Date', df.get('date')), errors='coerce'),
                            'hours_worked': df.get('Hours', df.get('hours', 0)),
                            'location': df.get('Location', df.get('location')),
                            'equipment_used': df.get('Equipment', df.get('equipment')),
                            'source_file': f"usage_{os.path.basename(file_path)}"
                        }
                        
                        usage_df = pd.DataFrame(usage_attendance)
                        consolidated_attendance.append(usage_df)
                        
                except Exception as e:
                    logger.error(f"Error processing usage file {file_path}: {e}")
        
        if consolidated_attendance:
            combined_df = pd.concat(consolidated_attendance, ignore_index=True)
            
            # Deduplication: Remove duplicate employee-date combinations
            if 'employee_id' in combined_df.columns and 'date' in combined_df.columns:
                deduplicated = combined_df.drop_duplicates(subset=['employee_id', 'date'], keep='last')
            elif 'employee_name' in combined_df.columns and 'date' in combined_df.columns:
                deduplicated = combined_df.drop_duplicates(subset=['employee_name', 'date'], keep='last')
            else:
                deduplicated = combined_df
            
            logger.info(f"Consolidated {len(combined_df)} attendance records into {len(deduplicated)} unique entries")
            return deduplicated
        
        return pd.DataFrame()
    
    def _consolidate_payroll_data(self) -> pd.DataFrame:
        """Consolidate payroll integration data"""
        payroll_files = []
        
        # Find payroll-related files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if any(keyword in file.lower() for keyword in ['payroll', 'timecard', 'hours', 'pay']):
                    if file.endswith(('.xlsx', '.csv')):
                        payroll_files.append(os.path.join(root, file))
        
        consolidated_payroll = []
        
        for file_path in payroll_files:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                df.columns = df.columns.str.lower().str.replace(' ', '_')
                
                payroll_data = {
                    'employee_id': df.get('employee_id', df.get('emp_id')),
                    'employee_name': df.get('employee_name', df.get('name')),
                    'pay_period': df.get('pay_period', df.get('period')),
                    'regular_hours': df.get('regular_hours', df.get('reg_hours')),
                    'overtime_hours': df.get('overtime_hours', df.get('ot_hours')),
                    'total_hours': df.get('total_hours', df.get('hours')),
                    'hourly_rate': df.get('hourly_rate', df.get('rate')),
                    'gross_pay': df.get('gross_pay', df.get('pay')),
                    'source_file': os.path.basename(file_path)
                }
                
                payroll_df = pd.DataFrame(payroll_data)
                consolidated_payroll.append(payroll_df)
                
            except Exception as e:
                logger.error(f"Error processing payroll file {file_path}: {e}")
        
        if consolidated_payroll:
            combined_df = pd.concat(consolidated_payroll, ignore_index=True)
            
            # Deduplication logic
            if 'employee_id' in combined_df.columns and 'pay_period' in combined_df.columns:
                deduplicated = combined_df.drop_duplicates(subset=['employee_id', 'pay_period'], keep='last')
            else:
                deduplicated = combined_df.drop_duplicates()
            
            logger.info(f"Consolidated {len(combined_df)} payroll records into {len(deduplicated)} unique entries")
            return deduplicated
        
        return pd.DataFrame()
    
    def _consolidate_usage_data(self) -> pd.DataFrame:
        """Consolidate equipment usage and utilization data"""
        usage_files = [
            'attached_assets/EQUIPMENT USAGE DETAIL 010125-053125.xlsx',
            'attached_assets/FleetUtilization (2).xlsx',
            'attached_assets/FleetUtilization (3).xlsx'
        ]
        
        # Add usage journal files
        usage_files.extend([
            f'attached_assets/{f}' for f in os.listdir('attached_assets') 
            if 'USAGE JOURNAL' in f.upper() and f.endswith('.xlsx')
        ])
        
        consolidated_usage = []
        
        for file_path in usage_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    df.columns = df.columns.str.lower().str.replace(' ', '_')
                    
                    usage_data = {
                        'asset_id': df.get('equipment_id', df.get('equipment', df.get('asset_id'))),
                        'date': pd.to_datetime(df.get('date', df.get('work_date')), errors='coerce'),
                        'hours_used': pd.to_numeric(df.get('hours', df.get('usage_hours', df.get('total_hours'))), errors='coerce'),
                        'operator': df.get('operator', df.get('driver')),
                        'project': df.get('project', df.get('job', df.get('job_number'))),
                        'location': df.get('location', df.get('job_site')),
                        'fuel_used': pd.to_numeric(df.get('fuel', df.get('fuel_gallons')), errors='coerce'),
                        'source_file': os.path.basename(file_path)
                    }
                    
                    usage_df = pd.DataFrame(usage_data)
                    usage_df = usage_df.dropna(subset=['asset_id'])
                    consolidated_usage.append(usage_df)
                    
                except Exception as e:
                    logger.error(f"Error processing usage file {file_path}: {e}")
        
        if consolidated_usage:
            combined_df = pd.concat(consolidated_usage, ignore_index=True)
            
            # Deduplication: asset_id + date combinations
            deduplicated = combined_df.drop_duplicates(subset=['asset_id', 'date'], keep='last')
            
            logger.info(f"Consolidated {len(combined_df)} usage records into {len(deduplicated)} unique entries")
            return deduplicated
        
        return pd.DataFrame()
    
    def _consolidate_billing_data(self) -> pd.DataFrame:
        """Consolidate billing and cost analysis data"""
        billing_files = [
            'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
            'attached_assets/RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm',
            'attached_assets/USAGE VS. COST ANALYSIS 010125-053125.xlsx'
        ]
        
        consolidated_billing = []
        
        for file_path in billing_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    df.columns = df.columns.str.lower().str.replace(' ', '_')
                    
                    billing_data = {
                        'asset_id': df.get('equipment_id', df.get('equipment_no', df.get('asset_id'))),
                        'billing_period': df.get('period', df.get('month', df.get('billing_month'))),
                        'revenue': pd.to_numeric(df.get('revenue', df.get('billing_amount', df.get('income'))), errors='coerce'),
                        'costs': pd.to_numeric(df.get('cost', df.get('total_cost', df.get('expense'))), errors='coerce'),
                        'hours_billed': pd.to_numeric(df.get('hours', df.get('billable_hours')), errors='coerce'),
                        'rate_per_hour': pd.to_numeric(df.get('rate', df.get('hourly_rate')), errors='coerce'),
                        'source_file': os.path.basename(file_path)
                    }
                    
                    billing_df = pd.DataFrame(billing_data)
                    billing_df = billing_df.dropna(subset=['asset_id'])
                    consolidated_billing.append(billing_df)
                    
                except Exception as e:
                    logger.error(f"Error processing billing file {file_path}: {e}")
        
        if consolidated_billing:
            combined_df = pd.concat(consolidated_billing, ignore_index=True)
            
            # Deduplication: asset_id + billing_period
            deduplicated = combined_df.drop_duplicates(subset=['asset_id', 'billing_period'], keep='last')
            
            logger.info(f"Consolidated {len(combined_df)} billing records into {len(deduplicated)} unique entries")
            return deduplicated
        
        return pd.DataFrame()
    
    def _consolidate_geofencing_data(self) -> pd.DataFrame:
        """Consolidate geofencing and GPS data"""
        # Look for GPS/coordinate data in various files
        geo_data = []
        
        # Check for GPS coordinates in image metadata or coordinate files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if any(keyword in file.lower() for keyword in ['gps', 'coordinates', 'location', 'geofence']):
                    if file.endswith(('.csv', '.xlsx', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            if file.endswith('.csv'):
                                df = pd.read_csv(file_path)
                            elif file.endswith('.xlsx'):
                                df = pd.read_excel(file_path)
                            
                            # Look for coordinate columns
                            lat_cols = [col for col in df.columns if 'lat' in col.lower()]
                            lon_cols = [col for col in df.columns if 'lon' in col.lower() or 'lng' in col.lower()]
                            
                            if lat_cols and lon_cols:
                                geo_data.append({
                                    'latitude': df[lat_cols[0]],
                                    'longitude': df[lon_cols[0]],
                                    'location_name': df.get('name', df.get('location')),
                                    'source_file': os.path.basename(file_path)
                                })
                                
                        except Exception as e:
                            logger.error(f"Error processing geo file {file_path}: {e}")
        
        if geo_data:
            combined_df = pd.concat([pd.DataFrame(data) for data in geo_data], ignore_index=True)
            deduplicated = combined_df.drop_duplicates(subset=['latitude', 'longitude'], keep='last')
            
            logger.info(f"Consolidated {len(combined_df)} geofencing records into {len(deduplicated)} unique locations")
            return deduplicated
        
        return pd.DataFrame()
    
    def export_consolidated_data(self, output_dir: str = 'consolidated_data'):
        """Export all consolidated data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for data_type, df in self.consolidated_data.items():
            if not df.empty:
                output_path = f"{output_dir}/{data_type}_consolidated.xlsx"
                df.to_excel(output_path, index=False)
                logger.info(f"Exported {len(df)} {data_type} records to {output_path}")
        
        # Generate summary report
        summary = {
            'consolidation_date': datetime.now().isoformat(),
            'data_summary': {
                data_type: len(df) for data_type, df in self.consolidated_data.items()
            }
        }
        
        import json
        with open(f"{output_dir}/consolidation_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def run_data_consolidation():
    """Execute the complete data consolidation process"""
    consolidator = TRAXOVODataConsolidator()
    consolidated = consolidator.consolidate_all_data()
    summary = consolidator.export_consolidated_data()
    
    print("Data Consolidation Complete!")
    print(f"Summary: {summary['data_summary']}")
    
    return consolidated, summary

if __name__ == "__main__":
    run_data_consolidation()