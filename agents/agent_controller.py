"""
Agent Controller

This module provides a unified interface to access all GENIUS CORE agents
and coordinate their interactions in the data processing pipeline.
"""
import logging
import json
import time
import os
from datetime import datetime

# We'll import yaml only when needed to avoid dependency issues

# Import all agent modules
from agents.driver_classifier_agent import handle as driver_classifier
from agents.geo_validator_agent import handle as geo_validator
from agents.report_generator_agent import handle as report_generator
from agents.output_formatter_agent import handle as output_formatter

# Define agent mapping
AGENT_MAPPING = {
    "driver_classifier": driver_classifier,
    "geo_validator": geo_validator,
    "report_generator": report_generator,
    "output_formatter": output_formatter
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentController:
    """Controller for coordinating agent interactions"""
    
    def __init__(self, config_path=None):
        """
        Initialize the agent controller
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.mode = self.config.get('mode', 'development')
        self.feature_flags = self.config.get('feature_flags', {})
        
        # Enable parallel multi-agent processing
        self.parallel_mode = True
        self.max_concurrent_agents = 4
        self.desktop_sync_safe = True
        
        # Configure logging based on config
        log_level = self.config.get('logging_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        logger.info(f"Agent Controller initialized in {self.mode.upper()} mode")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
    
    def _load_config(self, config_path):
        """
        Load configuration from YAML file
        
        Args:
            config_path (str): Path to configuration file
            
        Returns:
            dict: Configuration data
        """
        default_config = {
            'mode': 'development',
            'logging_level': 'INFO',
            'feature_flags': {
                'enable_driver_chunking': False,
                'enable_async_tasks': False
            }
        }
        
        if not config_path:
            # Try to load based on environment
            if os.environ.get('TRAXORA_ENV') == 'production':
                config_path = 'prod_config.yaml'
            else:
                config_path = 'dev_config.yaml'
        
        # First check if the file exists to avoid YAML import errors
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file {config_path} not found, using defaults")
            return default_config
            
        try:
            # Only import yaml if we need it
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except ImportError:
            logger.warning("YAML module not available, using default configuration")
            return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
    
    def process_driver_data(self, data, filter_options=None):
        """
        Process driver data through the complete pipeline
        
        Args:
            data (list/dict): Driver data to process
            filter_options (dict): Filtering options
            
        Returns:
            dict: Processed results and report
        """
        start_time = time.time()
        logger.info(f"Starting driver data processing pipeline with {len(data) if isinstance(data, list) else 1} records")
        
        try:
            # Step 1: Classify drivers
            logger.info("Step 1: Classifying drivers")
            classified_data = driver_classifier(data)
            
            # Step 2: Validate locations
            logger.info("Step 2: Validating locations")
            # Extract job sites from data if available
            job_sites = {}
            if isinstance(data, list):
                for item in data:
                    site = item.get('job_site')
                    if site and isinstance(site, dict):
                        job_sites[site.get('id')] = site
            
            validated_data = geo_validator(classified_data['classified_drivers'], job_sites)
            
            # Step 3: Generate report
            logger.info("Step 3: Generating report")
            report_data = {
                'drivers': classified_data['classified_drivers'],
                'validation': validated_data,
                'data_sources': ['driver_data', 'location_data']
            }
            
            report_config = {
                'report_type': 'driver',
                'include_details': True,
                'filter_zeros': self.config.get('filter_zeros', True)
            }
            
            report = report_generator(report_data, report_config)
            
            # Step 4: Format output
            logger.info("Step 4: Formatting output")
            output_format = filter_options.get('format', 'json') if filter_options else 'json'
            formatted_output = output_formatter(report, output_format)
            
            processing_time = time.time() - start_time
            
            # Log the complete processing
            self._log_pipeline_usage({
                'records_processed': len(data) if isinstance(data, list) else 1,
                'output_format': output_format,
                'processing_time': round(processing_time, 3)
            })
            
            return {
                'success': True,
                'processing_time': round(processing_time, 3),
                'report': report,
                'formatted_output': formatted_output['formatted_data'] if 'formatted_data' in formatted_output else None
            }
        
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': round(time.time() - start_time, 3)
            }
    
    def classify_drivers(self, data):
        """
        Standalone driver classification
        
        Args:
            data (list/dict): Driver data to classify
            
        Returns:
            dict: Classification results
        """
        try:
            return driver_classifier(data)
        except Exception as e:
            logger.error(f"Error in driver classification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_locations(self, data, job_sites=None):
        """
        Standalone location validation
        
        Args:
            data (list/dict): Location data to validate
            job_sites (list/dict): Job site reference data
            
        Returns:
            dict: Validation results
        """
        try:
            return geo_validator(data, job_sites)
        except Exception as e:
            logger.error(f"Error in location validation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_report(self, data, config=None):
        """
        Standalone report generation
        
        Args:
            data (dict): Data for report generation
            config (dict): Report configuration
            
        Returns:
            dict: Generated report
        """
        try:
            return report_generator(data, config)
        except Exception as e:
            logger.error(f"Error in report generation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def format_output(self, data, format_type='json', config=None):
        """
        Standalone output formatting
        
        Args:
            data (dict): Data to format
            format_type (str): Output format type
            config (dict): Formatting configuration
            
        Returns:
            dict: Formatted output
        """
        try:
            return output_formatter(data, format_type, config)
        except Exception as e:
            logger.error(f"Error in output formatting: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _log_pipeline_usage(self, stats):
        """
        Log pipeline usage statistics
        
        Args:
            stats (dict): Pipeline statistics
        """
        usage_log = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "pipeline": "driver_processing",
            **stats
        }
        
        logger.info(f"Pipeline usage: {json.dumps(usage_log)}")
        
        try:
            with open("logs/pipeline_usage.log", "a") as f:
                f.write(json.dumps(usage_log) + "\n")
        except Exception as e:
            logger.warning(f"Could not write to pipeline usage log: {e}")

# Singleton instance
_instance = None

def get_controller(config_path=None):
    """
    Get the agent controller instance
    
    Args:
        config_path (str): Optional path to configuration file
        
    Returns:
        AgentController: Agent controller instance
    """
    global _instance
    if _instance is None:
        _instance = AgentController(config_path)
    return _instance
    
def handle(agent_name, data, config=None):
    """
    Unified interface to handle requests to any agent
    
    Args:
        agent_name (str): Name of the agent to use
        data (any): Data to process
        config (dict): Optional configuration
        
    Returns:
        dict: Results from the agent
    """
    if agent_name not in AGENT_MAPPING:
        logger.error(f"Unknown agent: {agent_name}")
        return {
            "success": False,
            "error": f"Unknown agent: {agent_name}",
            "available_agents": list(AGENT_MAPPING.keys())
        }
        
    try:
        logger.info(f"Routing request to {agent_name} agent")
        agent_func = AGENT_MAPPING[agent_name]
        if config:
            return agent_func(data, config)
        else:
            return agent_func(data)
    except Exception as e:
        logger.error(f"Error in {agent_name} agent: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": agent_name
        }

if __name__ == "__main__":
    # Example usage
    controller = get_controller()
    
    # Test data
    test_data = [
        {"driver_id": 1, "name": "John Doe", "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": 101},
        {"driver_id": 2, "name": "Jane Smith", "vehicle_type": "sedan", "usage_type": "on-road", "jobsite_id": 102},
        {"driver_id": 3, "name": "Bob Johnson", "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": 101}
    ]
    
    # Process through pipeline
    result = controller.process_driver_data(test_data)
    
    # Print summary
    if result['success']:
        print(f"Successfully processed {len(test_data)} records in {result['processing_time']} seconds")
        print("Report summary:")
        if 'report' in result and 'summary' in result['report']:
            for key, value in result['report']['summary'].items():
                print(f"  {key}: {value}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")