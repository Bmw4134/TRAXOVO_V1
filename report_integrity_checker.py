#!/usr/bin/env python3
"""
Report Integrity Checker

This script performs comprehensive integrity validation of the Daily Driver Reports
to ensure complete data consistency across all sources and output formats.
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
import traceback
from typing import Dict, List, Set, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs/validation', exist_ok=True)

# Add file handler for this script
file_handler = logging.FileHandler('logs/validation/integrity_checker.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def count_unique_drivers(file_path: str) -> int:
    """Count unique drivers in a file"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return 0
            
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return 0
            
        # Standardize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Look for driver column
        driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
        driver_col = None
        for col in driver_cols:
            if col in df.columns:
                driver_col = col
                break
                
        if not driver_col:
            logger.warning(f"Driver column not found in {file_path}")
            return 0
            
        # Extract unique driver names
        driver_names = df[driver_col].astype(str).str.strip()
        unique_drivers = set(driver_names)
        
        # Remove empty names
        if '' in unique_drivers:
            unique_drivers.remove('')
        if 'nan' in unique_drivers:
            unique_drivers.remove('nan')
        if 'none' in unique_drivers:
            unique_drivers.remove('none')
        if 'null' in unique_drivers:
            unique_drivers.remove('null')
            
        return len(unique_drivers)
        
    except Exception as e:
        logger.error(f"Error counting drivers in {file_path}: {e}")
        logger.error(traceback.format_exc())
        return 0

def load_json_report(date_str: str) -> Dict:
    """Load JSON report data"""
    try:
        report_path = Path(f"reports/daily_drivers/daily_report_{date_str}.json")
        if not report_path.exists():
            logger.error(f"Report not found: {report_path}")
            return {}
            
        with open(report_path, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error loading report: {e}")
        logger.error(traceback.format_exc())
        return {}

def get_driver_source_crossmatch(date_str: str) -> Tuple[int, int, float]:
    """Calculate driver crossmatch rate between telematics and Start Time sheet"""
    try:
        # Get all driving history files
        driving_history_files = []
        for root, _, files in os.walk('data/driving_history'):
            for file in files:
                file_path = os.path.join(root, file)
                if date_str.replace('-', '') in file or date_str in file:
                    driving_history_files.append(file_path)
        
        # Get all baseline/start time files
        start_time_files = []
        for root, _, files in os.walk('data/start_time_job'):
            for file in files:
                file_path = os.path.join(root, file)
                if 'baseline' in file or date_str.replace('-', '') in file or date_str in file:
                    start_time_files.append(file_path)
        
        # Extract driver names from driving history
        telematics_drivers = set()
        for file_path in driving_history_files:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for driver column
            driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
            driver_col = None
            for col in driver_cols:
                if col in df.columns:
                    driver_col = col
                    break
                    
            if not driver_col:
                continue
                
            # Extract driver names
            driver_names = df[driver_col].astype(str).str.strip()
            for driver in driver_names:
                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                    telematics_drivers.add(driver.lower())
        
        # Extract driver names from start time job
        start_time_drivers = set()
        for file_path in start_time_files:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for driver column
            driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
            driver_col = None
            for col in driver_cols:
                if col in df.columns:
                    driver_col = col
                    break
                    
            if not driver_col:
                continue
                
            # Extract driver names
            driver_names = df[driver_col].astype(str).str.strip()
            for driver in driver_names:
                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                    start_time_drivers.add(driver.lower())
        
        # Calculate crossmatch
        if not start_time_drivers:
            return 0, 0, 0.0
            
        matches = telematics_drivers.intersection(start_time_drivers)
        match_rate = len(matches) / len(start_time_drivers) * 100
        
        return len(matches), len(start_time_drivers), match_rate
        
    except Exception as e:
        logger.error(f"Error calculating crossmatch: {e}")
        logger.error(traceback.format_exc())
        return 0, 0, 0.0

def get_jobsite_accuracy(date_str: str) -> Tuple[int, int, float]:
    """Calculate job site location accuracy"""
    try:
        # Load report data
        report_data = load_json_report(date_str)
        if not report_data:
            return 0, 0, 0.0
            
        drivers = report_data.get('drivers', [])
        if not drivers:
            return 0, 0, 0.0
            
        # Count on job and not on job
        total_drivers = len(drivers)
        not_on_job = sum(1 for d in drivers if d.get('status') == 'Not On Job')
        on_job = total_drivers - not_on_job
        
        accuracy_rate = on_job / total_drivers * 100 if total_drivers > 0 else 0.0
        
        return on_job, total_drivers, accuracy_rate
        
    except Exception as e:
        logger.error(f"Error calculating job site accuracy: {e}")
        logger.error(traceback.format_exc())
        return 0, 0, 0.0

def check_for_ghost_entries(date_str: str) -> List[str]:
    """Check for ghost entries (unmatched names) in the final report"""
    try:
        # Load report data
        report_data = load_json_report(date_str)
        if not report_data:
            return []
            
        # Get all driver names from the report
        report_drivers = set()
        for driver in report_data.get('drivers', []):
            driver_name = driver.get('driver_name', '').strip().lower()
            if driver_name:
                report_drivers.add(driver_name)
        
        # Get all start time job files
        start_time_files = []
        for root, _, files in os.walk('data/start_time_job'):
            for file in files:
                file_path = os.path.join(root, file)
                if 'baseline' in file or date_str.replace('-', '') in file or date_str in file:
                    start_time_files.append(file_path)
        
        # Extract driver names from start time job
        start_time_drivers = set()
        for file_path in start_time_files:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for driver column
            driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
            driver_col = None
            for col in driver_cols:
                if col in df.columns:
                    driver_col = col
                    break
                    
            if not driver_col:
                continue
                
            # Extract driver names
            driver_names = df[driver_col].astype(str).str.strip()
            for driver in driver_names:
                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                    start_time_drivers.add(driver.lower())
        
        # Get all driving history files
        driving_history_files = []
        for root, _, files in os.walk('data/driving_history'):
            for file in files:
                file_path = os.path.join(root, file)
                if date_str.replace('-', '') in file or date_str in file:
                    driving_history_files.append(file_path)
        
        # Extract driver names from driving history
        driving_history_drivers = set()
        for file_path in driving_history_files:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for driver column
            driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
            driver_col = None
            for col in driver_cols:
                if col in df.columns:
                    driver_col = col
                    break
                    
            if not driver_col:
                continue
                
            # Extract driver names
            driver_names = df[driver_col].astype(str).str.strip()
            for driver in driver_names:
                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                    driving_history_drivers.add(driver.lower())
        
        # Find ghost entries (in report but not in either source)
        all_source_drivers = start_time_drivers.union(driving_history_drivers)
        ghost_entries = []
        
        for driver in report_drivers:
            if driver.lower() not in all_source_drivers:
                ghost_entries.append(driver)
                
        return ghost_entries
        
    except Exception as e:
        logger.error(f"Error checking for ghost entries: {e}")
        logger.error(traceback.format_exc())
        return []

def check_classification_mismatches(date_str: str) -> Dict[str, Any]:
    """Check for classification mismatches between driver status and summary counts"""
    try:
        # Load report data
        report_data = load_json_report(date_str)
        if not report_data:
            return {'mismatches': True, 'errors': ['Report not found']}
            
        # Get drivers and summary
        drivers = report_data.get('drivers', [])
        summary = report_data.get('summary', {})
        
        if not summary:
            return {'mismatches': True, 'errors': ['Summary not found']}
            
        # Calculate actual counts
        actual_counts = {
            'total': len(drivers),
            'late': sum(1 for d in drivers if d.get('status') == 'Late'),
            'early_end': sum(1 for d in drivers if d.get('status') == 'Early End'),
            'not_on_job': sum(1 for d in drivers if d.get('status') == 'Not On Job'),
            'on_time': sum(1 for d in drivers if d.get('status') == 'On Time')
        }
        
        # Compare with summary
        mismatches = []
        for field in ['total', 'late', 'early_end', 'not_on_job', 'on_time']:
            if actual_counts[field] != summary.get(field, 0):
                mismatches.append(f"{field}: {actual_counts[field]} != {summary.get(field, 0)}")
                
        return {
            'mismatches': len(mismatches) > 0,
            'errors': mismatches,
            'actual_counts': actual_counts,
            'summary_counts': summary
        }
        
    except Exception as e:
        logger.error(f"Error checking classification mismatches: {e}")
        logger.error(traceback.format_exc())
        return {'mismatches': True, 'errors': [str(e)]}

def validate_output_files(date_str: str) -> Dict[str, Any]:
    """Validate PDF and Excel output files against JSON master structure"""
    try:
        # Define expected output files
        reports_dir = Path('reports/daily_drivers')
        exports_dir = Path('exports/daily_reports')
        
        expected_files = {
            'reports_json': reports_dir / f"daily_report_{date_str}.json",
            'reports_excel': reports_dir / f"daily_report_{date_str}.xlsx",
            'reports_pdf': reports_dir / f"daily_report_{date_str}.pdf",
            'exports_json': exports_dir / f"daily_report_{date_str}.json",
            'exports_excel': exports_dir / f"{date_str}_DailyDriverReport.xlsx",
            'exports_excel_legacy': exports_dir / f"daily_report_{date_str}.xlsx",
            'exports_pdf': exports_dir / f"{date_str}_DailyDriverReport.pdf",
            'exports_pdf_legacy': exports_dir / f"daily_report_{date_str}.pdf"
        }
        
        # Check file existence
        missing_files = []
        file_sizes = {}
        
        for file_type, file_path in expected_files.items():
            if not file_path.exists():
                missing_files.append(f"{file_type}: {file_path}")
            else:
                file_sizes[file_type] = file_path.stat().st_size
        
        if missing_files:
            return {'valid': False, 'errors': missing_files}
        
        # Check sizes
        size_issues = []
        min_json_size = 1024  # 1 KB minimum
        min_excel_size = 5 * 1024  # 5 KB minimum
        min_pdf_size = 10 * 1024  # 10 KB minimum
        
        if file_sizes.get('reports_json', 0) < min_json_size:
            size_issues.append(f"reports_json too small: {file_sizes.get('reports_json', 0)} bytes")
            
        if file_sizes.get('exports_json', 0) < min_json_size:
            size_issues.append(f"exports_json too small: {file_sizes.get('exports_json', 0)} bytes")
            
        if file_sizes.get('reports_excel', 0) < min_excel_size:
            size_issues.append(f"reports_excel too small: {file_sizes.get('reports_excel', 0)} bytes")
            
        if file_sizes.get('exports_excel', 0) < min_excel_size:
            size_issues.append(f"exports_excel too small: {file_sizes.get('exports_excel', 0)} bytes")
            
        if file_sizes.get('reports_pdf', 0) < min_pdf_size:
            size_issues.append(f"reports_pdf too small: {file_sizes.get('reports_pdf', 0)} bytes")
            
        if file_sizes.get('exports_pdf', 0) < min_pdf_size:
            size_issues.append(f"exports_pdf too small: {file_sizes.get('exports_pdf', 0)} bytes")
        
        if size_issues:
            return {'valid': False, 'errors': size_issues, 'file_sizes': file_sizes}
        
        # Compare JSON files
        try:
            with open(expected_files['reports_json'], 'r') as f:
                reports_data = json.load(f)
                
            with open(expected_files['exports_json'], 'r') as f:
                exports_data = json.load(f)
                
            # Compare top-level keys
            if set(reports_data.keys()) != set(exports_data.keys()):
                return {
                    'valid': False, 
                    'errors': [f"JSON keys mismatch: {set(reports_data.keys())} != {set(exports_data.keys())}"]
                }
                
            # Compare summary
            reports_summary = reports_data.get('summary', {})
            exports_summary = exports_data.get('summary', {})
            
            summary_mismatches = []
            for field in ['total', 'late', 'early_end', 'not_on_job', 'on_time']:
                if reports_summary.get(field, 0) != exports_summary.get(field, 0):
                    summary_mismatches.append(
                        f"{field}: {reports_summary.get(field, 0)} != {exports_summary.get(field, 0)}"
                    )
                    
            if summary_mismatches:
                return {'valid': False, 'errors': summary_mismatches}
                
            # Compare driver count
            if len(reports_data.get('drivers', [])) != len(exports_data.get('drivers', [])):
                return {
                    'valid': False,
                    'errors': [
                        "Driver count mismatch: "
                        f"{len(reports_data.get('drivers', []))} != {len(exports_data.get('drivers', []))}"
                    ]
                }
            
            # Check Excel files
            try:
                reports_df = pd.read_excel(expected_files['reports_excel'])
                exports_df = pd.read_excel(expected_files['exports_excel'])
                
                if len(reports_df) != len(exports_df):
                    return {
                        'valid': False,
                        'errors': [f"Excel row count mismatch: {len(reports_df)} != {len(exports_df)}"]
                    }
                    
                if len(reports_df) != len(reports_data.get('drivers', [])):
                    return {
                        'valid': False,
                        'errors': [
                            "Excel-JSON row count mismatch: "
                            f"{len(reports_df)} != {len(reports_data.get('drivers', []))}"
                        ]
                    }
            except Exception as e:
                return {'valid': False, 'errors': [f"Excel comparison error: {e}"]}
                
            # All validations passed
            return {
                'valid': True,
                'file_sizes': file_sizes
            }
                
        except Exception as e:
            return {'valid': False, 'errors': [f"JSON comparison error: {e}"]}
        
    except Exception as e:
        logger.error(f"Error validating output files: {e}")
        logger.error(traceback.format_exc())
        return {'valid': False, 'errors': [str(e)]}

def report_integrity_check(date_str: str) -> Dict[str, Any]:
    """
    Perform a comprehensive integrity check on a Daily Driver Report
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Integrity check results
    """
    logger.info(f"Performing integrity check for {date_str}")
    
    try:
        # Create report directories
        reports_dir = Path('reports/integrity')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize results
        results = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "Drivers_Sourced": {
                "StartTimeJob": 0,
                "DrivingHistory": 0,
                "ActivityDetail": 0,
                "FinalReport": 0
            },
            "Crossmatch_Score": 0,
            "Jobsite_Accuracy": 0,
            "Summary_Match": False,
            "Errors_Found": []
        }
        
        # 1. Count unique drivers in each source
        # Count start time job drivers
        start_time_drivers = 0
        for root, _, files in os.walk('data/start_time_job'):
            for file in files:
                file_path = os.path.join(root, file)
                if 'baseline' in file or date_str.replace('-', '') in file or date_str in file:
                    start_time_drivers += count_unique_drivers(file_path)
        
        # Count driving history drivers
        driving_history_drivers = 0
        for root, _, files in os.walk('data/driving_history'):
            for file in files:
                file_path = os.path.join(root, file)
                if date_str.replace('-', '') in file or date_str in file:
                    driving_history_drivers += count_unique_drivers(file_path)
        
        # Count activity detail drivers
        activity_detail_drivers = 0
        for root, _, files in os.walk('data/activity_detail'):
            for file in files:
                file_path = os.path.join(root, file)
                if date_str.replace('-', '') in file or date_str in file:
                    activity_detail_drivers += count_unique_drivers(file_path)
        
        # Count drivers in final report
        report_data = load_json_report(date_str)
        final_report_drivers = len(report_data.get('drivers', []))
        
        results["Drivers_Sourced"]["StartTimeJob"] = start_time_drivers
        results["Drivers_Sourced"]["DrivingHistory"] = driving_history_drivers
        results["Drivers_Sourced"]["ActivityDetail"] = activity_detail_drivers
        results["Drivers_Sourced"]["FinalReport"] = final_report_drivers
        
        # 2. Calculate driver crossmatch
        matches, total, crossmatch_score = get_driver_source_crossmatch(date_str)
        results["Crossmatch_Score"] = round(crossmatch_score, 1)
        
        # 3. Calculate job site accuracy
        on_job, total_drivers, accuracy_rate = get_jobsite_accuracy(date_str)
        results["Jobsite_Accuracy"] = round(accuracy_rate, 1)
        
        # 4. Check for ghost entries
        ghost_entries = check_for_ghost_entries(date_str)
        if ghost_entries:
            results["Errors_Found"].append(f"Ghost entries found: {ghost_entries}")
        
        # 5. Check for classification mismatches
        classification_check = check_classification_mismatches(date_str)
        results["Summary_Match"] = not classification_check['mismatches']
        if classification_check['mismatches']:
            results["Errors_Found"].extend(classification_check['errors'])
        
        # 6. Validate output files
        output_check = validate_output_files(date_str)
        if not output_check['valid']:
            results["Errors_Found"].extend(output_check['errors'])
        
        # Save results to file
        output_file = reports_dir / f"integrity_check_{date_str}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info(f"Integrity check complete for {date_str}")
        logger.info(f"Results saved to {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in integrity check: {e}")
        logger.error(traceback.format_exc())
        return {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "Errors_Found": [str(e)],
            "error": True
        }

def prepare_may_19_test_data():
    """Prepare test data for May 19 report"""
    try:
        logger.info("Preparing test data for May 19 report")
        
        # Create base directories if they don't exist
        for directory in [
            'data/driving_history',
            'data/activity_detail',
            'data/assets_time_on_site'
        ]:
            os.makedirs(directory, exist_ok=True)
            
        # Copy and modify May 16 data to May 19
        
        # 1. Driving history
        may16_driving = 'data/driving_history/DrivingHistory_20250516.csv'
        may19_driving = 'data/driving_history/DrivingHistory_20250519.csv'
        
        if os.path.exists(may16_driving):
            # Read May 16 data
            df = pd.read_csv(may16_driving)
            
            # Update dates to May 19
            if 'datetime' in df.columns:
                df['datetime'] = df['datetime'].str.replace('2025-05-16', '2025-05-19')
                
            # Save as May 19 data
            df.to_csv(may19_driving, index=False)
            logger.info(f"Created {may19_driving}")
            
        # 2. Activity detail
        may16_activity = 'data/activity_detail/ActivityDetail_20250516.csv'
        may19_activity = 'data/activity_detail/ActivityDetail_20250519.csv'
        
        if os.path.exists(may16_activity):
            # Read May 16 data
            df = pd.read_csv(may16_activity)
            
            # Update dates to May 19
            if 'datetime' in df.columns:
                df['datetime'] = df['datetime'].str.replace('2025-05-16', '2025-05-19')
                
            # Save as May 19 data
            df.to_csv(may19_activity, index=False)
            logger.info(f"Created {may19_activity}")
            
        # 3. Assets time on site
        may16_assets = 'data/assets_time_on_site/AssetsTimeOnSite_20250516.csv'
        may19_assets = 'data/assets_time_on_site/AssetsTimeOnSite_20250519.csv'
        
        if os.path.exists(may16_assets):
            # Read May 16 data
            df = pd.read_csv(may16_assets)
            
            # Update dates to May 19
            if 'time_in' in df.columns:
                df['time_in'] = df['time_in'].str.replace('2025-05-16', '2025-05-19')
            if 'time_out' in df.columns:
                df['time_out'] = df['time_out'].str.replace('2025-05-16', '2025-05-19')
                
            # Save as May 19 data
            df.to_csv(may19_assets, index=False)
            logger.info(f"Created {may19_assets}")
            
        logger.info("Test data preparation complete for May 19")
        return True
        
    except Exception as e:
        logger.error(f"Error preparing May 19 test data: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Report Integrity Checker')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--prepare-may19', action='store_true', help='Prepare test data for May 19')
    
    args = parser.parse_args()
    
    if args.prepare_may19:
        if prepare_may_19_test_data():
            print("Successfully prepared test data for May 19")
        else:
            print("Failed to prepare test data for May 19")
        return
    
    results = report_integrity_check(args.date)
    
    print(f"\nIntegrity Check Results for {args.date}:")
    print("=" * 60)
    print(f"Start Time Job Drivers: {results['Drivers_Sourced']['StartTimeJob']}")
    print(f"Driving History Drivers: {results['Drivers_Sourced']['DrivingHistory']}")
    print(f"Activity Detail Drivers: {results['Drivers_Sourced']['ActivityDetail']}")
    print(f"Final Report Drivers: {results['Drivers_Sourced']['FinalReport']}")
    print("-" * 60)
    print(f"Driver ID Crossmatch Score: {results['Crossmatch_Score']}%")
    print(f"Job Site Location Accuracy: {results['Jobsite_Accuracy']}%")
    print(f"Summary Counts Match: {results['Summary_Match']}")
    print("-" * 60)
    
    if results['Errors_Found']:
        print("Errors Found:")
        for i, error in enumerate(results['Errors_Found'], 1):
            print(f"{i}. {error}")
    else:
        print("No errors found. All integrity checks passed!")
    
    print("\nResults saved to reports/integrity/")

if __name__ == '__main__':
    main()