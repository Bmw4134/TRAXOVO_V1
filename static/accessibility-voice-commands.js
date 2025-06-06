/**
 * Enhanced Accessibility Voice Commands for TRAXOVO
 * Voice navigation and visual assistance features
 */

class AccessibilityVoiceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.speechSynthesis = window.speechSynthesis;
        this.currentAnnouncement = null;
        
        this.accessibilityCommands = {
            // Navigation commands
            'read page': () => this.readPageContent(),
            'describe page': () => this.describePageLayout(),
            'what is on screen': () => this.announceScreenContent(),
            'read buttons': () => this.readAllButtons(),
            'read links': () => this.readAllLinks(),
            'where am i': () => this.announceCurrentLocation(),
            
            // Visual assistance commands
            'zoom in': () => this.adjustZoom('in'),
            'zoom out': () => this.adjustZoom('out'),
            'increase font size': () => this.adjustFontSize('increase'),
            'decrease font size': () => this.adjustFontSize('decrease'),
            'high contrast': () => this.toggleHighContrast(),
            'normal contrast': () => this.disableHighContrast(),
            
            // Content reading commands
            'read main content': () => this.readMainContent(),
            'read navigation': () => this.readNavigation(),
            'read status': () => this.readSystemStatus(),
            'what can i do': () => this.announceAvailableActions(),
            
            // Interface commands
            'click fleet tracking': () => this.navigateAndAnnounce('/fleet-tracking', 'Opening Fleet Tracking'),
            'click attendance': () => this.navigateAndAnnounce('/attendance-matrix', 'Opening Attendance Matrix'),
            'click automation': () => this.navigateAndAnnounce('/', 'Opening Automation Hub'),
            'click voice dashboard': () => this.navigateAndAnnounce('/voice-dashboard', 'Opening Voice Dashboard'),
            'click nexus intelligence': () => this.navigateAndAnnounce('/nexus-intelligence', 'Opening AI Intelligence Dashboard'),
            
            // Audio feedback commands
            'stop reading': () => this.stopSpeech(),
            'repeat': () => this.repeatLastAnnouncement(),
            'speak slower': () => this.adjustSpeechRate('slower'),
            'speak faster': () => this.adjustSpeechRate('faster'),
            'mute announcements': () => this.toggleAnnouncements(),
            
            // Help commands
            'voice help': () => this.announceVoiceHelp(),
            'accessibility help': () => this.announceAccessibilityHelp(),
            'what commands': () => this.listAvailableCommands()
        };
        
        this.speechRate = 1.0;
        this.speechVolume = 1.0;
        this.announcementsEnabled = true;
        this.lastAnnouncement = '';
        
        this.init();
    }
    
    init() {
        this.createAccessibilityButton();
        this.setupKeyboardShortcuts();
        this.announcePageLoad();
        
        // Auto-announce important changes
        this.setupMutationObserver();
    }
    
    createAccessibilityButton() {
        const button = document.createElement('button');
        button.id = 'accessibility-voice-btn';
        button.className = 'accessibility-voice-button';
        button.innerHTML = '🎤♿';
        button.title = 'Accessibility Voice Commands (Alt+A)';
        button.style.cssText = `
            position: fixed;
            bottom: 120px;
            right: 30px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            border: none;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            box-shadow: 0 10px 25px rgba(40, 167, 69, 0.4);
            transition: all 0.3s ease;
            z-index: 1001;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        button.onclick = () => this.toggleAccessibilityVoice();
        document.body.appendChild(button);
        this.accessibilityButton = button;
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                this.toggleAccessibilityVoice();
            }
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                this.readPageContent();
            }
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.stopSpeech();
            }
        });
    }
    
    toggleAccessibilityVoice() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    startListening() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.speak('Voice recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.accessibilityButton.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
            this.accessibilityButton.innerHTML = '🔴♿';
            this.speak('Accessibility voice commands active. Say voice help for available commands.');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
            this.processAccessibilityCommand(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.speak('Voice command failed. Please try again.');
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
        this.accessibilityButton.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        this.accessibilityButton.innerHTML = '🎤♿';
        this.speak('Voice commands deactivated');
    }
    
    processAccessibilityCommand(transcript) {
        console.log('Accessibility command:', transcript);
        
        let commandExecuted = false;
        
        for (const [command, action] of Object.entries(this.accessibilityCommands)) {
            if (transcript.includes(command)) {
                action();
                commandExecuted = true;
                break;
            }
        }
        
        if (!commandExecuted) {
            this.speak(`Command not recognized: ${transcript}. Say voice help for available commands.`);
        }
    }
    
    speak(text, priority = false) {
        if (!this.announcementsEnabled && !priority) return;
        
        if (this.currentAnnouncement) {
            this.speechSynthesis.cancel();
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = this.speechRate;
        utterance.volume = this.speechVolume;
        utterance.voice = this.speechSynthesis.getVoices().find(voice => voice.lang === 'en-US') || null;
        
        this.currentAnnouncement = utterance;
        this.lastAnnouncement = text;
        
        utterance.onend = () => {
            this.currentAnnouncement = null;
        };
        
        this.speechSynthesis.speak(utterance);
    }
    
    readPageContent() {
        const title = document.title;
        const mainContent = this.extractMainContent();
        const announcement = `Page title: ${title}. ${mainContent}`;
        this.speak(announcement);
    }
    
    describePageLayout() {
        const description = this.generatePageDescription();
        this.speak(description);
    }
    
    announceScreenContent() {
        const buttons = document.querySelectorAll('button, .nav-link, .btn').length;
        const cards = document.querySelectorAll('.dashboard-card, .module-card, .metric-card').length;
        const links = document.querySelectorAll('a').length;
        
        const content = `Screen contains ${buttons} interactive buttons, ${cards} information cards, and ${links} links. Current page is ${document.title}.`;
        this.speak(content);
    }
    
    readAllButtons() {
        const buttons = document.querySelectorAll('button, .nav-link, .btn');
        let buttonText = 'Available buttons: ';
        
        buttons.forEach((button, index) => {
            const text = button.textContent.trim() || button.title || button.getAttribute('aria-label') || `Button ${index + 1}`;
            buttonText += `${text}, `;
        });
        
        this.speak(buttonText);
    }
    
    readAllLinks() {
        const links = document.querySelectorAll('a');
        let linkText = 'Available links: ';
        
        links.forEach((link, index) => {
            const text = link.textContent.trim() || link.title || `Link ${index + 1}`;
            linkText += `${text}, `;
        });
        
        this.speak(linkText);
    }
    
    announceCurrentLocation() {
        const currentPath = window.location.pathname;
        const pageTitle = document.title;
        
        let location = '';
        if (currentPath === '/') {
            location = 'You are on the main dashboard';
        } else if (currentPath.includes('fleet')) {
            location = 'You are on the fleet tracking page';
        } else if (currentPath.includes('attendance')) {
            location = 'You are on the attendance matrix page';
        } else if (currentPath.includes('nexus')) {
            location = 'You are on the AI intelligence dashboard';
        } else if (currentPath.includes('voice')) {
            location = 'You are on the voice dashboard';
        } else {
            location = `You are on ${pageTitle}`;
        }
        
        this.speak(location);
    }
    
    adjustZoom(direction) {
        const currentZoom = parseFloat(document.body.style.zoom) || 1;
        const newZoom = direction === 'in' ? currentZoom + 0.1 : currentZoom - 0.1;
        const clampedZoom = Math.max(0.5, Math.min(3, newZoom));
        
        document.body.style.zoom = clampedZoom;
        this.speak(`Zoom level set to ${Math.round(clampedZoom * 100)} percent`);
    }
    
    adjustFontSize(direction) {
        const currentSize = parseFloat(getComputedStyle(document.body).fontSize) || 16;
        const newSize = direction === 'increase' ? currentSize + 2 : currentSize - 2;
        const clampedSize = Math.max(12, Math.min(24, newSize));
        
        document.body.style.fontSize = `${clampedSize}px`;
        this.speak(`Font size set to ${clampedSize} pixels`);
    }
    
    toggleHighContrast() {
        document.body.style.cssText += `
            background: black !important;
            color: white !important;
        `;
        
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            el.style.backgroundColor = 'black';
            el.style.color = 'white';
            el.style.borderColor = 'white';
        });
        
        this.speak('High contrast mode enabled');
    }
    
    disableHighContrast() {
        location.reload();
        this.speak('Normal contrast restored');
    }
    
    navigateAndAnnounce(url, announcement) {
        this.speak(announcement);
        setTimeout(() => {
            window.location.href = url;
        }, 1000);
    }
    
    readMainContent() {
        const mainContent = this.extractMainContent();
        this.speak(`Main content: ${mainContent}`);
    }
    
    readNavigation() {
        const navElements = document.querySelectorAll('nav, .nav-link, .navigation');
        let navText = 'Navigation options: ';
        
        navElements.forEach(nav => {
            const text = nav.textContent.trim();
            if (text) navText += `${text}, `;
        });
        
        this.speak(navText);
    }
    
    readSystemStatus() {
        const statusElements = document.querySelectorAll('.status, .metric-value, .performance-score');
        let statusText = 'System status: ';
        
        statusElements.forEach(status => {
            const text = status.textContent.trim();
            if (text) statusText += `${text}, `;
        });
        
        if (statusText === 'System status: ') {
            statusText = 'All systems operational';
        }
        
        this.speak(statusText);
    }
    
    announceAvailableActions() {
        const actions = [
            'Access Fleet Tracking',
            'View Attendance Matrix', 
            'Open Automation Hub',
            'Voice Dashboard',
            'AI Intelligence Dashboard',
            'User Data Integration'
        ];
        
        this.speak(`Available actions: ${actions.join(', ')}`);
    }
    
    stopSpeech() {
        this.speechSynthesis.cancel();
        this.currentAnnouncement = null;
    }
    
    repeatLastAnnouncement() {
        if (this.lastAnnouncement) {
            this.speak(this.lastAnnouncement);
        } else {
            this.speak('No previous announcement to repeat');
        }
    }
    
    adjustSpeechRate(direction) {
        this.speechRate = direction === 'slower' ? Math.max(0.5, this.speechRate - 0.2) : Math.min(2, this.speechRate + 0.2);
        this.speak(`Speech rate adjusted to ${this.speechRate.toFixed(1)}`);
    }
    
    toggleAnnouncements() {
        this.announcementsEnabled = !this.announcementsEnabled;
        this.speak(this.announcementsEnabled ? 'Announcements enabled' : 'Announcements disabled', true);
    }
    
    announceVoiceHelp() {
        const helpText = `
            Voice commands available:
            Navigation: read page, describe page, what is on screen, where am i.
            Visual assistance: zoom in, zoom out, increase font size, high contrast.
            Content: read buttons, read links, read main content.
            Actions: click fleet tracking, click attendance, click automation.
            Audio: stop reading, repeat, speak slower, speak faster.
            Say accessibility help for more options.
        `;
        this.speak(helpText);
    }
    
    announceAccessibilityHelp() {
        const helpText = `
            Accessibility features:
            Press Alt plus A to toggle voice commands.
            Press Alt plus R to read page content.
            Press Alt plus S to stop speech.
            Voice commands include zoom control, contrast adjustment, and content reading.
            All buttons and links are announced when requested.
        `;
        this.speak(helpText);
    }
    
    listAvailableCommands() {
        const commands = Object.keys(this.accessibilityCommands).slice(0, 10).join(', ');
        this.speak(`Available commands include: ${commands}, and more. Say voice help for details.`);
    }
    
    extractMainContent() {
        const contentSelectors = [
            '.container p',
            '.hero-subtitle',
            '.header p',
            'main',
            '.content'
        ];
        
        let content = '';
        for (const selector of contentSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length > 10) {
                    content += text + '. ';
                }
            });
            if (content) break;
        }
        
        return content || 'TRAXOVO Operational Intelligence Platform with fleet tracking, attendance management, and AI-driven analytics.';
    }
    
    generatePageDescription() {
        const title = document.title;
        const headings = document.querySelectorAll('h1, h2, h3').length;
        const cards = document.querySelectorAll('.dashboard-card, .module-card, .metric-card').length;
        const buttons = document.querySelectorAll('button, .btn, .nav-link').length;
        
        return `Page layout: ${title} with ${headings} headings, ${cards} information cards, and ${buttons} interactive elements. Use voice commands to navigate and interact.`;
    }
    
    announcePageLoad() {
        setTimeout(() => {
            this.speak('TRAXOVO platform loaded. Press Alt A for voice commands or say voice help for assistance.', true);
        }, 2000);
    }
    
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Announce significant page changes
                    const hasImportantContent = Array.from(mutation.addedNodes).some(node => 
                        node.nodeType === 1 && (
                            node.classList.contains('dashboard-card') ||
                            node.classList.contains('metric-card') ||
                            node.tagName === 'MAIN'
                        )
                    );
                    
                    if (hasImportantContent) {
                        setTimeout(() => {
                            this.speak('Page content updated');
                        }, 500);
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Initialize accessibility voice controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.accessibilityVoiceController = new AccessibilityVoiceController();
});

// Add accessibility CSS
const accessibilityCSS = `
.accessibility-voice-button:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 35px rgba(40, 167, 69, 0.6);
}

.accessibility-voice-button.listening {
    animation: accessibilityPulse 1.5s ease-in-out infinite;
}

@keyframes accessibilityPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

/* High contrast accessibility styles */
.high-contrast {
    background: black !important;
    color: white !important;
}

.high-contrast * {
    background-color: black !important;
    color: white !important;
    border-color: white !important;
}

/* Focus indicators for keyboard navigation */
button:focus, a:focus, input:focus {
    outline: 3px solid #007bff !important;
    outline-offset: 2px !important;
}
`;

const accessibilityStyleSheet = document.createElement('style');
accessibilityStyleSheet.textContent = accessibilityCSS;
document.head.appendChild(accessibilityStyleSheet);