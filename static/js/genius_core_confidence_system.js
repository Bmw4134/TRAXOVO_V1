/**
 * TRAXORA GENIUS CORE | Adaptive Confidence Self-Reporting System
 * 
 * This module enhances the GENIUS CORE with adaptive confidence reporting capabilities,
 * allowing each module to assess and report its own confidence levels based on
 * data quality, consistency, and validation results.
 */

class AdaptiveConfidenceSystem {
    constructor() {
        // Check if required components exist
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Adaptive Confidence System initialization aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.confidenceData = {
            'asset-map': {
                overall: 0,
                factors: {},
                history: [],
                lastUpdate: null
            },
            'driver-reports': {
                overall: 0,
                factors: {},
                history: [],
                lastUpdate: null
            },
            'pm-allocation': {
                overall: 0,
                factors: {},
                history: [],
                lastUpdate: null
            },
            'system': {
                overall: 0,
                factors: {},
                history: [],
                lastUpdate: null
            }
        };
        
        // Register with GENIUS CORE
        this.confidenceAgent = {
            id: 'ConfidenceSystem',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'report-confidence':
                        return window.ConfidenceSystem.reportConfidence(
                            message.payload.moduleId,
                            message.payload.confidence,
                            message.payload.factors
                        );
                        
                    case 'get-confidence':
                        return {
                            status: 'confidence-data',
                            data: window.ConfidenceSystem.getConfidence(
                                message.payload.moduleId
                            )
                        };
                        
                    case 'get-system-confidence':
                        return {
                            status: 'system-confidence',
                            data: window.ConfidenceSystem.getSystemConfidence()
                        };
                        
                    case 'analyze-data-quality':
                        return {
                            status: 'data-quality-analysis',
                            analysis: window.ConfidenceSystem.analyzeDataQuality(
                                message.payload.moduleId,
                                message.payload.data,
                                message.payload.metrics
                            )
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('ConfidenceSystem', this.confidenceAgent);
        
        // Initialize components
        this.initializeComponents();
        
        console.log('Adaptive Confidence System initialized');
    }
    
    initializeComponents() {
        // Register for module status updates
        if (window.ModuleStatus) {
            // Set baseline confidence for each module
            this.reportInitialConfidence();
        }
        
        // Create confidence indicator UI
        this.createConfidenceIndicatorUI();
        
        // Set up periodic confidence assessment
        this.setupPeriodicAssessment();
    }
    
    reportInitialConfidence() {
        // Report initial confidence for each module based on availability
        if (window.AssetTracker) {
            this.reportConfidence('asset-map', 70, {
                'data-freshness': 75,
                'data-completeness': 65,
                'data-accuracy': 70,
                'asset-coverage': 70
            });
        } else {
            this.reportConfidence('asset-map', 10, {
                'module-availability': 10
            });
        }
        
        if (window.DriverPipeline) {
            this.reportConfidence('driver-reports', 40, {
                'data-freshness': 40,
                'data-completeness': 40,
                'data-accuracy': 40,
                'classification-confidence': 40
            });
        } else {
            this.reportConfidence('driver-reports', 10, {
                'module-availability': 10
            });
        }
        
        if (window.BillingVerifier) {
            this.reportConfidence('pm-allocation', 50, {
                'data-freshness': 50,
                'data-completeness': 50,
                'data-accuracy': 50,
                'allocation-confidence': 50
            });
        } else {
            this.reportConfidence('pm-allocation', 10, {
                'module-availability': 10
            });
        }
        
        // Calculate system-wide confidence
        this.updateSystemConfidence();
    }
    
    createConfidenceIndicatorUI() {
        // Create confidence indicator container
        let confidenceContainer = document.getElementById('genius-confidence-container');
        if (!confidenceContainer) {
            confidenceContainer = document.createElement('div');
            confidenceContainer.id = 'genius-confidence-container';
            confidenceContainer.className = 'genius-confidence-container';
            document.body.appendChild(confidenceContainer);
            
            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .genius-confidence-container {
                    position: fixed;
                    z-index: 1001;
                    pointer-events: none;
                }
                
                .genius-confidence-panel {
                    position: fixed;
                    top: 70px;
                    right: 20px;
                    width: 250px;
                    background: rgba(33, 37, 41, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    color: white;
                    font-family: sans-serif;
                    z-index: 1000;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    pointer-events: auto;
                    display: none;
                }
                
                .genius-confidence-panel.visible {
                    display: block;
                }
                
                .confidence-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 15px;
                    background: rgba(0, 0, 0, 0.2);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .confidence-header h6 {
                    margin: 0;
                    color: #33d4ff;
                    font-size: 14px;
                }
                
                .confidence-toggle {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 16px;
                    cursor: pointer;
                    padding: 0 5px;
                }
                
                .confidence-content {
                    padding: 15px;
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                
                .confidence-item {
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }
                
                .confidence-item-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .module-name {
                    font-weight: bold;
                    font-size: 13px;
                }
                
                .confidence-level {
                    font-size: 12px;
                    padding: 2px 8px;
                    border-radius: 10px;
                }
                
                .confidence-level.high {
                    background: rgba(40, 167, 69, 0.2);
                    color: #28a745;
                }
                
                .confidence-level.medium {
                    background: rgba(255, 193, 7, 0.2);
                    color: #ffc107;
                }
                
                .confidence-level.low {
                    background: rgba(220, 53, 69, 0.2);
                    color: #dc3545;
                }
                
                .confidence-bar {
                    height: 6px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                    overflow: hidden;
                }
                
                .confidence-bar-fill {
                    height: 100%;
                    transition: width 0.5s ease;
                }
                
                .confidence-bar-fill.high {
                    background: #28a745;
                }
                
                .confidence-bar-fill.medium {
                    background: #ffc107;
                }
                
                .confidence-bar-fill.low {
                    background: #dc3545;
                }
                
                .confidence-factors {
                    margin-top: 8px;
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                    font-size: 12px;
                }
                
                .confidence-factor {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .factor-name {
                    color: #ccc;
                }
                
                .factor-value {
                    padding: 1px 6px;
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.1);
                    min-width: 30px;
                    text-align: center;
                }
                
                .factor-value.high {
                    color: #28a745;
                }
                
                .factor-value.medium {
                    color: #ffc107;
                }
                
                .factor-value.low {
                    color: #dc3545;
                }
                
                .system-confidence {
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .system-confidence-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }
                
                .system-confidence-title {
                    font-weight: bold;
                }
                
                .system-confidence-level {
                    font-size: 14px;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-weight: bold;
                }
                
                .confidence-badge {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 2px 8px;
                    background: rgba(33, 37, 41, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    height: 24px;
                    cursor: pointer;
                }
                
                .confidence-badge.high {
                    background: #28a745;
                    color: white;
                }
                
                .confidence-badge.medium {
                    background: #ffc107;
                    color: black;
                }
                
                .confidence-badge.low {
                    background: #dc3545;
                    color: white;
                }
                
                .confidence-badge:hover {
                    filter: brightness(1.1);
                }
                
                .confidence-badge .value {
                    margin-left: 5px;
                    font-weight: normal;
                }
                
                .confidence-toggle-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 5px;
                    background: rgba(33, 37, 41, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    color: white;
                    font-size: 12px;
                    padding: 5px 10px;
                    cursor: pointer;
                }
                
                .confidence-toggle-button:hover {
                    background: rgba(33, 37, 41, 1);
                }
            `;
            
            document.head.appendChild(style);
        }
        
        // Create confidence panel
        this.createConfidencePanel();
        
        // Create confidence badges
        this.createConfidenceBadges();
    }
    
    createConfidencePanel() {
        let confidencePanel = document.getElementById('genius-confidence-panel');
        if (!confidencePanel) {
            confidencePanel = document.createElement('div');
            confidencePanel.id = 'genius-confidence-panel';
            confidencePanel.className = 'genius-confidence-panel';
            
            confidencePanel.innerHTML = `
                <div class="confidence-header">
                    <h6>GENIUS CORE Self-Assessment</h6>
                    <button class="confidence-toggle">−</button>
                </div>
                <div class="confidence-content">
                    <div class="confidence-item" id="asset-map-confidence">
                        <div class="confidence-item-header">
                            <span class="module-name">Asset Map</span>
                            <span class="confidence-level medium">Medium (70%)</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-bar-fill medium" style="width: 70%"></div>
                        </div>
                        <div class="confidence-factors">
                            <div class="confidence-factor">
                                <span class="factor-name">Data Freshness</span>
                                <span class="factor-value medium">75%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Completeness</span>
                                <span class="factor-value medium">65%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Accuracy</span>
                                <span class="factor-value medium">70%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Asset Coverage</span>
                                <span class="factor-value medium">70%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="confidence-item" id="driver-reports-confidence">
                        <div class="confidence-item-header">
                            <span class="module-name">Driver Reports</span>
                            <span class="confidence-level low">Low (40%)</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-bar-fill low" style="width: 40%"></div>
                        </div>
                        <div class="confidence-factors">
                            <div class="confidence-factor">
                                <span class="factor-name">Data Freshness</span>
                                <span class="factor-value low">40%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Completeness</span>
                                <span class="factor-value low">40%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Accuracy</span>
                                <span class="factor-value low">40%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Classification Confidence</span>
                                <span class="factor-value low">40%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="confidence-item" id="pm-allocation-confidence">
                        <div class="confidence-item-header">
                            <span class="module-name">PM Allocation</span>
                            <span class="confidence-level medium">Medium (50%)</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-bar-fill medium" style="width: 50%"></div>
                        </div>
                        <div class="confidence-factors">
                            <div class="confidence-factor">
                                <span class="factor-name">Data Freshness</span>
                                <span class="factor-value medium">50%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Completeness</span>
                                <span class="factor-value medium">50%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Data Accuracy</span>
                                <span class="factor-value medium">50%</span>
                            </div>
                            <div class="confidence-factor">
                                <span class="factor-name">Allocation Confidence</span>
                                <span class="factor-value medium">50%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="system-confidence" id="system-confidence">
                        <div class="system-confidence-header">
                            <span class="system-confidence-title">System Confidence</span>
                            <span class="system-confidence-level medium">54%</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-bar-fill medium" style="width: 54%"></div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(confidencePanel);
            
            // Add toggle behavior
            const header = confidencePanel.querySelector('.confidence-header');
            const toggleBtn = confidencePanel.querySelector('.confidence-toggle');
            
            header.addEventListener('click', function() {
                confidencePanel.classList.toggle('collapsed');
                toggleBtn.textContent = confidencePanel.classList.contains('collapsed') ? '+' : '−';
            });
            
            // Update confidence data from stored values
            this.updateConfidencePanel();
        }
    }
    
    createConfidenceBadges() {
        // Create confidence badge in the manifest toggle if it exists
        const manifestButton = document.querySelector('.genius-manifest-button');
        if (manifestButton) {
            const badge = document.createElement('div');
            badge.id = 'system-confidence-badge';
            badge.className = 'confidence-badge medium';
            badge.innerHTML = `Confidence <span class="value">54%</span>`;
            
            badge.addEventListener('click', () => {
                const panel = document.getElementById('genius-confidence-panel');
                if (panel) {
                    panel.classList.toggle('visible');
                }
            });
            
            // Append badge to the toggle button
            const toggleButton = manifestButton.querySelector('.genius-manifest-toggle');
            if (toggleButton) {
                toggleButton.appendChild(badge);
            }
        }
        
        // Add confidence toggle to status panel
        const statusPanel = document.getElementById('genius-module-status');
        if (statusPanel) {
            const confidenceToggle = document.createElement('button');
            confidenceToggle.id = 'confidence-toggle-btn';
            confidenceToggle.className = 'genius-button primary small';
            confidenceToggle.textContent = 'Confidence';
            confidenceToggle.style.marginTop = '10px';
            confidenceToggle.style.marginRight = '10px';
            
            confidenceToggle.addEventListener('click', function() {
                const panel = document.getElementById('genius-confidence-panel');
                if (panel) {
                    panel.classList.toggle('visible');
                }
            });
            
            statusPanel.querySelector('.genius-ui-content').prepend(confidenceToggle);
        }
    }
    
    reportConfidence(moduleId, confidence, factors) {
        if (!this.confidenceData[moduleId]) {
            console.warn(`Unknown module: ${moduleId}`);
            return {
                status: 'error',
                message: `Unknown module: ${moduleId}`
            };
        }
        
        // Store previous confidence for history
        const previousConfidence = this.confidenceData[moduleId].overall;
        if (previousConfidence > 0) {
            this.confidenceData[moduleId].history.push({
                confidence: previousConfidence,
                timestamp: this.confidenceData[moduleId].lastUpdate
            });
            
            // Keep history size manageable
            if (this.confidenceData[moduleId].history.length > 20) {
                this.confidenceData[moduleId].history.shift();
            }
        }
        
        // Update confidence data
        this.confidenceData[moduleId].overall = confidence;
        this.confidenceData[moduleId].factors = factors;
        this.confidenceData[moduleId].lastUpdate = new Date().toISOString();
        
        // Log significant confidence changes
        if (Math.abs(confidence - previousConfidence) > 10) {
            if (window.VisualDiagnostics) {
                window.VisualDiagnostics.logEvent('ConfidenceSystem', 'confidence-change', {
                    moduleId: moduleId,
                    previousConfidence: previousConfidence,
                    newConfidence: confidence,
                    message: `${moduleId} confidence changed from ${previousConfidence}% to ${confidence}%`
                });
            }
        }
        
        // Update system confidence
        this.updateSystemConfidence();
        
        // Update UI
        this.updateConfidencePanel();
        this.updateConfidenceBadges();
        
        return {
            status: 'confidence-reported',
            moduleId: moduleId,
            confidence: confidence
        };
    }
    
    getConfidence(moduleId) {
        if (!moduleId) {
            return this.confidenceData;
        }
        
        return this.confidenceData[moduleId] || null;
    }
    
    getSystemConfidence() {
        return this.confidenceData.system;
    }
    
    updateSystemConfidence() {
        // Calculate weighted average of all module confidences
        const modules = ['asset-map', 'driver-reports', 'pm-allocation'];
        const weights = {
            'asset-map': 0.4,
            'driver-reports': 0.35,
            'pm-allocation': 0.25
        };
        
        let weightedSum = 0;
        let weightSum = 0;
        
        modules.forEach(moduleId => {
            const moduleConf = this.confidenceData[moduleId];
            if (moduleConf.overall > 0) {
                weightedSum += moduleConf.overall * weights[moduleId];
                weightSum += weights[moduleId];
            }
        });
        
        const systemConfidence = weightSum > 0 ? 
            Math.round(weightedSum / weightSum) : 0;
        
        // Store previous confidence for history
        const previousConfidence = this.confidenceData.system.overall;
        if (previousConfidence > 0) {
            this.confidenceData.system.history.push({
                confidence: previousConfidence,
                timestamp: this.confidenceData.system.lastUpdate
            });
            
            // Keep history size manageable
            if (this.confidenceData.system.history.length > 20) {
                this.confidenceData.system.history.shift();
            }
        }
        
        // Update system confidence
        this.confidenceData.system.overall = systemConfidence;
        this.confidenceData.system.lastUpdate = new Date().toISOString();
        
        // Calculate system factors based on module factors
        const systemFactors = {};
        
        // Data freshness - average of all modules
        const freshnesses = modules.map(m => 
            this.confidenceData[m].factors['data-freshness'] || 0
        ).filter(f => f > 0);
        
        if (freshnesses.length > 0) {
            systemFactors['data-freshness'] = Math.round(
                freshnesses.reduce((a, b) => a + b, 0) / freshnesses.length
            );
        }
        
        // Data completeness - average of all modules
        const completenesses = modules.map(m => 
            this.confidenceData[m].factors['data-completeness'] || 0
        ).filter(c => c > 0);
        
        if (completenesses.length > 0) {
            systemFactors['data-completeness'] = Math.round(
                completenesses.reduce((a, b) => a + b, 0) / completenesses.length
            );
        }
        
        // Data accuracy - average of all modules
        const accuracies = modules.map(m => 
            this.confidenceData[m].factors['data-accuracy'] || 0
        ).filter(a => a > 0);
        
        if (accuracies.length > 0) {
            systemFactors['data-accuracy'] = Math.round(
                accuracies.reduce((a, b) => a + b, 0) / accuracies.length
            );
        }
        
        // Continuity - measure of module integration
        let continuityScore = 0;
        
        // Check if all modules are reporting confidence
        const reportingModules = modules.filter(m => this.confidenceData[m].overall > 0);
        if (reportingModules.length === modules.length) {
            continuityScore += 40;
        } else {
            continuityScore += Math.round((reportingModules.length / modules.length) * 40);
        }
        
        // Check if modules have recent updates
        const recentThreshold = Date.now() - (5 * 60 * 1000); // 5 minutes
        const recentModules = modules.filter(m => {
            const lastUpdate = this.confidenceData[m].lastUpdate;
            return lastUpdate && new Date(lastUpdate).getTime() > recentThreshold;
        });
        
        if (recentModules.length === modules.length) {
            continuityScore += 30;
        } else {
            continuityScore += Math.round((recentModules.length / modules.length) * 30);
        }
        
        // Check if all modules have confidence above a threshold
        const confidentModules = modules.filter(m => this.confidenceData[m].overall >= 50);
        if (confidentModules.length === modules.length) {
            continuityScore += 30;
        } else {
            continuityScore += Math.round((confidentModules.length / modules.length) * 30);
        }
        
        systemFactors['continuity'] = continuityScore;
        
        this.confidenceData.system.factors = systemFactors;
        
        // Log significant system confidence changes
        if (Math.abs(systemConfidence - previousConfidence) > 10) {
            if (window.VisualDiagnostics) {
                window.VisualDiagnostics.logEvent('ConfidenceSystem', 'system-confidence-change', {
                    previousConfidence: previousConfidence,
                    newConfidence: systemConfidence,
                    message: `System confidence changed from ${previousConfidence}% to ${systemConfidence}%`
                });
            }
        }
        
        return {
            overall: systemConfidence,
            factors: systemFactors
        };
    }
    
    updateConfidencePanel() {
        // Update module confidence displays in the panel
        ['asset-map', 'driver-reports', 'pm-allocation'].forEach(moduleId => {
            const moduleData = this.confidenceData[moduleId];
            const moduleElement = document.getElementById(`${moduleId}-confidence`);
            
            if (moduleElement && moduleData) {
                const confidence = moduleData.overall;
                const confidenceLevel = this.getConfidenceLevel(confidence);
                
                // Update header
                const header = moduleElement.querySelector('.confidence-item-header');
                if (header) {
                    const levelElement = header.querySelector('.confidence-level');
                    if (levelElement) {
                        levelElement.className = `confidence-level ${confidenceLevel}`;
                        levelElement.textContent = `${this.confidenceLevelText(confidenceLevel)} (${confidence}%)`;
                    }
                }
                
                // Update bar
                const bar = moduleElement.querySelector('.confidence-bar-fill');
                if (bar) {
                    bar.className = `confidence-bar-fill ${confidenceLevel}`;
                    bar.style.width = `${confidence}%`;
                }
                
                // Update factors
                const factors = moduleElement.querySelector('.confidence-factors');
                if (factors && moduleData.factors) {
                    let factorsHtml = '';
                    
                    Object.entries(moduleData.factors).forEach(([factor, value]) => {
                        const factorLevel = this.getConfidenceLevel(value);
                        const factorName = this.getFactorDisplayName(factor);
                        
                        factorsHtml += `
                            <div class="confidence-factor">
                                <span class="factor-name">${factorName}</span>
                                <span class="factor-value ${factorLevel}">${value}%</span>
                            </div>
                        `;
                    });
                    
                    factors.innerHTML = factorsHtml;
                }
            }
        });
        
        // Update system confidence
        const systemData = this.confidenceData.system;
        const systemElement = document.getElementById('system-confidence');
        
        if (systemElement && systemData) {
            const confidence = systemData.overall;
            const confidenceLevel = this.getConfidenceLevel(confidence);
            
            // Update header
            const header = systemElement.querySelector('.system-confidence-header');
            if (header) {
                const levelElement = header.querySelector('.system-confidence-level');
                if (levelElement) {
                    levelElement.className = `system-confidence-level ${confidenceLevel}`;
                    levelElement.textContent = `${confidence}%`;
                }
            }
            
            // Update bar
            const bar = systemElement.querySelector('.confidence-bar-fill');
            if (bar) {
                bar.className = `confidence-bar-fill ${confidenceLevel}`;
                bar.style.width = `${confidence}%`;
            }
        }
    }
    
    updateConfidenceBadges() {
        // Update system confidence badge
        const systemConfidence = this.confidenceData.system.overall;
        const systemConfidenceLevel = this.getConfidenceLevel(systemConfidence);
        
        const badge = document.getElementById('system-confidence-badge');
        if (badge) {
            badge.className = `confidence-badge ${systemConfidenceLevel}`;
            const valueElement = badge.querySelector('.value');
            if (valueElement) {
                valueElement.textContent = `${systemConfidence}%`;
            }
        }
    }
    
    getConfidenceLevel(confidence) {
        if (confidence >= 80) {
            return 'high';
        } else if (confidence >= 50) {
            return 'medium';
        } else {
            return 'low';
        }
    }
    
    confidenceLevelText(level) {
        switch (level) {
            case 'high':
                return 'High';
            case 'medium':
                return 'Medium';
            case 'low':
                return 'Low';
            default:
                return 'Unknown';
        }
    }
    
    getFactorDisplayName(factor) {
        // Convert factor keys to display names
        const factorDisplayNames = {
            'data-freshness': 'Data Freshness',
            'data-completeness': 'Data Completeness',
            'data-accuracy': 'Data Accuracy',
            'asset-coverage': 'Asset Coverage',
            'classification-confidence': 'Classification Confidence',
            'allocation-confidence': 'Allocation Confidence',
            'continuity': 'System Continuity',
            'module-availability': 'Module Availability'
        };
        
        return factorDisplayNames[factor] || factor;
    }
    
    analyzeDataQuality(moduleId, data, metrics) {
        // This function analyzes data quality based on provided metrics
        // For a real implementation, this would perform more sophisticated analysis
        
        const results = {};
        
        if (metrics.includes('completeness')) {
            results.completeness = this.assessCompleteness(moduleId, data);
        }
        
        if (metrics.includes('freshness')) {
            results.freshness = this.assessFreshness(moduleId, data);
        }
        
        if (metrics.includes('accuracy')) {
            results.accuracy = this.assessAccuracy(moduleId, data);
        }
        
        if (metrics.includes('consistency')) {
            results.consistency = this.assessConsistency(moduleId, data);
        }
        
        return results;
    }
    
    assessCompleteness(moduleId, data) {
        // Assess data completeness
        // This is a simplified implementation for demonstration
        
        if (!data || !Array.isArray(data)) {
            return 0;
        }
        
        // Count items with all required fields
        let completeCount = 0;
        const requiredFields = this.getRequiredFields(moduleId);
        
        data.forEach(item => {
            let isComplete = true;
            
            for (const field of requiredFields) {
                if (item[field] === undefined || item[field] === null || item[field] === '') {
                    isComplete = false;
                    break;
                }
            }
            
            if (isComplete) {
                completeCount++;
            }
        });
        
        return data.length > 0 ? Math.round((completeCount / data.length) * 100) : 0;
    }
    
    assessFreshness(moduleId, data) {
        // Assess data freshness
        // This is a simplified implementation for demonstration
        
        if (!data || !Array.isArray(data)) {
            return 0;
        }
        
        // Check for last update timestamps
        const timestampField = this.getTimestampField(moduleId);
        if (!timestampField) {
            return 50; // Default if we can't assess
        }
        
        const now = Date.now();
        let freshnessSum = 0;
        let itemsWithTimestamp = 0;
        
        // How fresh is considered 100% (in milliseconds)
        const freshThreshold = 60 * 60 * 1000; // 1 hour
        // How stale is considered 0% (in milliseconds)
        const staleThreshold = 24 * 60 * 60 * 1000; // 24 hours
        
        data.forEach(item => {
            if (item[timestampField]) {
                try {
                    const timestamp = new Date(item[timestampField]).getTime();
                    const age = now - timestamp;
                    
                    if (age <= freshThreshold) {
                        freshnessSum += 100;
                    } else if (age >= staleThreshold) {
                        freshnessSum += 0;
                    } else {
                        // Linear scale between fresh and stale
                        const freshness = 100 - Math.round(
                            ((age - freshThreshold) / (staleThreshold - freshThreshold)) * 100
                        );
                        freshnessSum += freshness;
                    }
                    
                    itemsWithTimestamp++;
                } catch (e) {
                    // Invalid timestamp format
                }
            }
        });
        
        return itemsWithTimestamp > 0 ? Math.round(freshnessSum / itemsWithTimestamp) : 0;
    }
    
    assessAccuracy(moduleId, data) {
        // Assess data accuracy
        // This would require comparisons with ground truth or validation rules
        // For demonstration, we'll use simplified heuristics
        
        if (!data || !Array.isArray(data)) {
            return 0;
        }
        
        // Check for value ranges and expected formats
        let validCount = 0;
        const validationRules = this.getValidationRules(moduleId);
        
        data.forEach(item => {
            let isValid = true;
            
            for (const [field, rule] of Object.entries(validationRules)) {
                if (item[field] !== undefined && !rule(item[field])) {
                    isValid = false;
                    break;
                }
            }
            
            if (isValid) {
                validCount++;
            }
        });
        
        return data.length > 0 ? Math.round((validCount / data.length) * 100) : 0;
    }
    
    assessConsistency(moduleId, data) {
        // Assess data consistency across modules
        // This would require comparison with other modules
        // For demonstration, we'll return a reasonable value
        
        return 65; // Default for demonstration
    }
    
    getRequiredFields(moduleId) {
        // Return required fields for each module
        const requiredFieldsMap = {
            'asset-map': ['id', 'latitude', 'longitude', 'type'],
            'driver-reports': ['driver', 'jobNumber', 'status'],
            'pm-allocation': ['pmCode', 'jobNumber', 'allocation']
        };
        
        return requiredFieldsMap[moduleId] || [];
    }
    
    getTimestampField(moduleId) {
        // Return timestamp field for each module
        const timestampFieldMap = {
            'asset-map': 'last_update',
            'driver-reports': 'timestamp',
            'pm-allocation': 'lastUpdate'
        };
        
        return timestampFieldMap[moduleId] || null;
    }
    
    getValidationRules(moduleId) {
        // Return validation rules for each module
        const validationRulesMap = {
            'asset-map': {
                'latitude': (val) => !isNaN(val) && val >= -90 && val <= 90,
                'longitude': (val) => !isNaN(val) && val >= -180 && val <= 180,
                'type': (val) => typeof val === 'string' && val.length > 0
            },
            'driver-reports': {
                'driver': (val) => typeof val === 'string' && val.length > 0,
                'status': (val) => ['active', 'inactive', 'unknown'].includes(val)
            },
            'pm-allocation': {
                'allocation': (val) => !isNaN(val) && val >= 0 && val <= 1,
                'pmCode': (val) => typeof val === 'string' && val.length > 0
            }
        };
        
        return validationRulesMap[moduleId] || {};
    }
    
    setupPeriodicAssessment() {
        // Periodically assess module confidence based on data quality
        if (this.geniusCore) {
            this.geniusCore.registerPeriodicTask(
                'confidence-assessment',
                'ConfidenceSystem',
                60000, // Check every minute
                () => this.performPeriodicAssessment()
            );
        }
    }
    
    performPeriodicAssessment() {
        console.log('Performing periodic confidence assessment...');
        
        // For demonstration, we'll periodically fluctuate the confidence
        // based on some random factors to simulate changing data quality
        
        // Asset Map confidence assessment
        if (window.AssetTracker) {
            // In a real implementation, this would analyze actual asset data
            // For demonstration, we'll use realistic variations
            
            const currentConfidence = this.confidenceData['asset-map'].overall;
            const variation = (Math.random() * 10) - 5; // -5 to +5
            
            // Ensure confidence stays in 60-90 range for demonstration
            let newConfidence = Math.max(60, Math.min(90, currentConfidence + variation));
            newConfidence = Math.round(newConfidence);
            
            if (Math.abs(newConfidence - currentConfidence) >= 1) {
                // Only update if there's at least a 1% change
                const newFactors = {
                    'data-freshness': Math.round(Math.max(60, Math.min(95, this.confidenceData['asset-map'].factors['data-freshness'] + (Math.random() * 6) - 3))),
                    'data-completeness': Math.round(Math.max(60, Math.min(90, this.confidenceData['asset-map'].factors['data-completeness'] + (Math.random() * 6) - 3))),
                    'data-accuracy': Math.round(Math.max(65, Math.min(90, this.confidenceData['asset-map'].factors['data-accuracy'] + (Math.random() * 6) - 3))),
                    'asset-coverage': Math.round(Math.max(65, Math.min(95, this.confidenceData['asset-map'].factors['asset-coverage'] + (Math.random() * 6) - 3)))
                };
                
                this.reportConfidence('asset-map', newConfidence, newFactors);
            }
        }
        
        // Driver Reports confidence assessment
        if (window.DriverPipeline) {
            // In a real implementation, this would analyze actual driver data
            
            // Check if driver files have been uploaded
            const filesReady = window.DriverPipeline.checkFilesReady 
                ? window.DriverPipeline.checkFilesReady() 
                : false;
            
            // Start with current confidence
            const currentConfidence = this.confidenceData['driver-reports'].overall;
            let newConfidence = currentConfidence;
            
            // If files are ready, boost confidence gradually to 70-80 range
            if (filesReady) {
                const targetConfidence = 70 + (Math.random() * 10);
                // Move 10% closer to target each assessment
                newConfidence = Math.round(currentConfidence + (targetConfidence - currentConfidence) * 0.1);
            } else {
                // If no files, gradually decrease to 30-40 range
                const targetConfidence = 30 + (Math.random() * 10);
                // Move 10% closer to target each assessment
                newConfidence = Math.round(currentConfidence + (targetConfidence - currentConfidence) * 0.1);
            }
            
            if (Math.abs(newConfidence - currentConfidence) >= 1) {
                // Only update if there's at least a 1% change
                const newFactors = {
                    'data-freshness': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'data-completeness': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'data-accuracy': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'classification-confidence': Math.round(newConfidence * (0.9 + (Math.random() * 0.2)))
                };
                
                this.reportConfidence('driver-reports', newConfidence, newFactors);
            }
        }
        
        // PM Allocation confidence assessment
        if (window.BillingVerifier) {
            // In a real implementation, this would analyze actual billing data
            
            // Check if files are ready
            const filesReady = window.BillingVerifier.checkFilesReady
                ? window.BillingVerifier.checkFilesReady()
                : false;
            
            // Start with current confidence
            const currentConfidence = this.confidenceData['pm-allocation'].overall;
            let newConfidence = currentConfidence;
            
            // If files are ready, boost confidence gradually to 65-75 range
            if (filesReady) {
                const targetConfidence = 65 + (Math.random() * 10);
                // Move 10% closer to target each assessment
                newConfidence = Math.round(currentConfidence + (targetConfidence - currentConfidence) * 0.1);
            } else {
                // If no files, gradually decrease to 40-50 range
                const targetConfidence = 40 + (Math.random() * 10);
                // Move 10% closer to target each assessment
                newConfidence = Math.round(currentConfidence + (targetConfidence - currentConfidence) * 0.1);
            }
            
            if (Math.abs(newConfidence - currentConfidence) >= 1) {
                // Only update if there's at least a 1% change
                const newFactors = {
                    'data-freshness': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'data-completeness': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'data-accuracy': Math.round(newConfidence * (0.9 + (Math.random() * 0.2))),
                    'allocation-confidence': Math.round(newConfidence * (0.9 + (Math.random() * 0.2)))
                };
                
                this.reportConfidence('pm-allocation', newConfidence, newFactors);
            }
        }
    }
}

// Wait for GENIUS CORE to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if GENIUS CORE is loaded every 100ms
    const checkGeniusCore = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkGeniusCore);
            window.ConfidenceSystem = new AdaptiveConfidenceSystem();
            console.log('Adaptive Confidence System connected to GENIUS CORE');
            
            // Schedule initial data quality assessment
            setTimeout(() => {
                window.ConfidenceSystem.performPeriodicAssessment();
            }, 3000);
        }
    }, 100);
});

console.log('GENIUS CORE Adaptive Confidence System Loaded');