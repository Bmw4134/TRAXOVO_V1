#!/usr/bin/env python3
"""
Report Audit and Gap Analysis Tool

This utility identifies drivers excluded from the final reports and explains why,
then patches the reports to include these exclusions with appropriate flags.
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import traceback
from typing import Dict, List, Set, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Add file handler for this script
os.makedirs('logs/audit', exist_ok=True)
file_handler = logging.FileHandler('logs/audit/report_audit.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def load_source_drivers(date_str: str) -> Dict[str, Set[str]]:
    """
    Load all drivers from all source files for a date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Set[str]]: Dictionary of driver sets by source type
    """
    source_drivers = {
        'start_time_job': set(),
        'driving_history': set(),
        'activity_detail': set()
    }
    
    # Find files for the date
    files_map = {}
    for source_type in source_drivers.keys():
        files_map[source_type] = []
        dir_path = f"data/{source_type}"
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path):
                    # Determine if file matches the date
                    if (date_str.replace('-', '') in file or 
                        date_str in file or 
                        source_type == 'start_time_job' and 'baseline' in file):
                        files_map[source_type].append(file_path)
    
    # Process files and extract drivers
    for source_type, file_paths in files_map.items():
        for file_path in file_paths:
            try:
                # Determine file type and load
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                else:
                    continue
                    
                # Standardize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Determine driver column
                driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
                driver_col = None
                for col in driver_cols:
                    if col in df.columns:
                        driver_col = col
                        break
                
                if driver_col:
                    # Extract and normalize driver names
                    for driver in df[driver_col].astype(str).str.strip():
                        if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                            source_drivers[source_type].add(driver.strip().lower())
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    return source_drivers

def load_final_report_drivers(date_str: str) -> Set[str]:
    """
    Load all drivers from the final report
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Set[str]: Set of driver names
    """
    report_drivers = set()
    
    report_path = Path(f"reports/daily_drivers/daily_report_{date_str}.json")
    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        return report_drivers
        
    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
            
        for driver in report_data.get('drivers', []):
            driver_name = driver.get('driver_name', '').strip()
            if driver_name:
                report_drivers.add(driver_name.lower())
                
    except Exception as e:
        logger.error(f"Error loading final report: {e}")
        
    return report_drivers

def analyze_excluded_drivers(date_str: str) -> Dict[str, Any]:
    """
    Analyze drivers excluded from the final report
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    logger.info(f"Analyzing excluded drivers for {date_str}")
    
    # Load all source drivers
    source_drivers = load_source_drivers(date_str)
    
    # Load final report drivers
    final_report_drivers = load_final_report_drivers(date_str)
    
    # Find all unique drivers across all sources
    all_drivers = set()
    for source_type, drivers in source_drivers.items():
        all_drivers.update(drivers)
    
    # Find excluded drivers
    excluded_drivers = all_drivers - final_report_drivers
    
    # Analyze exclusion reasons
    exclusion_analysis = {}
    
    for driver in excluded_drivers:
        # Initialize exclusion reason
        exclusion_analysis[driver] = {
            'sources': [],
            'reason': '',
            'should_be_included_as': ''
        }
        
        # Determine which sources the driver appears in
        for source_type, drivers in source_drivers.items():
            if driver in drivers:
                exclusion_analysis[driver]['sources'].append(source_type)
        
        # Determine exclusion reason and suggested category
        if 'start_time_job' not in exclusion_analysis[driver]['sources']:
            exclusion_analysis[driver]['reason'] = 'No match in StartTimeJob'
            exclusion_analysis[driver]['should_be_included_as'] = 'Unmatched'
        elif ('driving_history' not in exclusion_analysis[driver]['sources'] and 
              'activity_detail' not in exclusion_analysis[driver]['sources']):
            exclusion_analysis[driver]['reason'] = 'No telematics data'
            exclusion_analysis[driver]['should_be_included_as'] = 'Telemetry Missing'
    
    # Count exclusion statistics
    stats = {
        'total_excluded': len(excluded_drivers),
        'unmatched_with_telematics': sum(1 for d in exclusion_analysis.values() 
                                        if ('driving_history' in d['sources'] or 'activity_detail' in d['sources'])
                                        and 'start_time_job' not in d['sources']),
        'start_time_job_without_telematics': sum(1 for d in exclusion_analysis.values() 
                                               if 'start_time_job' in d['sources']
                                               and 'driving_history' not in d['sources']
                                               and 'activity_detail' not in d['sources']),
        'job_site_conflicts': 0  # This requires more complex analysis of GPS coordinates
    }
    
    return {
        'date': date_str,
        'exclusion_analysis': exclusion_analysis,
        'stats': stats
    }

def patch_report_with_exclusions(date_str: str, analysis: Dict[str, Any]) -> bool:
    """
    Patch the final report to include excluded drivers with appropriate flags
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        analysis (Dict[str, Any]): Analysis results
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Patching report for {date_str}")
    
    report_path = Path(f"reports/daily_drivers/daily_report_{date_str}.json")
    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        return False
        
    try:
        # Load report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
            
        # Make a backup
        backup_path = Path(f"reports/daily_drivers/daily_report_{date_str}.backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        with open(backup_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Extract drivers and update summary
        drivers = report_data.get('drivers', [])
        summary = report_data.get('summary', {})
        
        # Add excluded drivers
        excluded_count = 0
        for driver_name, info in analysis['exclusion_analysis'].items():
            # Create driver entry
            driver_entry = {
                'driver_name': driver_name.title(),  # Capitalize name for display
                'asset_id': "Unknown",
                'job_site': "Unknown",
                'scheduled_start': "Unknown",
                'scheduled_end': "Unknown",
                'actual_start': "Unknown",
                'actual_end': "Unknown",
                'status': info['should_be_included_as'],
                'status_reason': info['reason'],
                'exclusion_flag': True,  # Flag to identify added drivers
                'sources': info['sources']
            }
            
            # Add to drivers list
            drivers.append(driver_entry)
            excluded_count += 1
        
        # Update drivers list
        report_data['drivers'] = drivers
        
        # Update summary
        total = summary.get('total', 0) + excluded_count
        summary['total'] = total
        summary['excluded'] = excluded_count
        report_data['summary'] = summary
        
        # Update metadata
        metadata = report_data.get('metadata', {})
        metadata['patched_at'] = datetime.now().isoformat()
        metadata['patched_with'] = "report_audit_fill_gaps.py"
        metadata['exclusion_analysis'] = analysis['stats']
        report_data['metadata'] = metadata
        
        # Save updated report
        patched_path = Path(f"reports/daily_drivers/daily_report_{date_str}_with_exclusions.json")
        with open(patched_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        logger.info(f"Patched report saved to {patched_path}")
        
        # Create Excel version of patched report
        try:
            # Convert drivers list to DataFrame
            df = pd.DataFrame(drivers)
            
            # Save to Excel
            excel_path = Path(f"reports/daily_drivers/daily_report_{date_str}_with_exclusions.xlsx")
            df.to_excel(excel_path, index=False)
            
            logger.info(f"Excel report saved to {excel_path}")
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error patching report: {e}")
        logger.error(traceback.format_exc())
        return False

def report_audit_fill_gaps(date_str: str) -> Dict[str, Any]:
    """
    Main function to audit reports and fill gaps
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Audit results
    """
    logger.info(f"Running report audit and gap filling for {date_str}")
    
    try:
        # Analyze excluded drivers
        analysis = analyze_excluded_drivers(date_str)
        
        # Save analysis to file
        analysis_path = Path(f"reports/audit/exclusion_analysis_{date_str}.json")
        os.makedirs(analysis_path.parent, exist_ok=True)
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
            
        logger.info(f"Analysis saved to {analysis_path}")
        
        # Patch report with exclusions
        if patch_report_with_exclusions(date_str, analysis):
            analysis['patched'] = True
        else:
            analysis['patched'] = False
            
        return analysis
        
    except Exception as e:
        logger.error(f"Error in report_audit_fill_gaps: {e}")
        logger.error(traceback.format_exc())
        return {
            'date': date_str,
            'error': str(e),
            'patched': False
        }

def print_analysis_summary(analysis: Dict[str, Any]):
    """Print a summary of the analysis"""
    print(f"\nExcluded Driver Analysis for {analysis['date']}:")
    print("=" * 70)
    
    # Print exclusion statistics
    stats = analysis.get('stats', {})
    print(f"Total Excluded Drivers: {stats.get('total_excluded', 0)}")
    print(f"Unmatched Drivers with Telematics: {stats.get('unmatched_with_telematics', 0)}")
    print(f"StartTimeJob Drivers without Telematics: {stats.get('start_time_job_without_telematics', 0)}")
    print(f"Job Site Conflicts: {stats.get('job_site_conflicts', 0)}")
    print("-" * 70)
    
    # Print detailed exclusion analysis
    exclusion_analysis = analysis.get('exclusion_analysis', {})
    if exclusion_analysis:
        print("Excluded Driver Details:")
        for i, (driver, info) in enumerate(exclusion_analysis.items(), 1):
            sources = ", ".join(info['sources'])
            print(f"{i}. {driver.title()}:")
            print(f"   Sources: {sources}")
            print(f"   Reason: {info['reason']}")
            print(f"   Should be included as: {info['should_be_included_as']}")
            print()
    else:
        print("No excluded drivers found.")
    
    # Print patching status
    if analysis.get('patched', False):
        print("Report successfully patched with excluded drivers.")
    else:
        print("Failed to patch report with excluded drivers.")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python report_audit_fill_gaps.py <date>")
        print("Example: python report_audit_fill_gaps.py 2025-05-16")
        return
        
    date_str = sys.argv[1]
    
    # Run audit and gap filling
    analysis = report_audit_fill_gaps(date_str)
    
    # Print summary
    print_analysis_summary(analysis)

if __name__ == '__main__':
    main()