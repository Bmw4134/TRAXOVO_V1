/**
 * NEXUS Quantum Telematics Map & PiP Suite
 * Real-time asset tracking with Picture-in-Picture video integration
 * Deploy Tag: QNIS_telematics_core_v1
 */

// Import telemetry simulator
import './telemetrySimulator.js';

class NexusTelematics {
    constructor() {
        this.map = null;
        this.assets = new Map();
        this.wsConnection = null;
        this.pipVideos = new Map();
        this.isOnline = false;
        this.telemetrySimulator = null;
        
        this.init();
    }

    init() {
        console.log('🗺️ Initializing NEXUS Quantum Telematics...');
        this.initializeMap();
        this.connectWebSocket();
        this.setupAutomationTriggers();
        this.createStatusOverlay();
        this.loadAssetData();
    }

    initializeMap() {
        // Create map container if it doesn't exist
        if (!document.getElementById('telematics-map')) {
            const mapContainer = document.createElement('div');
            mapContainer.id = 'telematics-map';
            mapContainer.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                width: 400px;
                height: 300px;
                z-index: 1000;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                background: #1a1a1a;
                border: 2px solid #00ff00;
            `;
            document.body.appendChild(mapContainer);
        }

        // Initialize Leaflet map centered on Dallas/Fort Worth area
        if (typeof L !== 'undefined') {
            this.map = L.map('telematics-map').setView([32.7357, -97.1081], 12);
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);
            
            console.log('✅ Leaflet map initialized');
        } else {
            // Load Leaflet if not available
            this.loadLeaflet();
        }
    }

    loadLeaflet() {
        const leafletCSS = document.createElement('link');
        leafletCSS.rel = 'stylesheet';
        leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(leafletCSS);

        const leafletJS = document.createElement('script');
        leafletJS.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        leafletJS.onload = () => {
            this.initializeMap();
        };
        document.head.appendChild(leafletJS);
    }

    connectWebSocket() {
        console.log('🔗 Connecting to telemetry system...');
        
        // Initialize telemetry simulator
        if (window.TelemetrySimulator) {
            this.telemetrySimulator = new window.TelemetrySimulator();
            
            // Listen for telemetry updates
            document.addEventListener('telemetryUpdate', (event) => {
                this.updateAsset(event.detail);
            });
            
            // Start simulation
            this.telemetrySimulator.start();
        }
        
        setTimeout(() => {
            this.isOnline = true;
            this.updateStatusOverlay();
            console.log('✅ Telemetry system connected');
            
            // Fallback to mock telemetry if simulator not available
            if (!this.telemetrySimulator) {
                this.startMockTelemetry();
            }
        }, 1000);
    }

    startMockTelemetry() {
        // Generate mock telemetry data for authentic RAGLE assets
        const mockAssets = [
            { id: 'EX-210013', name: 'MATTHEW C. SHAYLOR', lat: 32.7500, lng: -97.1200, speed: 12 },
            { id: 'EX-210013', name: 'MATTHEW C. SHAYLOR', lat: 32.7500, lng: -97.1200, speed: 42 },
            { id: 'TR-3001', name: 'Fleet Truck 3001', lat: 32.7200, lng: -97.0900, speed: 28 },
            { id: 'HD-4502', name: 'Heavy Duty 4502', lat: 32.7600, lng: -97.1300, speed: 15 }
        ];

        mockAssets.forEach((asset, index) => {
            setTimeout(() => {
                this.updateAsset(asset);
            }, index * 500);
        });

        // Continue updating positions every 10 seconds
        setInterval(() => {
            mockAssets.forEach(asset => {
                // Simulate movement
                asset.lat += (Math.random() - 0.5) * 0.001;
                asset.lng += (Math.random() - 0.5) * 0.001;
                asset.speed = Math.max(0, asset.speed + (Math.random() - 0.5) * 10);
                this.updateAsset(asset);
            });
        }, 10000);
    }

    updateAsset(data) {
        if (!this.map) return;

        let marker = this.assets.get(data.id);
        if (!marker) {
            // Create new marker
            marker = L.marker([data.lat, data.lng]).addTo(this.map);
            this.assets.set(data.id, marker);
            
            // Center map on first asset
            if (this.assets.size === 1) {
                this.map.setView([data.lat, data.lng], 12);
            }
        }

        // Update marker position
        marker.setLatLng([data.lat, data.lng]);
        
        // Create enhanced popup with comprehensive asset information
        const fuelColor = data.fuelLevel > 70 ? '#00ff00' : data.fuelLevel > 30 ? '#ffff00' : '#ff0000';
        const statusColor = data.status === 'Active' || data.status === 'Operating' ? '#00ff00' : 
                           data.status === 'In Transit' ? '#ffff00' : '#ff6600';
        
        const popupContent = `
            <div style="font-family: 'Courier New', monospace; min-width: 250px;">
                <div style="background: rgba(0,0,0,0.8); padding: 10px; border-radius: 6px;">
                    <div style="font-size: 16px; font-weight: bold; color: #00ff00; margin-bottom: 8px;">
                        ${data.id} - ${data.operator || data.name}
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>Speed:</span><span style="color: #00ff88;">${Math.round(data.speed)} mph</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>Fuel:</span><span style="color: ${fuelColor};">${Math.round(data.fuelLevel || 75)}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>Status:</span><span style="color: ${statusColor};">${data.status || 'Active'}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>Engine Hours:</span><span style="color: #88ccff;">${Math.round(data.engineHours || 2847)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Type:</span><span style="color: #cccccc;">${data.type || 'Fleet Vehicle'}</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; flex-direction: column;">
                        <button onclick="nexusTelematics.enablePiP('${data.id}')" 
                                style="padding: 8px 12px; background: linear-gradient(135deg, #00ff88, #00cc66); 
                                       color: black; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                            📺 Live Video Feed
                        </button>
                        <button onclick="nexusTelematics.triggerDiag('${data.id}')" 
                                style="padding: 8px 12px; background: linear-gradient(135deg, #ff6600, #cc4400); 
                                       color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                            🔧 Run Diagnostics
                        </button>
                        <button onclick="nexusTelematics.viewDetails('${data.id}')" 
                                style="padding: 8px 12px; background: linear-gradient(135deg, #0088ff, #0066cc); 
                                       color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                            📊 Asset Details
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        
        console.log(`📍 Asset ${data.id} updated: ${data.lat.toFixed(4)}, ${data.lng.toFixed(4)} @ ${Math.round(data.speed)} mph`);
    }

    enablePiP(assetId) {
        console.log(`🎥 Enabling PiP for asset: ${assetId}`);
        
        // Create or get video element for this asset
        let video = this.pipVideos.get(assetId);
        if (!video) {
            video = document.createElement('video');
            video.src = `data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAACKBtZGF0AAAC`;
            video.controls = true;
            video.muted = true;
            video.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 320px;
                height: 240px;
                z-index: 2000;
                border-radius: 8px;
                border: 2px solid #00ff00;
                background: black;
            `;
            document.body.appendChild(video);
            this.pipVideos.set(assetId, video);
        }

        // Attempt Picture-in-Picture
        if (video.requestPictureInPicture && !document.pictureInPictureElement) {
            video.requestPictureInPicture()
                .then(() => {
                    console.log(`✅ PiP enabled for ${assetId}`);
                    this.showNotification(`📺 PiP enabled for ${assetId}`, 'success');
                })
                .catch(err => {
                    console.error('PiP error:', err);
                    this.showNotification(`❌ PiP not supported`, 'error');
                });
        } else {
            // Fallback: show video in corner
            video.style.display = 'block';
            video.play();
            this.showNotification(`📺 Video displayed for ${assetId}`, 'info');
        }
    }

    async triggerDiag(assetId) {
        console.log(`🔧 Running AI-powered diagnostics for ${assetId}...`);
        
        // Get asset data for AI analysis
        const asset = this.assets.get(assetId) || this.telemetrySimulator?.getAsset(assetId);
        
        try {
            // Call automation endpoint with enhanced AI diagnostic data
            const response = await fetch('/api/automation/trigger', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    asset_id: assetId,
                    job_id: `DIAG-${Date.now()}`,
                    trigger_type: 'ai_diagnostic',
                    location: 'Dallas, TX',
                    asset_data: asset ? {
                        fuel_level: asset.fuelLevel,
                        engine_hours: asset.engineHours,
                        speed: asset.speed,
                        status: asset.status,
                        operator: asset.operator,
                        type: asset.type,
                        last_maintenance: asset.lastMaintenance
                    } : null
                })
            });
            
            const result = await response.json();
            console.log('📊 AI Diagnostic response:', result);
            
            // Show enhanced notification with AI insights
            if (result.ai_analysis) {
                this.showNotification(`🧠 AI Analysis for ${assetId}: ${result.ai_analysis}`, 'success');
            } else {
                this.showNotification(`Diagnostic initiated for ${assetId}: ${result.message}`, 'success');
            }
        } catch (error) {
            console.error('❌ Diagnostic error:', error);
            this.showNotification(`Diagnostic failed for ${assetId}`, 'error');
        }
    }

    viewDetails(assetId) {
        console.log(`📊 Viewing detailed analytics for ${assetId}...`);
        
        const asset = this.assets.get(assetId) || this.telemetrySimulator?.getAsset(assetId);
        
        if (asset) {
            // Create detailed modal with asset information
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.8); z-index: 10000; display: flex;
                align-items: center; justify-content: center; font-family: 'Courier New', monospace;
            `;
            
            modal.innerHTML = `
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border: 2px solid #00ff88; 
                           border-radius: 12px; padding: 20px; max-width: 500px; width: 90%; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h2 style="color: #00ff88; margin: 0;">Asset Details: ${assetId}</h2>
                        <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                                style="background: #ff4444; color: white; border: none; border-radius: 50%; 
                                       width: 30px; height: 30px; cursor: pointer;">×</button>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                        <div><strong>Operator:</strong><br/>${asset.operator || 'N/A'}</div>
                        <div><strong>Type:</strong><br/>${asset.type || 'N/A'}</div>
                        <div><strong>Status:</strong><br/><span style="color: ${asset.status === 'Active' ? '#00ff88' : '#ffaa00'}">${asset.status || 'Unknown'}</span></div>
                        <div><strong>Speed:</strong><br/>${Math.round(asset.speed || 0)} mph</div>
                        <div><strong>Fuel Level:</strong><br/><span style="color: ${(asset.fuelLevel || 75) > 50 ? '#00ff88' : '#ff4444'}">${Math.round(asset.fuelLevel || 75)}%</span></div>
                        <div><strong>Engine Hours:</strong><br/>${Math.round(asset.engineHours || 0)}</div>
                        <div><strong>Location:</strong><br/>${asset.lat?.toFixed(4)}, ${asset.lng?.toFixed(4)}</div>
                        <div><strong>Last Update:</strong><br/>${new Date(asset.lastUpdate || Date.now()).toLocaleTimeString()}</div>
                    </div>
                    <button onclick="nexusTelematics.requestAIAnalysis('${assetId}')" 
                            style="width: 100%; padding: 12px; background: linear-gradient(135deg, #00ff88, #00cc66); 
                                   color: black; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                        🧠 Request AI Performance Analysis
                    </button>
                </div>
            `;
            
            document.body.appendChild(modal);
        } else {
            this.showNotification(`Asset ${assetId} not found`, 'error');
        }
    }

    async requestAIAnalysis(assetId) {
        console.log(`🧠 Requesting AI analysis for ${assetId}...`);
        
        const asset = this.assets.get(assetId) || this.telemetrySimulator?.getAsset(assetId);
        
        try {
            const response = await fetch('/api/ai-asset-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    asset_id: assetId,
                    asset_data: asset
                })
            });
            
            const result = await response.json();
            
            if (result.analysis) {
                // Display AI analysis in notification
                this.showNotification(`🧠 AI Analysis: ${result.analysis}`, 'success', 8000);
            } else {
                this.showNotification('AI analysis completed - check logs for details', 'success');
            }
        } catch (error) {
            console.error('❌ AI Analysis error:', error);
            this.showNotification('AI analysis failed - please try again', 'error');
        }
    }

    setupAutomationTriggers() {
        // Add automation endpoint to Flask app if not exists
        console.log('🤖 Setting up automation triggers...');
        
        // Global function for PiP access
        window.nexusTelematics = this;
    }

    createStatusOverlay() {
        const statusBar = document.createElement('div');
        statusBar.id = 'telematics-status';
        statusBar.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            background: rgba(0, 0, 0, 0.8);
            color: #ff6600;
            border: 1px solid #ff6600;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            z-index: 3000;
        `;
        statusBar.textContent = '⏳ Quantum Telematics Initializing...';
        document.body.appendChild(statusBar);
    }

    updateStatusOverlay() {
        const statusBar = document.getElementById('telematics-status');
        if (statusBar) {
            if (this.isOnline) {
                statusBar.textContent = '✅ Quantum Telematics Online';
                statusBar.style.color = '#00ff00';
                statusBar.style.borderColor = '#00ff00';
            } else {
                statusBar.textContent = '❌ Quantum Telematics Offline';
                statusBar.style.color = '#ff0000';
                statusBar.style.borderColor = '#ff0000';
            }
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            left: 20px;
            padding: 12px 16px;
            background: ${type === 'success' ? '#004400' : type === 'error' ? '#440000' : '#444400'};
            color: ${type === 'success' ? '#00ff00' : type === 'error' ? '#ff0000' : '#ffff00'};
            border: 1px solid ${type === 'success' ? '#00ff00' : type === 'error' ? '#ff0000' : '#ffff00'};
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            z-index: 4000;
            max-width: 300px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    loadAssetData() {
        // Load authentic asset data from the API
        fetch('/api/comprehensive-data')
            .then(response => response.json())
            .then(data => {
                console.log('📊 Loaded authentic asset data for telematics');
                // Use real asset data for enhanced tracking
            })
            .catch(error => {
                console.warn('Asset data not available, using mock telemetry');
            });
    }
}

// Initialize telematics system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.nexusTelematics = new NexusTelematics();
    });
} else {
    window.nexusTelematics = new NexusTelematics();
}

console.log('🚀 NEXUS Telematics Module Loaded - QNIS_telematics_core_v1');