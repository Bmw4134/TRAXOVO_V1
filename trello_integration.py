"""
TRAXOVO Trello Integration Module
Advanced project management and task automation with authentic fleet data
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

class TrelloIntegration:
    """Trello integration for TRAXOVO fleet management and project tracking"""
    
    def __init__(self):
        self.api_key = os.environ.get("TRELLO_API_KEY")
        self.token = os.environ.get("TRELLO_TOKEN")
        self.base_url = "https://api.trello.com/1"
        self.headers = {
            "Accept": "application/json"
        }
        
    def get_connection_status(self) -> Dict:
        """Check Trello API connection status"""
        if not self.api_key or not self.token:
            return {
                "status": "disconnected",
                "message": "Trello API credentials not configured",
                "requires_setup": True
            }
        
        try:
            response = requests.get(
                f"{self.base_url}/members/me",
                params={"key": self.api_key, "token": self.token}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "status": "connected",
                    "user": user_data.get("fullName", "Unknown"),
                    "username": user_data.get("username", ""),
                    "boards_count": len(user_data.get("idBoards", [])),
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Trello API error: {response.status_code}",
                    "requires_setup": True
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "requires_setup": True
            }
    
    def get_fleet_management_boards(self) -> List[Dict]:
        """Get Trello boards for fleet management"""
        if not self.api_key or not self.token:
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/members/me/boards",
                params={"key": self.api_key, "token": self.token}
            )
            
            if response.status_code == 200:
                boards = response.json()
                fleet_boards = []
                
                for board in boards:
                    if any(keyword in board.get("name", "").lower() 
                          for keyword in ["fleet", "asset", "maintenance", "traxovo", "ragle"]):
                        fleet_boards.append({
                            "id": board["id"],
                            "name": board["name"],
                            "url": board["url"],
                            "closed": board.get("closed", False),
                            "last_activity": board.get("dateLastActivity")
                        })
                
                return fleet_boards
            
        except Exception as e:
            print(f"Error fetching Trello boards: {e}")
            
        return []
    
    def create_fleet_management_board(self, board_name: str = "TRAXOVO Fleet Management") -> Dict:
        """Create a new Trello board for fleet management"""
        if not self.api_key or not self.token:
            return {"error": "Trello credentials not configured"}
        
        try:
            response = requests.post(
                f"{self.base_url}/boards/",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "name": board_name,
                    "desc": "TRAXOVO Fleet Management Board - Asset tracking, maintenance, and operations"
                }
            )
            
            if response.status_code == 200:
                board = response.json()
                
                # Create default lists for fleet management
                lists_to_create = [
                    "Asset Inventory",
                    "Maintenance Required",
                    "In Progress",
                    "Completed",
                    "Issues & Alerts"
                ]
                
                for list_name in lists_to_create:
                    self.create_list(board["id"], list_name)
                
                return {
                    "success": True,
                    "board": {
                        "id": board["id"],
                        "name": board["name"],
                        "url": board["url"]
                    }
                }
            
        except Exception as e:
            return {"error": f"Failed to create board: {str(e)}"}
    
    def create_list(self, board_id: str, list_name: str) -> Dict:
        """Create a list in a Trello board"""
        try:
            response = requests.post(
                f"{self.base_url}/lists",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "name": list_name,
                    "idBoard": board_id
                }
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Error creating list: {e}")
            
        return {}
    
    def create_asset_card(self, list_id: str, asset_data: Dict) -> Dict:
        """Create a Trello card for an asset"""
        if not self.api_key or not self.token:
            return {"error": "Trello credentials not configured"}
        
        try:
            card_name = f"Asset: {asset_data.get('name', 'Unknown')} - {asset_data.get('id', '')}"
            description = f"""
Asset Details:
- ID: {asset_data.get('id', 'N/A')}
- Type: {asset_data.get('type', 'N/A')}
- Status: {asset_data.get('status', 'N/A')}
- Location: {asset_data.get('location', 'N/A')}
- Last Update: {asset_data.get('last_update', 'N/A')}

Maintenance Info:
- Last Service: {asset_data.get('last_service', 'N/A')}
- Next Service Due: {asset_data.get('next_service', 'N/A')}
- Hours/Miles: {asset_data.get('usage', 'N/A')}
            """
            
            response = requests.post(
                f"{self.base_url}/cards",
                params={
                    "key": self.api_key,
                    "token": self.token,
                    "name": card_name,
                    "desc": description.strip(),
                    "idList": list_id
                }
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            return {"error": f"Failed to create card: {str(e)}"}
    
    def sync_fleet_assets_to_trello(self, board_id: str, assets_data: List[Dict]) -> Dict:
        """Sync fleet assets to Trello board"""
        if not assets_data:
            return {"error": "No asset data provided"}
        
        results = {
            "cards_created": 0,
            "cards_updated": 0,
            "errors": []
        }
        
        try:
            # Get board lists
            response = requests.get(
                f"{self.base_url}/boards/{board_id}/lists",
                params={"key": self.api_key, "token": self.token}
            )
            
            if response.status_code == 200:
                lists = response.json()
                asset_list = next((l for l in lists if "inventory" in l["name"].lower()), None)
                
                if asset_list:
                    for asset in assets_data[:10]:  # Limit to prevent API overload
                        card_result = self.create_asset_card(asset_list["id"], asset)
                        if "error" not in card_result:
                            results["cards_created"] += 1
                        else:
                            results["errors"].append(card_result["error"])
                            
        except Exception as e:
            results["errors"].append(f"Sync error: {str(e)}")
        
        return results
    
    def get_trello_dashboard_data(self) -> Dict:
        """Get comprehensive Trello dashboard data"""
        connection_status = self.get_connection_status()
        boards = self.get_fleet_management_boards()
        
        return {
            "connection": connection_status,
            "boards": boards,
            "board_count": len(boards),
            "integration_status": "active" if connection_status["status"] == "connected" else "inactive",
            "last_sync": datetime.now().isoformat(),
            "features": {
                "asset_tracking": True,
                "maintenance_cards": True,
                "project_management": True,
                "team_collaboration": True
            }
        }

def get_trello_integration():
    """Get Trello integration instance"""
    return TrelloIntegration()