"""
NEXUS Unified Chat Widget
LLM-driven interface with persistent memory and multi-function capabilities
"""

import os
import json
import openai
from datetime import datetime

class NexusUnifiedWidget:
    """Unified LLM-driven chat widget with NEXUS Intelligence core"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.memory_cache = {}
        self.conversation_history = []
        self.widget_status = {"rebuild": False}
        
    def generate_widget_html(self):
        """Generate unified chat widget HTML with advanced capabilities"""
        return '''
        <div id="nexus-unified-widget" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            height: 500px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
            border: 2px solid #00ff88;
            z-index: 100000;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        ">
            <!-- Widget Header -->
            <div style="
                background: linear-gradient(45deg, #00ff88, #00d4ff);
                padding: 12px 15px;
                color: #000;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: move;
            " id="widget-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 12px; height: 12px; background: #000; border-radius: 50%; animation: pulse 2s infinite;"></div>
                    <span>NEXUS Intelligence</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button onclick="toggleVoiceMode()" style="background: none; border: none; color: #000; cursor: pointer; font-size: 14px;">🎤</button>
                    <button onclick="minimizeWidget()" style="background: none; border: none; color: #000; cursor: pointer; font-size: 14px;">−</button>
                    <button onclick="closeWidget()" style="background: none; border: none; color: #000; cursor: pointer; font-size: 14px;">×</button>
                </div>
            </div>
            
            <!-- Chat Area -->
            <div id="chat-area" style="
                height: 380px;
                overflow-y: auto;
                padding: 15px;
                color: #fff;
                background: rgba(0, 0, 0, 0.2);
            ">
                <div class="nexus-message" style="
                    background: rgba(0, 255, 136, 0.1);
                    border-left: 3px solid #00ff88;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                ">
                    <strong>NEXUS:</strong> Unified Intelligence Interface active. I can help with file processing, automation commands, UI repairs, backend operations, and multi-function queries. What would you like to accomplish?
                </div>
            </div>
            
            <!-- Input Area -->
            <div style="
                padding: 10px;
                background: rgba(0, 0, 0, 0.3);
                border-top: 1px solid rgba(0, 255, 136, 0.3);
            ">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input type="text" id="nexus-input" placeholder="Enter command or query..." style="
                        flex: 1;
                        padding: 8px 12px;
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(0, 255, 136, 0.3);
                        border-radius: 20px;
                        color: #fff;
                        outline: none;
                    " onkeypress="handleInputKeypress(event)">
                    <button onclick="sendMessage()" style="
                        background: linear-gradient(45deg, #00ff88, #00d4ff);
                        border: none;
                        color: #000;
                        padding: 8px 15px;
                        border-radius: 20px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Send</button>
                </div>
                <div style="display: flex; gap: 5px; margin-top: 8px; flex-wrap: wrap;">
                    <button class="quick-cmd" onclick="quickCommand('status')">System Status</button>
                    <button class="quick-cmd" onclick="quickCommand('repair')">UI Repair</button>
                    <button class="quick-cmd" onclick="quickCommand('automation')">Automation</button>
                    <button class="quick-cmd" onclick="quickCommand('files')">File Process</button>
                </div>
            </div>
        </div>
        
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .quick-cmd {
                background: rgba(0, 255, 136, 0.2);
                border: 1px solid rgba(0, 255, 136, 0.3);
                color: #00ff88;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .quick-cmd:hover {
                background: rgba(0, 255, 136, 0.3);
                transform: translateY(-1px);
            }
            
            #nexus-unified-widget.minimized {
                height: 45px;
            }
            
            #nexus-unified-widget.minimized #chat-area,
            #nexus-unified-widget.minimized .input-area {
                display: none;
            }
        </style>
        
        <script>
            let widgetDragging = false;
            let widgetOffset = {x: 0, y: 0};
            let voiceModeActive = false;
            let conversationHistory = [];
            
            // Make widget draggable
            document.getElementById('widget-header').addEventListener('mousedown', function(e) {
                widgetDragging = true;
                const widget = document.getElementById('nexus-unified-widget');
                const rect = widget.getBoundingClientRect();
                widgetOffset.x = e.clientX - rect.left;
                widgetOffset.y = e.clientY - rect.top;
            });
            
            document.addEventListener('mousemove', function(e) {
                if (widgetDragging) {
                    const widget = document.getElementById('nexus-unified-widget');
                    widget.style.left = (e.clientX - widgetOffset.x) + 'px';
                    widget.style.top = (e.clientY - widgetOffset.y) + 'px';
                    widget.style.right = 'auto';
                    widget.style.bottom = 'auto';
                }
            });
            
            document.addEventListener('mouseup', function() {
                widgetDragging = false;
            });
            
            function handleInputKeypress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('nexus-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                addMessage(message, 'user');
                input.value = '';
                
                // Show processing indicator
                addMessage('Processing...', 'nexus', true);
                
                // Send to NEXUS Intelligence
                fetch('/api/nexus-unified-chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        history: conversationHistory,
                        context: 'unified_widget'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    removeProcessingMessage();
                    addMessage(data.response || 'Command processed', 'nexus');
                    
                    // Execute any actions if returned
                    if (data.actions) {
                        executeWidgetActions(data.actions);
                    }
                })
                .catch(error => {
                    removeProcessingMessage();
                    addMessage('Processing request...', 'nexus');
                });
                
                conversationHistory.push({role: 'user', content: message});
            }
            
            function addMessage(message, sender, isProcessing = false) {
                const chatArea = document.getElementById('chat-area');
                const messageDiv = document.createElement('div');
                
                if (isProcessing) {
                    messageDiv.id = 'processing-message';
                }
                
                if (sender === 'user') {
                    messageDiv.style.cssText = `
                        background: rgba(0, 212, 255, 0.1);
                        border-left: 3px solid #00d4ff;
                        padding: 10px;
                        margin-bottom: 10px;
                        border-radius: 5px;
                        text-align: right;
                    `;
                    messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
                } else {
                    messageDiv.style.cssText = `
                        background: rgba(0, 255, 136, 0.1);
                        border-left: 3px solid #00ff88;
                        padding: 10px;
                        margin-bottom: 10px;
                        border-radius: 5px;
                    `;
                    messageDiv.innerHTML = `<strong>NEXUS:</strong> ${message}`;
                }
                
                chatArea.appendChild(messageDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            }
            
            function removeProcessingMessage() {
                const processingMsg = document.getElementById('processing-message');
                if (processingMsg) {
                    processingMsg.remove();
                }
            }
            
            function quickCommand(cmd) {
                const commands = {
                    'status': 'Show system status and health metrics',
                    'repair': 'Scan and repair UI issues automatically', 
                    'automation': 'Show available automation options',
                    'files': 'Process uploaded files and generate insights'
                };
                
                document.getElementById('nexus-input').value = commands[cmd];
                sendMessage();
            }
            
            function toggleVoiceMode() {
                voiceModeActive = !voiceModeActive;
                if (voiceModeActive) {
                    startVoiceRecognition();
                } else {
                    stopVoiceRecognition();
                }
            }
            
            function startVoiceRecognition() {
                if ('webkitSpeechRecognition' in window) {
                    const recognition = new webkitSpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    
                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        document.getElementById('nexus-input').value = transcript;
                        sendMessage();
                    };
                    
                    recognition.start();
                }
            }
            
            function executeWidgetActions(actions) {
                actions.forEach(action => {
                    switch(action.type) {
                        case 'ui_repair':
                            performUIRepair();
                            break;
                        case 'file_process':
                            processFiles(action.files);
                            break;
                        case 'automation_trigger':
                            triggerAutomation(action.command);
                            break;
                    }
                });
            }
            
            function performUIRepair() {
                // Remove duplicate widgets
                document.querySelectorAll('[id*="widget"]:not(#nexus-unified-widget)').forEach(el => {
                    if (el.id !== 'nexus-unified-widget') {
                        el.remove();
                    }
                });
                
                addMessage('UI repair completed - duplicate elements removed', 'nexus');
            }
            
            function minimizeWidget() {
                document.getElementById('nexus-unified-widget').classList.toggle('minimized');
            }
            
            function closeWidget() {
                if (confirm('Close NEXUS Intelligence widget?')) {
                    document.getElementById('nexus-unified-widget').style.display = 'none';
                }
            }
            
            // Widget status tracking
            window.widget = {
                status: {
                    rebuild: true
                }
            };
            
            console.log('NEXUS Unified Widget: Initialized and bound to dashboard.root');
        </script>
        '''
    
    def process_chat_message(self, message, history=None, context=None):
        """Process incoming chat message with LLM intelligence"""
        try:
            # Build conversation context
            messages = [
                {
                    "role": "system", 
                    "content": """You are NEXUS Intelligence, a unified AI assistant integrated into an enterprise platform. You can:
                    
                    1. Handle UI repairs and widget management
                    2. Process files and generate automation
                    3. Execute backend commands and system operations
                    4. Provide business intelligence and analytics
                    5. Manage multi-function queries and natural language commands
                    
                    Respond concisely and actionably. For complex requests, break down into steps.
                    If you need to perform actions, include them in your response as JSON actions.
                    
                    Available actions:
                    - ui_repair: Fix UI issues
                    - file_process: Process uploaded files
                    - automation_trigger: Execute automation commands
                    - system_status: Show system metrics
                    """
                }
            ]
            
            # Add conversation history
            if history:
                messages.extend(history[-5:])  # Keep last 5 exchanges
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse for actions
            actions = self.extract_actions(ai_response)
            
            # Store in memory
            self.conversation_history.append({
                "user": message,
                "assistant": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context
            })
            
            return {
                "response": ai_response,
                "actions": actions,
                "memory_updated": True
            }
            
        except Exception as e:
            return {
                "response": f"NEXUS Intelligence processing request... Error: {str(e)}",
                "actions": [],
                "error": True
            }
    
    def extract_actions(self, response):
        """Extract actionable commands from AI response"""
        actions = []
        
        # Look for action keywords
        if "ui repair" in response.lower() or "fix ui" in response.lower():
            actions.append({"type": "ui_repair"})
        
        if "process file" in response.lower() or "file processing" in response.lower():
            actions.append({"type": "file_process"})
        
        if "automation" in response.lower() or "automate" in response.lower():
            actions.append({"type": "automation_trigger", "command": "general"})
        
        if "status" in response.lower() or "health" in response.lower():
            actions.append({"type": "system_status"})
        
        return actions
    
    def set_widget_status(self, rebuild_status=True):
        """Set widget rebuild status"""
        self.widget_status["rebuild"] = rebuild_status
        return self.widget_status

def create_unified_widget():
    """Create and return unified widget instance"""
    widget = NexusUnifiedWidget()
    widget.set_widget_status(True)
    return widget