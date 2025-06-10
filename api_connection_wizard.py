"""
TRAXOVO API Connection Wizard
One-click API setup and configuration system
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from free_api_integrations import FreeAPIIntegrations

class APIConnectionWizard:
    """One-click API connection and setup wizard"""
    
    def __init__(self):
        self.api_integrations = FreeAPIIntegrations()
        self.connection_history = []
        self.mascot_responses = self._initialize_mascot()
        
    def _initialize_mascot(self) -> Dict:
        """Initialize API mascot guide with helpful tips"""
        return {
            "name": "NEXUS Bot",
            "personality": "Helpful and enthusiastic",
            "welcome_message": "Hi there! I'm NEXUS Bot, your friendly API guide. Let me help you connect to amazing free APIs!",
            "tips": {
                "weather": "🌤️ Weather data helps optimize fleet operations - perfect for planning equipment deployment!",
                "market": "📈 Market intelligence keeps you ahead of currency fluctuations and crypto trends!",
                "fuel": "⛽ Fuel price tracking can save thousands in fleet operating costs!",
                "tech": "🚀 Technology trends help you discover the latest fleet management innovations!",
                "time": "🕐 Time coordination is crucial for global operations - never miss a deadline!",
                "public": "🌍 Geographic data provides valuable insights for expansion planning!"
            },
            "encouragement": [
                "Great choice! This API will supercharge your operations!",
                "Excellent! You're building a powerful intelligence network!",
                "Smart move! This data will give you a competitive edge!",
                "Perfect! Your fleet management just got an upgrade!",
                "Outstanding! You're making data-driven decisions!"
            ]
        }
    
    def start_connection_wizard(self) -> Dict:
        """Start the one-click connection wizard"""
        return {
            "wizard_title": "TRAXOVO API Connection Wizard",
            "mascot": {
                "name": self.mascot_responses["name"],
                "message": self.mascot_responses["welcome_message"],
                "avatar": "🤖"
            },
            "available_apis": self._get_available_apis(),
            "wizard_steps": [
                "Select APIs to connect",
                "Automatic connection testing",
                "Configuration optimization",
                "Integration completion"
            ],
            "estimated_time": "30 seconds",
            "difficulty": "Beginner-friendly",
            "started_at": datetime.now().isoformat()
        }
    
    def _get_available_apis(self) -> List[Dict]:
        """Get list of available APIs with connection info"""
        return [
            {
                "id": "weather_intelligence",
                "name": "Weather Intelligence",
                "icon": "🌤️",
                "description": "Real-time weather for fleet operations",
                "setup_time": "5 seconds",
                "complexity": "Easy",
                "value": "High",
                "mascot_tip": self.mascot_responses["tips"]["weather"]
            },
            {
                "id": "market_intelligence", 
                "name": "Market Intelligence",
                "icon": "📈",
                "description": "Financial markets and crypto data",
                "setup_time": "3 seconds",
                "complexity": "Easy",
                "value": "Medium",
                "mascot_tip": self.mascot_responses["tips"]["market"]
            },
            {
                "id": "fuel_price_intelligence",
                "name": "Fuel Price Intelligence", 
                "icon": "⛽",
                "description": "Fleet fuel cost optimization",
                "setup_time": "2 seconds",
                "complexity": "Easy",
                "value": "Very High",
                "mascot_tip": self.mascot_responses["tips"]["fuel"]
            },
            {
                "id": "technology_intelligence",
                "name": "Technology Intelligence",
                "icon": "🚀", 
                "description": "Tech trends and innovations",
                "setup_time": "4 seconds",
                "complexity": "Easy",
                "value": "Medium",
                "mascot_tip": self.mascot_responses["tips"]["tech"]
            },
            {
                "id": "time_intelligence",
                "name": "Time Intelligence",
                "icon": "🕐",
                "description": "Global time coordination",
                "setup_time": "2 seconds", 
                "complexity": "Easy",
                "value": "High",
                "mascot_tip": self.mascot_responses["tips"]["time"]
            },
            {
                "id": "public_data_intelligence",
                "name": "Public Data Intelligence",
                "icon": "🌍",
                "description": "Geographic and institutional data",
                "setup_time": "3 seconds",
                "complexity": "Easy", 
                "value": "Medium",
                "mascot_tip": self.mascot_responses["tips"]["public"]
            }
        ]
    
    def connect_api(self, api_id: str) -> Dict:
        """One-click API connection"""
        start_time = time.time()
        
        # Simulate connection process with real testing
        connection_steps = [
            {"step": "Initializing connection", "progress": 10},
            {"step": "Testing API endpoint", "progress": 30},
            {"step": "Validating response", "progress": 60},
            {"step": "Optimizing configuration", "progress": 80},
            {"step": "Connection complete", "progress": 100}
        ]
        
        try:
            # Test the actual API
            if api_id == "weather_intelligence":
                result = self.api_integrations.get_weather_intelligence()
            elif api_id == "market_intelligence":
                result = self.api_integrations.get_market_intelligence()
            elif api_id == "fuel_price_intelligence":
                result = self.api_integrations.get_fuel_price_intelligence()
            elif api_id == "technology_intelligence":
                result = self.api_integrations.get_tech_intelligence()
            elif api_id == "time_intelligence":
                result = self.api_integrations.get_time_intelligence()
            elif api_id == "public_data_intelligence":
                result = self.api_integrations.get_public_data_intelligence()
            else:
                return {"error": f"Unknown API: {api_id}"}
            
            connection_time = round(time.time() - start_time, 2)
            success = result.get("status") == "success"
            
            # Record connection attempt
            connection_record = {
                "api_id": api_id,
                "connected_at": datetime.now().isoformat(),
                "success": success,
                "connection_time": connection_time,
                "test_result": result
            }
            self.connection_history.append(connection_record)
            
            if success:
                mascot_message = self.mascot_responses["encouragement"][
                    len(self.connection_history) % len(self.mascot_responses["encouragement"])
                ]
            else:
                mascot_message = "Don't worry! Let's troubleshoot this together. The API might be temporarily unavailable."
            
            return {
                "connection_status": "success" if success else "failed",
                "api_id": api_id,
                "connection_steps": connection_steps,
                "connection_time": f"{connection_time}s",
                "test_result": result,
                "mascot": {
                    "message": mascot_message,
                    "avatar": "🎉" if success else "🔧"
                },
                "next_steps": self._get_next_steps(api_id, success),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "connection_status": "error",
                "api_id": api_id,
                "error": str(e),
                "mascot": {
                    "message": "Oops! Something unexpected happened. Let's try again!",
                    "avatar": "🤔"
                },
                "troubleshooting": self._get_troubleshooting_tips(api_id)
            }
    
    def _get_next_steps(self, api_id: str, success: bool) -> List[str]:
        """Get recommended next steps after connection"""
        if success:
            return [
                f"✓ {api_id.replace('_', ' ').title()} is now active",
                "Configure automatic data refresh intervals",
                "Set up alerts and notifications",
                "Explore advanced features",
                "Connect more APIs for comprehensive intelligence"
            ]
        else:
            return [
                "Check internet connectivity",
                "Retry connection in a few moments", 
                "Contact support if issue persists",
                "Try connecting other APIs in the meantime"
            ]
    
    def _get_troubleshooting_tips(self, api_id: str) -> List[str]:
        """Get troubleshooting tips for API connection issues"""
        return [
            "Verify internet connection is stable",
            "Check if API provider is experiencing downtime",
            "Ensure firewall isn't blocking requests",
            "Try refreshing the page and reconnecting",
            "Contact TRAXOVO support for assistance"
        ]
    
    def connect_all_apis(self) -> Dict:
        """One-click connect all available APIs"""
        start_time = time.time()
        connection_results = {}
        
        available_apis = self._get_available_apis()
        
        for i, api in enumerate(available_apis):
            api_id = api["id"]
            connection_result = self.connect_api(api_id)
            connection_results[api_id] = connection_result
            
            # Update progress
            progress = round(((i + 1) / len(available_apis)) * 100)
            
        total_time = round(time.time() - start_time, 2)
        successful_connections = sum(1 for result in connection_results.values() 
                                   if result.get("connection_status") == "success")
        
        return {
            "bulk_connection_status": "completed",
            "total_apis": len(available_apis),
            "successful_connections": successful_connections,
            "failed_connections": len(available_apis) - successful_connections,
            "success_rate": round((successful_connections / len(available_apis)) * 100, 1),
            "total_time": f"{total_time}s",
            "connection_results": connection_results,
            "mascot": {
                "message": f"Amazing! You've connected {successful_connections} APIs in just {total_time} seconds!",
                "avatar": "🚀"
            },
            "completed_at": datetime.now().isoformat()
        }
    
    def get_connection_history(self) -> Dict:
        """Get API connection history and statistics"""
        if not self.connection_history:
            return {
                "message": "No API connections yet",
                "mascot": {
                    "message": "Ready to connect your first API? Let's get started!",
                    "avatar": "🌟"
                }
            }
        
        successful_connections = [c for c in self.connection_history if c["success"]]
        avg_connection_time = sum(c["connection_time"] for c in self.connection_history) / len(self.connection_history)
        
        return {
            "connection_summary": {
                "total_attempts": len(self.connection_history),
                "successful_connections": len(successful_connections),
                "success_rate": round((len(successful_connections) / len(self.connection_history)) * 100, 1),
                "average_connection_time": round(avg_connection_time, 2)
            },
            "recent_connections": self.connection_history[-5:],  # Last 5 connections
            "connection_timeline": self._generate_connection_timeline(),
            "mascot": {
                "message": f"You've successfully connected {len(successful_connections)} APIs! Your fleet intelligence is growing!",
                "avatar": "📊"
            }
        }
    
    def _generate_connection_timeline(self) -> List[Dict]:
        """Generate visual timeline of connections"""
        timeline = []
        for connection in self.connection_history:
            timeline.append({
                "timestamp": connection["connected_at"],
                "api": connection["api_id"].replace("_", " ").title(),
                "status": "✓" if connection["success"] else "✗",
                "time": f"{connection['connection_time']}s"
            })
        return timeline

def get_api_connection_wizard():
    """Get API connection wizard instance"""
    return APIConnectionWizard()

if __name__ == "__main__":
    wizard = get_api_connection_wizard()
    start_info = wizard.start_connection_wizard()
    print(json.dumps(start_info, indent=2))