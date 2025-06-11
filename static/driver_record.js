/**
 * Daily Driver Recording System for TRAXOVO
 * Comprehensive driver activity tracking and session logging
 */

class DriverRecorder {
    constructor() {
        this.isRecording = false;
        this.sessionData = {
            sessionId: this.generateSessionId(),
            startTime: null,
            endTime: null,
            activities: [],
            location: null,
            permissions: {
                microphone: false,
                location: false,
                camera: false
            }
        };
        this.mediaRecorder = null;
        this.locationWatcher = null;
        this.recordingInterval = null;
        
        this.initializeRecorder();
    }
    
    generateSessionId() {
        return 'driver_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async initializeRecorder() {
        console.log('Initializing Driver Recording System...');
        
        // Check and request permissions
        await this.requestPermissions();
        
        // Initialize UI elements
        this.createRecorderInterface();
        
        console.log('Driver Recording System initialized');
    }
    
    async requestPermissions() {
        try {
            // Request microphone permission
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    this.sessionData.permissions.microphone = true;
                    stream.getTracks().forEach(track => track.stop());
                    console.log('Microphone permission granted');
                } catch (err) {
                    console.log('Microphone permission denied:', err);
                }
            }
            
            // Request location permission
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        this.sessionData.permissions.location = true;
                        this.sessionData.location = {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            timestamp: position.timestamp
                        };
                        console.log('Location permission granted');
                    },
                    (error) => {
                        console.log('Location permission denied:', error);
                    }
                );
            }
            
        } catch (error) {
            console.error('Permission request failed:', error);
        }
    }
    
    createRecorderInterface() {
        // Check if interface already exists
        if (document.querySelector('.driver-recorder-interface')) return;
        
        const recorderHTML = `
            <div class="driver-recorder-interface" style="
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                border: 2px solid #00ff88;
                border-radius: 15px;
                padding: 15px;
                z-index: 9999;
                box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
                min-width: 280px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            ">
                <div class="recorder-header" style="
                    color: #00ff88;
                    font-weight: bold;
                    margin-bottom: 10px;
                    text-align: center;
                ">
                    📹 Daily Driver Recording
                </div>
                
                <div class="recorder-status" style="
                    color: #ffffff;
                    font-size: 12px;
                    margin-bottom: 10px;
                    text-align: center;
                ">
                    Status: <span id="recording-status">Ready</span>
                </div>
                
                <div class="recorder-controls" style="
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                ">
                    <button id="start-recording-btn" style="
                        background: #00ff88;
                        color: #1a1a2e;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: bold;
                        cursor: pointer;
                        font-size: 14px;
                    ">Start</button>
                    
                    <button id="stop-recording-btn" style="
                        background: #ff4444;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-weight: bold;
                        cursor: pointer;
                        font-size: 14px;
                        display: none;
                    ">Stop</button>
                    
                    <button id="toggle-recorder-btn" style="
                        background: #666;
                        color: white;
                        border: none;
                        padding: 8px 12px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 12px;
                    ">−</button>
                </div>
                
                <div class="recorder-info" style="
                    color: #aaa;
                    font-size: 10px;
                    margin-top: 8px;
                    text-align: center;
                ">
                    Session: ${this.sessionData.sessionId.substr(-8)}
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', recorderHTML);
        
        // Bind event listeners
        this.bindRecorderEvents();
    }
    
    bindRecorderEvents() {
        const startBtn = document.getElementById('start-recording-btn');
        const stopBtn = document.getElementById('stop-recording-btn');
        const toggleBtn = document.getElementById('toggle-recorder-btn');
        const recorderInterface = document.querySelector('.driver-recorder-interface');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startRecording());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const controls = recorderInterface.querySelector('.recorder-controls');
                const info = recorderInterface.querySelector('.recorder-info');
                const isMinimized = controls.style.display === 'none';
                
                controls.style.display = isMinimized ? 'flex' : 'none';
                info.style.display = isMinimized ? 'block' : 'none';
                toggleBtn.textContent = isMinimized ? '−' : '+';
            });
        }
    }
    
    async startRecording() {
        if (this.isRecording) return;
        
        console.log('Starting driver recording session...');
        
        this.isRecording = true;
        this.sessionData.startTime = new Date().toISOString();
        
        // Update UI
        const statusElement = document.getElementById('recording-status');
        const startBtn = document.getElementById('start-recording-btn');
        const stopBtn = document.getElementById('stop-recording-btn');
        
        if (statusElement) statusElement.textContent = 'Recording';
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'block';
        
        // Start location tracking
        this.startLocationTracking();
        
        // Start activity logging
        this.startActivityLogging();
        
        // Start audio recording if permissions available
        if (this.sessionData.permissions.microphone) {
            await this.startAudioRecording();
        }
        
        console.log('Driver recording started:', this.sessionData.sessionId);
        
        // Log start event
        this.logActivity('recording_started', {
            sessionId: this.sessionData.sessionId,
            permissions: this.sessionData.permissions,
            timestamp: this.sessionData.startTime
        });
    }
    
    stopRecording() {
        if (!this.isRecording) return;
        
        console.log('Stopping driver recording session...');
        
        this.isRecording = false;
        this.sessionData.endTime = new Date().toISOString();
        
        // Update UI
        const statusElement = document.getElementById('recording-status');
        const startBtn = document.getElementById('start-recording-btn');
        const stopBtn = document.getElementById('stop-recording-btn');
        
        if (statusElement) statusElement.textContent = 'Saving...';
        if (startBtn) startBtn.style.display = 'block';
        if (stopBtn) stopBtn.style.display = 'none';
        
        // Stop all tracking
        this.stopLocationTracking();
        this.stopActivityLogging();
        this.stopAudioRecording();
        
        // Save session data
        this.saveSessionData();
        
        console.log('Driver recording stopped and saved');
        
        // Update status
        setTimeout(() => {
            if (statusElement) statusElement.textContent = 'Ready';
        }, 2000);
    }
    
    startLocationTracking() {
        if (!this.sessionData.permissions.location) return;
        
        this.locationWatcher = navigator.geolocation.watchPosition(
            (position) => {
                this.logActivity('location_update', {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: position.timestamp
                });
            },
            (error) => {
                console.error('Location tracking error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    }
    
    stopLocationTracking() {
        if (this.locationWatcher) {
            navigator.geolocation.clearWatch(this.locationWatcher);
            this.locationWatcher = null;
        }
    }
    
    startActivityLogging() {
        this.recordingInterval = setInterval(() => {
            this.logActivity('heartbeat', {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title
            });
        }, 30000); // Log every 30 seconds
    }
    
    stopActivityLogging() {
        if (this.recordingInterval) {
            clearInterval(this.recordingInterval);
            this.recordingInterval = null;
        }
    }
    
    async startAudioRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            const audioChunks = [];
            this.mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                this.logActivity('audio_recorded', {
                    size: audioBlob.size,
                    duration: this.getRecordingDuration()
                });
            };
            
            this.mediaRecorder.start();
            console.log('Audio recording started');
            
        } catch (error) {
            console.error('Audio recording failed:', error);
        }
    }
    
    stopAudioRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
    
    getRecordingDuration() {
        if (!this.sessionData.startTime) return 0;
        return new Date() - new Date(this.sessionData.startTime);
    }
    
    logActivity(type, data) {
        const activity = {
            type,
            timestamp: new Date().toISOString(),
            data
        };
        
        this.sessionData.activities.push(activity);
        console.log('Activity logged:', type, data);
    }
    
    saveSessionData() {
        try {
            // Save to localStorage
            const sessionKey = `driver_session_${this.sessionData.sessionId}`;
            localStorage.setItem(sessionKey, JSON.stringify(this.sessionData));
            
            // Also save to session storage for immediate access
            sessionStorage.setItem('current_driver_session', JSON.stringify(this.sessionData));
            
            // Create audit log entry
            this.createAuditLog();
            
            console.log('Session data saved successfully');
            
        } catch (error) {
            console.error('Failed to save session data:', error);
        }
    }
    
    createAuditLog() {
        const auditEntry = {
            cycle_tag: 'mobile_override_pass_v2',
            session_id: this.sessionData.sessionId,
            start_time: this.sessionData.startTime,
            end_time: this.sessionData.endTime,
            duration: this.getRecordingDuration(),
            activities_count: this.sessionData.activities.length,
            permissions: this.sessionData.permissions,
            timestamp: new Date().toISOString()
        };
        
        // Save to session audit
        const existingAudit = JSON.parse(localStorage.getItem('session_audit') || '[]');
        existingAudit.push(auditEntry);
        localStorage.setItem('session_audit', JSON.stringify(existingAudit));
        
        console.log('Audit log created:', auditEntry);
    }
    
    // Public methods for external access
    getSessionStatus() {
        return {
            isRecording: this.isRecording,
            sessionId: this.sessionData.sessionId,
            startTime: this.sessionData.startTime,
            activitiesCount: this.sessionData.activities.length,
            permissions: this.sessionData.permissions
        };
    }
    
    exportSessionData() {
        return JSON.stringify(this.sessionData, null, 2);
    }
}

// Initialize driver recorder
let driverRecorder;

function initializeDriverRecorder() {
    if (!driverRecorder) {
        driverRecorder = new DriverRecorder();
        console.log('Driver recorder initialized globally');
    }
    return driverRecorder;
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDriverRecorder);
} else {
    initializeDriverRecorder();
}

// Global access functions
window.startDriverRecording = () => {
    if (!driverRecorder) {
        driverRecorder = initializeDriverRecorder();
    }
    return driverRecorder.startRecording();
};

window.stopDriverRecording = () => {
    if (driverRecorder) {
        return driverRecorder.stopRecording();
    }
};

window.getDriverRecorderStatus = () => {
    if (driverRecorder) {
        return driverRecorder.getSessionStatus();
    }
    return { error: 'Recorder not initialized' };
};

window.driverRecorder = driverRecorder;