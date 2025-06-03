"""
TRAXORA GENIUS CORE | Driver Pipeline

This is the main driver pipeline module that orchestrates all components:
- Processes data from multiple sources (DrivingHistory, ActivityDetail, AssetTimeOnSite)
- Validates locations against job site geofences
- Classifies drivers based on workbook logic
- Generates comprehensive reports with Activity Detail metrics

The pipeline implements strict validation and cross-referencing from all data sources
with full traceability for every decision.
"""
import os
import logging
import json
from datetime import datetime, date, time
import traceback
from typing import Dict, List, Tuple, Optional, Any, Union

# Import utility modules
from utils.data_ingestor import DataIngestor
from utils.driver_classifier import classify_driver, get_status_counts, get_time_statistics
from utils.geo_validator import validate_driver_locations
from utils.report_generator import ReportGenerator
from utils.output_formatter import OutputFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DriverPipeline:
    """Main driver pipeline for the GENIUS CORE system"""
    
    def __init__(self, config=None):
        """
        Initialize the driver pipeline
        
        Args:
            config (dict, optional): Configuration settings
        """
        self.config = config or {}
        self.date_str = self.config.get('date_str', datetime.now().strftime('%Y-%m-%d'))
        
        # Parse target date
        self.target_date = datetime.now().date()
        if self.date_str:
            try:
                self.target_date = datetime.strptime(self.date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date format: {self.date_str}, using current date")
                self.date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Set data paths
        self.data_dir = self.config.get('data_dir', 'data')
        self.driving_history_path = self.config.get('driving_history_path', 
                                                   os.path.join(self.data_dir, 'driving_history'))
        self.activity_detail_path = self.config.get('activity_detail_path',
                                                   os.path.join(self.data_dir, 'activity_detail'))
        self.asset_time_path = self.config.get('asset_time_path',
                                              os.path.join(self.data_dir, 'asset_time'))
        
        # Set output paths
        self.output_dir = self.config.get('output_dir', os.path.join('reports', self.date_str))
        
        # Initialize components
        self.data_ingestor = DataIngestor()
        
        # Job site definitions with geofences
        self.job_sites = self.config.get('job_sites', [])
        
        # Scheduled times for drivers (from equipment billing sheet)
        self.scheduled_times = self.config.get('scheduled_times', {})
        
        # Job assignments
        self.job_assignments = self.config.get('job_assignments', {})
        
        # Initialize results storage
        self.results = {
            'date': self.date_str,
            'ingestion_results': {},
            'classification_results': {},
            'report_files': {}
        }
        
        # Initialize traceable log
        self.genius_core_log = []
        
        # Create required directories
        os.makedirs(self.driving_history_path, exist_ok=True)
        os.makedirs(self.activity_detail_path, exist_ok=True)
        os.makedirs(self.asset_time_path, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def log_genius_core_event(self, event_type, details=None):
        """
        Log an event to the GENIUS CORE timeline
        
        Args:
            event_type (str): Type of event
            details (dict, optional): Event details
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details or {}
        }
        self.genius_core_log.append(event)
        logger.info(f"GENIUS CORE: {event_type} - {details}")
    
    def ingest_data(self):
        """
        Ingest all data from various sources
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.log_genius_core_event('INGESTION_START', {
                'driving_history_path': self.driving_history_path,
                'activity_detail_path': self.activity_detail_path,
                'asset_time_path': self.asset_time_path
            })
            
            # Process driving history data
            driving_history_results = self.data_ingestor.ingest_directory(
                self.driving_history_path, 'driving_history')
            
            # Process activity detail data
            activity_detail_results = self.data_ingestor.ingest_directory(
                self.activity_detail_path, 'activity_detail')
            
            # Process asset time data
            asset_time_results = self.data_ingestor.ingest_directory(
                self.asset_time_path, 'asset_time')
            
            # Store ingestion results
            self.results['ingestion_results'] = {
                'driving_history': driving_history_results,
                'activity_detail': activity_detail_results,
                'asset_time': asset_time_results
            }
            
            # Get metrics
            metrics = self.data_ingestor.get_metrics()
            self.results['metrics'] = metrics
            
            # Log summary
            total_records = (
                metrics['driving_history']['valid_records'] +
                metrics['activity_detail']['valid_records'] +
                metrics['asset_time']['valid_records']
            )
            
            self.log_genius_core_event('INGESTION_COMPLETE', {
                'total_records': total_records,
                'driving_history_records': metrics['driving_history']['valid_records'],
                'activity_detail_records': metrics['activity_detail']['valid_records'],
                'asset_time_records': metrics['asset_time']['valid_records']
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error during data ingestion: {e}")
            logger.error(traceback.format_exc())
            self.log_genius_core_event('INGESTION_ERROR', {
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return False
    
    def classify_drivers(self):
        """
        Classify all drivers based on their data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.log_genius_core_event('CLASSIFICATION_START')
            
            # Get all driver data
            all_drivers = self.data_ingestor.get_all_drivers()
            
            # Process each driver
            classification_results = {}
            
            for normalized_name, driver_data in all_drivers.items():
                # Get driver's start/end times
                times = self.data_ingestor.get_driver_start_end_times(
                    normalized_name=normalized_name)
                
                # Get driver's assigned job (if any)
                assigned_job = None
                if normalized_name in self.job_assignments:
                    assigned_job = self.job_assignments[normalized_name]
                
                # Get scheduled times (if any)
                scheduled_start = None
                scheduled_end = None
                
                if normalized_name in self.scheduled_times:
                    scheduled_times = self.scheduled_times[normalized_name]
                    scheduled_start = scheduled_times.get('start')
                    scheduled_end = scheduled_times.get('end')
                
                # Get actual start/end times
                actual_start = None
                actual_end = None
                
                if times:
                    actual_start = times.get('actual_start_time')
                    actual_end = times.get('actual_end_time')
                
                # Validate locations against job sites
                driver_locations = []
                for record in driver_data.get('driving_records', []):
                    if record.get('latitude') and record.get('longitude'):
                        driver_locations.append({
                            'timestamp': record.get('timestamp'),
                            'latitude': record.get('latitude'),
                            'longitude': record.get('longitude')
                        })
                
                geo_validation = None
                if driver_locations and self.job_sites:
                    geo_validation = validate_driver_locations(
                        driver_locations, self.job_sites, assigned_job)
                
                # Classify driver
                classification = classify_driver(
                    driver_data=driver_data,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                    job_site=next((js for js in self.job_sites if js.get('job_number') == assigned_job), None),
                    job_assignments=self.job_assignments,
                    asset_data=None,  # Not used in this version
                    geo_validations=geo_validation.get('all_validations', []) if geo_validation else None
                )
                
                # Update driver data with additional info
                driver_data['scheduled_start'] = scheduled_start
                driver_data['scheduled_end'] = scheduled_end
                driver_data['assigned_job'] = assigned_job
                
                if geo_validation and geo_validation.get('closest_job_site'):
                    driver_data['actual_job'] = geo_validation.get('closest_job_site')
                
                # Store classification results
                classification_results[normalized_name] = {
                    'driver_data': driver_data,
                    'classification': classification,
                    'geo_validation': geo_validation
                }
                
                # Log classification
                self.log_genius_core_event('DRIVER_CLASSIFIED', {
                    'driver_name': driver_data.get('name', 'Unknown'),
                    'normalized_name': normalized_name,
                    'status': classification.get('status', 'Unknown'),
                    'reasons': classification.get('reasons', []),
                    'validation_score': classification.get('validation_score', 0)
                })
            
            # Store classification results
            self.results['classification_results'] = classification_results
            
            # Calculate summary statistics
            classifications = [data['classification'] for data in classification_results.values()]
            status_counts = get_status_counts(classifications)
            time_stats = get_time_statistics(classifications)
            
            self.results['status_counts'] = status_counts
            self.results['time_stats'] = time_stats
            
            # Log summary
            self.log_genius_core_event('CLASSIFICATION_COMPLETE', {
                'total_drivers': status_counts.get('total', 0),
                'on_time': status_counts.get('on_time', 0),
                'late': status_counts.get('late', 0),
                'early_end': status_counts.get('early_end', 0),
                'not_on_job': status_counts.get('not_on_job', 0),
                'unknown': status_counts.get('unknown', 0)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error during driver classification: {e}")
            logger.error(traceback.format_exc())
            self.log_genius_core_event('CLASSIFICATION_ERROR', {
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return False
    
    def generate_reports(self):
        """
        Generate all reports
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.log_genius_core_event('REPORT_GENERATION_START')
            
            # Initialize report generator
            report_generator = ReportGenerator(
                date_str=self.date_str,
                output_dir=self.output_dir
            )
            
            # Get classification results
            classification_results = self.results.get('classification_results', {})
            
            # Add driver data to report
            for normalized_name, data in classification_results.items():
                report_generator.add_driver_data(
                    data['driver_data'],
                    data['classification']
                )
            
            # Generate reports
            json_path = report_generator.save_json_report()
            excel_path = report_generator.save_excel_report()
            categorized_paths = report_generator.generate_categorized_reports()
            
            # Store report paths
            self.results['report_files']['json'] = json_path
            self.results['report_files']['excel'] = excel_path
            self.results['report_files'].update(categorized_paths)
            
            # Initialize output formatter
            output_formatter = OutputFormatter(
                report_data=report_generator.report_data,
                date_str=self.date_str,
                output_dir=self.output_dir
            )
            
            # Generate formatted reports
            pdf_path = output_formatter.create_pdf_report()
            comprehensive_excel_path = output_formatter.create_comprehensive_excel()
            pmr_paths = output_formatter.create_pmr_reports()
            
            # Store formatted report paths
            self.results['report_files']['pdf'] = pdf_path
            self.results['report_files']['comprehensive_excel'] = comprehensive_excel_path
            for key, path in pmr_paths.items():
                self.results['report_files'][f'pmr_{key}_pdf'] = path
            
            # Generate summary
            summary = report_generator.report_data.get('summary', {})
            
            # Log completion
            self.log_genius_core_event('REPORT_GENERATION_COMPLETE', {
                'report_files': list(self.results['report_files'].keys()),
                'total_drivers': summary.get('total_drivers', 0),
                'on_time': summary.get('on_time', 0),
                'late': summary.get('late', 0),
                'early_end': summary.get('early_end', 0),
                'not_on_job': summary.get('not_on_job', 0)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error during report generation: {e}")
            logger.error(traceback.format_exc())
            self.log_genius_core_event('REPORT_GENERATION_ERROR', {
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return False
    
    def save_genius_core_log(self):
        """
        Save the GENIUS CORE log to a file
        
        Returns:
            str: Path to the log file
        """
        log_path = os.path.join(self.output_dir, f"genius_core_log_{self.date_str}.json")
        
        with open(log_path, 'w') as f:
            json.dump(self.genius_core_log, f, indent=2)
        
        logger.info(f"Saved GENIUS CORE log to {log_path}")
        return log_path
    
    def run(self):
        """
        Run the complete pipeline
        
        Returns:
            dict: Pipeline results
        """
        try:
            self.log_genius_core_event('PIPELINE_START', {
                'date': self.date_str,
                'target_date': self.target_date.isoformat(),
                'config': self.config
            })
            
            # Ingest data
            ingest_success = self.ingest_data()
            if not ingest_success:
                logger.error("Data ingestion failed, pipeline aborted")
                self.log_genius_core_event('PIPELINE_ABORTED', {
                    'reason': 'Data ingestion failed'
                })
                return self.results
            
            # Classify drivers
            classify_success = self.classify_drivers()
            if not classify_success:
                logger.error("Driver classification failed, pipeline aborted")
                self.log_genius_core_event('PIPELINE_ABORTED', {
                    'reason': 'Driver classification failed'
                })
                return self.results
            
            # Generate reports
            report_success = self.generate_reports()
            if not report_success:
                logger.error("Report generation failed, pipeline aborted")
                self.log_genius_core_event('PIPELINE_ABORTED', {
                    'reason': 'Report generation failed'
                })
                return self.results
            
            # Save GENIUS CORE log
            log_path = self.save_genius_core_log()
            self.results['genius_core_log'] = log_path
            
            # Log completion
            self.log_genius_core_event('PIPELINE_COMPLETE', {
                'classification_count': len(self.results.get('classification_results', {})),
                'report_files': list(self.results.get('report_files', {}).keys())
            })
            
            return self.results
            
        except Exception as e:
            logger.error(f"Error in pipeline execution: {e}")
            logger.error(traceback.format_exc())
            self.log_genius_core_event('PIPELINE_ERROR', {
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Save log even on error
            log_path = self.save_genius_core_log()
            self.results['genius_core_log'] = log_path
            
            return self.results


def run_pipeline(date_str=None, config=None):
    """
    Run the driver pipeline for a specific date
    
    Args:
        date_str (str, optional): Date string in YYYY-MM-DD format
        config (dict, optional): Configuration settings
    
    Returns:
        dict: Pipeline results
    """
    # Use provided config or create default
    pipeline_config = config or {}
    
    # Set date if provided
    if date_str:
        pipeline_config['date_str'] = date_str
    
    # Initialize pipeline
    pipeline = DriverPipeline(pipeline_config)
    
    # Run pipeline
    results = pipeline.run()
    
    return results


if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the driver reporting pipeline')
    parser.add_argument('--date', type=str, help='Date to process (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--driving-history', type=str, help='Path to driving history directory')
    parser.add_argument('--activity-detail', type=str, help='Path to activity detail directory')
    parser.add_argument('--asset-time', type=str, help='Path to asset time directory')
    parser.add_argument('--output-dir', type=str, help='Path to output directory')
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
            sys.exit(1)
    
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
    
    # Run pipeline
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