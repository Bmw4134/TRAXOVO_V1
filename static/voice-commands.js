/**
 * TRAXOVO Voice Command System
 * Real-time voice navigation and control
 */

class VoiceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.commands = {
            'dashboard': () => window.location.href = '/',
            'automation hub': () => window.location.href = '/',
            'fleet tracking': () => window.location.href = '/fleet-tracking',
            'location tracking': () => window.location.href = '/location-tracking', 
            'attendance': () => window.location.href = '/attendance-matrix',
            'attendance matrix': () => window.location.href = '/attendance-matrix',
            'automation status': () => window.location.href = '/automation-status',
            'voice control': () => window.location.href = '/voice-dashboard',
            'voice dashboard': () => window.location.href = '/voice-dashboard',
            'asset mapping': () => window.location.href = '/asset-mapping',
            'legacy mapping': () => window.location.href = '/legacy-mapping',
            'system status': () => window.location.href = '/automation-status',
            'help': () => this.showHelp(),
            'stop listening': () => this.stopListening()
        };
        
        this.init();
    }
    
    init() {
        this.createVoiceButton();
        this.createStatusIndicator();
        this.setupKeyboardShortcuts();
    }
    
    createVoiceButton() {
        const button = document.createElement('button');
        button.id = 'voice-control-btn';
        button.className = 'voice-control-button';
        button.innerHTML = '🎤';
        button.title = 'Voice Commands (Alt+V)';
        button.onclick = () => this.toggleVoiceRecognition();
        document.body.appendChild(button);
        this.voiceButton = button;
    }
    
    createStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'voice-status';
        indicator.className = 'voice-status';
        indicator.innerHTML = 'Voice Ready';
        document.body.appendChild(indicator);
        this.statusIndicator = indicator;
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 'v') {
                e.preventDefault();
                this.toggleVoiceRecognition();
            }
        });
    }
    
    toggleVoiceRecognition() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    startListening() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('Voice recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.voiceButton.classList.add('listening');
            this.voiceButton.innerHTML = '🔴';
            this.showStatus('Listening for commands...', 'listening');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
            this.processCommand(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.showStatus('Voice command failed', 'error');
            this.stopListening();
        };
        
        this.recognition.onend = () => {
            if (this.isListening) {
                setTimeout(() => this.recognition.start(), 100);
            }
        };
        
        this.recognition.start();
    }
    
    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isListening = false;
        this.voiceButton.classList.remove('listening');
        this.voiceButton.innerHTML = '🎤';
        this.showStatus('Voice Ready', 'ready');
    }
    
    processCommand(transcript) {
        console.log('Voice command:', transcript);
        this.logCommand(transcript);
        
        let commandExecuted = false;
        
        for (const [command, action] of Object.entries(this.commands)) {
            if (transcript.includes(command)) {
                this.showStatus(`Executing: ${command}`, 'executing');
                action();
                commandExecuted = true;
                break;
            }
        }
        
        if (!commandExecuted) {
            this.showStatus(`Unknown command: "${transcript}"`, 'error');
            setTimeout(() => this.showStatus('Listening...', 'listening'), 2000);
        }
    }
    
    showStatus(message, type = 'info') {
        this.statusIndicator.textContent = message;
        this.statusIndicator.className = `voice-status visible ${type}`;
        
        if (type !== 'listening') {
            setTimeout(() => {
                this.statusIndicator.classList.remove('visible');
            }, 3000);
        }
    }
    
    logCommand(command) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `${timestamp}: "${command}"`;
        
        // Add to command log if it exists
        const commandLog = document.getElementById('command-log');
        if (commandLog) {
            const entry = document.createElement('div');
            entry.className = 'command-entry';
            entry.innerHTML = `<span class="command-timestamp">${timestamp}</span> ${command}`;
            commandLog.appendChild(entry);
            commandLog.scrollTop = commandLog.scrollHeight;
        }
        
        console.log('Voice Command:', logEntry);
    }
    
    showHelp() {
        const helpText = `
Available Voice Commands:
• "Dashboard" - Go to main dashboard
• "Fleet Tracking" - Open fleet tracking
• "Attendance Matrix" - View attendance
• "Automation Status" - Check system status
• "Voice Dashboard" - Voice control center
• "Asset Mapping" - Legacy asset mapping
• "Help" - Show this help
• "Stop Listening" - Stop voice recognition
        `;
        
        alert(helpText);
    }
}

// Initialize voice controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceController = new VoiceController();
});

// Add CSS for voice status indicator
const voiceCSS = `
.voice-status {
    position: fixed;
    bottom: 120px;
    right: 30px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px 20px;
    border-radius: 25px;
    font-size: 0.9rem;
    opacity: 0;
    transition: all 0.3s ease;
    z-index: 1000;
    pointer-events: none;
}

.voice-status.visible {
    opacity: 1;
}

.voice-status.listening {
    background: rgba(102, 126, 234, 0.9);
}

.voice-status.executing {
    background: rgba(40, 167, 69, 0.9);
}

.voice-status.error {
    background: rgba(220, 53, 69, 0.9);
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = voiceCSS;
document.head.appendChild(styleSheet);