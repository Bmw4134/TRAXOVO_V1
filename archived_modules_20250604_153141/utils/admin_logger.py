"""
TRAXOVO Admin Activity Logger
Backend logging system for Watson administrative actions
"""

import os
import json
from datetime import datetime
from typing import Dict, List

class AdminLogger:
    """Centralized logging for administrative actions"""
    
    def __init__(self):
        self.log_file = 'admin_activity.log'
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Ensure log file exists"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_action(self, action: str, user: str, details: Dict = None, ip_address: str = None):
        """Log administrative action"""
        try:
            # Read existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Create new log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'user': user,
                'ip_address': ip_address or 'unknown',
                'details': details or {},
                'success': True
            }
            
            # Add to logs (keep last 1000 entries)
            logs.append(log_entry)
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Logging error: {e}")
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent administrative logs"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Return most recent logs
            return logs[-limit:] if logs else []
            
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def get_logs_by_user(self, user: str, limit: int = 50) -> List[Dict]:
        """Get logs for specific user"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Filter by user
            user_logs = [log for log in logs if log.get('user') == user]
            return user_logs[-limit:] if user_logs else []
            
        except Exception as e:
            print(f"Error reading user logs: {e}")
            return []
    
    def get_logs_summary(self) -> Dict:
        """Get summary of log activity"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            if not logs:
                return {
                    'total_actions': 0,
                    'unique_users': 0,
                    'recent_activity': 0,
                    'top_actions': []
                }
            
            # Calculate summary
            total_actions = len(logs)
            unique_users = len(set(log.get('user', 'unknown') for log in logs))
            
            # Recent activity (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp']) > yesterday
            ]
            recent_activity = len(recent_logs)
            
            # Top actions
            action_counts = {}
            for log in logs[-100:]:  # Last 100 actions
                action = log.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
            
            top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_actions': total_actions,
                'unique_users': unique_users,
                'recent_activity': recent_activity,
                'top_actions': top_actions
            }
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                'total_actions': 0,
                'unique_users': 0,
                'recent_activity': 0,
                'top_actions': []
            }

# Global logger instance
admin_logger = AdminLogger()