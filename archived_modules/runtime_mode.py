"""
TRAXORA Runtime Mode Configuration

This module provides runtime environment detection and configuration for the TRAXORA system,
enabling dual-mode operation (development vs. production).
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_dev_mode():
    """
    Determine if the system is running in development mode.
    
    Returns:
        bool: True if in development mode, False if in production mode
    """
    # Check environment variable first (highest priority)
    env_mode = os.getenv("REPLIT_PROFILE", "dev")
    
    # Check for .replit configuration file
    try:
        with open('.replit', 'r') as f:
            replit_config = f.read()
            if 'profile = "prod"' in replit_config:
                return False
    except Exception:
        # If file doesn't exist or can't be read, use environment variable
        pass
    
    # Default to development mode unless explicitly set to production
    return env_mode == "dev"

def get_runtime_config():
    """
    Get runtime configuration based on the current mode.
    
    Returns:
        dict: Configuration settings for current runtime mode
    """
    dev_mode = is_dev_mode()
    
    if dev_mode:
        logger.info("TRAXORA running in DEVELOPMENT mode")
        return {
            'mode': 'dev',
            'log_level': logging.DEBUG,
            'strict_validation': False,
            'allow_experimental': True,
            'timeout_seconds': 30,
            'fallback_enabled': True,
            'agent_path': 'dev/agents',
            'validation_hooks': False,
            'verbose_logs': True,
        }
    else:
        logger.info("TRAXORA running in PRODUCTION mode")
        return {
            'mode': 'prod',
            'log_level': logging.INFO,
            'strict_validation': True,
            'allow_experimental': False,
            'timeout_seconds': 15,
            'fallback_enabled': True,
            'agent_path': 'prod/agents',
            'validation_hooks': True,
            'verbose_logs': False,
        }

# Expose configuration as a module-level variable for easy imports
config = get_runtime_config()

def setup_logging():
    """Configure logging based on runtime mode"""
    log_level = config['log_level']
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Silence some verbose libraries in production
    if not config['verbose_logs']:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

def load_appropriate_agents():
    """
    Load the appropriate agent function modules based on runtime mode.
    
    Returns:
        dict: Dictionary of loaded agent modules with their functions
    """
    agents = {}
    
    try:
        if config['mode'] == 'dev':
            # Import development agent functions
            import dev.agents.driver_classifier as dev_driver_classifier
            import dev.agents.geo_validator as dev_geo_validator
            import dev.agents.report_generator as dev_report_generator
            
            agents = {
                'driver_classifier': {
                    'classify_driver': dev_driver_classifier.classify_driver,
                    'batch_classify_drivers': dev_driver_classifier.batch_classify_drivers,
                    'strict': False
                },
                'geo_validator': {
                    'validate_location': dev_geo_validator.validate_location,
                    'batch_validate_locations': dev_geo_validator.batch_validate_locations,
                    'strict': False
                },
                'report_generator': {
                    'generate_driver_report': dev_report_generator.generate_driver_report,
                    'generate_jobsite_report': dev_report_generator.generate_jobsite_report,
                    'export_report_to_json': dev_report_generator.export_report_to_json,
                    'strict': False
                }
            }
            logger.info("Loaded development agent function modules")
        else:
            # Import production agent functions
            import prod.agents.driver_classifier as prod_driver_classifier
            import prod.agents.geo_validator as prod_geo_validator
            import prod.agents.report_generator as prod_report_generator
            
            agents = {
                'driver_classifier': {
                    'classify_driver': prod_driver_classifier.classify_driver,
                    'batch_classify_drivers': prod_driver_classifier.batch_classify_drivers,
                    'strict': True
                },
                'geo_validator': {
                    'validate_location': prod_geo_validator.validate_location,
                    'batch_validate_locations': prod_geo_validator.batch_validate_locations,
                    'strict': True
                },
                'report_generator': {
                    'generate_driver_report': prod_report_generator.generate_driver_report,
                    'generate_jobsite_report': prod_report_generator.generate_jobsite_report,
                    'export_report_to_json': prod_report_generator.export_report_to_json,
                    'strict': True
                }
            }
            logger.info("Loaded production agent function modules")
    except ImportError as e:
        logger.warning(f"Could not load all agents: {str(e)}")
        logger.info("Using available agents only")
    
    return agents

# Initialize logging when module is imported
setup_logging()