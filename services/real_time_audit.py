"""
Real-Time Development Audit System
Monitors all changes, metric updates, and data modifications in real-time
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import threading
import logging

class RealTimeAudit:
    """Real-time audit system for development monitoring"""
    
    def __init__(self):
        self.audit_log = []
        self.active_changes = {}
        self.data_changes = {}
        self.metric_changes = {}
        self.file_changes = {}
        self.lock = threading.Lock()
        
    def log_change(self, category: str, action: str, details: Dict[str, Any]):
        """Log any development change in real-time"""
        with self.lock:
            change_entry = {
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'action': action,
                'details': details,
                'id': f"{category}_{int(time.time() * 1000)}"
            }
            
            self.audit_log.append(change_entry)
            
            # Keep only last 100 entries for performance
            if len(self.audit_log) > 100:
                self.audit_log = self.audit_log[-100:]
                
            # Update category-specific tracking
            if category == 'data':
                self.data_changes[change_entry['id']] = change_entry
            elif category == 'metrics':
                self.metric_changes[change_entry['id']] = change_entry
            elif category == 'file':
                self.file_changes[change_entry['id']] = change_entry
                
            logging.info(f"AUDIT: {category} - {action} - {details}")
    
    def log_metric_update(self, metric_name: str, old_value: Any, new_value: Any, source: str):
        """Log metric changes"""
        self.log_change('metrics', 'update', {
            'metric': metric_name,
            'old_value': old_value,
            'new_value': new_value,
            'source': source,
            'change_type': 'value_update'
        })
    
    def log_data_source_change(self, source: str, operation: str, record_count: int = None):
        """Log data source modifications"""
        self.log_change('data', 'source_change', {
            'source': source,
            'operation': operation,
            'record_count': record_count,
            'authentic_data': True
        })
    
    def log_file_modification(self, file_path: str, modification_type: str, lines_changed: int = None):
        """Log file changes"""
        self.log_change('file', 'modification', {
            'file': file_path,
            'type': modification_type,
            'lines_changed': lines_changed
        })
    
    def log_api_call(self, endpoint: str, status: str, response_time: float = None):
        """Log API interactions"""
        self.log_change('api', 'call', {
            'endpoint': endpoint,
            'status': status,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_recent_changes(self, limit: int = 20) -> List[Dict]:
        """Get recent changes for real-time display"""
        with self.lock:
            return self.audit_log[-limit:] if self.audit_log else []
    
    def get_changes_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get changes filtered by category"""
        with self.lock:
            filtered = [entry for entry in self.audit_log if entry['category'] == category]
            return filtered[-limit:] if filtered else []
    
    def get_current_metrics_state(self) -> Dict:
        """Get current state of all tracked metrics"""
        return {
            'total_changes': len(self.audit_log),
            'data_changes': len(self.data_changes),
            'metric_changes': len(self.metric_changes),
            'file_changes': len(self.file_changes),
            'last_update': datetime.now().isoformat()
        }
    
    def export_audit_log(self) -> str:
        """Export full audit log as JSON"""
        with self.lock:
            return json.dumps({
                'audit_log': self.audit_log,
                'summary': self.get_current_metrics_state(),
                'exported_at': datetime.now().isoformat()
            }, indent=2)

# Global audit instance
audit_system = RealTimeAudit()

def get_audit_system():
    """Get the global audit system instance"""
    return audit_system