"""
Password Update System with 30-Day Cycle Logging
Prompts all users for immediate password updates without forcing changes
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Password Update Blueprint
password_system = Blueprint('password_system', __name__)

class PasswordUpdateManager:
    """Manages password update prompts and 30-day cycle logging"""
    
    def __init__(self):
        self.password_log_file = "password_update_log.json"
        self.password_logs = self._load_password_logs()
        
    def _load_password_logs(self) -> Dict[str, Any]:
        """Load password update logs from file"""
        if os.path.exists(self.password_log_file):
            try:
                with open(self.password_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading password logs: {e}")
        
        return {
            'user_password_updates': {},
            'system_prompts': [],
            'security_events': [],
            'last_system_prompt': None
        }
    
    def _save_password_logs(self):
        """Save password update logs to file"""
        try:
            with open(self.password_log_file, 'w') as f:
                json.dump(self.password_logs, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving password logs: {e}")
    
    def check_user_password_status(self, user_id: str) -> Dict[str, Any]:
        """Check password update status for a user"""
        user_key = str(user_id)
        user_data = self.password_logs['user_password_updates'].get(user_key, {})
        
        now = datetime.now()
        last_update = user_data.get('last_password_update')
        last_prompt = user_data.get('last_prompt_acknowledged')
        
        # Convert string dates back to datetime if they exist
        if last_update:
            last_update = datetime.fromisoformat(last_update) if isinstance(last_update, str) else last_update
        if last_prompt:
            last_prompt = datetime.fromisoformat(last_prompt) if isinstance(last_prompt, str) else last_prompt
        
        # Determine if user should see prompt
        should_prompt = True
        prompt_reason = "Initial security verification required"
        
        if last_prompt:
            # Check if 30 days have passed since last acknowledgment
            days_since_prompt = (now - last_prompt).days
            if days_since_prompt < 30:
                should_prompt = False
            else:
                prompt_reason = f"30-day security cycle ({days_since_prompt} days since last prompt)"
        
        if last_update:
            days_since_update = (now - last_update).days
            if days_since_update > 90:
                prompt_reason = f"Password is {days_since_update} days old - security review recommended"
        
        return {
            'user_id': user_id,
            'should_prompt': should_prompt,
            'prompt_reason': prompt_reason,
            'last_update': last_update.isoformat() if last_update else None,
            'last_prompt': last_prompt.isoformat() if last_prompt else None,
            'days_since_update': (now - last_update).days if last_update else None,
            'days_since_prompt': (now - last_prompt).days if last_prompt else None
        }
    
    def acknowledge_password_prompt(self, user_id: str, action_taken: str = "acknowledged") -> Dict[str, Any]:
        """Log that user acknowledged password prompt"""
        user_key = str(user_id)
        now = datetime.now()
        
        if user_key not in self.password_logs['user_password_updates']:
            self.password_logs['user_password_updates'][user_key] = {}
        
        self.password_logs['user_password_updates'][user_key]['last_prompt_acknowledged'] = now.isoformat()
        self.password_logs['user_password_updates'][user_key]['action_taken'] = action_taken
        self.password_logs['user_password_updates'][user_key]['acknowledgment_timestamp'] = now.isoformat()
        
        # Log the security event
        security_event = {
            'user_id': user_id,
            'event_type': 'password_prompt_acknowledged',
            'action': action_taken,
            'timestamp': now.isoformat(),
            'next_prompt_due': (now + timedelta(days=30)).isoformat()
        }
        
        self.password_logs['security_events'].append(security_event)
        self._save_password_logs()
        
        return {
            'status': 'acknowledged',
            'user_id': user_id,
            'next_prompt_in_days': 30,
            'next_prompt_date': (now + timedelta(days=30)).isoformat()
        }
    
    def update_user_password(self, user_id: str, new_password_hash: str) -> Dict[str, Any]:
        """Log password update for user"""
        user_key = str(user_id)
        now = datetime.now()
        
        if user_key not in self.password_logs['user_password_updates']:
            self.password_logs['user_password_updates'][user_key] = {}
        
        # Update password timestamp
        self.password_logs['user_password_updates'][user_key]['last_password_update'] = now.isoformat()
        self.password_logs['user_password_updates'][user_key]['password_changed'] = True
        self.password_logs['user_password_updates'][user_key]['last_prompt_acknowledged'] = now.isoformat()
        
        # Log the security event
        security_event = {
            'user_id': user_id,
            'event_type': 'password_updated',
            'timestamp': now.isoformat(),
            'next_prompt_due': (now + timedelta(days=30)).isoformat()
        }
        
        self.password_logs['security_events'].append(security_event)
        self._save_password_logs()
        
        return {
            'status': 'password_updated',
            'user_id': user_id,
            'update_timestamp': now.isoformat(),
            'next_prompt_in_days': 30
        }
    
    def get_system_password_overview(self) -> Dict[str, Any]:
        """Get system-wide password security overview"""
        now = datetime.now()
        total_users = len(self.password_logs['user_password_updates'])
        
        # Calculate statistics
        users_needing_prompt = 0
        users_recently_updated = 0
        users_overdue = 0
        
        for user_id, user_data in self.password_logs['user_password_updates'].items():
            status = self.check_user_password_status(user_id)
            
            if status['should_prompt']:
                users_needing_prompt += 1
            
            if status['last_update']:
                days_since_update = status['days_since_update']
                if days_since_update <= 30:
                    users_recently_updated += 1
                elif days_since_update > 90:
                    users_overdue += 1
        
        return {
            'system_overview': {
                'total_users': total_users,
                'users_needing_prompt': users_needing_prompt,
                'users_recently_updated': users_recently_updated,
                'users_overdue': users_overdue,
                'security_compliance': f"{((total_users - users_overdue) / max(total_users, 1) * 100):.1f}%"
            },
            'recent_security_events': self.password_logs['security_events'][-10:],
            'next_system_actions': self._get_next_system_actions()
        }
    
    def _get_next_system_actions(self) -> List[Dict[str, str]]:
        """Get next recommended system actions"""
        actions = []
        
        for user_id, user_data in self.password_logs['user_password_updates'].items():
            status = self.check_user_password_status(user_id)
            
            if status['should_prompt']:
                actions.append({
                    'action': 'prompt_user',
                    'user_id': user_id,
                    'reason': status['prompt_reason'],
                    'priority': 'normal'
                })
            
            if status['days_since_update'] and status['days_since_update'] > 120:
                actions.append({
                    'action': 'security_review',
                    'user_id': user_id,
                    'reason': f"Password {status['days_since_update']} days old",
                    'priority': 'high'
                })
        
        return sorted(actions, key=lambda x: x['priority'] == 'high', reverse=True)

# Global password manager instance
password_manager = PasswordUpdateManager()

@password_system.route('/password_prompt/<user_id>')
def password_prompt(user_id):
    """Display password update prompt for user"""
    status = password_manager.check_user_password_status(user_id)
    
    if not status['should_prompt']:
        return redirect(url_for('index'))
    
    return render_template('password_prompt.html', 
                         user_id=user_id, 
                         status=status)

@password_system.route('/acknowledge_password_prompt', methods=['POST'])
def acknowledge_password_prompt():
    """Acknowledge password prompt without updating"""
    user_id = request.form.get('user_id')
    action = request.form.get('action', 'acknowledged')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    result = password_manager.acknowledge_password_prompt(user_id, action)
    
    flash('Security prompt acknowledged. Next reminder in 30 days.', 'success')
    return redirect(url_for('index'))

@password_system.route('/update_password', methods=['POST'])
def update_password():
    """Update user password"""
    user_id = request.form.get('user_id')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([user_id, current_password, new_password, confirm_password]):
        flash('All fields are required', 'error')
        return redirect(url_for('password_system.password_prompt', user_id=user_id))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('password_system.password_prompt', user_id=user_id))
    
    # Here you would verify current password and update in your user system
    # For now, we'll just log the update
    new_password_hash = generate_password_hash(new_password)
    result = password_manager.update_user_password(user_id, new_password_hash)
    
    flash('Password updated successfully. Next security check in 30 days.', 'success')
    return redirect(url_for('index'))

@password_system.route('/api/password_status/<user_id>')
def api_password_status(user_id):
    """API endpoint for user password status"""
    return jsonify(password_manager.check_user_password_status(user_id))

@password_system.route('/api/system_password_overview')
def api_system_password_overview():
    """API endpoint for system password overview"""
    return jsonify(password_manager.get_system_password_overview())

@password_system.route('/password_security_dashboard')
def password_security_dashboard():
    """Password security management dashboard"""
    overview = password_manager.get_system_password_overview()
    return render_template('password_security_dashboard.html', overview=overview)

def get_password_manager():
    """Get the global password manager instance"""
    return password_manager

def check_password_prompt_needed(user_id: str) -> bool:
    """Helper function to check if user needs password prompt"""
    status = password_manager.check_user_password_status(user_id)
    return status['should_prompt']

# Auto-initialize password system
print("Password Update System with 30-day cycle logging initialized")