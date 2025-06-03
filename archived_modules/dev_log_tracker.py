"""
Development Log Tracker for Watson Account
Tracks system changes, deployments, and development activities
"""

import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, session, jsonify

dev_log_bp = Blueprint('dev_log', __name__)

class DevLogTracker:
    def __init__(self):
        self.log_file = "dev_logs/watson_dev_log.json"
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs("dev_logs", exist_ok=True)
        if not os.path.exists(self.log_file):
            self.initialize_log_file()
    
    def initialize_log_file(self):
        """Initialize empty log file with KPI tracking"""
        initial_data = {
            "watson_account": {
                "created": datetime.now().isoformat(),
                "total_logs": 0,
                "total_dev_time": 0,
                "categories": {
                    "deployment": [],
                    "authentication": [],
                    "ui_fixes": [],
                    "module_integration": [],
                    "data_integration": [],
                    "system_health": []
                },
                "module_kpis": {
                    "fleet_map": {
                        "name": "Fleet Map",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "active",
                        "performance_score": 95,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "driver_attendance": {
                        "name": "Driver Attendance",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 92,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "equipment_billing": {
                        "name": "Equipment Billing",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 88,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "job_sites": {
                        "name": "Job Sites",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 90,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "may_reporting": {
                        "name": "May Reporting",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 85,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "system_admin": {
                        "name": "System Admin",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 93,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "workflow_optimization": {
                        "name": "Workflow Optimization",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 87,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "kaizen": {
                        "name": "Kaizen",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 89,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    },
                    "asset_manager": {
                        "name": "Asset Manager",
                        "total_time": 0,
                        "sessions": 0,
                        "last_activity": None,
                        "status": "stable",
                        "performance_score": 91,
                        "error_count": 0,
                        "api_calls": 0,
                        "load_time": 0.0
                    }
                },
                "deployment_metrics": {
                    "total_deployments": 0,
                    "successful_deployments": 0,
                    "failed_deployments": 0,
                    "average_deployment_time": 0.0,
                    "uptime_percentage": 99.9,
                    "last_deployment": None
                },
                "performance_metrics": {
                    "total_requests": 0,
                    "average_response_time": 0.0,
                    "error_rate": 0.0,
                    "peak_concurrent_users": 0,
                    "data_processed_mb": 0.0
                }
            }
        }
        with open(self.log_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    def add_log_entry(self, category, title, description, severity="info"):
        """Add a new log entry"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            self.initialize_log_file()
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "description": description,
            "severity": severity,
            "user": session.get('username', 'system'),
            "id": data["watson_account"]["total_logs"] + 1
        }
        
        if category not in data["watson_account"]["categories"]:
            data["watson_account"]["categories"][category] = []
        
        data["watson_account"]["categories"][category].insert(0, entry)
        data["watson_account"]["total_logs"] += 1
        
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return entry
    
    def get_recent_logs(self, limit=20):
        """Get recent log entries across all categories"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            all_logs = []
            for category, logs in data["watson_account"]["categories"].items():
                for log in logs:
                    log["category"] = category
                    all_logs.append(log)
            
            all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return all_logs[:limit]
        except:
            return []
    
    def get_logs_by_category(self, category):
        """Get logs for specific category"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            return data["watson_account"]["categories"].get(category, [])
        except:
            return []

# Global tracker instance
dev_tracker = DevLogTracker()

@dev_log_bp.route('/dev-log')
def dev_log_dashboard():
    """Development log dashboard for Watson"""
    if session.get('username') != 'watson':
        return "Access denied. Watson account required.", 403
    
    recent_logs = dev_tracker.get_recent_logs(50)
    return render_template('dev_log_dashboard.html', logs=recent_logs)

@dev_log_bp.route('/api/dev-log/add', methods=['POST'])
def add_dev_log():
    """Add new development log entry"""
    if session.get('username') != 'watson':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    entry = dev_tracker.add_log_entry(
        category=data.get('category', 'system_health'),
        title=data.get('title', ''),
        description=data.get('description', ''),
        severity=data.get('severity', 'info')
    )
    
    return jsonify({'success': True, 'entry': entry})

@dev_log_bp.route('/api/dev-log/category/<category>')
def get_category_logs(category):
    """Get logs for specific category"""
    if session.get('username') != 'watson':
        return jsonify({'error': 'Access denied'}), 403
    
    logs = dev_tracker.get_logs_by_category(category)
    return jsonify({'logs': logs})

# Auto-log system events
def log_system_event(category, title, description, severity="info"):
    """Auto-log system events"""
    try:
        dev_tracker.add_log_entry(category, title, description, severity)
    except:
        pass  # Silently fail if no request context