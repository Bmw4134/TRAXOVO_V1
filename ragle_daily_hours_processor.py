"""
RAGLE DAILY HOURS-QUANTITIES REVIEW PROCESSOR
Processes authentic RAGLE INC daily operational data from Excel workbook
"""

import pandas as pd
import os
from datetime import datetime
import json

class RagleDailyHoursProcessor:
    def __init__(self):
        self.data_file = "attached_assets/RAGLE DAILY HOURS-QUANTITIES REVIEW_1749591557087.xlsx"
        self.processed_data = {}
        self.summary_metrics = {}
        
    def load_daily_hours_data(self):
        """Load and process RAGLE daily hours and quantities data"""
        try:
            if not os.path.exists(self.data_file):
                print(f"⚠️ File not found: {self.data_file}")
                return False
                
            # Load Excel file with multiple sheets
            excel_data = pd.read_excel(self.data_file, sheet_name=None, engine='openpyxl')
            
            print(f"✓ Loaded RAGLE daily hours review with {len(excel_data)} sheets")
            
            # Process each sheet
            for sheet_name, df in excel_data.items():
                print(f"Processing sheet: {sheet_name} ({len(df)} rows)")
                self.processed_data[sheet_name] = self._process_sheet_data(df, sheet_name)
            
            self._calculate_summary_metrics()
            return True
            
        except Exception as e:
            print(f"Error loading RAGLE daily hours data: {e}")
            return False
    
    def _process_sheet_data(self, df, sheet_name):
        """Process individual sheet data based on content"""
        try:
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            # Process based on sheet content patterns
            processed_sheet = {
                "sheet_name": sheet_name,
                "total_rows": len(df),
                "columns": list(df.columns),
                "data_summary": {}
            }
            
            # Look for common RAGLE data patterns
            if any(col.lower().find('hours') != -1 for col in df.columns):
                processed_sheet["data_type"] = "hours_tracking"
                processed_sheet["data_summary"] = self._process_hours_data(df)
                
            elif any(col.lower().find('quantity') != -1 for col in df.columns):
                processed_sheet["data_type"] = "quantities_tracking"
                processed_sheet["data_summary"] = self._process_quantities_data(df)
                
            elif any(col.lower().find('equipment') != -1 for col in df.columns):
                processed_sheet["data_type"] = "equipment_tracking"
                processed_sheet["data_summary"] = self._process_equipment_data(df)
                
            else:
                processed_sheet["data_type"] = "general_data"
                processed_sheet["data_summary"] = self._process_general_data(df)
            
            return processed_sheet
            
        except Exception as e:
            print(f"Error processing sheet {sheet_name}: {e}")
            return {"error": str(e)}
    
    def _process_hours_data(self, df):
        """Process hours tracking data"""
        summary = {
            "total_records": len(df),
            "date_range": {},
            "hours_metrics": {}
        }
        
        # Look for date columns
        date_columns = [col for col in df.columns if any(term in col.lower() for term in ['date', 'day', 'time'])]
        if date_columns:
            summary["date_columns"] = date_columns
            
        # Look for hours columns
        hours_columns = [col for col in df.columns if 'hour' in col.lower()]
        if hours_columns:
            summary["hours_columns"] = hours_columns
            for col in hours_columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    summary["hours_metrics"][col] = {
                        "total": float(df[col].sum()) if not df[col].isna().all() else 0,
                        "average": float(df[col].mean()) if not df[col].isna().all() else 0,
                        "max": float(df[col].max()) if not df[col].isna().all() else 0
                    }
        
        return summary
    
    def _process_quantities_data(self, df):
        """Process quantities tracking data"""
        summary = {
            "total_records": len(df),
            "quantity_metrics": {}
        }
        
        quantity_columns = [col for col in df.columns if any(term in col.lower() for term in ['quantity', 'qty', 'amount', 'volume'])]
        
        for col in quantity_columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                summary["quantity_metrics"][col] = {
                    "total": float(df[col].sum()) if not df[col].isna().all() else 0,
                    "average": float(df[col].mean()) if not df[col].isna().all() else 0,
                    "records": int(df[col].count())
                }
        
        return summary
    
    def _process_equipment_data(self, df):
        """Process equipment tracking data"""
        summary = {
            "total_records": len(df),
            "equipment_count": 0,
            "equipment_types": []
        }
        
        # Look for equipment identifiers
        equipment_columns = [col for col in df.columns if any(term in col.lower() for term in ['equipment', 'asset', 'machine', 'unit'])]
        
        if equipment_columns:
            for col in equipment_columns:
                unique_equipment = df[col].dropna().unique()
                summary["equipment_count"] += len(unique_equipment)
                summary["equipment_types"].extend(unique_equipment.tolist())
        
        return summary
    
    def _process_general_data(self, df):
        """Process general data patterns"""
        summary = {
            "total_records": len(df),
            "columns_analyzed": len(df.columns),
            "data_patterns": {}
        }
        
        # Analyze each column
        for col in df.columns:
            col_info = {
                "data_type": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isna().sum())
            }
            
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["numeric_summary"] = {
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isna().all() else None
                }
            
            summary["data_patterns"][col] = col_info
        
        return summary
    
    def _calculate_summary_metrics(self):
        """Calculate overall summary metrics"""
        self.summary_metrics = {
            "total_sheets": len(self.processed_data),
            "total_records": sum(sheet.get("total_rows", 0) for sheet in self.processed_data.values() if isinstance(sheet, dict)),
            "data_types_found": [],
            "processing_timestamp": datetime.now().isoformat()
        }
        
        # Collect data types
        for sheet in self.processed_data.values():
            if isinstance(sheet, dict) and "data_type" in sheet:
                if sheet["data_type"] not in self.summary_metrics["data_types_found"]:
                    self.summary_metrics["data_types_found"].append(sheet["data_type"])
    
    def get_summary_report(self):
        """Generate comprehensive summary report"""
        return {
            "file_info": {
                "filename": os.path.basename(self.data_file),
                "processing_status": "completed" if self.processed_data else "failed"
            },
            "summary_metrics": self.summary_metrics,
            "sheet_details": self.processed_data
        }
    
    def export_processed_data(self, output_file="ragle_daily_hours_processed.json"):
        """Export processed data to JSON"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.get_summary_report(), f, indent=2, default=str)
            print(f"✓ Exported processed data to {output_file}")
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False

def process_ragle_daily_hours():
    """Main function to process RAGLE daily hours data"""
    processor = RagleDailyHoursProcessor()
    
    print("🔄 Processing RAGLE DAILY HOURS-QUANTITIES REVIEW...")
    success = processor.load_daily_hours_data()
    
    if success:
        report = processor.get_summary_report()
        print(f"✓ Successfully processed {report['summary_metrics']['total_sheets']} sheets")
        print(f"✓ Total records: {report['summary_metrics']['total_records']}")
        print(f"✓ Data types found: {', '.join(report['summary_metrics']['data_types_found'])}")
        
        # Export for integration
        processor.export_processed_data()
        return report
    else:
        print("❌ Failed to process RAGLE daily hours data")
        return None

if __name__ == "__main__":
    process_ragle_daily_hours()