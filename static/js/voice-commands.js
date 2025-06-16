/**
 * TRAXOVO Voice Command Integration
 * Natural language voice control for the platform
 */

(function() {
    'use strict';
    
    class TRAXOVOVoiceCommands {
        constructor() {
            this.isListening = false;
            this.recognition = null;
            this.isSupported = false;
            this.init();
        }
        
        init() {
            this.checkBrowserSupport();
            this.setupVoiceRecognition();
            this.createVoiceInterface();
            this.bindEvents();
        }
        
        checkBrowserSupport() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                this.isSupported = true;
                console.log('Voice commands: Browser support detected');
            } else {
                console.warn('Voice commands: Browser not supported');
            }
        }
        
        setupVoiceRecognition() {
            if (!this.isSupported) return;
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceButton(true);
                this.showListeningIndicator();
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.updateVoiceButton(false);
                this.hideListeningIndicator();
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.processVoiceCommand(transcript);
            };
            
            this.recognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                this.showError('Voice recognition failed: ' + event.error);
                this.isListening = false;
                this.updateVoiceButton(false);
                this.hideListeningIndicator();
            };
        }
        
        createVoiceInterface() {
            const voiceContainer = document.createElement('div');
            voiceContainer.className = 'voice-command-container';
            voiceContainer.innerHTML = `
                <div class="voice-controls">
                    <button id="voiceButton" class="btn btn-voice" ${!this.isSupported ? 'disabled' : ''}>
                        <i class="fas fa-microphone"></i>
                        <span class="voice-text">Voice Command</span>
                    </button>
                    <div id="voiceStatus" class="voice-status"></div>
                </div>
                
                <div id="listeningIndicator" class="listening-indicator" style="display: none;">
                    <div class="pulse-animation"></div>
                    <span>Listening...</span>
                </div>
                
                <div id="voiceResults" class="voice-results"></div>
                
                <div class="voice-help">
                    <small class="text-muted">
                        Try: "Go to dashboard", "Show status", "Optimize system", "Open Ragle"
                    </small>
                </div>
            `;
            
            // Add to dashboard
            const dashboard = document.querySelector('.container');
            if (dashboard) {
                dashboard.insertBefore(voiceContainer, dashboard.firstChild);
            }
            
            this.addVoiceStyles();
        }
        
        addVoiceStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .voice-command-container {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }
                
                .voice-controls {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 15px;
                }
                
                .btn-voice {
                    background: rgba(255,255,255,0.2);
                    border: 2px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                }
                
                .btn-voice:hover:not(:disabled) {
                    background: rgba(255,255,255,0.3);
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                }
                
                .btn-voice:active {
                    transform: translateY(0);
                }
                
                .btn-voice.listening {
                    background: #e74c3c;
                    border-color: #c0392b;
                    animation: pulse 1.5s infinite;
                }
                
                .btn-voice:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .listening-indicator {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: white;
                    font-weight: 500;
                }
                
                .pulse-animation {
                    width: 20px;
                    height: 20px;
                    background: #e74c3c;
                    border-radius: 50%;
                    animation: pulse 1s infinite;
                }
                
                .voice-status {
                    color: rgba(255,255,255,0.9);
                    font-size: 14px;
                    min-height: 20px;
                }
                
                .voice-results {
                    background: rgba(255,255,255,0.1);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                    color: white;
                    min-height: 60px;
                    display: none;
                }
                
                .voice-help {
                    text-align: center;
                }
                
                .voice-help .text-muted {
                    color: rgba(255,255,255,0.7) !important;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.7; }
                    100% { transform: scale(1); opacity: 1; }
                }
                
                .command-result {
                    background: rgba(46, 204, 113, 0.2);
                    border-left: 4px solid #2ecc71;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                }
                
                .command-error {
                    background: rgba(231, 76, 60, 0.2);
                    border-left: 4px solid #e74c3c;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                }
            `;
            document.head.appendChild(style);
        }
        
        bindEvents() {
            const voiceButton = document.getElementById('voiceButton');
            if (voiceButton) {
                voiceButton.addEventListener('click', () => {
                    if (this.isListening) {
                        this.stopListening();
                    } else {
                        this.startListening();
                    }
                });
            }
        }
        
        startListening() {
            if (!this.isSupported || !this.recognition) {
                this.showError('Voice recognition not supported');
                return;
            }
            
            try {
                this.recognition.start();
                this.updateStatus('Click the microphone and speak your command...');
            } catch (error) {
                console.error('Failed to start voice recognition:', error);
                this.showError('Failed to start listening');
            }
        }
        
        stopListening() {
            if (this.recognition && this.isListening) {
                this.recognition.stop();
            }
        }
        
        async processVoiceCommand(transcript) {
            this.updateStatus(`Processing: "${transcript}"`);
            this.showResult(`You said: "${transcript}"`);
            
            try {
                const response = await fetch('/api/voice/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: transcript })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.executeCommand(data.result);
                } else {
                    this.showError(data.error || 'Command processing failed');
                }
                
            } catch (error) {
                console.error('Voice command processing error:', error);
                this.showError('Failed to process command');
            }
        }
        
        executeCommand(result) {
            const execution = result.execution;
            const interpretation = result.command_analysis.interpretation;
            
            this.showResult(`Understood: ${interpretation}`, 'success');
            
            switch (execution.type) {
                case 'redirect':
                    this.showResult(`Navigating to ${execution.url}...`, 'success');
                    setTimeout(() => {
                        window.location.href = execution.url;
                    }, 1000);
                    break;
                    
                case 'system_command':
                    this.executeSystemCommand(execution.command);
                    break;
                    
                case 'ragle_command':
                    this.executeRagleCommand(execution.command);
                    break;
                    
                default:
                    this.showResult(execution.message, 'info');
            }
        }
        
        executeSystemCommand(command) {
            // Execute system commands in the existing command interface
            const commandInput = document.getElementById('commandInput');
            const executeButton = document.getElementById('executeCommand');
            
            if (commandInput && executeButton) {
                commandInput.value = command;
                executeButton.click();
                this.showResult(`Executed system command: ${command}`, 'success');
            } else {
                this.showResult(`System command: ${command}`, 'info');
            }
        }
        
        executeRagleCommand(command) {
            // Execute Ragle commands if on the Ragle page
            if (window.location.pathname.includes('/ragle')) {
                if (typeof executeCommand === 'function') {
                    executeCommand(command);
                    this.showResult(`Executed Ragle command: ${command}`, 'success');
                } else {
                    this.showResult(`Ragle command: ${command} (navigate to Ragle system to execute)`, 'info');
                }
            } else {
                this.showResult(`Ragle command: ${command} (navigate to Ragle system first)`, 'info');
            }
        }
        
        updateVoiceButton(listening) {
            const button = document.getElementById('voiceButton');
            const icon = button?.querySelector('i');
            const text = button?.querySelector('.voice-text');
            
            if (button) {
                button.classList.toggle('listening', listening);
            }
            
            if (icon) {
                icon.className = listening ? 'fas fa-stop' : 'fas fa-microphone';
            }
            
            if (text) {
                text.textContent = listening ? 'Stop Listening' : 'Voice Command';
            }
        }
        
        showListeningIndicator() {
            const indicator = document.getElementById('listeningIndicator');
            if (indicator) {
                indicator.style.display = 'flex';
            }
        }
        
        hideListeningIndicator() {
            const indicator = document.getElementById('listeningIndicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }
        
        updateStatus(message) {
            const status = document.getElementById('voiceStatus');
            if (status) {
                status.textContent = message;
            }
        }
        
        showResult(message, type = 'info') {
            const results = document.getElementById('voiceResults');
            if (!results) return;
            
            results.style.display = 'block';
            
            const resultElement = document.createElement('div');
            resultElement.className = `command-${type}`;
            resultElement.textContent = message;
            
            results.appendChild(resultElement);
            
            // Remove old results after a while
            setTimeout(() => {
                if (resultElement.parentNode) {
                    resultElement.remove();
                }
                
                if (results.children.length === 0) {
                    results.style.display = 'none';
                }
            }, 5000);
        }
        
        showError(message) {
            this.showResult(`Error: ${message}`, 'error');
            this.updateStatus('Ready for voice commands');
        }
    }
    
    // Initialize voice commands when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.TRAXOVOVoiceCommands = new TRAXOVOVoiceCommands();
        });
    } else {
        window.TRAXOVOVoiceCommands = new TRAXOVOVoiceCommands();
    }
    
})();