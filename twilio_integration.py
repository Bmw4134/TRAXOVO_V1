"""
TRAXOVO Twilio Integration Module
SMS notifications for fleet management, alerts, and driver communication
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class TwilioIntegration:
    """Twilio SMS integration for TRAXOVO fleet management notifications"""
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
    def get_connection_status(self) -> Dict:
        """Check Twilio API connection status"""
        if not self.account_sid or not self.auth_token or not self.phone_number:
            return {
                "status": "disconnected",
                "message": "Twilio credentials not configured",
                "requires_setup": True,
                "missing_credentials": [
                    cred for cred in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
                    if not os.environ.get(cred)
                ]
            }
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            # Test connection by fetching account info
            account = client.api.accounts(self.account_sid).fetch()
            
            return {
                "status": "connected",
                "account_name": account.friendly_name,
                "account_status": account.status,
                "phone_number": self.phone_number,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Twilio connection failed: {str(e)}",
                "requires_setup": True
            }
    
    def send_fleet_alert(self, to_number: str, message: str, alert_type: str = "general") -> Dict:
        """Send SMS alert for fleet management"""
        if not self.account_sid or not self.auth_token or not self.phone_number:
            return {"error": "Twilio credentials not configured"}
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            # Format message with TRAXOVO branding
            formatted_message = f"TRAXOVO Alert [{alert_type.upper()}]: {message}"
            
            message = client.messages.create(
                body=formatted_message,
                from_=self.phone_number,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_number,
                "sent_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to send SMS: {str(e)}"}
    
    def send_maintenance_reminder(self, driver_phone: str, asset_id: str, maintenance_type: str) -> Dict:
        """Send maintenance reminder SMS to driver"""
        message = f"Maintenance reminder for asset {asset_id}: {maintenance_type} is due. Please contact fleet management."
        return self.send_fleet_alert(driver_phone, message, "maintenance")
    
    def send_route_update(self, driver_phone: str, route_info: str) -> Dict:
        """Send route update SMS to driver"""
        message = f"Route update: {route_info}"
        return self.send_fleet_alert(driver_phone, message, "route")
    
    def send_emergency_alert(self, phone_numbers: List[str], emergency_message: str) -> Dict:
        """Send emergency alert to multiple recipients"""
        results = []
        
        for phone in phone_numbers:
            result = self.send_fleet_alert(phone, emergency_message, "emergency")
            results.append({
                "phone": phone,
                "result": result
            })
        
        return {
            "total_sent": len([r for r in results if "success" in r["result"]]),
            "total_failed": len([r for r in results if "error" in r["result"]]),
            "details": results
        }
    
    def get_message_history(self, limit: int = 20) -> List[Dict]:
        """Get recent SMS message history"""
        if not self.account_sid or not self.auth_token:
            return []
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            messages = client.messages.list(limit=limit)
            
            history = []
            for msg in messages:
                history.append({
                    "sid": msg.sid,
                    "to": msg.to,
                    "from": msg.from_,
                    "body": msg.body,
                    "status": msg.status,
                    "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                    "direction": msg.direction
                })
            
            return history
            
        except Exception as e:
            print(f"Error fetching message history: {e}")
            return []
    
    def get_usage_statistics(self) -> Dict:
        """Get Twilio usage statistics"""
        if not self.account_sid or not self.auth_token:
            return {"error": "Twilio credentials not configured"}
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            # Get account balance
            balance = client.balance.fetch()
            
            # Get recent messages count
            messages = client.messages.list(limit=50)
            
            return {
                "account_balance": balance.balance,
                "currency": balance.currency,
                "recent_messages": len(messages),
                "active_phone_number": self.phone_number,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to get usage stats: {str(e)}"}
    
    def get_twilio_dashboard_data(self) -> Dict:
        """Get comprehensive Twilio dashboard data"""
        connection_status = self.get_connection_status()
        usage_stats = self.get_usage_statistics() if connection_status["status"] == "connected" else {}
        message_history = self.get_message_history(10) if connection_status["status"] == "connected" else []
        
        return {
            "connection": connection_status,
            "usage": usage_stats,
            "recent_messages": message_history,
            "message_count": len(message_history),
            "integration_status": "active" if connection_status["status"] == "connected" else "inactive",
            "features": {
                "fleet_alerts": True,
                "maintenance_reminders": True,
                "route_updates": True,
                "emergency_notifications": True,
                "driver_communication": True
            }
        }

def get_twilio_integration():
    """Get Twilio integration instance"""
    return TwilioIntegration()