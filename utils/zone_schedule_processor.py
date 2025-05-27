"""
Zone Schedule Rules Processor for TRAXOVO

This module processes PM-defined work hour rules from Excel data and creates
zone_schedule_rules.json for attendance validation across job zones.
"""
import json
import os
import pandas as pd
import logging
from datetime import datetime, time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ZoneScheduleProcessor:
    """Process Excel data to create zone schedule rules for attendance validation"""
    
    def __init__(self):
        self.config_path = 'config/zone_schedule_rules.json'
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs('config', exist_ok=True)
    
    def process_excel_pm_data(self, excel_file_path: str, sheet_name: str = 'PM') -> Dict[str, Any]:
        """
        Process PM sheet from Daily Driver Excel report
        
        Args:
            excel_file_path (str): Path to Excel file
            sheet_name (str): Name of sheet containing PM data
            
        Returns:
            Dict: Processed zone schedule rules
        """
        try:
            # Read PM sheet from Excel
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            logger.info(f"Successfully loaded PM data from {excel_file_path}")
            
            # Process the PM data
            zone_rules = self._extract_zone_rules(df)
            
            # Save to JSON configuration
            self._save_zone_rules(zone_rules)
            
            return zone_rules
            
        except Exception as e:
            logger.error(f"Error processing Excel PM data: {e}")
            return self._get_default_zone_rules()
    
    def process_csv_pm_data(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Process PM data from CSV file
        
        Args:
            csv_file_path (str): Path to CSV file
            
        Returns:
            Dict: Processed zone schedule rules
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Successfully loaded PM data from {csv_file_path}")
            
            # Process the PM data
            zone_rules = self._extract_zone_rules(df)
            
            # Save to JSON configuration
            self._save_zone_rules(zone_rules)
            
            return zone_rules
            
        except Exception as e:
            logger.error(f"Error processing CSV PM data: {e}")
            return self._get_default_zone_rules()
    
    def _extract_zone_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract zone rules from DataFrame"""
        zone_rules = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "source": "PM Excel/CSV Data",
            "zones": {}
        }
        
        # Expected columns in PM data
        required_columns = ['zone_id', 'zone_name', 'sr_pm', 'start_time', 'end_time', 'late_threshold']
        
        # Check if we have the required columns (case-insensitive)
        df_columns_lower = [col.lower().replace(' ', '_') for col in df.columns]
        
        for _, row in df.iterrows():
            try:
                # Extract zone information
                zone_id = self._safe_get_value(row, ['zone_id', 'Zone_ID', 'Zone ID', 'ID'])
                zone_name = self._safe_get_value(row, ['zone_name', 'Zone_Name', 'Zone Name', 'Name'])
                sr_pm = self._safe_get_value(row, ['sr_pm', 'Sr_PM', 'Sr PM', 'PM', 'Project Manager'])
                start_time = self._safe_get_value(row, ['start_time', 'Start_Time', 'Start Time', 'Start'])
                end_time = self._safe_get_value(row, ['end_time', 'End_Time', 'End Time', 'End'])
                late_threshold = self._safe_get_value(row, ['late_threshold', 'Late_Threshold', 'Late Threshold', 'Late'])
                
                if zone_id and zone_name:
                    zone_rules["zones"][str(zone_id)] = {
                        "zone_id": str(zone_id),
                        "zone_name": str(zone_name),
                        "sr_pm": str(sr_pm) if sr_pm else "Unassigned",
                        "schedule": {
                            "start_time": self._parse_time(start_time) or "06:00",
                            "end_time": self._parse_time(end_time) or "19:00",
                            "late_threshold_minutes": self._parse_threshold(late_threshold) or 15,
                            "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                        },
                        "attendance_rules": {
                            "allow_early_start": True,
                            "early_start_limit_minutes": 30,
                            "allow_late_end": True,
                            "late_end_limit_minutes": 60,
                            "require_gps_validation": True,
                            "min_work_hours": 8.0
                        }
                    }
                    
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
        
        # If no zones were processed, use defaults
        if not zone_rules["zones"]:
            logger.warning("No valid zones found in PM data, using defaults")
            zone_rules = self._get_default_zone_rules()
        
        return zone_rules
    
    def _safe_get_value(self, row, possible_keys: List[str]):
        """Safely get value from row using multiple possible column names"""
        for key in possible_keys:
            if key in row.index:
                return row[key]
            # Try case-insensitive match
            for actual_key in row.index:
                if actual_key.lower().replace(' ', '_') == key.lower().replace(' ', '_'):
                    return row[actual_key]
        return None
    
    def _parse_time(self, time_value) -> str:
        """Parse time value to HH:MM format"""
        if pd.isna(time_value):
            return None
            
        if isinstance(time_value, str):
            # Handle various time formats
            time_value = time_value.strip()
            if ':' in time_value:
                return time_value[:5]  # Take HH:MM part
            elif len(time_value) == 4 and time_value.isdigit():
                return f"{time_value[:2]}:{time_value[2:]}"
        
        elif isinstance(time_value, (int, float)):
            # Handle numeric time (e.g., 630 for 6:30)
            hours = int(time_value // 100)
            minutes = int(time_value % 100)
            return f"{hours:02d}:{minutes:02d}"
        
        return None
    
    def _parse_threshold(self, threshold_value) -> int:
        """Parse late threshold to minutes"""
        if pd.isna(threshold_value):
            return None
            
        if isinstance(threshold_value, (int, float)):
            return int(threshold_value)
        
        if isinstance(threshold_value, str):
            # Extract numeric value
            import re
            numbers = re.findall(r'\d+', threshold_value)
            if numbers:
                return int(numbers[0])
        
        return None
    
    def _get_default_zone_rules(self) -> Dict[str, Any]:
        """Get default zone rules when PM data is not available"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "source": "Default Configuration",
            "zones": {
                "DFW_CENTRAL": {
                    "zone_id": "DFW_CENTRAL",
                    "zone_name": "DFW Central Region",
                    "sr_pm": "Default PM",
                    "schedule": {
                        "start_time": "06:00",
                        "end_time": "19:00",
                        "late_threshold_minutes": 15,
                        "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    },
                    "attendance_rules": {
                        "allow_early_start": True,
                        "early_start_limit_minutes": 30,
                        "allow_late_end": True,
                        "late_end_limit_minutes": 60,
                        "require_gps_validation": True,
                        "min_work_hours": 8.0
                    }
                },
                "HOUSTON_EAST": {
                    "zone_id": "HOUSTON_EAST",
                    "zone_name": "Houston East Region",
                    "sr_pm": "Default PM",
                    "schedule": {
                        "start_time": "06:00",
                        "end_time": "19:00",
                        "late_threshold_minutes": 15,
                        "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    },
                    "attendance_rules": {
                        "allow_early_start": True,
                        "early_start_limit_minutes": 30,
                        "allow_late_end": True,
                        "late_end_limit_minutes": 60,
                        "require_gps_validation": True,
                        "min_work_hours": 8.0
                    }
                },
                "WEST_TEXAS_MIDLAND": {
                    "zone_id": "WEST_TEXAS_MIDLAND",
                    "zone_name": "West Texas Midland Region",
                    "sr_pm": "Default PM",
                    "schedule": {
                        "start_time": "06:00",
                        "end_time": "19:00",
                        "late_threshold_minutes": 15,
                        "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                    },
                    "attendance_rules": {
                        "allow_early_start": True,
                        "early_start_limit_minutes": 30,
                        "allow_late_end": True,
                        "late_end_limit_minutes": 60,
                        "require_gps_validation": True,
                        "min_work_hours": 8.0
                    }
                }
            }
        }
    
    def _save_zone_rules(self, zone_rules: Dict[str, Any]):
        """Save zone rules to JSON configuration file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(zone_rules, f, indent=2)
            logger.info(f"Zone schedule rules saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving zone rules: {e}")
    
    def load_zone_rules(self) -> Dict[str, Any]:
        """Load zone rules from JSON configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Zone rules file not found at {self.config_path}, using defaults")
                return self._get_default_zone_rules()
        except Exception as e:
            logger.error(f"Error loading zone rules: {e}")
            return self._get_default_zone_rules()
    
    def get_zone_schedule(self, zone_id: str) -> Dict[str, Any]:
        """Get schedule for specific zone"""
        zone_rules = self.load_zone_rules()
        return zone_rules.get("zones", {}).get(zone_id, {})
    
    def validate_attendance(self, zone_id: str, check_time: datetime, gps_coordinates: tuple = None) -> Dict[str, Any]:
        """
        Validate attendance against zone schedule rules
        
        Args:
            zone_id (str): Zone identifier
            check_time (datetime): Time to validate
            gps_coordinates (tuple): Optional GPS coordinates (lat, lng)
            
        Returns:
            Dict: Validation result
        """
        zone_schedule = self.get_zone_schedule(zone_id)
        
        if not zone_schedule:
            return {
                "valid": False,
                "reason": f"Zone {zone_id} not found",
                "zone_id": zone_id
            }
        
        schedule = zone_schedule.get("schedule", {})
        rules = zone_schedule.get("attendance_rules", {})
        
        # Check if it's a working day
        day_name = check_time.strftime("%A").lower()
        if day_name not in schedule.get("working_days", []):
            return {
                "valid": False,
                "reason": f"Not a working day ({day_name})",
                "zone_id": zone_id
            }
        
        # Parse schedule times
        start_time_str = schedule.get("start_time", "06:00")
        end_time_str = schedule.get("end_time", "19:00")
        
        start_hour, start_min = map(int, start_time_str.split(':'))
        end_hour, end_min = map(int, end_time_str.split(':'))
        
        # Create datetime objects for comparison
        check_date = check_time.date()
        schedule_start = datetime.combine(check_date, time(start_hour, start_min))
        schedule_end = datetime.combine(check_date, time(end_hour, end_min))
        
        # Apply early start allowance
        if rules.get("allow_early_start", True):
            early_limit = rules.get("early_start_limit_minutes", 30)
            earliest_allowed = schedule_start - pd.Timedelta(minutes=early_limit)
        else:
            earliest_allowed = schedule_start
        
        # Apply late end allowance  
        if rules.get("allow_late_end", True):
            late_limit = rules.get("late_end_limit_minutes", 60)
            latest_allowed = schedule_end + pd.Timedelta(minutes=late_limit)
        else:
            latest_allowed = schedule_end
        
        # Validate time window
        if check_time < earliest_allowed:
            return {
                "valid": False,
                "reason": f"Too early (before {earliest_allowed.strftime('%H:%M')})",
                "zone_id": zone_id
            }
        
        if check_time > latest_allowed:
            return {
                "valid": False,
                "reason": f"Too late (after {latest_allowed.strftime('%H:%M')})",
                "zone_id": zone_id
            }
        
        # Check if late
        late_threshold = schedule.get("late_threshold_minutes", 15)
        late_cutoff = schedule_start + pd.Timedelta(minutes=late_threshold)
        is_late = check_time > late_cutoff
        
        return {
            "valid": True,
            "zone_id": zone_id,
            "is_late": is_late,
            "late_minutes": max(0, (check_time - schedule_start).total_seconds() / 60) if is_late else 0,
            "schedule_start": schedule_start.isoformat(),
            "schedule_end": schedule_end.isoformat(),
            "sr_pm": zone_schedule.get("sr_pm", "Unknown")
        }