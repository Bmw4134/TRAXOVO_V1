"""
TRAXOVO Gamified Learning Overlay System
Interactive training and skill development with achievement tracking
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from flask import Blueprint, render_template, request, jsonify, session
import sqlite3

@dataclass
class Achievement:
    """Achievement badge definition"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    points: int
    requirements: Dict[str, Any]
    unlocked: bool = False
    unlock_date: Optional[str] = None

@dataclass
class LearningModule:
    """Interactive learning module"""
    id: str
    title: str
    description: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: int  # minutes
    prerequisites: List[str]
    steps: List[Dict[str, Any]]
    completed: bool = False
    progress: int = 0

@dataclass
class UserProgress:
    """User learning progress tracking"""
    user_id: str
    total_points: int
    level: int
    current_streak: int
    longest_streak: int
    modules_completed: List[str]
    achievements_unlocked: List[str]
    last_activity: str
    skill_levels: Dict[str, int]

class GamifiedLearningSystem:
    """Core gamification engine for TRAXOVO learning"""
    
    def __init__(self):
        self.db_path = "learning_progress.db"
        self.init_database()
        self.achievements = self._load_achievements()
        self.learning_modules = self._load_learning_modules()
        
    def init_database(self):
        """Initialize SQLite database for progress tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                modules_completed TEXT DEFAULT '[]',
                achievements_unlocked TEXT DEFAULT '[]',
                last_activity TEXT,
                skill_levels TEXT DEFAULT '{}'
            )
        ''')
        
        # Activity log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                activity_type TEXT,
                module_id TEXT,
                points_earned INTEGER,
                timestamp TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_achievements(self) -> List[Achievement]:
        """Load achievement definitions"""
        achievements = [
            Achievement(
                id="first_login",
                name="Welcome Aboard",
                description="Complete your first login to TRAXOVO",
                icon="fas fa-rocket",
                category="Getting Started",
                points=10,
                requirements={"action": "login", "count": 1}
            ),
            Achievement(
                id="dashboard_explorer",
                name="Dashboard Explorer",
                description="Explore all main dashboard sections",
                icon="fas fa-compass",
                category="Navigation",
                points=25,
                requirements={"action": "visit_sections", "count": 5}
            ),
            Achievement(
                id="fleet_master",
                name="Fleet Master",
                description="Complete fleet management training",
                icon="fas fa-truck",
                category="Fleet Management",
                points=50,
                requirements={"module": "fleet_basics", "completion": True}
            ),
            Achievement(
                id="data_wizard",
                name="Data Wizard",
                description="Upload and process 10 reports successfully",
                icon="fas fa-chart-line",
                category="Data Management",
                points=75,
                requirements={"action": "upload_reports", "count": 10}
            ),
            Achievement(
                id="efficiency_expert",
                name="Efficiency Expert",
                description="Achieve 95% accuracy in QA/QC tasks",
                icon="fas fa-star",
                category="Quality Assurance",
                points=100,
                requirements={"metric": "qa_accuracy", "threshold": 95}
            ),
            Achievement(
                id="streak_champion",
                name="Streak Champion",
                description="Maintain a 30-day learning streak",
                icon="fas fa-fire",
                category="Consistency",
                points=200,
                requirements={"action": "daily_streak", "count": 30}
            ),
            Achievement(
                id="quantum_pioneer",
                name="Quantum Pioneer",
                description="Master all QQ ASI-AGI-AI features",
                icon="fas fa-atom",
                category="Advanced",
                points=500,
                requirements={"modules": ["quantum_basics", "asi_features", "agi_tools"], "all_completed": True}
            )
        ]
        return achievements
    
    def _load_learning_modules(self) -> List[LearningModule]:
        """Load interactive learning modules"""
        modules = [
            LearningModule(
                id="traxovo_basics",
                title="TRAXOVO Platform Basics",
                description="Learn the fundamentals of the TRAXOVO intelligence platform",
                category="Getting Started",
                difficulty="beginner",
                estimated_time=15,
                prerequisites=[],
                steps=[
                    {
                        "type": "introduction",
                        "title": "Welcome to TRAXOVO",
                        "content": "TRAXOVO is your comprehensive fleet intelligence platform",
                        "action": "read"
                    },
                    {
                        "type": "interactive",
                        "title": "Navigate the Dashboard",
                        "content": "Click on each section to explore",
                        "action": "click_elements",
                        "targets": [".nav-link", ".dashboard-card"]
                    },
                    {
                        "type": "quiz",
                        "title": "Knowledge Check",
                        "questions": [
                            {
                                "question": "What does TRAXOVO specialize in?",
                                "options": ["Fleet Intelligence", "Social Media", "Gaming", "E-commerce"],
                                "correct": 0
                            }
                        ]
                    }
                ]
            ),
            LearningModule(
                id="fleet_basics",
                title="Fleet Management Fundamentals",
                description="Master fleet tracking, asset management, and operational insights",
                category="Fleet Management",
                difficulty="beginner",
                estimated_time=25,
                prerequisites=["traxovo_basics"],
                steps=[
                    {
                        "type": "demonstration",
                        "title": "Fleet Map Overview",
                        "content": "Understanding real-time asset tracking",
                        "action": "guided_tour",
                        "target_page": "/fleet-map"
                    },
                    {
                        "type": "hands_on",
                        "title": "Asset Analysis",
                        "content": "Click on assets to view QQ Excellence metrics",
                        "action": "interact_with_assets",
                        "required_interactions": 3
                    }
                ]
            ),
            LearningModule(
                id="quantum_basics",
                title="Quantum ASI Features",
                description="Introduction to QQ-enhanced analytics and ASI capabilities",
                category="Advanced",
                difficulty="intermediate",
                estimated_time=35,
                prerequisites=["traxovo_basics", "fleet_basics"],
                steps=[
                    {
                        "type": "concept",
                        "title": "Understanding QQ Technology",
                        "content": "Quantum-enhanced AI for superior decision making",
                        "action": "read"
                    },
                    {
                        "type": "practical",
                        "title": "Using ASI Insights",
                        "content": "Apply ASI recommendations to optimize operations",
                        "action": "complete_task",
                        "task_id": "asi_optimization"
                    }
                ]
            )
        ]
        return modules
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get user's learning progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_progress WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            return UserProgress(
                user_id=result[0],
                total_points=result[1],
                level=result[2],
                current_streak=result[3],
                longest_streak=result[4],
                modules_completed=json.loads(result[5]),
                achievements_unlocked=json.loads(result[6]),
                last_activity=result[7],
                skill_levels=json.loads(result[8])
            )
        else:
            # Create new user progress
            new_progress = UserProgress(
                user_id=user_id,
                total_points=0,
                level=1,
                current_streak=0,
                longest_streak=0,
                modules_completed=[],
                achievements_unlocked=[],
                last_activity=datetime.now().isoformat(),
                skill_levels={}
            )
            self.save_user_progress(new_progress)
            return new_progress
        
        conn.close()
    
    def save_user_progress(self, progress: UserProgress):
        """Save user progress to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress 
            (user_id, total_points, level, current_streak, longest_streak, 
             modules_completed, achievements_unlocked, last_activity, skill_levels)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            progress.user_id,
            progress.total_points,
            progress.level,
            progress.current_streak,
            progress.longest_streak,
            json.dumps(progress.modules_completed),
            json.dumps(progress.achievements_unlocked),
            progress.last_activity,
            json.dumps(progress.skill_levels)
        ))
        
        conn.commit()
        conn.close()
    
    def award_points(self, user_id: str, points: int, activity_type: str, details: str = ""):
        """Award points to user and check for achievements"""
        progress = self.get_user_progress(user_id)
        progress.total_points += points
        progress.level = self.calculate_level(progress.total_points)
        progress.last_activity = datetime.now().isoformat()
        
        # Log activity
        self.log_activity(user_id, activity_type, "", points, details)
        
        # Check for new achievements
        self.check_achievements(user_id, progress)
        
        self.save_user_progress(progress)
        return progress
    
    def calculate_level(self, total_points: int) -> int:
        """Calculate user level based on total points"""
        if total_points < 100:
            return 1
        elif total_points < 300:
            return 2
        elif total_points < 600:
            return 3
        elif total_points < 1000:
            return 4
        elif total_points < 1500:
            return 5
        else:
            return min(10, 5 + (total_points - 1500) // 500)
    
    def check_achievements(self, user_id: str, progress: UserProgress):
        """Check and award new achievements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for achievement in self.achievements:
            if achievement.id in progress.achievements_unlocked:
                continue
                
            if self.check_achievement_requirements(user_id, achievement, progress):
                progress.achievements_unlocked.append(achievement.id)
                progress.total_points += achievement.points
                
                # Log achievement unlock
                self.log_activity(
                    user_id, 
                    "achievement_unlocked", 
                    achievement.id,
                    achievement.points,
                    f"Unlocked: {achievement.name}"
                )
        
        conn.close()
    
    def check_achievement_requirements(self, user_id: str, achievement: Achievement, progress: UserProgress) -> bool:
        """Check if user meets achievement requirements"""
        req = achievement.requirements
        
        if req.get("action") == "login" and req.get("count", 0) <= 1:
            return True
        elif req.get("action") == "visit_sections":
            # Check if user has visited required number of sections
            return len(progress.skill_levels) >= req.get("count", 5)
        elif req.get("module"):
            return req["module"] in progress.modules_completed
        elif req.get("modules") and req.get("all_completed"):
            return all(mod in progress.modules_completed for mod in req["modules"])
        elif req.get("action") == "daily_streak":
            return progress.current_streak >= req.get("count", 30)
        
        return False
    
    def log_activity(self, user_id: str, activity_type: str, module_id: str, points: int, details: str):
        """Log user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_log 
            (user_id, activity_type, module_id, points_earned, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, module_id, points, datetime.now().isoformat(), details))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user leaderboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, total_points, level 
            FROM user_progress 
            ORDER BY total_points DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "user_id": result[0],
                "total_points": result[1],
                "level": result[2],
                "rank": idx + 1
            }
            for idx, result in enumerate(results)
        ]

# Global instance
learning_system = GamifiedLearningSystem()

# Flask Blueprint
gamified_learning = Blueprint('gamified_learning', __name__)

@gamified_learning.route('/learning-overlay')
def learning_overlay():
    """Main learning overlay interface"""
    user_id = session.get('user_id', 'demo_user')
    progress = learning_system.get_user_progress(user_id)
    available_modules = learning_system.learning_modules
    achievements = learning_system.achievements
    leaderboard = learning_system.get_leaderboard()
    
    return render_template('learning_overlay.html',
                         progress=progress,
                         modules=available_modules,
                         achievements=achievements,
                         leaderboard=leaderboard)

@gamified_learning.route('/api/learning/start-module/<module_id>')
def start_module(module_id):
    """Start a learning module"""
    user_id = session.get('user_id', 'demo_user')
    
    module = next((m for m in learning_system.learning_modules if m.id == module_id), None)
    if not module:
        return jsonify({"error": "Module not found"}), 404
    
    # Award points for starting module
    learning_system.award_points(user_id, 5, "module_started", f"Started: {module.title}")
    
    return jsonify({
        "module": asdict(module),
        "success": True
    })

@gamified_learning.route('/api/learning/complete-step', methods=['POST'])
def complete_step():
    """Complete a learning step"""
    user_id = session.get('user_id', 'demo_user')
    data = request.get_json()
    
    module_id = data.get('module_id')
    step_index = data.get('step_index')
    
    # Award points for step completion
    points = 10 + (step_index * 2)  # Increasing points per step
    learning_system.award_points(user_id, points, "step_completed", 
                                f"Completed step {step_index + 1} in {module_id}")
    
    return jsonify({"points_awarded": points, "success": True})

@gamified_learning.route('/api/learning/complete-module', methods=['POST'])
def complete_module():
    """Complete entire learning module"""
    user_id = session.get('user_id', 'demo_user')
    data = request.get_json()
    
    module_id = data.get('module_id')
    module = next((m for m in learning_system.learning_modules if m.id == module_id), None)
    
    if not module:
        return jsonify({"error": "Module not found"}), 404
    
    progress = learning_system.get_user_progress(user_id)
    if module_id not in progress.modules_completed:
        progress.modules_completed.append(module_id)
        
        # Award completion bonus
        bonus_points = 50 if module.difficulty == "beginner" else 75 if module.difficulty == "intermediate" else 100
        learning_system.award_points(user_id, bonus_points, "module_completed", 
                                   f"Completed: {module.title}")
        
        learning_system.save_user_progress(progress)
    
    return jsonify({"bonus_points": bonus_points, "success": True})

@gamified_learning.route('/api/learning/user-stats')
def user_stats():
    """Get user learning statistics"""
    user_id = session.get('user_id', 'demo_user')
    progress = learning_system.get_user_progress(user_id)
    
    return jsonify({
        "progress": asdict(progress),
        "next_level_points": (progress.level * 200) - progress.total_points,
        "achievements_available": len([a for a in learning_system.achievements if a.id not in progress.achievements_unlocked])
    })

def get_learning_system():
    """Get the global learning system instance"""
    return learning_system