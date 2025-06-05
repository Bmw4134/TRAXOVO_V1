"""
Outlook Calendar Scraper with BMI Priority Mapping
Automates calendar entry extraction and priority assignment using Business Momentum Index
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CalendarEntry:
    """Calendar entry data structure"""
    id: str
    subject: str
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    body: str
    attendees: List[str]
    importance: str
    categories: List[str]
    bmi_priority: float
    dynamic_weight: float
    automation_score: float

@dataclass
class BMIModel:
    """Business Momentum Index model for priority calculation"""
    urgency_weight: float = 0.3
    impact_weight: float = 0.25
    resource_weight: float = 0.2
    strategic_weight: float = 0.15
    automation_weight: float = 0.1

class OutlookCalendarScraper:
    """
    Advanced Outlook calendar scraper with BMI priority mapping
    Integrates with Microsoft Graph API for authentic calendar data
    """
    
    def __init__(self):
        self.client_id = os.environ.get('MICROSOFT_CLIENT_ID')
        self.client_secret = os.environ.get('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.environ.get('MICROSOFT_TENANT_ID')
        self.access_token = None
        self.bmi_model = BMIModel()
        
        # Initialize BMI priority keywords
        self.priority_keywords = {
            'high_urgency': ['urgent', 'asap', 'emergency', 'critical', 'deadline', 'due today'],
            'high_impact': ['executive', 'board', 'strategic', 'revenue', 'client', 'contract'],
            'resource_intensive': ['meeting', 'conference', 'presentation', 'review', 'planning'],
            'strategic': ['planning', 'roadmap', 'vision', 'goals', 'quarterly', 'annual'],
            'automation_ready': ['routine', 'weekly', 'daily', 'recurring', 'standard', 'regular']
        }
        
        logger.info("Outlook Calendar Scraper initialized with BMI priority mapping")
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.error("Microsoft Graph API credentials not configured")
            return False
        
        auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        auth_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            if self.access_token:
                logger.info("Successfully authenticated with Microsoft Graph API")
                return True
            else:
                logger.error("Failed to obtain access token")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def get_calendar_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Retrieve calendar events for the specified period"""
        if not self.access_token:
            if not self.authenticate():
                return []
        
        # Calculate date range
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        
        # Microsoft Graph API endpoint for calendar events
        events_url = "https://graph.microsoft.com/v1.0/me/calendar/events"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            '$filter': f"start/dateTime ge '{start_date}' and start/dateTime le '{end_date}'",
            '$select': 'id,subject,start,end,location,body,attendees,importance,categories',
            '$orderby': 'start/dateTime',
            '$top': 100
        }
        
        try:
            response = requests.get(events_url, headers=headers, params=params)
            response.raise_for_status()
            
            events_data = response.json()
            events = events_data.get('value', [])
            
            logger.info(f"Retrieved {len(events)} calendar events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve calendar events: {str(e)}")
            return []
    
    def calculate_bmi_priority(self, event: Dict[str, Any]) -> float:
        """Calculate BMI priority score for calendar event"""
        subject = event.get('subject', '').lower()
        body = event.get('body', {}).get('content', '').lower()
        importance = event.get('importance', 'normal').lower()
        attendees_count = len(event.get('attendees', []))
        
        # Text content for analysis
        content = f"{subject} {body}"
        
        # Calculate component scores
        urgency_score = self._calculate_urgency_score(content, importance)
        impact_score = self._calculate_impact_score(content, attendees_count)
        resource_score = self._calculate_resource_score(content, attendees_count)
        strategic_score = self._calculate_strategic_score(content)
        automation_score = self._calculate_automation_score(content)
        
        # Apply BMI weights
        bmi_priority = (
            urgency_score * self.bmi_model.urgency_weight +
            impact_score * self.bmi_model.impact_weight +
            resource_score * self.bmi_model.resource_weight +
            strategic_score * self.bmi_model.strategic_weight +
            automation_score * self.bmi_model.automation_weight
        )
        
        return round(bmi_priority, 3)
    
    def _calculate_urgency_score(self, content: str, importance: str) -> float:
        """Calculate urgency component of BMI"""
        score = 0.0
        
        # Base score from Outlook importance
        if importance == 'high':
            score += 0.7
        elif importance == 'normal':
            score += 0.4
        
        # Keyword-based urgency detection
        urgency_keywords = self.priority_keywords['high_urgency']
        keyword_matches = sum(1 for keyword in urgency_keywords if keyword in content)
        score += min(keyword_matches * 0.15, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_impact_score(self, content: str, attendees_count: int) -> float:
        """Calculate impact component of BMI"""
        score = 0.0
        
        # Attendee count impact
        if attendees_count >= 10:
            score += 0.6
        elif attendees_count >= 5:
            score += 0.4
        elif attendees_count >= 2:
            score += 0.2
        
        # Keyword-based impact detection
        impact_keywords = self.priority_keywords['high_impact']
        keyword_matches = sum(1 for keyword in impact_keywords if keyword in content)
        score += min(keyword_matches * 0.1, 0.4)
        
        return min(score, 1.0)
    
    def _calculate_resource_score(self, content: str, attendees_count: int) -> float:
        """Calculate resource intensity component of BMI"""
        score = 0.0
        
        # Meeting complexity based on attendees
        score += min(attendees_count * 0.05, 0.5)
        
        # Resource-intensive keywords
        resource_keywords = self.priority_keywords['resource_intensive']
        keyword_matches = sum(1 for keyword in resource_keywords if keyword in content)
        score += min(keyword_matches * 0.1, 0.5)
        
        return min(score, 1.0)
    
    def _calculate_strategic_score(self, content: str) -> float:
        """Calculate strategic importance component of BMI"""
        score = 0.0
        
        # Strategic keywords
        strategic_keywords = self.priority_keywords['strategic']
        keyword_matches = sum(1 for keyword in strategic_keywords if keyword in content)
        score += min(keyword_matches * 0.15, 0.8)
        
        return min(score, 1.0)
    
    def _calculate_automation_score(self, content: str) -> float:
        """Calculate automation readiness component of BMI"""
        score = 0.0
        
        # Automation-ready keywords (inverse scoring - routine tasks get lower priority)
        automation_keywords = self.priority_keywords['automation_ready']
        keyword_matches = sum(1 for keyword in automation_keywords if keyword in content)
        
        # Lower score for automatable tasks
        if keyword_matches > 0:
            score = max(0.2, 1.0 - (keyword_matches * 0.15))
        else:
            score = 0.8  # Non-routine tasks get higher automation score
        
        return min(score, 1.0)
    
    def process_calendar_entries(self, days_ahead: int = 7) -> List[CalendarEntry]:
        """Process calendar entries with BMI priority mapping"""
        events = self.get_calendar_events(days_ahead)
        
        processed_entries = []
        
        for event in events:
            try:
                # Calculate BMI priority
                bmi_priority = self.calculate_bmi_priority(event)
                
                # Calculate dynamic weight based on time proximity
                start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                time_until_event = (start_time - datetime.now()).total_seconds() / 3600  # hours
                
                if time_until_event <= 2:
                    dynamic_weight = 1.0  # Very high for imminent events
                elif time_until_event <= 24:
                    dynamic_weight = 0.8  # High for today's events
                elif time_until_event <= 168:  # Within a week
                    dynamic_weight = 0.6
                else:
                    dynamic_weight = 0.4
                
                # Calculate automation readiness score
                automation_score = self._calculate_automation_score(
                    f"{event.get('subject', '')} {event.get('body', {}).get('content', '')}"
                )
                
                # Create calendar entry
                entry = CalendarEntry(
                    id=event['id'],
                    subject=event.get('subject', ''),
                    start_time=start_time,
                    end_time=datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')),
                    location=event.get('location', {}).get('displayName'),
                    body=event.get('body', {}).get('content', ''),
                    attendees=[attendee.get('emailAddress', {}).get('address', '') 
                              for attendee in event.get('attendees', [])],
                    importance=event.get('importance', 'normal'),
                    categories=event.get('categories', []),
                    bmi_priority=bmi_priority,
                    dynamic_weight=dynamic_weight,
                    automation_score=automation_score
                )
                
                processed_entries.append(entry)
                
            except Exception as e:
                logger.error(f"Error processing calendar entry: {str(e)}")
                continue
        
        # Sort by combined priority score
        processed_entries.sort(
            key=lambda x: (x.bmi_priority * x.dynamic_weight), 
            reverse=True
        )
        
        logger.info(f"Processed {len(processed_entries)} calendar entries with BMI priority mapping")
        return processed_entries
    
    def map_to_dynamic_calendar(self, entries: List[CalendarEntry]) -> Dict[str, Any]:
        """Map processed entries to DynamicCalendar format"""
        dynamic_calendar = {
            'metadata': {
                'total_entries': len(entries),
                'processing_timestamp': datetime.now().isoformat(),
                'bmi_model_version': '1.0',
                'priority_distribution': self._calculate_priority_distribution(entries)
            },
            'calendar_entries': [],
            'priority_insights': self._generate_priority_insights(entries),
            'automation_opportunities': self._identify_automation_opportunities(entries)
        }
        
        for entry in entries:
            calendar_entry = {
                'id': entry.id,
                'title': entry.subject,
                'start_datetime': entry.start_time.isoformat(),
                'end_datetime': entry.end_time.isoformat(),
                'location': entry.location,
                'description': entry.body[:200] + '...' if len(entry.body) > 200 else entry.body,
                'attendees': entry.attendees,
                'priority_level': self._categorize_priority(entry.bmi_priority),
                'bmi_score': entry.bmi_priority,
                'dynamic_weight': entry.dynamic_weight,
                'automation_readiness': entry.automation_score,
                'combined_priority': round(entry.bmi_priority * entry.dynamic_weight, 3),
                'outlook_importance': entry.importance,
                'categories': entry.categories,
                'time_until_event_hours': round((entry.start_time - datetime.now()).total_seconds() / 3600, 1)
            }
            
            dynamic_calendar['calendar_entries'].append(calendar_entry)
        
        return dynamic_calendar
    
    def _calculate_priority_distribution(self, entries: List[CalendarEntry]) -> Dict[str, int]:
        """Calculate priority level distribution"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for entry in entries:
            priority_level = self._categorize_priority(entry.bmi_priority)
            distribution[priority_level] += 1
        
        return distribution
    
    def _categorize_priority(self, bmi_score: float) -> str:
        """Categorize BMI score into priority levels"""
        if bmi_score >= 0.8:
            return 'critical'
        elif bmi_score >= 0.6:
            return 'high'
        elif bmi_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_priority_insights(self, entries: List[CalendarEntry]) -> Dict[str, Any]:
        """Generate insights about calendar priorities"""
        if not entries:
            return {}
        
        total_entries = len(entries)
        high_priority_count = len([e for e in entries if e.bmi_priority >= 0.6])
        
        return {
            'high_priority_percentage': round((high_priority_count / total_entries) * 100, 1),
            'average_bmi_score': round(sum(e.bmi_priority for e in entries) / total_entries, 3),
            'most_critical_event': {
                'title': entries[0].subject,
                'priority_score': entries[0].bmi_priority,
                'start_time': entries[0].start_time.isoformat()
            } if entries else None,
            'calendar_density': self._calculate_calendar_density(entries),
            'conflict_detection': self._detect_scheduling_conflicts(entries)
        }
    
    def _identify_automation_opportunities(self, entries: List[CalendarEntry]) -> List[Dict[str, Any]]:
        """Identify calendar entries suitable for automation"""
        automation_opportunities = []
        
        for entry in entries:
            if entry.automation_score <= 0.5:  # Low score indicates high automation potential
                opportunity = {
                    'event_title': entry.subject,
                    'automation_potential': round(1.0 - entry.automation_score, 3),
                    'suggested_automation': self._suggest_automation_type(entry),
                    'time_savings_estimate': self._estimate_time_savings(entry)
                }
                automation_opportunities.append(opportunity)
        
        return sorted(automation_opportunities, key=lambda x: x['automation_potential'], reverse=True)
    
    def _suggest_automation_type(self, entry: CalendarEntry) -> str:
        """Suggest appropriate automation type for calendar entry"""
        content = f"{entry.subject} {entry.body}".lower()
        
        if any(keyword in content for keyword in ['standup', 'daily', 'weekly']):
            return 'automated_recurring_meeting'
        elif any(keyword in content for keyword in ['report', 'status', 'update']):
            return 'automated_report_generation'
        elif any(keyword in content for keyword in ['reminder', 'follow-up', 'check-in']):
            return 'automated_reminder_system'
        else:
            return 'workflow_automation'
    
    def _estimate_time_savings(self, entry: CalendarEntry) -> str:
        """Estimate potential time savings from automation"""
        duration = (entry.end_time - entry.start_time).total_seconds() / 3600
        
        if duration <= 0.5:
            return '15-30 minutes'
        elif duration <= 1:
            return '30-60 minutes'
        else:
            return f'{int(duration * 0.5)}-{int(duration * 0.8)} hours'
    
    def _calculate_calendar_density(self, entries: List[CalendarEntry]) -> float:
        """Calculate calendar density (meetings per day)"""
        if not entries:
            return 0.0
        
        total_days = 7  # Default week view
        return round(len(entries) / total_days, 2)
    
    def _detect_scheduling_conflicts(self, entries: List[CalendarEntry]) -> List[Dict[str, Any]]:
        """Detect potential scheduling conflicts"""
        conflicts = []
        
        for i, entry1 in enumerate(entries):
            for entry2 in entries[i+1:]:
                if self._events_overlap(entry1, entry2):
                    conflict = {
                        'event1': entry1.subject,
                        'event2': entry2.subject,
                        'overlap_start': max(entry1.start_time, entry2.start_time).isoformat(),
                        'overlap_end': min(entry1.end_time, entry2.end_time).isoformat()
                    }
                    conflicts.append(conflict)
        
        return conflicts
    
    def _events_overlap(self, event1: CalendarEntry, event2: CalendarEntry) -> bool:
        """Check if two events overlap in time"""
        return (event1.start_time < event2.end_time and event2.start_time < event1.end_time)

# Global scraper instance
outlook_scraper = None

def get_outlook_scraper():
    """Get the global Outlook calendar scraper instance"""
    global outlook_scraper
    if outlook_scraper is None:
        outlook_scraper = OutlookCalendarScraper()
    return outlook_scraper

def scrape_weekly_calendar() -> Dict[str, Any]:
    """Scrape this week's calendar entries with BMI priority mapping"""
    scraper = get_outlook_scraper()
    
    try:
        # Process calendar entries
        entries = scraper.process_calendar_entries(days_ahead=7)
        
        # Map to dynamic calendar format
        dynamic_calendar = scraper.map_to_dynamic_calendar(entries)
        
        logger.info(f"Successfully processed {len(entries)} calendar entries")
        return dynamic_calendar
        
    except Exception as e:
        logger.error(f"Failed to scrape weekly calendar: {str(e)}")
        return {
            'error': str(e),
            'status': 'failed',
            'metadata': {
                'processing_timestamp': datetime.now().isoformat()
            }
        }

def get_calendar_priority_insights() -> Dict[str, Any]:
    """Get calendar priority insights and automation opportunities"""
    scraper = get_outlook_scraper()
    
    try:
        entries = scraper.process_calendar_entries(days_ahead=7)
        
        insights = {
            'priority_distribution': scraper._calculate_priority_distribution(entries),
            'automation_opportunities': scraper._identify_automation_opportunities(entries),
            'calendar_insights': scraper._generate_priority_insights(entries),
            'bmi_model_metrics': {
                'urgency_weight': scraper.bmi_model.urgency_weight,
                'impact_weight': scraper.bmi_model.impact_weight,
                'resource_weight': scraper.bmi_model.resource_weight,
                'strategic_weight': scraper.bmi_model.strategic_weight,
                'automation_weight': scraper.bmi_model.automation_weight
            }
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get calendar insights: {str(e)}")
        return {'error': str(e), 'status': 'failed'}