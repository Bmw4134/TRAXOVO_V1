
// Voice Commands Module
(function() {
    'use strict';
    
    let recognition;
    let isListening = false;
    
    function initVoiceCommands() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.log('Voice commands not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = handleVoiceCommand;
        recognition.onerror = handleVoiceError;
        
        addVoiceButton();
    }
    
    function addVoiceButton() {
        const voiceBtn = document.createElement('button');
        voiceBtn.innerHTML = '🎤';
        voiceBtn.className = 'btn btn-outline-secondary voice-btn';
        voiceBtn.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;';
        voiceBtn.onclick = toggleVoiceRecognition;
        
        document.body.appendChild(voiceBtn);
    }
    
    function toggleVoiceRecognition() {
        if (isListening) {
            recognition.stop();
            isListening = false;
        } else {
            recognition.start();
            isListening = true;
        }
    }
    
    function handleVoiceCommand(event) {
        const command = event.results[0][0].transcript.toLowerCase();
        console.log('Voice command:', command);
        
        if (command.includes('dashboard')) {
            window.location.href = '/dashboard';
        } else if (command.includes('logout')) {
            window.location.href = '/logout';
        } else if (command.includes('ragle')) {
            window.location.href = '/ragle';
        }
        
        isListening = false;
    }
    
    function handleVoiceError(event) {
        console.log('Voice recognition error:', event.error);
        isListening = false;
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initVoiceCommands);
    } else {
        initVoiceCommands();
    }
    
})();
