"""
Zone Schedule Rules Processor for TRAXOVO Live Field Test

Extracts attendance rules from PM sheet in Daily Driver Excel files.
Validates GPS and timecard activity against per-zone rules.
Output: zone_schedule_rules.json for /secure-attendance logic.
"""
import logging
import json
import pandas as pd
from datetime import datetime, time
from pathlib import Path

logger = logging.getLogger(__name__)

class ZoneScheduleRulesProcessor:
    def __init__(self):
        self.rules_file = "zone_schedule_rules.json"
        self.default_rules = {
            "default": {
                "start_time": "06:00",
                "end_time": "17:00", 
                "late_threshold_minutes": 15,
                "early_leave_threshold_minutes": 30,
                "zone_name": "Default Zone",
                "pm_manager": "System Default"
            }
        }
        
    def extract_pm_rules_from_excel(self, excel_file_path):
        """
        Extract zone rules from PM sheet in Daily Driver Excel file.
        
        Expected PM sheet structure:
        - Zone ID | Zone Name | Start Time | End Time | Late Threshold | Early Threshold | PM Manager
        """
        try:
            logger.info(f"Processing PM rules from: {excel_file_path}")
            
            # Read PM sheet from Excel file
            pm_df = pd.read_excel(excel_file_path, sheet_name='PM', skiprows=1)
            
            rules = {}
            
            for _, row in pm_df.iterrows():
                zone_id = str(row.get('Zone ID', '')).strip()
                zone_name = str(row.get('Zone Name', '')).strip()
                start_time = self._parse_time(row.get('Start Time', '06:00'))
                end_time = self._parse_time(row.get('End Time', '17:00'))
                late_threshold = int(row.get('Late Threshold', 15))
                early_threshold = int(row.get('Early Threshold', 30))
                pm_manager = str(row.get('PM Manager', 'Unknown')).strip()
                
                if zone_id and zone_name:
                    rules[zone_id] = {
                        "zone_name": zone_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "late_threshold_minutes": late_threshold,
                        "early_leave_threshold_minutes": early_threshold,
                        "pm_manager": pm_manager,
                        "extracted_date": datetime.now().isoformat()
                    }
                    
            logger.info(f"✅ Extracted {len(rules)} zone rules from PM sheet")
            return rules
            
        except Exception as e:
            logger.error(f"Failed to extract PM rules: {e}")
            return {}
    
    def _parse_time(self, time_value):
        """Parse time from various formats to HH:MM string"""
        if pd.isna(time_value):
            return "06:00"
            
        if isinstance(time_value, str):
            try:
                # Handle "6:00 AM" format
                if 'AM' in time_value.upper() or 'PM' in time_value.upper():
                    dt = datetime.strptime(time_value.upper().strip(), '%I:%M %p')
                    return dt.strftime('%H:%M')
                # Handle "06:00" format
                elif ':' in time_value:
                    return time_value.strip()
            except:
                pass
                
        # Handle datetime objects
        if hasattr(time_value, 'time'):
            return time_value.time().strftime('%H:%M')
            
        return "06:00"  # Default fallback
    
    def validate_attendance_against_rules(self, driver_data, zone_id):
        """
        Validate GPS and timecard activity against zone rules.
        
        Returns validation flags for secure-attendance logic.
        """
        rules = self.load_zone_rules()
        zone_rule = rules.get(zone_id, rules.get('default', self.default_rules['default']))
        
        validation = {
            'zone_id': zone_id,
            'zone_name': zone_rule.get('zone_name', 'Unknown Zone'),
            'rule_applied': True,
            'flags': []
        }
        
        try:
            # Parse driver times
            arrival_time = self._parse_driver_time(driver_data.get('start_time'))
            departure_time = self._parse_driver_time(driver_data.get('end_time'))
            
            # Parse zone rules
            expected_start = self._parse_rule_time(zone_rule['start_time'])
            expected_end = self._parse_rule_time(zone_rule['end_time'])
            
            # Validate arrival
            if arrival_time and expected_start:
                late_minutes = (arrival_time - expected_start).total_seconds() / 60
                if late_minutes > zone_rule['late_threshold_minutes']:
                    validation['flags'].append({
                        'type': 'LATE_ARRIVAL',
                        'minutes_late': int(late_minutes),
                        'threshold': zone_rule['late_threshold_minutes']
                    })
            
            # Validate departure
            if departure_time and expected_end:
                early_minutes = (expected_end - departure_time).total_seconds() / 60
                if early_minutes > zone_rule['early_leave_threshold_minutes']:
                    validation['flags'].append({
                        'type': 'EARLY_DEPARTURE', 
                        'minutes_early': int(early_minutes),
                        'threshold': zone_rule['early_leave_threshold_minutes']
                    })
                    
            # GPS vs Timecard validation
            has_gps = driver_data.get('gps_data', False)
            has_timecard = driver_data.get('timecard_data', False)
            
            if not has_gps and has_timecard:
                validation['flags'].append({'type': 'TIMECARD_NO_GPS'})
            elif has_gps and not has_timecard:
                validation['flags'].append({'type': 'GPS_NO_TIMECARD'})
            elif has_gps and has_timecard:
                validation['flags'].append({'type': 'VALID_MATCH'})
            else:
                validation['flags'].append({'type': 'NO_DATA'})
                
        except Exception as e:
            logger.error(f"Validation error for zone {zone_id}: {e}")
            validation['rule_applied'] = False
            validation['flags'] = [{'type': 'VALIDATION_ERROR', 'error': str(e)}]
        
        return validation
    
    def _parse_driver_time(self, time_str):
        """Parse driver time string to datetime"""
        if not time_str:
            return None
        try:
            return datetime.strptime(str(time_str), '%H:%M:%S').time()
        except:
            try:
                return datetime.strptime(str(time_str), '%H:%M').time()
            except:
                return None
    
    def _parse_rule_time(self, time_str):
        """Parse rule time string to time object"""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except:
            return time(6, 0)  # Default 6:00 AM
    
    def save_zone_rules(self, rules):
        """Save zone rules to JSON file"""
        try:
            with open(self.rules_file, 'w') as f:
                json.dump(rules, f, indent=2)
            logger.info(f"✅ Zone rules saved to {self.rules_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save zone rules: {e}")
            return False
    
    def load_zone_rules(self):
        """Load zone rules from JSON file"""
        try:
            if Path(self.rules_file).exists():
                with open(self.rules_file, 'r') as f:
                    rules = json.load(f)
                logger.info(f"✅ Zone rules loaded from {self.rules_file}")
                return rules
            else:
                logger.info("Using default zone rules")
                return self.default_rules
        except Exception as e:
            logger.error(f"Failed to load zone rules: {e}")
            return self.default_rules
    
    def get_zone_summary(self):
        """Get summary of all configured zones"""
        rules = self.load_zone_rules()
        summary = []
        
        for zone_id, rule in rules.items():
            summary.append({
                'zone_id': zone_id,
                'zone_name': rule.get('zone_name', 'Unknown'),
                'schedule': f"{rule.get('start_time', '06:00')} - {rule.get('end_time', '17:00')}",
                'pm_manager': rule.get('pm_manager', 'Unknown'),
                'late_threshold': f"{rule.get('late_threshold_minutes', 15)} min",
                'early_threshold': f"{rule.get('early_leave_threshold_minutes', 30)} min"
            })
            
        return summary