"""
Time Card Automation System
Automated time entry, tracking, and submission for workforce management
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TimeEntry:
    """Time entry data structure"""
    entry_id: str
    employee_id: str
    employee_name: str
    date: str
    clock_in: str
    clock_out: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    total_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    project_code: Optional[str] = None
    notes: Optional[str] = None
    status: str = "draft"
    submitted_at: Optional[str] = None

class TimeCardAutomation:
    """Automated time card entry and management system"""
    
    def __init__(self):
        self.timecard_file = "employee_timecards.json"
        self.templates_file = "timecard_templates.json"
        self.entries = {}
        self.templates = {}
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize time card system"""
        self._load_existing_data()
        self._create_default_templates()
    
    def _load_existing_data(self):
        """Load existing time entries"""
        if os.path.exists(self.timecard_file):
            try:
                with open(self.timecard_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data:
                        entry = TimeEntry(**entry_data)
                        self.entries[entry.entry_id] = entry
            except Exception as e:
                print(f"Error loading timecard data: {e}")
    
    def _save_data(self):
        """Save time entries to file"""
        try:
            entries_data = [asdict(entry) for entry in self.entries.values()]
            with open(self.timecard_file, 'w') as f:
                json.dump(entries_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving timecard data: {e}")
    
    def _create_default_templates(self):
        """Create default time entry templates"""
        self.templates = {
            "standard_day": {
                "name": "Standard 8-Hour Day",
                "clock_in": "08:00",
                "clock_out": "17:00",
                "lunch_start": "12:00",
                "lunch_end": "13:00",
                "break_start": "10:15",
                "break_end": "10:30"
            },
            "early_shift": {
                "name": "Early Shift",
                "clock_in": "06:00",
                "clock_out": "15:00",
                "lunch_start": "11:00",
                "lunch_end": "12:00",
                "break_start": "08:15",
                "break_end": "08:30"
            },
            "late_shift": {
                "name": "Late Shift",
                "clock_in": "14:00",
                "clock_out": "23:00",
                "lunch_start": "18:00",
                "lunch_end": "19:00",
                "break_start": "16:15",
                "break_end": "16:30"
            },
            "remote_work": {
                "name": "Remote Work Day",
                "clock_in": "09:00",
                "clock_out": "18:00",
                "lunch_start": "12:30",
                "lunch_end": "13:30",
                "break_start": "15:00",
                "break_end": "15:15"
            }
        }
    
    def create_time_entry(self, employee_id: str, employee_name: str, 
                         date: str = None, template: str = None) -> str:
        """Create new time entry"""
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        entry_id = f"tc_{employee_id}_{date}_{int(time.time())}"
        
        # Apply template if specified
        template_data = {}
        if template and template in self.templates:
            template_data = self.templates[template].copy()
            template_data.pop('name', None)
        
        entry = TimeEntry(
            entry_id=entry_id,
            employee_id=employee_id,
            employee_name=employee_name,
            date=date,
            clock_in=template_data.get('clock_in', '09:00'),
            clock_out=template_data.get('clock_out'),
            break_start=template_data.get('break_start'),
            break_end=template_data.get('break_end'),
            lunch_start=template_data.get('lunch_start'),
            lunch_end=template_data.get('lunch_end')
        )
        
        self.entries[entry_id] = entry
        self._calculate_hours(entry_id)
        self._save_data()
        
        return entry_id
    
    def update_time_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing time entry"""
        
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        
        for field, value in updates.items():
            if hasattr(entry, field):
                setattr(entry, field, value)
        
        self._calculate_hours(entry_id)
        self._save_data()
        
        return True
    
    def _calculate_hours(self, entry_id: str):
        """Calculate total and overtime hours"""
        
        entry = self.entries[entry_id]
        
        if not entry.clock_in or not entry.clock_out:
            return
        
        try:
            # Parse times
            clock_in = datetime.strptime(f"{entry.date} {entry.clock_in}", "%Y-%m-%d %H:%M")
            clock_out = datetime.strptime(f"{entry.date} {entry.clock_out}", "%Y-%m-%d %H:%M")
            
            # Handle overnight shifts
            if clock_out < clock_in:
                clock_out += timedelta(days=1)
            
            # Calculate worked time
            worked_time = clock_out - clock_in
            
            # Subtract breaks
            if entry.break_start and entry.break_end:
                break_start = datetime.strptime(f"{entry.date} {entry.break_start}", "%Y-%m-%d %H:%M")
                break_end = datetime.strptime(f"{entry.date} {entry.break_end}", "%Y-%m-%d %H:%M")
                break_duration = break_end - break_start
                worked_time -= break_duration
            
            # Subtract lunch
            if entry.lunch_start and entry.lunch_end:
                lunch_start = datetime.strptime(f"{entry.date} {entry.lunch_start}", "%Y-%m-%d %H:%M")
                lunch_end = datetime.strptime(f"{entry.date} {entry.lunch_end}", "%Y-%m-%d %H:%M")
                lunch_duration = lunch_end - lunch_start
                worked_time -= lunch_duration
            
            # Convert to hours
            total_hours = worked_time.total_seconds() / 3600
            entry.total_hours = round(total_hours, 2)
            
            # Calculate overtime (over 8 hours)
            if total_hours > 8:
                entry.overtime_hours = round(total_hours - 8, 2)
            else:
                entry.overtime_hours = 0
                
        except Exception as e:
            print(f"Error calculating hours: {e}")
    
    def submit_timecard(self, entry_id: str) -> bool:
        """Submit timecard for approval"""
        
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        entry.status = "submitted"
        entry.submitted_at = datetime.now().isoformat()
        
        self._save_data()
        return True
    
    def get_employee_timecards(self, employee_id: str, 
                              start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get timecards for specific employee"""
        
        employee_entries = []
        
        for entry in self.entries.values():
            if entry.employee_id == employee_id:
                # Filter by date range if provided
                if start_date and entry.date < start_date:
                    continue
                if end_date and entry.date > end_date:
                    continue
                
                employee_entries.append(asdict(entry))
        
        # Sort by date (newest first)
        employee_entries.sort(key=lambda x: x['date'], reverse=True)
        
        return employee_entries
    
    def get_weekly_summary(self, employee_id: str, week_start: str = None) -> Dict[str, Any]:
        """Get weekly time summary for employee"""
        
        if not week_start:
            # Get current week start (Monday)
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        week_start_date = datetime.strptime(week_start, "%Y-%m-%d")
        week_end_date = week_start_date + timedelta(days=6)
        week_end = week_end_date.strftime("%Y-%m-%d")
        
        weekly_entries = self.get_employee_timecards(
            employee_id, 
            start_date=week_start, 
            end_date=week_end
        )
        
        total_hours = sum(entry.get('total_hours', 0) for entry in weekly_entries)
        total_overtime = sum(entry.get('overtime_hours', 0) for entry in weekly_entries)
        days_worked = len([entry for entry in weekly_entries if entry.get('total_hours', 0) > 0])
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'total_hours': round(total_hours, 2),
            'total_overtime': round(total_overtime, 2),
            'days_worked': days_worked,
            'entries': weekly_entries,
            'average_daily_hours': round(total_hours / max(days_worked, 1), 2)
        }
    
    def auto_fill_week(self, employee_id: str, employee_name: str, 
                      template: str = "standard_day", week_start: str = None) -> List[str]:
        """Automatically fill timecard for the week"""
        
        if not week_start:
            # Get current week start (Monday)
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        week_start_date = datetime.strptime(week_start, "%Y-%m-%d")
        created_entries = []
        
        # Create entries for Monday through Friday
        for i in range(5):  # Monday to Friday
            work_date = (week_start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Check if entry already exists for this date
            existing_entry = None
            for entry in self.entries.values():
                if entry.employee_id == employee_id and entry.date == work_date:
                    existing_entry = entry.entry_id
                    break
            
            if not existing_entry:
                entry_id = self.create_time_entry(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    date=work_date,
                    template=template
                )
                created_entries.append(entry_id)
        
        return created_entries
    
    def get_timecard_templates(self) -> Dict[str, Any]:
        """Get available timecard templates"""
        return self.templates
    
    def process_automation_request(self, request: str, employee_id: str, 
                                 employee_name: str) -> Dict[str, Any]:
        """Process natural language automation request"""
        
        request_lower = request.lower()
        
        # Detect automation type
        if "fill week" in request_lower or "weekly timecard" in request_lower:
            # Auto-fill week
            template = "standard_day"
            if "early" in request_lower:
                template = "early_shift"
            elif "late" in request_lower:
                template = "late_shift"
            elif "remote" in request_lower:
                template = "remote_work"
            
            created_entries = self.auto_fill_week(employee_id, employee_name, template)
            
            return {
                'action': 'auto_fill_week',
                'template_used': template,
                'entries_created': len(created_entries),
                'entry_ids': created_entries,
                'success': True,
                'message': f"Created {len(created_entries)} timecard entries for the week using {template} template"
            }
        
        elif "today" in request_lower or "clock in" in request_lower:
            # Create today's timecard
            template = "standard_day"
            if "early" in request_lower:
                template = "early_shift"
            elif "late" in request_lower:
                template = "late_shift"
            elif "remote" in request_lower:
                template = "remote_work"
            
            entry_id = self.create_time_entry(employee_id, employee_name, template=template)
            
            return {
                'action': 'create_today',
                'template_used': template,
                'entry_id': entry_id,
                'success': True,
                'message': f"Created timecard entry for today using {template} template"
            }
        
        elif "summary" in request_lower or "report" in request_lower:
            # Generate weekly summary
            summary = self.get_weekly_summary(employee_id)
            
            return {
                'action': 'weekly_summary',
                'summary': summary,
                'success': True,
                'message': f"Generated weekly summary: {summary['total_hours']} total hours"
            }
        
        else:
            return {
                'action': 'unknown',
                'success': False,
                'message': 'Could not understand automation request. Try: "fill my week", "create today\'s timecard", or "show weekly summary"'
            }

def get_timecard_automation():
    """Get timecard automation instance"""
    if not hasattr(get_timecard_automation, 'instance'):
        get_timecard_automation.instance = TimeCardAutomation()
    return get_timecard_automation.instance