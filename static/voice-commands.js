/**
 * TRAXOVO Voice Command Integration
 * Navigate key platform features using voice commands
 */

class TRAXOVOVoiceCommands {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.commands = {
            // Navigation commands
            'dashboard': '/dashboard',
            'go to dashboard': '/dashboard',
            'home': '/dashboard',
            'billing': '/billing',
            'billing intelligence': '/billing',
            'revenue': '/billing',
            'attendance': '/attendance-matrix',
            'attendance matrix': '/attendance-matrix',
            'fleet map': '/fleet-map',
            'fleet': '/fleet-map',
            'assets': '/asset-manager',
            'asset manager': '/asset-manager',
            'upload': '/upload',
            'upload files': '/upload',
            'safe mode': '/safemode',
            'diagnostics': '/safemode',
            'logout': '/logout',
            'sign out': '/logout',
            
            // Functional commands
            'purge records': () => this.executePurge(),
            'purge data': () => this.executePurge(),
            'clear data': () => this.executePurge(),
            'refresh page': () => location.reload(),
            'reload': () => location.reload(),
            'refresh': () => location.reload(),
            
            // Data commands
            'show stats': () => this.showDatabaseStats(),
            'database stats': () => this.showDatabaseStats(),
            'system status': () => this.showSystemStatus(),
            
            // Quick access
            'watson admin': '/watson-admin',
            'admin dashboard': '/watson-admin'
        };
        
        this.setupVoiceRecognition();
        this.createVoiceButton();
        this.setupKeyboardShortcuts();
    }
    
    setupVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Voice recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateVoiceButton();
            this.showVoiceIndicator('Listening...');
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateVoiceButton();
            this.hideVoiceIndicator();
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            this.processCommand(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.showVoiceIndicator('Voice command failed', 'error');
            setTimeout(() => this.hideVoiceIndicator(), 2000);
        };
    }
    
    createVoiceButton() {
        const voiceButton = document.createElement('button');
        voiceButton.id = 'voice-command-btn';
        voiceButton.className = 'voice-command-button';
        voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceButton.title = 'Voice Commands (Alt+V)';
        voiceButton.onclick = () => this.toggleVoiceRecognition();
        
        // Add to page
        document.body.appendChild(voiceButton);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .voice-command-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                color: white;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
                transition: all 0.3s ease;
                z-index: 1000;
            }
            
            .voice-command-button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(37, 99, 235, 0.4);
            }
            
            .voice-command-button.listening {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            .voice-indicator {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 1rem 2rem;
                border-radius: 10px;
                font-size: 1.1rem;
                z-index: 1001;
                backdrop-filter: blur(10px);
            }
            
            .voice-indicator.error {
                background: rgba(220, 38, 38, 0.9);
            }
            
            .voice-indicator.success {
                background: rgba(16, 185, 129, 0.9);
            }
            
            @media (max-width: 768px) {
                .voice-command-button {
                    bottom: 80px;
                    right: 15px;
                    width: 50px;
                    height: 50px;
                    font-size: 1rem;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt+V for voice commands
            if (e.altKey && e.key.toLowerCase() === 'v') {
                e.preventDefault();
                this.toggleVoiceRecognition();
            }
            
            // Alt+Number for quick navigation
            if (e.altKey && e.key >= '1' && e.key <= '9') {
                e.preventDefault();
                const shortcuts = [
                    '/dashboard',      // Alt+1
                    '/attendance-matrix', // Alt+2
                    '/fleet-map',      // Alt+3
                    '/asset-manager',  // Alt+4
                    '/billing',        // Alt+5
                    '/upload',         // Alt+6
                    '/safemode',       // Alt+7
                    '/watson-admin',   // Alt+8
                    '/logout'          // Alt+9
                ];
                
                const index = parseInt(e.key) - 1;
                if (shortcuts[index]) {
                    window.location.href = shortcuts[index];
                }
            }
        });
    }
    
    toggleVoiceRecognition() {
        if (!this.recognition) {
            this.showVoiceIndicator('Voice commands not supported', 'error');
            setTimeout(() => this.hideVoiceIndicator(), 2000);
            return;
        }
        
        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }
    
    updateVoiceButton() {
        const button = document.getElementById('voice-command-btn');
        if (button) {
            if (this.isListening) {
                button.classList.add('listening');
                button.innerHTML = '<i class="fas fa-stop"></i>';
                button.title = 'Stop listening';
            } else {
                button.classList.remove('listening');
                button.innerHTML = '<i class="fas fa-microphone"></i>';
                button.title = 'Voice Commands (Alt+V)';
            }
        }
    }
    
    processCommand(transcript) {
        console.log('Voice command:', transcript);
        
        // Check for exact matches first
        if (this.commands[transcript]) {
            this.executeCommand(this.commands[transcript], transcript);
            return;
        }
        
        // Check for partial matches
        for (const [command, action] of Object.entries(this.commands)) {
            if (transcript.includes(command)) {
                this.executeCommand(action, command);
                return;
            }
        }
        
        this.showVoiceIndicator(`Command not recognized: "${transcript}"`, 'error');
        setTimeout(() => this.hideVoiceIndicator(), 3000);
    }
    
    executeCommand(action, commandName) {
        if (typeof action === 'function') {
            action();
            this.showVoiceIndicator(`Executing: ${commandName}`, 'success');
        } else if (typeof action === 'string') {
            this.showVoiceIndicator(`Navigating to: ${commandName}`, 'success');
            setTimeout(() => {
                window.location.href = action;
            }, 1000);
        }
        
        setTimeout(() => this.hideVoiceIndicator(), 2000);
    }
    
    executePurge() {
        if (confirm('Are you sure you want to purge all records?')) {
            fetch('/api/purge-records', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.showVoiceIndicator('Records purged successfully', 'success');
                    } else {
                        this.showVoiceIndicator('Purge failed', 'error');
                    }
                })
                .catch(error => {
                    console.error('Purge error:', error);
                    this.showVoiceIndicator('Purge failed', 'error');
                });
        }
    }
    
    showDatabaseStats() {
        fetch('/api/database-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showVoiceIndicator(`Records: ${data.total_records}, Size: ${data.size}`, 'success');
                } else {
                    this.showVoiceIndicator('Could not fetch stats', 'error');
                }
            })
            .catch(error => {
                console.error('Stats error:', error);
                this.showVoiceIndicator('Stats unavailable', 'error');
            });
    }
    
    showSystemStatus() {
        this.showVoiceIndicator('TRAXOVO System: Active', 'success');
    }
    
    showVoiceIndicator(message, type = 'info') {
        this.hideVoiceIndicator(); // Remove any existing indicator
        
        const indicator = document.createElement('div');
        indicator.id = 'voice-indicator';
        indicator.className = `voice-indicator ${type}`;
        indicator.textContent = message;
        
        document.body.appendChild(indicator);
    }
    
    hideVoiceIndicator() {
        const indicator = document.getElementById('voice-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // Public method to get available commands
    getAvailableCommands() {
        return Object.keys(this.commands);
    }
}

// Initialize voice commands when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.traxovoVoice = new TRAXOVOVoiceCommands();
    
    // Show initial help
    setTimeout(() => {
        if (window.traxovoVoice.recognition) {
            console.log('TRAXOVO Voice Commands Ready:');
            console.log('- Press Alt+V or click the microphone button');
            console.log('- Say commands like: "dashboard", "billing", "attendance", "fleet map"');
            console.log('- Use Alt+1-9 for quick keyboard navigation');
        }
    }, 1000);
});