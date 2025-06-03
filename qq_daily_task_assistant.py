"""
QQ Enhanced Daily Task Assistant
Universal tool for task completion with Teams integration and peer collaboration
"""

import os
import json
import requests
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from dataclasses import dataclass
from typing import List, Dict, Optional

task_assistant_bp = Blueprint('task_assistant', __name__)

@dataclass
class TaskRequest:
    id: str
    user_name: str
    task_description: str
    urgency_level: str  # low, medium, high, critical
    skills_needed: List[str]
    deadline: datetime
    status: str  # open, in_progress, completed, escalated
    created_at: datetime
    responses: List[Dict]

@dataclass
class UserProfile:
    name: str
    email: str
    department: str
    skills: List[str]
    availability_status: str
    teams_id: Optional[str]

class QQDailyTaskAssistant:
    """QQ-enhanced task completion and collaboration system"""
    
    def __init__(self):
        self.active_requests = {}
        self.user_profiles = {}
        self.completed_tasks = []
        self.initialize_sample_users()
    
    def initialize_sample_users(self):
        """Initialize sample user profiles"""
        self.user_profiles = {
            "bwatson@ragleinc.com": UserProfile(
                name="Brett Watson",
                email="bwatson@ragleinc.com",
                department="Operations",
                skills=["Fleet Management", "Data Analysis", "Project Management"],
                availability_status="available",
                teams_id="brett.watson@teams"
            ),
            "admin@ragleinc.com": UserProfile(
                name="Admin User",
                email="admin@ragleinc.com",
                department="IT",
                skills=["System Administration", "Technical Support", "Database Management"],
                availability_status="available",
                teams_id="admin@teams"
            )
        }
    
    def create_task_request(self, user_email: str, task_description: str, 
                           urgency: str, skills_needed: List[str], 
                           deadline_hours: int = 24) -> str:
        """Create a new task assistance request"""
        
        request_id = f"task_{int(datetime.now().timestamp())}"
        deadline = datetime.now() + timedelta(hours=deadline_hours)
        
        task_request = TaskRequest(
            id=request_id,
            user_name=self.user_profiles.get(user_email, UserProfile("Unknown", user_email, "", [], "")).name,
            task_description=task_description,
            urgency_level=urgency,
            skills_needed=skills_needed,
            deadline=deadline,
            status="open",
            created_at=datetime.now(),
            responses=[]
        )
        
        self.active_requests[request_id] = task_request
        
        # Auto-match with available users
        potential_helpers = self._find_potential_helpers(skills_needed)
        
        # Send notifications
        self._notify_potential_helpers(task_request, potential_helpers)
        
        return request_id
    
    def _find_potential_helpers(self, skills_needed: List[str]) -> List[UserProfile]:
        """Find users with matching skills"""
        potential_helpers = []
        
        for user in self.user_profiles.values():
            if user.availability_status == "available":
                skill_match = any(skill in user.skills for skill in skills_needed)
                if skill_match:
                    potential_helpers.append(user)
        
        return potential_helpers
    
    def _notify_potential_helpers(self, task_request: TaskRequest, helpers: List[UserProfile]):
        """Send notifications to potential helpers"""
        notification_data = {
            "task_id": task_request.id,
            "description": task_request.task_description,
            "urgency": task_request.urgency_level,
            "deadline": task_request.deadline.isoformat(),
            "requester": task_request.user_name
        }
        
        for helper in helpers:
            # Log notification (in production, would send Teams message)
            print(f"📢 Notifying {helper.name} about task: {task_request.task_description}")
    
    def respond_to_task(self, task_id: str, responder_email: str, 
                       response_type: str, message: str, 
                       estimated_time: Optional[int] = None) -> bool:
        """Respond to a task request"""
        
        if task_id not in self.active_requests:
            return False
        
        task = self.active_requests[task_id]
        responder = self.user_profiles.get(responder_email)
        
        response = {
            "responder_name": responder.name if responder else "Unknown",
            "responder_email": responder_email,
            "response_type": response_type,  # offer_help, provide_info, escalate, complete
            "message": message,
            "estimated_time_minutes": estimated_time,
            "timestamp": datetime.now().isoformat()
        }
        
        task.responses.append(response)
        
        # Update task status based on response
        if response_type == "complete":
            task.status = "completed"
            self.completed_tasks.append(task)
            del self.active_requests[task_id]
        elif response_type == "offer_help":
            task.status = "in_progress"
        
        return True
    
    def get_daily_dashboard_data(self) -> Dict:
        """Get dashboard data for daily task overview"""
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate metrics
        total_active = len(self.active_requests)
        completed_today = len([t for t in self.completed_tasks 
                              if t.created_at >= today_start])
        
        urgent_tasks = len([t for t in self.active_requests.values() 
                           if t.urgency_level in ["high", "critical"]])
        
        # QQ enhancement calculations
        qq_efficiency_score = min(100, (completed_today / max(1, total_active + completed_today)) * 100)
        qq_collaboration_score = len([t for t in self.active_requests.values() if t.responses]) / max(1, total_active) * 100
        
        return {
            "total_active_requests": total_active,
            "completed_today": completed_today,
            "urgent_tasks": urgent_tasks,
            "available_helpers": len([u for u in self.user_profiles.values() 
                                    if u.availability_status == "available"]),
            "qq_efficiency_score": round(qq_efficiency_score, 1),
            "qq_collaboration_score": round(qq_collaboration_score, 1),
            "active_requests": [self._serialize_task(t) for t in self.active_requests.values()],
            "recent_completions": [self._serialize_task(t) for t in self.completed_tasks[-5:]]
        }
    
    def _serialize_task(self, task: TaskRequest) -> Dict:
        """Serialize task for JSON response"""
        return {
            "id": task.id,
            "user_name": task.user_name,
            "task_description": task.task_description,
            "urgency_level": task.urgency_level,
            "skills_needed": task.skills_needed,
            "deadline": task.deadline.isoformat(),
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "response_count": len(task.responses),
            "responses": task.responses
        }
    
    def create_teams_meeting(self, task_id: str, participants: List[str]) -> Dict:
        """Create Teams meeting for task collaboration"""
        
        # In production, would integrate with Microsoft Graph API
        meeting_data = {
            "meeting_id": f"teams_meeting_{task_id}",
            "join_url": f"https://teams.microsoft.com/l/meetup-join/{task_id}",
            "task_id": task_id,
            "participants": participants,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }
        
        return meeting_data
    
    def escalate_to_management(self, task_id: str, reason: str) -> bool:
        """Escalate task to management level"""
        
        if task_id not in self.active_requests:
            return False
        
        task = self.active_requests[task_id]
        task.status = "escalated"
        task.urgency_level = "critical"
        
        # Add escalation response
        escalation_response = {
            "responder_name": "System",
            "responder_email": "system@traxovo.com",
            "response_type": "escalate",
            "message": f"Task escalated to management. Reason: {reason}",
            "timestamp": datetime.now().isoformat()
        }
        
        task.responses.append(escalation_response)
        
        # Notify management (in production, would send alerts)
        print(f"🚨 ESCALATION: Task {task_id} escalated - {reason}")
        
        return True

# Global task assistant instance
qq_task_assistant = QQDailyTaskAssistant()

@task_assistant_bp.route('/daily_task_assistant')
def daily_task_assistant():
    """Daily Task Assistant Dashboard"""
    return render_template('daily_task_assistant.html')

@task_assistant_bp.route('/api/create_task_request', methods=['POST'])
def create_task_request():
    """API endpoint to create new task request"""
    data = request.get_json()
    
    user_email = data.get('user_email', 'unknown@ragleinc.com')
    task_description = data.get('task_description')
    urgency = data.get('urgency', 'medium')
    skills_needed = data.get('skills_needed', [])
    deadline_hours = data.get('deadline_hours', 24)
    
    if not task_description:
        return jsonify({"error": "Task description required"}), 400
    
    request_id = qq_task_assistant.create_task_request(
        user_email, task_description, urgency, skills_needed, deadline_hours
    )
    
    return jsonify({
        "success": True,
        "request_id": request_id,
        "message": "Task request created and notifications sent"
    })

@task_assistant_bp.route('/api/respond_to_task', methods=['POST'])
def respond_to_task():
    """API endpoint to respond to task"""
    data = request.get_json()
    
    task_id = data.get('task_id')
    responder_email = data.get('responder_email', 'unknown@ragleinc.com')
    response_type = data.get('response_type')
    message = data.get('message')
    estimated_time = data.get('estimated_time')
    
    success = qq_task_assistant.respond_to_task(
        task_id, responder_email, response_type, message, estimated_time
    )
    
    return jsonify({"success": success})

@task_assistant_bp.route('/api/daily_dashboard_data')
def get_daily_dashboard_data():
    """API endpoint for daily dashboard data"""
    return jsonify(qq_task_assistant.get_daily_dashboard_data())

@task_assistant_bp.route('/api/create_teams_meeting', methods=['POST'])
def create_teams_meeting():
    """API endpoint to create Teams meeting"""
    data = request.get_json()
    
    task_id = data.get('task_id')
    participants = data.get('participants', [])
    
    meeting_data = qq_task_assistant.create_teams_meeting(task_id, participants)
    return jsonify(meeting_data)

@task_assistant_bp.route('/api/escalate_task', methods=['POST'])
def escalate_task():
    """API endpoint to escalate task"""
    data = request.get_json()
    
    task_id = data.get('task_id')
    reason = data.get('reason', 'No specific reason provided')
    
    success = qq_task_assistant.escalate_to_management(task_id, reason)
    return jsonify({"success": success})

def get_qq_task_assistant():
    """Get the global task assistant instance"""
    return qq_task_assistant