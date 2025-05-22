"""
Driver Classifier Agent (Development Version)

This agent analyzes driver activity data and classifies drivers based on their behavior,
location patterns, and schedule compliance. It provides detailed classification
with confidence scores and supporting evidence.

Part of the GENIUS CORE modular architecture.
"""
import logging
import json
from datetime import datetime, time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Classification confidence thresholds
HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.65
LOW_CONFIDENCE = 0.40

class DriverClassifierAgent:
    """Agent for classifying drivers based on activity and location data"""
    
    def __init__(self, config=None):
        """
        Initialize the Driver Classifier Agent
        
        Args:
            config (dict): Configuration parameters for the agent
        """
        self.config = config or {}
        self.validation_level = self.config.get('validation_level', 'standard')
        self.allow_incomplete_data = self.config.get('allow_incomplete_data', True)
        self.debug_mode = self.config.get('debug_mode', False)
        
        logger.info(f"Driver Classifier Agent initialized with validation level: {self.validation_level}")
        
    def classify_driver(self, driver_data, job_site_data=None, time_rules=None):
        """
        Classify a driver based on their activity data
        
        Args:
            driver_data (dict): Driver activity data
            job_site_data (dict): Job site reference data
            time_rules (dict): Time-based classification rules
            
        Returns:
            dict: Classification results with confidence scores
        """
        if not driver_data:
            logger.warning("No driver data provided for classification")
            return self._generate_empty_classification()
            
        # Extract key data for classification
        name = driver_data.get('name', 'Unknown')
        job_site = driver_data.get('job_site', 'Unknown')
        start_time = driver_data.get('start_time', 'Unknown')
        end_time = driver_data.get('end_time', 'Unknown')
        
        logger.debug(f"Classifying driver: {name}, Job Site: {job_site}, Times: {start_time}-{end_time}")
        
        # Initialize classification result
        classification = {
            'driver_name': name,
            'job_site': job_site,
            'classification': 'unknown',
            'confidence': 0.0,
            'evidence': [],
            'flags': [],
            'validation_level': self.validation_level,
            'processed_at': datetime.now().isoformat()
        }
        
        # Apply classification logic
        if start_time == 'Unknown' or end_time == 'Unknown':
            if self.allow_incomplete_data:
                classification['classification'] = 'unverified'
                classification['confidence'] = LOW_CONFIDENCE * 0.5
                classification['evidence'].append("Incomplete time data")
                classification['flags'].append("missing_time_data")
            else:
                classification['classification'] = 'invalid'
                classification['confidence'] = 0.0
                classification['evidence'].append("Missing required time data")
                classification['flags'].append("insufficient_data")
            
            return classification
            
        # Determine classification based on time data
        time_classification = self._classify_by_time(start_time, end_time, time_rules)
        classification['classification'] = time_classification['status']
        classification['confidence'] = time_classification['confidence']
        classification['evidence'].extend(time_classification['evidence'])
        
        # Apply location validation if job site data is available
        if job_site_data and job_site in job_site_data:
            location_validation = self._validate_location(driver_data, job_site_data[job_site])
            
            # Adjust classification based on location validation
            if location_validation['verified']:
                classification['evidence'].append(f"Location verified at {job_site}")
                classification['confidence'] = min(1.0, classification['confidence'] + 0.15)
            else:
                classification['flags'].append("location_mismatch")
                classification['evidence'].append(location_validation['reason'])
                classification['confidence'] = max(0.0, classification['confidence'] - 0.25)
        
        # Apply final confidence-based adjustments
        if classification['confidence'] >= HIGH_CONFIDENCE:
            classification['validation_level'] = 'high'
        elif classification['confidence'] >= MEDIUM_CONFIDENCE:
            classification['validation_level'] = 'medium'
        else:
            classification['validation_level'] = 'low'
            
        return classification
        
    def batch_classify_drivers(self, drivers_data, job_sites_data=None, time_rules=None):
        """
        Classify multiple drivers in batch mode
        
        Args:
            drivers_data (list): List of driver activity data
            job_sites_data (dict): Job site reference data
            time_rules (dict): Time-based classification rules
            
        Returns:
            list: Classification results for all drivers
        """
        results = []
        
        if not drivers_data:
            logger.warning("No drivers data provided for batch classification")
            return results
            
        logger.info(f"Batch classifying {len(drivers_data)} drivers")
        
        # Convert job_sites_data list to dict for easier lookup if needed
        job_sites_dict = {}
        if job_sites_data and isinstance(job_sites_data, list):
            for site in job_sites_data:
                site_name = site.get('name')
                if site_name:
                    job_sites_dict[site_name] = site
        elif job_sites_data and isinstance(job_sites_data, dict):
            job_sites_dict = job_sites_data
            
        # Process each driver
        for driver in drivers_data:
            if isinstance(driver, dict):
                result = self.classify_driver(driver, job_sites_dict, time_rules)
                results.append(result)
            else:
                logger.warning(f"Invalid driver data format: {type(driver)}")
                
        # Generate summary statistics
        classification_counts = {}
        for result in results:
            classification = result.get('classification', 'unknown')
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
            
        logger.info(f"Classification summary: {json.dumps(classification_counts)}")
        
        return results
        
    def _classify_by_time(self, start_time, end_time, time_rules=None):
        """
        Classify driver based on start and end times
        
        Args:
            start_time (str): Driver start time
            end_time (str): Driver end time
            time_rules (dict): Custom time rules
            
        Returns:
            dict: Classification result with status, confidence and evidence
        """
        # Default time rules if none provided
        if not time_rules:
            time_rules = {
                'work_start': '07:00',
                'work_end': '17:00',
                'late_threshold': 15,  # minutes
                'early_end_threshold': 15,  # minutes
            }
            
        result = {
            'status': 'unknown',
            'confidence': 0.0,
            'evidence': []
        }
        
        try:
            # Parse start and end times
            start_dt = self._parse_time(start_time)
            end_dt = self._parse_time(end_time)
            work_start = self._parse_time(time_rules['work_start'])
            work_end = self._parse_time(time_rules['work_end'])
            
            if not start_dt or not end_dt:
                result['status'] = 'unknown'
                result['confidence'] = LOW_CONFIDENCE * 0.2
                result['evidence'].append("Could not parse time values")
                return result
                
            # Calculate minutes late
            minutes_late = 0
            if start_dt > work_start:
                minutes_late = (start_dt.hour - work_start.hour) * 60 + (start_dt.minute - work_start.minute)
                
            # Calculate minutes early end
            minutes_early = 0
            if end_dt < work_end:
                minutes_early = (work_end.hour - end_dt.hour) * 60 + (work_end.minute - end_dt.minute)
                
            # Determine status
            late_threshold = time_rules.get('late_threshold', 15)
            early_end_threshold = time_rules.get('early_end_threshold', 15)
            
            if minutes_late > late_threshold:
                result['status'] = 'late'
                result['confidence'] = MEDIUM_CONFIDENCE + (min(minutes_late, 120) / 240)  # Max boost for 2+ hours late
                result['evidence'].append(f"Started {minutes_late} minutes after work start time")
            elif minutes_early > early_end_threshold:
                result['status'] = 'early_end'
                result['confidence'] = MEDIUM_CONFIDENCE + (min(minutes_early, 120) / 240)  # Max boost for 2+ hours early
                result['evidence'].append(f"Ended {minutes_early} minutes before work end time")
            else:
                result['status'] = 'on_time'
                result['confidence'] = HIGH_CONFIDENCE
                result['evidence'].append("Within acceptable time thresholds")
                
            # Additional evidence
            result['evidence'].append(f"Start: {start_time}, End: {end_time}")
            result['evidence'].append(f"Work hours: {time_rules['work_start']} - {time_rules['work_end']}")
            
        except Exception as e:
            logger.error(f"Error in time classification: {str(e)}")
            result['status'] = 'error'
            result['confidence'] = 0.0
            result['evidence'].append(f"Error in classification: {str(e)}")
            
        return result
        
    def _validate_location(self, driver_data, job_site_data):
        """
        Validate driver location against job site data
        
        Args:
            driver_data (dict): Driver activity data
            job_site_data (dict): Job site reference data
            
        Returns:
            dict: Validation result
        """
        result = {
            'verified': False,
            'reason': "Location could not be verified"
        }
        
        # Extract location data
        driver_location = driver_data.get('location')
        job_site_location = job_site_data.get('location')
        
        if not driver_location or not job_site_location:
            result['reason'] = "Missing location data for validation"
            return result
            
        # Simple name-based matching in development mode
        driver_job_site = driver_data.get('job_site', '').lower()
        reference_job_site = job_site_data.get('name', '').lower()
        
        if driver_job_site and reference_job_site and driver_job_site == reference_job_site:
            result['verified'] = True
            result['reason'] = "Job site name matches"
            
        return result
        
    def _parse_time(self, time_str):
        """
        Parse time string to time object
        
        Args:
            time_str (str): Time string to parse
            
        Returns:
            time: Parsed time object or None if invalid
        """
        if not time_str or time_str == 'Unknown':
            return None
            
        formats = [
            '%H:%M',
            '%H:%M:%S',
            '%I:%M %p',
            '%I:%M:%S %p',
            '%I:%M%p',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
                
        logger.warning(f"Could not parse time string: {time_str}")
        return None
        
    def _generate_empty_classification(self):
        """
        Generate an empty classification result
        
        Returns:
            dict: Empty classification result
        """
        return {
            'driver_name': 'Unknown',
            'job_site': 'Unknown',
            'classification': 'invalid',
            'confidence': 0.0,
            'evidence': ["No data provided for classification"],
            'flags': ["no_data"],
            'validation_level': 'none',
            'processed_at': datetime.now().isoformat()
        }


# Standalone usage
if __name__ == "__main__":
    # Test the agent with sample data
    sample_driver = {
        'name': 'John Doe',
        'job_site': 'Main Street Project',
        'start_time': '07:30',
        'end_time': '16:45'
    }
    
    sample_job_site = {
        'Main Street Project': {
            'name': 'Main Street Project',
            'location': 'Main Street',
            'work_start': '07:00',
            'work_end': '17:00'
        }
    }
    
    agent = DriverClassifierAgent({'validation_level': 'high', 'debug_mode': True})
    result = agent.classify_driver(sample_driver, sample_job_site)
    
    print(json.dumps(result, indent=2))