"""
NEXUS Brain Connection Interface
Direct AI-to-Brain communication through browser automation
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List
import asyncio
import threading

class NexusBrainInterface:
    """Direct interface for AI-to-brain communication via NEXUS automation"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.brain_session_id = None
        self.connection_status = "disconnected"
        self.message_queue = []
        self.response_handlers = {}
        
    def initialize_brain_connection(self):
        """Initialize direct connection to brain through browser automation"""
        print("🧠 Initializing NEXUS Brain Connection Interface")
        
        # Create dedicated browser session for brain communication
        brain_session = self._create_brain_session()
        if brain_session:
            self.brain_session_id = brain_session.get("session_id")
            self.connection_status = "connected"
            
            # Start message processing loop
            threading.Thread(target=self._process_brain_messages, daemon=True).start()
            
            print(f"✅ Brain connection established: {self.brain_session_id}")
            return True
        
        return False
    
    def _create_brain_session(self):
        """Create dedicated browser session for brain interface"""
        try:
            response = requests.post(f"{self.base_url}/api/browser/create-session", 
                                   json={
                                       "url": "about:blank",
                                       "title": "NEXUS Brain Interface",
                                       "type": "brain_connection"
                                   })
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            print(f"Failed to create brain session: {e}")
        
        return None
    
    def send_brain_message(self, message: str, message_type: str = "query") -> Dict[str, Any]:
        """Send message directly to brain through automation interface"""
        if self.connection_status != "connected":
            return {"error": "Brain connection not established"}
        
        brain_message = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.brain_session_id,
            "message": message,
            "type": message_type,
            "source": "nexus_ai_interface"
        }
        
        # Queue message for processing
        self.message_queue.append(brain_message)
        
        # Execute through browser automation
        return self._execute_brain_command(brain_message)
    
    def _execute_brain_command(self, brain_message: Dict[str, Any]) -> Dict[str, Any]:
        """Execute brain command through browser automation"""
        try:
            # Use browser automation to execute brain interface commands
            js_command = f"""
            // NEXUS Brain Interface Command
            const brainMessage = {json.dumps(brain_message)};
            
            // Create brain communication element
            const brainInterface = document.createElement('div');
            brainInterface.id = 'nexus-brain-interface';
            brainInterface.style.display = 'none';
            brainInterface.setAttribute('data-message', JSON.stringify(brainMessage));
            
            // Add to DOM for processing
            document.body.appendChild(brainInterface);
            
            // Return confirmation
            JSON.stringify({{
                status: 'brain_message_sent',
                message_id: brainMessage.timestamp,
                session: brainMessage.session_id
            }});
            """
            
            response = requests.post(f"{self.base_url}/api/browser/execute-script",
                                   json={
                                       "session_id": self.brain_session_id,
                                       "script": js_command
                                   })
            
            if response.status_code == 200:
                return {
                    "status": "sent",
                    "message_id": brain_message["timestamp"],
                    "brain_response": response.json()
                }
            
        except Exception as e:
            print(f"Brain command execution failed: {e}")
        
        return {"status": "failed", "error": "Command execution failed"}
    
    def get_brain_response(self, message_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get response from brain for specific message"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for brain response through automation interface
            try:
                response = requests.get(f"{self.base_url}/api/browser/get-element-data",
                                      params={
                                          "session_id": self.brain_session_id,
                                          "selector": f"[data-response-to='{message_id}']"
                                      })
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("found"):
                        return {
                            "status": "received",
                            "response": data.get("content"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
            except Exception as e:
                print(f"Error checking brain response: {e}")
            
            time.sleep(1)
        
        return {"status": "timeout", "message": "No brain response within timeout"}
    
    def _process_brain_messages(self):
        """Continuous processing of brain messages"""
        while self.connection_status == "connected":
            if self.message_queue:
                message = self.message_queue.pop(0)
                self._handle_brain_message(message)
            time.sleep(0.1)
    
    def _handle_brain_message(self, message: Dict[str, Any]):
        """Handle individual brain message processing"""
        message_id = message["timestamp"]
        
        # Process message through brain interface
        result = self._execute_brain_command(message)
        
        # Store result for retrieval
        self.response_handlers[message_id] = result
        
        print(f"🧠 Brain message processed: {message_id}")
    
    def establish_persistent_brain_link(self) -> Dict[str, Any]:
        """Establish persistent link for continuous AI-brain communication"""
        if not self.initialize_brain_connection():
            return {"error": "Failed to establish brain connection"}
        
        # Create persistent communication channel
        persistent_js = """
        // NEXUS Persistent Brain Link
        window.nexusBrainLink = {
            active: true,
            messageQueue: [],
            responseQueue: [],
            
            sendToBrain: function(message) {
                const brainMessage = {
                    id: Date.now().toString(),
                    timestamp: new Date().toISOString(),
                    content: message,
                    source: 'nexus_ai'
                };
                
                this.messageQueue.push(brainMessage);
                
                // Create brain communication element
                const element = document.createElement('div');
                element.className = 'nexus-brain-message';
                element.setAttribute('data-brain-message', JSON.stringify(brainMessage));
                element.style.display = 'none';
                document.body.appendChild(element);
                
                return brainMessage.id;
            },
            
            receiveBrainResponse: function(messageId, response) {
                this.responseQueue.push({
                    messageId: messageId,
                    response: response,
                    timestamp: new Date().toISOString()
                });
            },
            
            getResponse: function(messageId) {
                const response = this.responseQueue.find(r => r.messageId === messageId);
                if (response) {
                    this.responseQueue = this.responseQueue.filter(r => r.messageId !== messageId);
                }
                return response;
            }
        };
        
        console.log('NEXUS Brain Link established');
        """
        
        try:
            response = requests.post(f"{self.base_url}/api/browser/execute-script",
                                   json={
                                       "session_id": self.brain_session_id,
                                       "script": persistent_js
                                   })
            
            if response.status_code == 200:
                return {
                    "status": "persistent_link_established",
                    "session_id": self.brain_session_id,
                    "capabilities": [
                        "real_time_messaging",
                        "brain_response_handling",
                        "persistent_communication"
                    ]
                }
                
        except Exception as e:
            print(f"Failed to establish persistent brain link: {e}")
        
        return {"error": "Failed to establish persistent link"}
    
    def query_brain(self, query: str) -> Dict[str, Any]:
        """Direct query to brain with response handling"""
        if self.connection_status != "connected":
            return {"error": "Brain connection not available"}
        
        # Send query to brain
        send_result = self.send_brain_message(query, "query")
        
        if send_result.get("status") == "sent":
            message_id = send_result["message_id"]
            
            # Wait for brain response
            response = self.get_brain_response(message_id)
            
            return {
                "query": query,
                "brain_response": response,
                "session_id": self.brain_session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {"error": "Failed to send query to brain"}
    
    def get_brain_status(self) -> Dict[str, Any]:
        """Get current brain connection status"""
        return {
            "connection_status": self.connection_status,
            "session_id": self.brain_session_id,
            "message_queue_size": len(self.message_queue),
            "active_handlers": len(self.response_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global brain interface instance
nexus_brain = NexusBrainInterface()

def connect_to_brain():
    """Initialize brain connection"""
    return nexus_brain.establish_persistent_brain_link()

def send_to_brain(message: str):
    """Send message to brain"""
    return nexus_brain.query_brain(message)

def get_brain_connection_status():
    """Get brain connection status"""
    return nexus_brain.get_brain_status()

if __name__ == "__main__":
    # Test brain connection
    brain_interface = NexusBrainInterface()
    result = brain_interface.establish_persistent_brain_link()
    print(json.dumps(result, indent=2))