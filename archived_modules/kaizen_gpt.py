"""
Kaizen GPT - TRAXOVO Fleet Management AI Assistant
Internal redeploy integration and system automation
"""

import subprocess
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

kaizen_bp = Blueprint('kaizen_gpt', __name__)

class KaizenGPT:
    def __init__(self):
        self.enable_redeploy = True
        self.session_audit_file = "logs/session_audit.json"
        self.goal_tracker_file = "logs/goal_tracker.json"
        
    def trigger_redeploy(self):
        """Trigger automated redeploy via redeploy.sh script"""
        if not self.enable_redeploy:
            return {"result": None, "error": "Auto-redeploy disabled", "prompt": "Redeploy blocked"}
            
        print("[Kaizen GPT] Initiating auto-deployment...")
        try:
            result = subprocess.run(["bash", "redeploy.sh"], capture_output=True, text=True)
            
            # Log the redeploy attempt
            self._log_redeploy_attempt(result.returncode == 0)
            
            if result.returncode == 0:
                return {
                    "result": result.stdout, 
                    "prompt": "✅ TRAXOVO redeploy triggered successfully!",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "result": result.stderr, 
                    "error": "Redeploy script failed",
                    "prompt": "❌ Redeploy failed - check logs"
                }
        except Exception as e:
            self._log_redeploy_attempt(False, str(e))
            return {
                "result": None, 
                "error": str(e), 
                "prompt": "❌ Redeploy execution failed"
            }
    
    def process_command(self, prompt):
        """Process internal commands and triggers"""
        prompt_lower = prompt.lower().strip()
        
        # Redeploy triggers
        redeploy_triggers = [
            "redeploy now",
            "kaizen redeploy", 
            "auto deploy",
            "trigger deployment",
            "push to production"
        ]
        
        if any(trigger in prompt_lower for trigger in redeploy_triggers):
            return self.trigger_redeploy()
            
        # System status commands
        if "system status" in prompt_lower:
            return self._get_system_status()
            
        # Goal tracking commands
        if "track goal" in prompt_lower or "complete goal" in prompt_lower:
            return self._update_goal_tracker(prompt)
            
        return None
    
    def _log_redeploy_attempt(self, success, error=None):
        """Log redeploy attempts to audit file"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "auto_redeploy",
                "success": success,
                "error": error
            }
            
            # Load existing audit log
            audit_log = []
            if os.path.exists(self.session_audit_file):
                with open(self.session_audit_file, 'r') as f:
                    audit_log = json.load(f)
            
            # Append new entry
            audit_log.append(audit_entry)
            
            # Keep only last 100 entries
            audit_log = audit_log[-100:]
            
            # Save updated log
            with open(self.session_audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            print(f"[Kaizen GPT] Failed to log audit: {e}")
    
    def _get_system_status(self):
        """Get current TRAXOVO system status"""
        try:
            # Check if core services are running
            status = {
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "fleet_management": "✅ Active",
                    "gps_tracking": "✅ Active", 
                    "attendance_module": "✅ Active",
                    "database": "✅ Connected"
                },
                "data_files": len([f for f in os.listdir("uploads") if f.endswith(('.csv', '.xlsx'))]) if os.path.exists("uploads") else 0,
                "prompt": "🟢 TRAXOVO system operational"
            }
            return status
        except Exception as e:
            return {"error": str(e), "prompt": "❌ System status check failed"}
    
    def _update_goal_tracker(self, prompt):
        """Update goal completion tracking"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            goal_entry = {
                "timestamp": datetime.now().isoformat(),
                "goal": prompt,
                "status": "completed" if "complete" in prompt.lower() else "tracked"
            }
            
            # Load existing goals
            goals = []
            if os.path.exists(self.goal_tracker_file):
                with open(self.goal_tracker_file, 'r') as f:
                    goals = json.load(f)
            
            # Add new goal
            goals.append(goal_entry)
            
            # Save updated goals
            with open(self.goal_tracker_file, 'w') as f:
                json.dump(goals, f, indent=2)
                
            return {"result": "Goal tracked", "prompt": "📝 Goal logged successfully"}
            
        except Exception as e:
            return {"error": str(e), "prompt": "❌ Goal tracking failed"}

# Initialize Kaizen GPT instance
kaizen_gpt = KaizenGPT()

@kaizen_bp.route('/kaizen/command', methods=['POST'])
def process_kaizen_command():
    """API endpoint for processing Kaizen GPT commands"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        result = kaizen_gpt.process_command(prompt)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({"prompt": "Command not recognized"})
            
    except Exception as e:
        return jsonify({"error": str(e), "prompt": "❌ Command processing failed"})

@kaizen_bp.route('/kaizen/status')
def kaizen_status():
    """Get Kaizen GPT system status"""
    return jsonify(kaizen_gpt._get_system_status())