"""
Auto-Updating Formula Engine
Implements your copy-paste header system with auto-updating formulas
Based on your driver list creation methodology
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class AutoUpdatingFormulaEngine:
    """Your copy-paste header system with auto-updating formulas"""
    
    def __init__(self):
        self.formula_templates = {}
        self.header_mappings = {}
        self.auto_update_rules = {}
        self.processed_drivers = {}
        
    def initialize_driver_list_formulas(self):
        """Initialize the driver list formulas you created"""
        # Your original driver list structure from attendance matrix
        self.formula_templates = {
            'driver_attendance': {
                'header_row': ['Driver ID', 'Name', 'Equipment', 'Hours', 'Status', 'Location'],
                'formula_columns': {
                    'Hours': '=SUM(INDIRECT("start_time"&ROW()-1&":end_time"&ROW()-1))',
                    'Status': '=IF(Hours>8,"Overtime",IF(Hours<4,"Partial","Normal"))',
                    'Utilization': '=Hours/8*100',
                    'Performance': '=AVERAGE(INDIRECT("safety"&ROW()-1&":efficiency"&ROW()-1))'
                },
                'auto_update_range': 'A2:Z1000'
            },
            'equipment_billing': {
                'header_row': ['Asset ID', 'Equipment Type', 'Daily Rate', 'Hours', 'Total Cost'],
                'formula_columns': {
                    'Total Cost': '=Daily_Rate*Hours',
                    'Weekly Total': '=SUMIF($A$2:$A$1000,A2,$E$2:$E$1000)',
                    'Monthly Total': '=SUMIFS($E$2:$E$1000,$A$2:$A$1000,A2,$B$2:$B$1000,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1))'
                },
                'auto_update_range': 'A2:Z500'
            },
            'daily_driver_report': {
                'header_row': ['Date', 'Driver', 'Vehicle', 'Start Time', 'End Time', 'Miles', 'Hours'],
                'formula_columns': {
                    'Hours': '=(End_Time-Start_Time)*24',
                    'Daily_Total': '=SUMIF($B$2:$B$1000,B2,$G$2:$G$1000)',
                    'Weekly_Average': '=AVERAGEIFS($G$2:$G$1000,$A$2:$A$1000,">="&A2-7,$A$2:$A$1000,"<="&A2)',
                    'Efficiency_Score': '=IF(Hours>0,Miles/Hours*10,0)'
                },
                'auto_update_range': 'A2:Z2000'
            }
        }
        
    def setup_copy_paste_headers(self, sheet_type: str, data_range: str):
        """Setup your copy-paste header system"""
        if sheet_type not in self.formula_templates:
            return False
            
        template = self.formula_templates[sheet_type]
        
        # Create header mapping for copy-paste functionality
        self.header_mappings[sheet_type] = {
            'headers': template['header_row'],
            'formula_cells': template['formula_columns'],
            'update_range': template['auto_update_range'],
            'copy_paste_ready': True
        }
        
        return True
    
    def process_authentic_driver_data(self):
        """Process your authentic driver data with auto-updating formulas"""
        try:
            # Load your attendance driver module data
            attendance_file = 'attendance_dashboard_data.json'
            if os.path.exists(attendance_file):
                with open(attendance_file, 'r') as f:
                    attendance_data = json.load(f)
                    
                self.processed_drivers = attendance_data
            
            # Process activity detail with formulas
            activity_file = 'attached_assets/ActivityDetail (4)_1749454854416.csv'
            if os.path.exists(activity_file):
                # Apply your copy-paste header method
                activity_df = self._safe_read_csv(activity_file)
                if not activity_df.empty:
                    # Apply auto-updating formulas to each row
                    enhanced_data = self._apply_auto_formulas(activity_df, 'daily_driver_report')
                    self.processed_drivers['activity_with_formulas'] = enhanced_data
            
            # Process driving history with formulas
            driving_files = [f for f in os.listdir('attached_assets') if 'DrivingHistory' in f and f.endswith('.csv')]
            for driving_file in driving_files:
                file_path = f'attached_assets/{driving_file}'
                driving_df = self._safe_read_csv(file_path)
                if not driving_df.empty:
                    enhanced_driving = self._apply_auto_formulas(driving_df, 'driver_attendance')
                    self.processed_drivers[f'driving_{driving_file}'] = enhanced_driving
            
            return True
            
        except Exception as e:
            print(f"Driver data processing error: {e}")
            return False
    
    def _safe_read_csv(self, file_path: str) -> pd.DataFrame:
        """Safely read CSV with multiple encoding attempts"""
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(file_path, encoding=encoding, low_memory=False, 
                               on_bad_lines='skip', nrows=1000)
                return df
            except:
                continue
        return pd.DataFrame()
    
    def _apply_auto_formulas(self, df: pd.DataFrame, formula_type: str) -> Dict:
        """Apply your auto-updating formulas to dataframe"""
        if formula_type not in self.formula_templates:
            return df.to_dict('records')
            
        template = self.formula_templates[formula_type]
        enhanced_records = []
        
        for index, row in df.iterrows():
            record = row.to_dict()
            
            # Apply formula logic (simulated Excel formula behavior)
            if formula_type == 'daily_driver_report':
                # Hours calculation
                if 'start_time' in record and 'end_time' in record:
                    try:
                        start = pd.to_datetime(record['start_time'])
                        end = pd.to_datetime(record['end_time'])
                        hours = (end - start).total_seconds() / 3600
                        record['calculated_hours'] = round(hours, 2)
                        record['efficiency_score'] = hours * 10 if hours > 0 else 0
                    except:
                        record['calculated_hours'] = 0
                        record['efficiency_score'] = 0
            
            elif formula_type == 'driver_attendance':
                # Status calculation
                hours = record.get('hours', 0)
                try:
                    hours = float(hours) if hours else 0
                    if hours > 8:
                        record['status'] = 'Overtime'
                    elif hours < 4:
                        record['status'] = 'Partial'
                    else:
                        record['status'] = 'Normal'
                    
                    record['utilization'] = round((hours / 8) * 100, 1)
                except:
                    record['status'] = 'Unknown'
                    record['utilization'] = 0
            
            # Add formula metadata
            record['formula_applied'] = True
            record['formula_type'] = formula_type
            record['auto_update_enabled'] = True
            
            enhanced_records.append(record)
        
        return {
            'data': enhanced_records,
            'formulas_applied': len(enhanced_records),
            'template_used': formula_type,
            'copy_paste_ready': True
        }
    
    def generate_copy_paste_template(self, sheet_type: str) -> Dict:
        """Generate copy-paste template for Excel/Sheets"""
        if sheet_type not in self.formula_templates:
            return {}
            
        template = self.formula_templates[sheet_type]
        
        copy_paste_template = {
            'headers': template['header_row'],
            'sample_formulas': template['formula_columns'],
            'instructions': {
                'step1': 'Copy the header row to your spreadsheet',
                'step2': 'Paste data below headers starting at row 2',
                'step3': 'Copy formulas from sample_formulas to appropriate columns',
                'step4': 'Select formula cells and drag down to auto-fill',
                'step5': 'Formulas will auto-update when you add new rows'
            },
            'excel_ready': True,
            'auto_update_range': template['auto_update_range']
        }
        
        return copy_paste_template
    
    def save_enhanced_driver_data(self):
        """Save enhanced driver data with formulas"""
        try:
            output_data = {
                'formula_templates': self.formula_templates,
                'processed_drivers': self.processed_drivers,
                'header_mappings': self.header_mappings,
                'copy_paste_templates': {
                    sheet_type: self.generate_copy_paste_template(sheet_type)
                    for sheet_type in self.formula_templates.keys()
                },
                'processing_timestamp': datetime.now().isoformat(),
                'auto_update_enabled': True
            }
            
            with open('enhanced_driver_formulas.json', 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print("Enhanced driver data with auto-updating formulas saved")
            return True
            
        except Exception as e:
            print(f"Save error: {e}")
            return False

def initialize_auto_updating_system():
    """Initialize your auto-updating formula system"""
    engine = AutoUpdatingFormulaEngine()
    engine.initialize_driver_list_formulas()
    
    # Setup copy-paste headers for all sheet types
    for sheet_type in ['driver_attendance', 'equipment_billing', 'daily_driver_report']:
        engine.setup_copy_paste_headers(sheet_type, 'A2:Z1000')
    
    # Process authentic data
    engine.process_authentic_driver_data()
    engine.save_enhanced_driver_data()
    
    return engine

if __name__ == "__main__":
    engine = initialize_auto_updating_system()
    print("Auto-updating formula engine initialized with your driver list methodology")