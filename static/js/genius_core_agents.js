/**
 * TRAXORA GENIUS CORE | Multi-Agent Architecture
 * 
 * This module implements a pseudo-parallel agent architecture for monitoring
 * and tracking status across different system modules.
 */

class GeniusAgentSystem {
    constructor() {
        this.agents = {};
        this.messageQueue = [];
        this.taskRegistry = {};
        this.continuityMode = true;
        this.masterLog = [];
        
        // Initialize core agents
        this.registerAgent('AssetTracker', this.createAssetTrackerAgent());
        this.registerAgent('JobSiteMonitor', this.createJobSiteMonitorAgent());
        this.registerAgent('RecommendationEngine', this.createRecommendationAgent());
        this.registerAgent('AnomalyDetector', this.createAnomalyDetectorAgent());
        this.registerAgent('BillingVerifier', this.createBillingVerifierAgent());
        
        // Start the event loop
        this.startEventLoop();
        
        console.log('GENIUS CORE Multi-Agent System Initialized');
        this.broadcastMessage('SystemAgent', 'system-ready', {
            timestamp: new Date().toISOString(),
            status: 'GENIUS CORE CONTINUITY MODE ACTIVE'
        });
    }
    
    /**
     * Register a new agent in the system
     */
    registerAgent(agentId, agentObject) {
        this.agents[agentId] = agentObject;
        console.log(`Agent registered: ${agentId}`);
        return agentId;
    }
    
    /**
     * Send a message to a specific agent
     */
    sendMessage(fromAgent, toAgent, messageType, payload) {
        if (!this.agents[toAgent]) {
            console.warn(`Unknown agent: ${toAgent}`);
            return false;
        }
        
        const message = {
            from: fromAgent,
            to: toAgent,
            type: messageType,
            payload: payload,
            timestamp: new Date().toISOString(),
            id: this.generateMessageId()
        };
        
        this.messageQueue.push(message);
        return message.id;
    }
    
    /**
     * Broadcast a message to all agents
     */
    broadcastMessage(fromAgent, messageType, payload) {
        const messageId = this.generateMessageId();
        
        Object.keys(this.agents).forEach(agentId => {
            if (agentId !== fromAgent) {
                this.messageQueue.push({
                    from: fromAgent,
                    to: agentId,
                    type: messageType,
                    payload: payload,
                    timestamp: new Date().toISOString(),
                    id: messageId
                });
            }
        });
        
        return messageId;
    }
    
    /**
     * Process the next message in the queue
     */
    processNextMessage() {
        if (this.messageQueue.length === 0) return null;
        
        const message = this.messageQueue.shift();
        const targetAgent = this.agents[message.to];
        
        if (targetAgent && typeof targetAgent.handleMessage === 'function') {
            try {
                const response = targetAgent.handleMessage(message);
                this.logMessage(message, response);
                return response;
            } catch (error) {
                console.error(`Error processing message by agent ${message.to}:`, error);
                return { error: error.message };
            }
        }
        
        return null;
    }
    
    /**
     * Process all messages in the queue
     */
    processAllMessages() {
        while (this.messageQueue.length > 0) {
            this.processNextMessage();
        }
    }
    
    /**
     * Log a message and its response
     */
    logMessage(message, response) {
        this.masterLog.push({
            message: message,
            response: response,
            timestamp: new Date().toISOString()
        });
        
        // Limit log size to prevent memory issues
        if (this.masterLog.length > 1000) {
            this.masterLog.shift();
        }
    }
    
    /**
     * Generate a unique message ID
     */
    generateMessageId() {
        return 'msg_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Start the event loop
     */
    startEventLoop() {
        // Process messages every 100ms
        setInterval(() => {
            this.processAllMessages();
        }, 100);
        
        // Agents can also register periodic tasks
        setInterval(() => {
            this.runPeriodicTasks();
        }, 1000);
    }
    
    /**
     * Register a periodic task
     */
    registerPeriodicTask(taskId, agentId, interval, taskFunction) {
        this.taskRegistry[taskId] = {
            agentId: agentId,
            interval: interval,
            lastRun: 0,
            func: taskFunction
        };
    }
    
    /**
     * Run all due periodic tasks
     */
    runPeriodicTasks() {
        const now = Date.now();
        
        Object.keys(this.taskRegistry).forEach(taskId => {
            const task = this.taskRegistry[taskId];
            if (now - task.lastRun >= task.interval) {
                task.lastRun = now;
                try {
                    task.func();
                } catch (error) {
                    console.error(`Error running task ${taskId}:`, error);
                }
            }
        });
    }
    
    // Factory methods for different agent types
    
    /**
     * Create an asset tracker agent
     */
    createAssetTrackerAgent() {
        return {
            id: 'AssetTracker',
            assets: {},
            
            handleMessage(message) {
                switch (message.type) {
                    case 'asset-update':
                        this.updateAsset(message.payload);
                        return { status: 'asset-updated', assetId: message.payload.id };
                    
                    case 'request-asset':
                        return { 
                            status: 'asset-info', 
                            asset: this.assets[message.payload.id]
                        };
                    
                    case 'asset-history':
                        return {
                            status: 'asset-history',
                            history: this.getAssetHistory(message.payload.id)
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            },
            
            updateAsset(assetData) {
                const existingAsset = this.assets[assetData.id];
                
                // If we already have this asset, move current data to history
                if (existingAsset) {
                    if (!existingAsset.history) {
                        existingAsset.history = [];
                    }
                    
                    // Don't store all fields in history to save memory
                    const historyEntry = {
                        timestamp: existingAsset.lastUpdate,
                        location: existingAsset.location,
                        latitude: existingAsset.latitude,
                        longitude: existingAsset.longitude,
                        status: existingAsset.status
                    };
                    
                    existingAsset.history.unshift(historyEntry);
                    
                    // Keep history limited to 100 entries
                    if (existingAsset.history.length > 100) {
                        existingAsset.history.pop();
                    }
                }
                
                // Update current asset data
                this.assets[assetData.id] = {
                    ...assetData,
                    lastUpdate: new Date().toISOString(),
                    history: existingAsset ? existingAsset.history : []
                };
                
                return true;
            },
            
            getAssetHistory(assetId) {
                const asset = this.assets[assetId];
                if (!asset || !asset.history) return [];
                return asset.history;
            }
        };
    },
    
    /**
     * Create a job site monitor agent
     */
    createJobSiteMonitorAgent() {
        return {
            id: 'JobSiteMonitor',
            jobSites: {},
            siteAssets: {},
            
            handleMessage(message) {
                switch (message.type) {
                    case 'site-update':
                        this.updateJobSite(message.payload);
                        return { status: 'site-updated', siteId: message.payload.id };
                    
                    case 'asset-at-site':
                        this.recordAssetAtSite(message.payload.assetId, message.payload.siteId);
                        return { status: 'asset-site-recorded' };
                        
                    case 'site-assets':
                        return {
                            status: 'site-assets',
                            assets: this.getAssetsAtSite(message.payload.siteId)
                        };
                        
                    case 'asset-sites':
                        return {
                            status: 'asset-sites',
                            sites: this.getSitesForAsset(message.payload.assetId)
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            },
            
            updateJobSite(siteData) {
                this.jobSites[siteData.id] = {
                    ...siteData,
                    lastUpdate: new Date().toISOString()
                };
                return true;
            },
            
            recordAssetAtSite(assetId, siteId) {
                if (!this.siteAssets[siteId]) {
                    this.siteAssets[siteId] = [];
                }
                
                // Only add asset if it's not already recorded at this site
                if (!this.siteAssets[siteId].includes(assetId)) {
                    this.siteAssets[siteId].push(assetId);
                }
                
                return true;
            },
            
            getAssetsAtSite(siteId) {
                return this.siteAssets[siteId] || [];
            },
            
            getSitesForAsset(assetId) {
                return Object.keys(this.siteAssets).filter(siteId => 
                    this.siteAssets[siteId].includes(assetId)
                );
            }
        };
    },
    
    /**
     * Create a recommendation agent
     */
    createRecommendationAgent() {
        return {
            id: 'RecommendationEngine',
            recommendations: {},
            
            handleMessage(message) {
                switch (message.type) {
                    case 'request-recommendation':
                        return {
                            status: 'recommendation',
                            recommendation: this.getRecommendation(
                                message.payload.assetId,
                                message.payload.assetType,
                                message.payload.sites
                            )
                        };
                        
                    case 'record-recommendation':
                        this.recordRecommendation(
                            message.payload.assetId,
                            message.payload.siteId,
                            message.payload.score
                        );
                        return { status: 'recommendation-recorded' };
                        
                    case 'get-site-recommendations':
                        return {
                            status: 'site-recommendations',
                            recommendations: this.getSiteRecommendations(message.payload.siteId)
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            },
            
            getRecommendation(assetId, assetType, sites) {
                // This would contain the scoring logic, but simplified here
                const scoredSites = sites.map(site => ({
                    site: site,
                    score: Math.random() * 100 // Simplified random score
                }));
                
                // Sort sites by score (highest first)
                scoredSites.sort((a, b) => b.score - a.score);
                
                // Record this recommendation for future reference
                this.recordRecommendation(assetId, scoredSites[0].site.id, scoredSites[0].score);
                
                return scoredSites;
            },
            
            recordRecommendation(assetId, siteId, score) {
                if (!this.recommendations[assetId]) {
                    this.recommendations[assetId] = [];
                }
                
                this.recommendations[assetId].unshift({
                    siteId: siteId,
                    score: score,
                    timestamp: new Date().toISOString()
                });
                
                // Keep history limited
                if (this.recommendations[assetId].length > 20) {
                    this.recommendations[assetId].pop();
                }
                
                return true;
            },
            
            getSiteRecommendations(siteId) {
                const result = [];
                
                Object.keys(this.recommendations).forEach(assetId => {
                    const assetRecs = this.recommendations[assetId];
                    const matchingRecs = assetRecs.filter(rec => rec.siteId === siteId);
                    
                    if (matchingRecs.length > 0) {
                        result.push({
                            assetId: assetId,
                            recommendations: matchingRecs
                        });
                    }
                });
                
                return result;
            }
        };
    },
    
    /**
     * Create an anomaly detector agent
     */
    createAnomalyDetectorAgent() {
        return {
            id: 'AnomalyDetector',
            anomalies: [],
            
            handleMessage(message) {
                switch (message.type) {
                    case 'check-anomaly':
                        const anomaly = this.checkForAnomalies(message.payload);
                        if (anomaly) {
                            this.recordAnomaly(anomaly);
                        }
                        return { 
                            status: 'anomaly-check-complete',
                            anomalyDetected: !!anomaly,
                            anomaly: anomaly 
                        };
                        
                    case 'get-anomalies':
                        return {
                            status: 'anomalies',
                            anomalies: this.getAnomalies(message.payload)
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            },
            
            checkForAnomalies(data) {
                // Simplified anomaly detection
                // In a real system, this would contain sophisticated logic
                
                // Example: detect if asset moved too far in a short time
                if (data.type === 'asset-movement' && data.distance > 50 && data.timespan < 600) {
                    return {
                        type: 'suspicious-movement',
                        assetId: data.assetId,
                        details: `Asset moved ${data.distance}km in ${data.timespan} seconds`,
                        severity: 'high',
                        timestamp: new Date().toISOString()
                    };
                }
                
                // Example: detect if equipment type doesn't match job site type
                if (data.type === 'asset-at-site' && data.assetType === 'Bridge Machine' && 
                    !data.siteType.toLowerCase().includes('bridge')) {
                    return {
                        type: 'equipment-site-mismatch',
                        assetId: data.assetId,
                        siteId: data.siteId,
                        details: `Bridge machine at non-bridge site`,
                        severity: 'medium',
                        timestamp: new Date().toISOString()
                    };
                }
                
                return null;
            },
            
            recordAnomaly(anomaly) {
                this.anomalies.unshift(anomaly);
                
                // Keep anomalies limited
                if (this.anomalies.length > 1000) {
                    this.anomalies.pop();
                }
                
                return true;
            },
            
            getAnomalies(filter = {}) {
                let results = [...this.anomalies];
                
                // Apply filters
                if (filter.assetId) {
                    results = results.filter(a => a.assetId === filter.assetId);
                }
                
                if (filter.type) {
                    results = results.filter(a => a.type === filter.type);
                }
                
                if (filter.severity) {
                    results = results.filter(a => a.severity === filter.severity);
                }
                
                if (filter.limit) {
                    results = results.slice(0, filter.limit);
                }
                
                return results;
            }
        };
    },
    
    /**
     * Create a billing verifier agent
     */
    createBillingVerifierAgent() {
        return {
            id: 'BillingVerifier',
            verifications: {},
            
            handleMessage(message) {
                switch (message.type) {
                    case 'verify-billing':
                        const result = this.verifyBilling(
                            message.payload.assetId,
                            message.payload.siteId,
                            message.payload.period
                        );
                        return { 
                            status: 'verification-complete',
                            result: result
                        };
                        
                    case 'get-verifications':
                        return {
                            status: 'verifications',
                            verifications: this.getVerifications(message.payload)
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            },
            
            verifyBilling(assetId, siteId, period) {
                // In a real system, this would verify billing eligibility
                // based on asset presence at the site during the billing period
                
                const verificationId = `${assetId}_${siteId}_${period}`;
                
                // Simplified verification (random results)
                const result = {
                    assetId: assetId,
                    siteId: siteId,
                    period: period,
                    timeAtSite: Math.floor(Math.random() * 168), // Hours
                    eligibilityScore: Math.random() * 100,
                    verifiedBy: 'BillingVerifier',
                    timestamp: new Date().toISOString(),
                    status: Math.random() > 0.2 ? 'verified' : 'needs-review'
                };
                
                this.verifications[verificationId] = result;
                return result;
            },
            
            getVerifications(filter = {}) {
                let results = Object.values(this.verifications);
                
                // Apply filters
                if (filter.assetId) {
                    results = results.filter(v => v.assetId === filter.assetId);
                }
                
                if (filter.siteId) {
                    results = results.filter(v => v.siteId === filter.siteId);
                }
                
                if (filter.period) {
                    results = results.filter(v => v.period === filter.period);
                }
                
                if (filter.status) {
                    results = results.filter(v => v.status === filter.status);
                }
                
                return results;
            }
        };
    }
};

// Create and export the agent system
window.GeniusCore = new GeniusAgentSystem();

console.log('GENIUS CORE Multi-Agent Architecture Loaded');