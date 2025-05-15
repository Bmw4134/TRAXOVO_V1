"""
File Processor Module

This module processes various data files uploaded by users, including:
- DFW/HOU/WT Billing CSV Files
- Equipment Utilization Reports
- WEX Fuel Reports
- SelectFleet CSV Files

It extracts, transforms, and loads the data into the database for reporting.
"""
import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed_files')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')

# Ensure directories exist
for directory in [DATA_DIR, PROCESSED_DIR, UPLOAD_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class BillingFileProcessor:
    """
    Processes billing CSV files for different business units (DFW, HOU, WT)
    """
    
    def __init__(self, file_path, business_unit=None):
        """
        Initialize with file path and business unit
        
        Args:
            file_path (str): Path to the CSV file
            business_unit (str, optional): Business unit code (DFW, HOU, WT, etc.). Defaults to None.
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.business_unit = business_unit or self._detect_business_unit(self.file_name)
        self.processed_data = []
        self.meta_data = {
            'file_name': self.file_name,
            'business_unit': self.business_unit,
            'processed_at': datetime.now().isoformat(),
            'record_count': 0,
            'total_billing': 0.0,
            'status': 'pending'
        }
    
    def _detect_business_unit(self, file_name):
        """
        Detect business unit from file name
        
        Args:
            file_name (str): Name of the file
        
        Returns:
            str: Business unit code or 'UNKNOWN'
        """
        file_name_lower = file_name.lower()
        
        if '01 - dfw' in file_name_lower or 'dfw' in file_name_lower:
            return 'DFW'
        elif '02 - hou' in file_name_lower or 'hou' in file_name_lower:
            return 'HOU'
        elif '03 - wt' in file_name_lower or 'wt' in file_name_lower:
            return 'WT'
        elif 'select' in file_name_lower or 'sm - ' in file_name_lower:
            return 'SM'
        else:
            return 'UNKNOWN'
    
    def process(self):
        """
        Process the billing file and extract data
        
        Returns:
            dict: Dictionary with processed data and metadata
        """
        logger.info(f"Processing billing file: {self.file_path} for {self.business_unit}")
        
        try:
            # Read the CSV file
            with open(self.file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Check if file has data
            if not rows:
                logger.warning(f"Empty file: {self.file_path}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = 'Empty file'
                return {
                    'meta': self.meta_data,
                    'data': []
                }
            
            # Process each row
            for row in rows:
                # Skip empty rows
                if not row or not row[0]:
                    continue
                
                # Extract data from row
                # CSV format: asset_id,asset_desc,date,job_number,qty,cost_code,utilization,rate,billing_type,billing_rate,billing_amount
                if len(row) >= 11:
                    try:
                        record = {
                            'asset_id': row[0].strip(),
                            'asset_desc': row[1].strip(),
                            'date': row[2].strip(),
                            'job_number': row[3].strip(),
                            'qty': float(row[4]) if row[4].strip() else 0.0,
                            'cost_code': row[5].strip(),
                            'utilization': float(row[6]) if row[6].strip() else 0.0,
                            'rate': float(row[7]) if row[7].strip() else 0.0,
                            'billing_type': row[8].strip(),
                            'billing_rate': float(row[9]) if row[9].strip() else 0.0,
                            'billing_amount': float(row[10]) if row[10].strip() else 0.0,
                        }
                        
                        self.processed_data.append(record)
                        self.meta_data['total_billing'] += record['billing_amount']
                    except Exception as e:
                        logger.warning(f"Error processing row: {row}")
                        logger.warning(f"Error details: {e}")
            
            # Update metadata
            self.meta_data['record_count'] = len(self.processed_data)
            self.meta_data['status'] = 'success'
            
            # Save processed data to file
            self._save_processed_data()
            
            return {
                'meta': self.meta_data,
                'data': self.processed_data
            }
            
        except Exception as e:
            logger.error(f"Error processing file {self.file_path}: {e}")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = str(e)
            return {
                'meta': self.meta_data,
                'data': []
            }
    
    def _save_processed_data(self):
        """
        Save processed data to a JSON file
        
        Returns:
            str: Path to the saved file
        """
        # Create file name based on original file and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            PROCESSED_DIR, 
            f"{self.business_unit}_billing_{timestamp}.json"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save data as JSON
        with open(output_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'data': self.processed_data
            }, f, indent=2)
        
        logger.info(f"Saved processed data to {output_file}")
        return output_file

class UtilizationReportProcessor:
    """
    Processes equipment utilization reports in Excel format
    """
    
    def __init__(self, file_path):
        """
        Initialize with file path
        
        Args:
            file_path (str): Path to the Excel file
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.processed_data = []
        self.meta_data = {
            'file_name': self.file_name,
            'processed_at': datetime.now().isoformat(),
            'record_count': 0,
            'status': 'pending'
        }
    
    def process(self):
        """
        Process the utilization report and extract data
        
        Returns:
            dict: Dictionary with processed data and metadata
        """
        logger.info(f"Processing utilization report: {self.file_path}")
        
        try:
            # Read the Excel file
            df = pd.read_excel(self.file_path)
            
            # Check if file has data
            if df.empty:
                logger.warning(f"Empty file: {self.file_path}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = 'Empty file'
                return {
                    'meta': self.meta_data,
                    'data': []
                }
            
            # Clean up column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Extract data from DataFrame
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    record[col] = row[col]
                
                self.processed_data.append(record)
            
            # Update metadata
            self.meta_data['record_count'] = len(self.processed_data)
            self.meta_data['status'] = 'success'
            
            # Calculate summary metrics
            self._calculate_metrics()
            
            # Save processed data to file
            self._save_processed_data()
            
            return {
                'meta': self.meta_data,
                'data': self.processed_data
            }
            
        except Exception as e:
            logger.error(f"Error processing file {self.file_path}: {e}")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = str(e)
            return {
                'meta': self.meta_data,
                'data': []
            }
    
    def _calculate_metrics(self):
        """
        Calculate summary metrics for utilization data
        """
        try:
            # Convert to pandas DataFrame for easier analysis
            df = pd.DataFrame(self.processed_data)
            
            # Skip if no data
            if len(df) == 0:
                return
            
            # Find relevant columns
            utilization_col = next((col for col in df.columns if 'util' in col.lower()), None)
            asset_col = next((col for col in df.columns if 'asset' in col.lower()), None)
            hours_col = next((col for col in df.columns if 'hour' in col.lower()), None)
            
            if utilization_col:
                # Calculate average utilization
                avg_util = df[utilization_col].mean()
                self.meta_data['avg_utilization'] = float(avg_util)
                
                # Count assets below 30% utilization
                low_util_count = len(df[df[utilization_col] < 0.3])
                self.meta_data['low_utilization_count'] = low_util_count
            
            if asset_col and utilization_col:
                # Get top and bottom performers
                top_assets = df.sort_values(utilization_col, ascending=False).head(5)
                bottom_assets = df.sort_values(utilization_col, ascending=True).head(5)
                
                self.meta_data['top_performers'] = [
                    {
                        'asset': row[asset_col],
                        'utilization': float(row[utilization_col])
                    }
                    for _, row in top_assets.iterrows()
                ]
                
                self.meta_data['bottom_performers'] = [
                    {
                        'asset': row[asset_col],
                        'utilization': float(row[utilization_col])
                    }
                    for _, row in bottom_assets.iterrows()
                ]
        
        except Exception as e:
            logger.warning(f"Error calculating metrics: {e}")
    
    def _save_processed_data(self):
        """
        Save processed data to a JSON file
        
        Returns:
            str: Path to the saved file
        """
        # Create file name based on original file and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            PROCESSED_DIR, 
            f"utilization_report_{timestamp}.json"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save data as JSON
        with open(output_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'data': self.processed_data
            }, f, indent=2)
        
        logger.info(f"Saved processed data to {output_file}")
        return output_file

class WexFuelReportProcessor:
    """
    Processes WEX fuel reports in Excel or PDF format
    """
    
    def __init__(self, file_path):
        """
        Initialize with file path
        
        Args:
            file_path (str): Path to the fuel report file
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.processed_data = []
        self.meta_data = {
            'file_name': self.file_name,
            'processed_at': datetime.now().isoformat(),
            'record_count': 0,
            'total_gallons': 0.0,
            'total_amount': 0.0,
            'status': 'pending'
        }
    
    def process(self):
        """
        Process the WEX fuel report and extract data
        
        Returns:
            dict: Dictionary with processed data and metadata
        """
        logger.info(f"Processing WEX fuel report: {self.file_path}")
        
        try:
            # Determine file type
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            if file_ext == '.xlsx':
                # Process Excel format
                result = self._process_excel()
            elif file_ext == '.csv':
                # Process CSV format
                result = self._process_csv()
            elif file_ext == '.pdf':
                # Process PDF format
                # This would require a PDF parsing library
                logger.warning(f"PDF parsing not implemented yet for {self.file_path}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = 'PDF parsing not implemented'
                result = {
                    'meta': self.meta_data,
                    'data': []
                }
            else:
                logger.warning(f"Unsupported file format: {file_ext}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = f'Unsupported file format: {file_ext}'
                result = {
                    'meta': self.meta_data,
                    'data': []
                }
            
            # Save processed data
            self._save_processed_data()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {self.file_path}: {e}")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = str(e)
            return {
                'meta': self.meta_data,
                'data': []
            }
    
    def _process_excel(self):
        """
        Process Excel format fuel report
        
        Returns:
            dict: Processed data and metadata
        """
        # Read the Excel file
        df = pd.read_excel(self.file_path)
        
        # Check if file has data
        if df.empty:
            logger.warning(f"Empty file: {self.file_path}")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = 'Empty file'
            return {
                'meta': self.meta_data,
                'data': []
            }
        
        # Clean up column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Try to find key columns
        date_col = next((col for col in df.columns if 'date' in col.lower()), None)
        card_col = next((col for col in df.columns if 'card' in col.lower()), None)
        asset_col = next((col for col in df.columns if 'asset' in col.lower() or 'vehicle' in col.lower()), None)
        gallons_col = next((col for col in df.columns if 'gallon' in col.lower()), None)
        amount_col = next((col for col in df.columns if 'amount' in col.lower() or 'cost' in col.lower()), None)
        
        # Extract data from DataFrame
        for _, row in df.iterrows():
            record = {
                'date': row[date_col] if date_col else None,
                'card': row[card_col] if card_col else None,
                'asset': row[asset_col] if asset_col else None,
                'gallons': float(row[gallons_col]) if gallons_col and pd.notna(row[gallons_col]) else 0.0,
                'amount': float(row[amount_col]) if amount_col and pd.notna(row[amount_col]) else 0.0
            }
            
            # Add other columns
            for col in df.columns:
                if col not in [date_col, card_col, asset_col, gallons_col, amount_col]:
                    record[col] = row[col]
            
            self.processed_data.append(record)
            
            # Update totals
            self.meta_data['total_gallons'] += record['gallons']
            self.meta_data['total_amount'] += record['amount']
        
        # Update metadata
        self.meta_data['record_count'] = len(self.processed_data)
        self.meta_data['status'] = 'success'
        
        return {
            'meta': self.meta_data,
            'data': self.processed_data
        }
    
    def _process_csv(self):
        """
        Process CSV format fuel report
        
        Returns:
            dict: Processed data and metadata
        """
        # Read the CSV file
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check if file has data
        if not rows:
            logger.warning(f"Empty file: {self.file_path}")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = 'Empty file'
            return {
                'meta': self.meta_data,
                'data': []
            }
        
        # Process each row
        for row in rows:
            clean_row = {k.lower().strip().replace(' ', '_'): v for k, v in row.items()}
            
            # Try to find key fields
            date_field = next((k for k in clean_row if 'date' in k.lower()), None)
            card_field = next((k for k in clean_row if 'card' in k.lower()), None)
            asset_field = next((k for k in clean_row if 'asset' in k.lower() or 'vehicle' in k.lower()), None)
            gallons_field = next((k for k in clean_row if 'gallon' in k.lower()), None)
            amount_field = next((k for k in clean_row if 'amount' in k.lower() or 'cost' in k.lower()), None)
            
            record = {
                'date': clean_row.get(date_field) if date_field else None,
                'card': clean_row.get(card_field) if card_field else None,
                'asset': clean_row.get(asset_field) if asset_field else None,
                'gallons': float(clean_row.get(gallons_field, 0)) if gallons_field and clean_row.get(gallons_field) else 0.0,
                'amount': float(clean_row.get(amount_field, 0)) if amount_field and clean_row.get(amount_field) else 0.0
            }
            
            # Add other fields
            for k, v in clean_row.items():
                if k not in [date_field, card_field, asset_field, gallons_field, amount_field]:
                    record[k] = v
            
            self.processed_data.append(record)
            
            # Update totals
            self.meta_data['total_gallons'] += record['gallons']
            self.meta_data['total_amount'] += record['amount']
        
        # Update metadata
        self.meta_data['record_count'] = len(self.processed_data)
        self.meta_data['status'] = 'success'
        
        return {
            'meta': self.meta_data,
            'data': self.processed_data
        }
    
    def _save_processed_data(self):
        """
        Save processed data to a JSON file
        
        Returns:
            str: Path to the saved file
        """
        # Create file name based on original file and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            PROCESSED_DIR, 
            f"wex_fuel_{timestamp}.json"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save data as JSON
        with open(output_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'data': self.processed_data
            }, f, indent=2)
        
        logger.info(f"Saved processed data to {output_file}")
        return output_file

def detect_file_type(file_path):
    """
    Detect the type of file based on name and content
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: File type code (BILLING, UTILIZATION, WEX, UNKNOWN)
    """
    file_name = os.path.basename(file_path).lower()
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Check for billing files
    if (file_ext == '.csv' and 
        ('dfw' in file_name or 'hou' in file_name or 'wt' in file_name or 
         'select' in file_name or 'sm -' in file_name or 
         '01 -' in file_name or '02 -' in file_name or '03 -' in file_name)):
        return 'BILLING'
    
    # Check for utilization reports
    if (file_ext in ['.xlsx', '.xls'] and 
        ('util' in file_name or 'hour' in file_name or 'equipment' in file_name)):
        return 'UTILIZATION'
    
    # Check for WEX fuel reports
    if ('wex' in file_name or 'fuel' in file_name):
        return 'WEX'
    
    # Try to peek at content for CSV files
    if file_ext == '.csv':
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip().lower()
                if ('asset' in first_line and 'job' in first_line and 'billing' in first_line):
                    return 'BILLING'
                elif ('fuel' in first_line or 'gallon' in first_line or 'wex' in first_line):
                    return 'WEX'
        except Exception:
            pass
    
    # Try to peek at Excel files
    if file_ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(file_path, nrows=1)
            cols = [str(col).lower() for col in df.columns]
            if any('util' in col for col in cols) or any('hour' in col for col in cols):
                return 'UTILIZATION'
            elif any('fuel' in col for col in cols) or any('gallon' in col for col in cols):
                return 'WEX'
        except Exception:
            pass
    
    return 'UNKNOWN'

def process_file(file_path):
    """
    Process a file based on its type
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        dict: Processing results
    """
    # Detect file type
    file_type = detect_file_type(file_path)
    logger.info(f"Detected file type {file_type} for {file_path}")
    
    # Process based on file type
    if file_type == 'BILLING':
        processor = BillingFileProcessor(file_path)
        return processor.process()
    elif file_type == 'UTILIZATION':
        processor = UtilizationReportProcessor(file_path)
        return processor.process()
    elif file_type == 'WEX':
        processor = WexFuelReportProcessor(file_path)
        return processor.process()
    else:
        return {
            'meta': {
                'file_name': os.path.basename(file_path),
                'processed_at': datetime.now().isoformat(),
                'status': 'error',
                'error': 'Unknown file type'
            },
            'data': []
        }

def process_files_in_directory(directory=UPLOAD_DIR):
    """
    Process all files in a directory
    
    Args:
        directory (str, optional): Directory to process. Defaults to UPLOAD_DIR.
    
    Returns:
        list: List of processing results
    """
    results = []
    
    # Check if directory exists
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return results
    
    # Get all files in the directory
    files = [os.path.join(directory, f) for f in os.listdir(directory) 
             if os.path.isfile(os.path.join(directory, f))]
    
    # Process each file
    for file_path in files:
        results.append(process_file(file_path))
    
    return results

# Example usage
if __name__ == "__main__":
    # Test with a sample file
    file_path = "sample.csv"  # replace with a real file path for testing
    
    if os.path.exists(file_path):
        result = process_file(file_path)
        print(f"Processed {result['meta']['record_count']} records from {file_path}")
    else:
        print(f"File not found: {file_path}")