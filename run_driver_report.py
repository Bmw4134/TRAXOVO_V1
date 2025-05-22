#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Report CLI

This script provides a command-line interface to run the driver reporting pipeline.
It also includes sample data to demonstrate the pipeline functionality.
"""
import os
import json
import argparse
import logging
from datetime import datetime, time

from driver_pipeline import DriverPipeline, run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample job sites with geofences
SAMPLE_JOB_SITES = [
    {
        'job_number': '2024-001',
        'name': 'Downtown Project',
        'geofence': {
            'center_lat': 32.7767,
            'center_lon': -96.7970,
            'radius_km': 1.0
        }
    },
    {
        'job_number': '2024-002',
        'name': 'Highway Expansion',
        'geofence': {
            'center_lat': 32.8942,
            'center_lon': -97.0375,
            'radius_km': 2.0
        }
    },
    {
        'job_number': '2024-003',
        'name': 'North Bridge Repair',
        'geofence': {
            'center_lat': 33.0153,
            'center_lon': -96.9981,
            'radius_km': 0.5
        }
    }
]

# Sample scheduled times for drivers (HH:MM format)
SAMPLE_SCHEDULED_TIMES = {
    'john smith': {
        'start': time(7, 0),  # 7:00 AM
        'end': time(16, 0)    # 4:00 PM
    },
    'jane doe': {
        'start': time(7, 30), # 7:30 AM
        'end': time(16, 30)   # 4:30 PM
    },
    'robert johnson': {
        'start': time(8, 0),  # 8:00 AM
        'end': time(17, 0)    # 5:00 PM
    }
}

# Sample job assignments
SAMPLE_JOB_ASSIGNMENTS = {
    'john smith': '2024-001',
    'jane doe': '2024-002',
    'robert johnson': '2024-003'
}

def create_sample_config(date_str=None):
    """
    Create a sample configuration for the pipeline
    
    Args:
        date_str (str, optional): Date string in YYYY-MM-DD format
    
    Returns:
        dict: Configuration settings
    """
    # Use current date if not provided
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Create configuration
    config = {
        'date_str': date_str,
        'job_sites': SAMPLE_JOB_SITES,
        'scheduled_times': SAMPLE_SCHEDULED_TIMES,
        'job_assignments': SAMPLE_JOB_ASSIGNMENTS
    }
    
    return config

def setup_sample_data(data_dir='data'):
    """
    Create sample directory structure for testing
    
    Args:
        data_dir (str, optional): Base data directory
    
    Returns:
        tuple: Paths to data directories
    """
    # Create base directories
    driving_history_path = os.path.join(data_dir, 'driving_history')
    activity_detail_path = os.path.join(data_dir, 'activity_detail')
    asset_time_path = os.path.join(data_dir, 'asset_time')
    
    os.makedirs(driving_history_path, exist_ok=True)
    os.makedirs(activity_detail_path, exist_ok=True)
    os.makedirs(asset_time_path, exist_ok=True)
    
    # Return paths
    return (driving_history_path, activity_detail_path, asset_time_path)

def main():
    """
    Main function
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the driver reporting pipeline')
    parser.add_argument('--date', type=str, help='Date to process (YYYY-MM-DD)')
    parser.add_argument('--driving-history', type=str, help='Path to driving history file or directory')
    parser.add_argument('--activity-detail', type=str, help='Path to activity detail file or directory')
    parser.add_argument('--asset-time', type=str, help='Path to asset time file or directory')
    parser.add_argument('--output-dir', type=str, help='Output directory for reports')
    parser.add_argument('--sample', action='store_true', help='Use sample configuration')
    parser.add_argument('--save-config', type=str, help='Save configuration to file')
    args = parser.parse_args()
    
    # Create configuration
    config = {}
    
    # Use sample configuration if requested
    if args.sample:
        config = create_sample_config(args.date)
        logger.info("Using sample configuration")
    
    # Override config with command line arguments
    if args.date:
        config['date_str'] = args.date
    if args.driving_history:
        config['driving_history_path'] = args.driving_history
    if args.activity_detail:
        config['activity_detail_path'] = args.activity_detail
    if args.asset_time:
        config['asset_time_path'] = args.asset_time
    if args.output_dir:
        config['output_dir'] = args.output_dir
    
    # Save configuration if requested
    if args.save_config:
        with open(args.save_config, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        logger.info(f"Saved configuration to {args.save_config}")
    
    # Check for required data paths
    if not config.get('driving_history_path') and not args.sample:
        logger.info("No driving history path specified, setting up sample directory")
        driving_history_path, activity_detail_path, asset_time_path = setup_sample_data()
        config['driving_history_path'] = driving_history_path
        config['activity_detail_path'] = activity_detail_path
        config['asset_time_path'] = asset_time_path
    
    # Run pipeline
    logger.info("Running driver reporting pipeline")
    results = run_pipeline(config=config)
    
    # Print summary
    if 'status_counts' in results:
        print("\nDriver status summary:")
        for status, count in results['status_counts'].items():
            print(f"  {status}: {count}")
    
    if 'report_files' in results:
        print("\nGenerated report files:")
        for report_type, file_path in results['report_files'].items():
            print(f"  {report_type}: {file_path}")
    
    if results.get('genius_core_log'):
        print(f"\nGENIUS CORE log: {results['genius_core_log']}")

if __name__ == "__main__":
    main()