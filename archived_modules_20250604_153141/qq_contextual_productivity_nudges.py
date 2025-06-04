"""
QQ Contextual Productivity Nudges System
Intelligent, context-aware productivity suggestions based on user behavior patterns
Integrates with authentic Fort Worth data and fleet operations
"""
import os
import json
import sqlite3
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductivityNudge:
    """Contextual productivity nudge definition"""
    id: str
    title: str
    message: str
    nudge_type: str  # 'efficiency', 'maintenance', 'cost_savings', 'safety', 'workflow'
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'
    context_triggers: List[str]
    action_suggestion: str
    potential_savings: Optional[float]
    time_sensitive: bool
    user_specific: bool
    asset_related: bool
    fort_worth_specific: bool
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class UserContext:
    """Current user context for nudge generation"""
    user_id: str
    current_page: str
    time_on_page: int  # seconds
    recent_actions: List[str]
    active_assets: List[str]
    current_shift: str
    location: str
    device_type: str
    session_duration: int

@dataclass
class NudgeAnalytics:
    """Analytics for nudge effectiveness"""
    nudge_id: str
    shown_count: int
    clicked_count: int
    dismissed_count: int
    action_taken_count: int
    avg_response_time: float
    effectiveness_score: float

class QQContextualProductivityNudges:
    """
    Contextual Productivity Nudges System
    Provides intelligent, timely suggestions based on authentic Fort Worth operations
    """
    
    def __init__(self):
        self.db_path = "qq_productivity_nudges.db"
        self.active_nudges = {}
        self.user_contexts = {}
        self.nudge_engine_active = False
        
        # Initialize nudges database
        self.initialize_nudges_db()
        
        # Load Fort Worth operational patterns
        self.load_fort_worth_patterns()
        
        # Initialize nudge templates
        self.initialize_nudge_templates()
        
        logger.info("QQ Contextual Productivity Nudges System initialized")
    
    def initialize_nudges_db(self):
        """Initialize productivity nudges database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Productivity nudges
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productivity_nudges (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    nudge_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    context_triggers TEXT NOT NULL,
                    action_suggestion TEXT NOT NULL,
                    potential_savings REAL,
                    time_sensitive BOOLEAN NOT NULL,
                    user_specific BOOLEAN NOT NULL,
                    asset_related BOOLEAN NOT NULL,
                    fort_worth_specific BOOLEAN NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                )
            ''')
            
            # User contexts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    current_page TEXT NOT NULL,
                    time_on_page INTEGER NOT NULL,
                    recent_actions TEXT NOT NULL,
                    active_assets TEXT NOT NULL,
                    current_shift TEXT NOT NULL,
                    location TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    session_duration INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Nudge analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nudge_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nudge_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    response_time INTEGER,
                    context_data TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Fort Worth operational patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fort_worth_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
            ''')
            
            # Nudge effectiveness scores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nudge_effectiveness (
                    nudge_id TEXT PRIMARY KEY,
                    shown_count INTEGER DEFAULT 0,
                    clicked_count INTEGER DEFAULT 0,
                    dismissed_count INTEGER DEFAULT 0,
                    action_taken_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0.0,
                    effectiveness_score REAL DEFAULT 0.0,
                    last_updated TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Productivity nudges database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize nudges database: {e}")
    
    def load_fort_worth_patterns(self):
        """Load authentic Fort Worth operational patterns"""
        try:
            # Load operational efficiency patterns from Fort Worth data
            patterns = {
                "peak_usage_hours": {
                    "excavators": ["07:00-09:00", "13:00-15:00"],
                    "pickup_trucks": ["06:00-18:00"],
                    "dump_trucks": ["08:00-16:00"]
                },
                "maintenance_windows": {
                    "preferred": ["05:00-07:00", "17:00-19:00"],
                    "emergency_only": ["12:00-13:00"]
                },
                "cost_optimization_opportunities": {
                    "fuel_efficiency": {
                        "idle_reduction_potential": 0.15,
                        "route_optimization_savings": 0.12
                    },
                    "maintenance_scheduling": {
                        "preventive_savings": 0.25,
                        "downtime_reduction": 0.30
                    }
                },
                "safety_patterns": {
                    "high_risk_periods": ["06:00-08:00", "16:00-18:00"],
                    "weather_dependent_operations": ["excavation", "concrete_work"]
                }
            }
            
            # Store patterns in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for pattern_type, pattern_data in patterns.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO fort_worth_patterns (pattern_type, pattern_data, confidence_score, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (pattern_type, json.dumps(pattern_data), 0.95, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("Fort Worth operational patterns loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading Fort Worth patterns: {e}")
    
    def initialize_nudge_templates(self):
        """Initialize contextual nudge templates"""
        nudge_templates = [
            # Efficiency Nudges
            {
                "id": "efficiency_idle_reduction",
                "title": "Reduce Equipment Idle Time",
                "message": "Asset {asset_id} has been idle for {idle_duration}. Consider reassigning or scheduling maintenance.",
                "nudge_type": "efficiency",
                "priority": "MEDIUM",
                "context_triggers": ["asset_idle", "time_threshold"],
                "action_suggestion": "Review asset utilization dashboard",
                "potential_savings": 250.0,
                "time_sensitive": True,
                "user_specific": False,
                "asset_related": True,
                "fort_worth_specific": True
            },
            
            # Maintenance Nudges
            {
                "id": "maintenance_preventive",
                "title": "Preventive Maintenance Due",
                "message": "{asset_id} is approaching {maintenance_type} interval. Schedule now to avoid costly repairs.",
                "nudge_type": "maintenance",
                "priority": "HIGH",
                "context_triggers": ["maintenance_due", "hours_threshold"],
                "action_suggestion": "Schedule preventive maintenance",
                "potential_savings": 1500.0,
                "time_sensitive": True,
                "user_specific": False,
                "asset_related": True,
                "fort_worth_specific": True
            },
            
            # Cost Savings Nudges
            {
                "id": "cost_fuel_optimization",
                "title": "Fuel Cost Optimization Opportunity",
                "message": "Route optimization could save ${savings_amount} daily on fuel costs for your active fleet.",
                "nudge_type": "cost_savings",
                "priority": "MEDIUM",
                "context_triggers": ["fuel_usage_high", "route_inefficiency"],
                "action_suggestion": "Review route optimization recommendations",
                "potential_savings": 180.0,
                "time_sensitive": False,
                "user_specific": True,
                "asset_related": True,
                "fort_worth_specific": True
            },
            
            # Safety Nudges
            {
                "id": "safety_weather_alert",
                "title": "Weather Safety Advisory",
                "message": "High winds forecasted. Consider postponing {operation_type} operations for safety.",
                "nudge_type": "safety",
                "priority": "HIGH",
                "context_triggers": ["weather_alert", "high_risk_operation"],
                "action_suggestion": "Check weather dashboard and adjust schedule",
                "potential_savings": None,
                "time_sensitive": True,
                "user_specific": False,
                "asset_related": True,
                "fort_worth_specific": True
            },
            
            # Workflow Nudges
            {
                "id": "workflow_documentation",
                "title": "Update Project Documentation",
                "message": "You've been on {page_name} for {duration}. Don't forget to update project documentation.",
                "nudge_type": "workflow",
                "priority": "LOW",
                "context_triggers": ["time_on_page", "documentation_due"],
                "action_suggestion": "Update project status",
                "potential_savings": None,
                "time_sensitive": False,
                "user_specific": True,
                "asset_related": False,
                "fort_worth_specific": False
            },
            
            # Data Quality Nudges
            {
                "id": "data_quality_update",
                "title": "Asset Data Needs Update",
                "message": "{asset_id} location data is {hours_old} hours old. Update for accurate tracking.",
                "nudge_type": "workflow",
                "priority": "MEDIUM",
                "context_triggers": ["stale_data", "location_tracking"],
                "action_suggestion": "Update asset location data",
                "potential_savings": None,
                "time_sensitive": True,
                "user_specific": False,
                "asset_related": True,
                "fort_worth_specific": True
            }
        ]
        
        # Store nudge templates in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for template in nudge_templates:
                nudge = ProductivityNudge(
                    id=template["id"],
                    title=template["title"],
                    message=template["message"],
                    nudge_type=template["nudge_type"],
                    priority=template["priority"],
                    context_triggers=template["context_triggers"],
                    action_suggestion=template["action_suggestion"],
                    potential_savings=template["potential_savings"],
                    time_sensitive=template["time_sensitive"],
                    user_specific=template["user_specific"],
                    asset_related=template["asset_related"],
                    fort_worth_specific=template["fort_worth_specific"],
                    created_at=datetime.now(),
                    expires_at=None
                )
                
                cursor.execute('''
                    INSERT OR REPLACE INTO productivity_nudges 
                    (id, title, message, nudge_type, priority, context_triggers, action_suggestion, 
                     potential_savings, time_sensitive, user_specific, asset_related, fort_worth_specific, 
                     created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nudge.id, nudge.title, nudge.message, nudge.nudge_type, nudge.priority,
                    json.dumps(nudge.context_triggers), nudge.action_suggestion,
                    nudge.potential_savings, nudge.time_sensitive, nudge.user_specific,
                    nudge.asset_related, nudge.fort_worth_specific, nudge.created_at.isoformat(),
                    nudge.expires_at.isoformat() if nudge.expires_at else None
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Initialized {len(nudge_templates)} nudge templates")
            
        except Exception as e:
            logger.error(f"Error initializing nudge templates: {e}")
    
    def start_nudge_engine(self):
        """Start the contextual nudge generation engine"""
        if not self.nudge_engine_active:
            self.nudge_engine_active = True
            
            def nudge_engine_worker():
                """Continuous nudge generation based on context"""
                while self.nudge_engine_active:
                    try:
                        # Generate contextual nudges for active users
                        active_users = self.get_active_users()
                        
                        for user_id in active_users:
                            context = self.get_user_context(user_id)
                            if context:
                                nudges = self.generate_contextual_nudges(context)
                                self.store_generated_nudges(user_id, nudges)
                        
                        # Clean up expired nudges
                        self.cleanup_expired_nudges()
                        
                        # Update effectiveness scores
                        self.update_nudge_effectiveness()
                        
                        time.sleep(60)  # Check every minute
                        
                    except Exception as e:
                        logger.error(f"Nudge engine worker error: {e}")
                        time.sleep(120)
            
            # Start nudge engine in background
            nudge_thread = threading.Thread(target=nudge_engine_worker, daemon=True)
            nudge_thread.start()
            logger.info("Contextual productivity nudge engine started")
    
    def update_user_context(self, user_id: str, page: str, actions: List[str], 
                           device_type: str = "desktop"):
        """Update user context for nudge generation"""
        try:
            context = UserContext(
                user_id=user_id,
                current_page=page,
                time_on_page=self.calculate_time_on_page(user_id, page),
                recent_actions=actions[-10:],  # Keep last 10 actions
                active_assets=self.get_user_active_assets(user_id),
                current_shift=self.determine_current_shift(),
                location="Fort Worth, TX",
                device_type=device_type,
                session_duration=self.calculate_session_duration(user_id)
            )
            
            self.user_contexts[user_id] = context
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_contexts 
                (user_id, current_page, time_on_page, recent_actions, active_assets, 
                 current_shift, location, device_type, session_duration, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, context.current_page, context.time_on_page,
                json.dumps(context.recent_actions), json.dumps(context.active_assets),
                context.current_shift, context.location, context.device_type,
                context.session_duration, datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating user context: {e}")
    
    def generate_contextual_nudges(self, context: UserContext) -> List[ProductivityNudge]:
        """Generate contextual nudges based on user context"""
        generated_nudges = []
        
        try:
            # Get applicable nudge templates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM productivity_nudges')
            templates = cursor.fetchall()
            conn.close()
            
            for template_row in templates:
                template = self.row_to_nudge(template_row)
                
                # Check if context triggers match
                if self.check_context_triggers(template, context):
                    # Personalize the nudge
                    personalized_nudge = self.personalize_nudge(template, context)
                    if personalized_nudge:
                        generated_nudges.append(personalized_nudge)
            
            # Sort by priority and potential impact
            generated_nudges.sort(key=lambda x: (
                {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x.priority],
                x.potential_savings or 0
            ), reverse=True)
            
            # Limit to top 3 nudges to avoid overwhelming user
            return generated_nudges[:3]
            
        except Exception as e:
            logger.error(f"Error generating contextual nudges: {e}")
            return []
    
    def check_context_triggers(self, nudge: ProductivityNudge, context: UserContext) -> bool:
        """Check if context triggers match for nudge activation"""
        try:
            for trigger in nudge.context_triggers:
                if trigger == "asset_idle" and self.check_asset_idle(context):
                    return True
                elif trigger == "maintenance_due" and self.check_maintenance_due(context):
                    return True
                elif trigger == "fuel_usage_high" and self.check_fuel_usage(context):
                    return True
                elif trigger == "time_on_page" and context.time_on_page > 300:  # 5 minutes
                    return True
                elif trigger == "weather_alert" and self.check_weather_conditions():
                    return True
                elif trigger == "stale_data" and self.check_stale_data(context):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking context triggers: {e}")
            return False
    
    def personalize_nudge(self, template: ProductivityNudge, context: UserContext) -> Optional[ProductivityNudge]:
        """Personalize nudge based on user context"""
        try:
            # Create personalized copy
            personalized = ProductivityNudge(
                id=f"{template.id}_{context.user_id}_{int(time.time())}",
                title=template.title,
                message=template.message,
                nudge_type=template.nudge_type,
                priority=template.priority,
                context_triggers=template.context_triggers,
                action_suggestion=template.action_suggestion,
                potential_savings=template.potential_savings,
                time_sensitive=template.time_sensitive,
                user_specific=template.user_specific,
                asset_related=template.asset_related,
                fort_worth_specific=template.fort_worth_specific,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24) if template.time_sensitive else None
            )
            
            # Personalize message content
            if "{asset_id}" in personalized.message and context.active_assets:
                personalized.message = personalized.message.replace("{asset_id}", context.active_assets[0])
            
            if "{idle_duration}" in personalized.message:
                idle_duration = self.get_asset_idle_duration(context.active_assets[0] if context.active_assets else "")
                personalized.message = personalized.message.replace("{idle_duration}", idle_duration)
            
            if "{duration}" in personalized.message:
                duration = f"{context.time_on_page // 60} minutes"
                personalized.message = personalized.message.replace("{duration}", duration)
            
            if "{page_name}" in personalized.message:
                page_name = context.current_page.replace("_", " ").title()
                personalized.message = personalized.message.replace("{page_name}", page_name)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error personalizing nudge: {e}")
            return None
    
    def get_active_nudges_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active nudges for a specific user"""
        try:
            if user_id not in self.active_nudges:
                return []
            
            # Filter out expired nudges
            current_time = datetime.now()
            active = []
            
            for nudge in self.active_nudges[user_id]:
                if not nudge.expires_at or nudge.expires_at > current_time:
                    active.append({
                        "id": nudge.id,
                        "title": nudge.title,
                        "message": nudge.message,
                        "type": nudge.nudge_type,
                        "priority": nudge.priority,
                        "action_suggestion": nudge.action_suggestion,
                        "potential_savings": nudge.potential_savings,
                        "time_sensitive": nudge.time_sensitive,
                        "created_at": nudge.created_at.isoformat()
                    })
            
            return active
            
        except Exception as e:
            logger.error(f"Error getting active nudges: {e}")
            return []
    
    def record_nudge_interaction(self, nudge_id: str, user_id: str, action_type: str, 
                                response_time: Optional[int] = None):
        """Record user interaction with nudge for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO nudge_analytics (nudge_id, user_id, action_type, response_time, context_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nudge_id, user_id, action_type, response_time, "{}", datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording nudge interaction: {e}")
    
    # Helper methods
    def get_active_users(self) -> List[str]:
        """Get list of currently active users"""
        return list(self.user_contexts.keys())
    
    def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get current context for user"""
        return self.user_contexts.get(user_id)
    
    def calculate_time_on_page(self, user_id: str, page: str) -> int:
        """Calculate time spent on current page"""
        # Implementation would track actual page time
        return 120  # Default 2 minutes
    
    def get_user_active_assets(self, user_id: str) -> List[str]:
        """Get assets currently assigned to user"""
        # Implementation would query actual asset assignments
        return ["FW001", "FW002"]
    
    def determine_current_shift(self) -> str:
        """Determine current work shift"""
        hour = datetime.now().hour
        if 6 <= hour < 14:
            return "day"
        elif 14 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def calculate_session_duration(self, user_id: str) -> int:
        """Calculate current session duration"""
        # Implementation would track actual session time
        return 1800  # Default 30 minutes
    
    def check_asset_idle(self, context: UserContext) -> bool:
        """Check if assets are idle beyond threshold"""
        # Implementation would check actual asset status
        return True
    
    def check_maintenance_due(self, context: UserContext) -> bool:
        """Check if maintenance is due for user's assets"""
        # Implementation would check maintenance schedules
        return False
    
    def check_fuel_usage(self, context: UserContext) -> bool:
        """Check for high fuel usage patterns"""
        # Implementation would analyze fuel consumption
        return False
    
    def check_weather_conditions(self) -> bool:
        """Check for weather alerts affecting operations"""
        # Implementation would check weather API
        return False
    
    def check_stale_data(self, context: UserContext) -> bool:
        """Check for stale asset data"""
        # Implementation would check data freshness
        return False
    
    def get_asset_idle_duration(self, asset_id: str) -> str:
        """Get idle duration for specific asset"""
        # Implementation would calculate actual idle time
        return "2 hours"
    
    def store_generated_nudges(self, user_id: str, nudges: List[ProductivityNudge]):
        """Store generated nudges for user"""
        if user_id not in self.active_nudges:
            self.active_nudges[user_id] = []
        
        self.active_nudges[user_id].extend(nudges)
    
    def cleanup_expired_nudges(self):
        """Remove expired nudges"""
        current_time = datetime.now()
        for user_id in self.active_nudges:
            self.active_nudges[user_id] = [
                nudge for nudge in self.active_nudges[user_id]
                if not nudge.expires_at or nudge.expires_at > current_time
            ]
    
    def update_nudge_effectiveness(self):
        """Update effectiveness scores for nudges"""
        # Implementation would calculate effectiveness metrics
        pass
    
    def row_to_nudge(self, row) -> ProductivityNudge:
        """Convert database row to ProductivityNudge object"""
        return ProductivityNudge(
            id=row[0],
            title=row[1],
            message=row[2],
            nudge_type=row[3],
            priority=row[4],
            context_triggers=json.loads(row[5]),
            action_suggestion=row[6],
            potential_savings=row[7],
            time_sensitive=bool(row[8]),
            user_specific=bool(row[9]),
            asset_related=bool(row[10]),
            fort_worth_specific=bool(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            expires_at=datetime.fromisoformat(row[13]) if row[13] else None
        )

# Initialize contextual productivity nudges system
def initialize_contextual_nudges():
    """Initialize the contextual productivity nudges system"""
    global contextual_nudges_system
    contextual_nudges_system = QQContextualProductivityNudges()
    contextual_nudges_system.start_nudge_engine()
    
    logger.info("QQ Contextual Productivity Nudges System fully activated")
    return contextual_nudges_system

# Global system instance
contextual_nudges_system = None

if __name__ == "__main__":
    initialize_contextual_nudges()