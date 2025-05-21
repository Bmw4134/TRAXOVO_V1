/**
 * TRAXORA GENIUS CORE | Continuity Manager
 * 
 * This module implements the cross-module continuity protocol for the GENIUS CORE system,
 * enabling data sharing and synchronized operations between different agents.
 */

class ContinuityManager {
    constructor() {
        // Check if required components exist
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Continuity Manager initialization aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.moduleData = {
            'asset-map': {
                assets: [],
                jobSites: [],
                conflicts: [],
                lastUpdate: null
            },
            'driver-reports': {
                drivers: [],
                classifications: {},
                unmatched: [],
                lastUpdate: null
            },
            'pm-allocation': {
                pmCodes: [],
                allocations: {},
                jobAssignments: {},
                lastUpdate: null
            }
        };
        
        // Register with GENIUS CORE
        this.continuityAgent = {
            id: 'ContinuityManager',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'register-module-data':
                        return window.ContinuityManager.registerModuleData(
                            message.payload.moduleId,
                            message.payload.dataType,
                            message.payload.data
                        );
                        
                    case 'get-module-data':
                        return {
                            status: 'module-data',
                            data: window.ContinuityManager.getModuleData(
                                message.payload.moduleId,
                                message.payload.dataType
                            )
                        };
                        
                    case 'check-data-consistency':
                        return {
                            status: 'consistency-check-result',
                            result: window.ContinuityManager.checkDataConsistency(
                                message.payload.modules
                            )
                        };
                        
                    case 'cross-validate':
                        return {
                            status: 'cross-validation-result',
                            result: window.ContinuityManager.crossValidate(
                                message.payload.sourceModule,
                                message.payload.targetModule,
                                message.payload.entity,
                                message.payload.options
                            )
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('ContinuityManager', this.continuityAgent);
        
        // Setup continuity checks
        this.setupContinuityProtocol();
        
        console.log('Continuity Manager initialized');
    }
    
    setupContinuityProtocol() {
        // Setup event listeners for various module interactions
        if (window.ModuleStatus) {
            // Monitor module status changes
            this.geniusCore.registerPeriodicTask(
                'continuity-check',
                'ContinuityManager',
                60000, // Check every minute
                () => this.performContinuityCheck()
            );
        }
        
        // Register cross-module validators
        this.registerDriverToPmValidator();
        this.registerAssetToDriverValidator();
        this.registerAssetToPmValidator();
        
        // Initialize handshake between modules
        setTimeout(() => this.initiateHandshake(), 3000);
    }
    
    registerModuleData(moduleId, dataType, data) {
        if (!this.moduleData[moduleId]) {
            return { 
                status: 'error', 
                message: `Unknown module: ${moduleId}` 
            };
        }
        
        if (!this.moduleData[moduleId][dataType] && this.moduleData[moduleId][dataType] !== null) {
            return { 
                status: 'error', 
                message: `Unknown data type for module ${moduleId}: ${dataType}` 
            };
        }
        
        // Store the data
        this.moduleData[moduleId][dataType] = data;
        this.moduleData[moduleId].lastUpdate = new Date().toISOString();
        
        console.log(`Registered data for ${moduleId}.${dataType}`);
        
        // Send notifications to interested modules
        this.notifyModules(moduleId, dataType, data);
        
        return { 
            status: 'data-registered',
            moduleId: moduleId,
            dataType: dataType
        };
    }
    
    getModuleData(moduleId, dataType) {
        if (!this.moduleData[moduleId]) {
            return null;
        }
        
        return dataType ? this.moduleData[moduleId][dataType] : this.moduleData[moduleId];
    }
    
    notifyModules(sourceModuleId, dataType, data) {
        // Define which modules should be notified based on the data that changed
        const notificationMap = {
            'asset-map': {
                'assets': ['driver-reports', 'pm-allocation'],
                'jobSites': ['driver-reports', 'pm-allocation'],
                'conflicts': ['driver-reports', 'pm-allocation']
            },
            'driver-reports': {
                'drivers': ['pm-allocation'],
                'classifications': ['pm-allocation'],
                'unmatched': ['asset-map']
            },
            'pm-allocation': {
                'pmCodes': ['driver-reports'],
                'allocations': ['driver-reports'],
                'jobAssignments': ['asset-map', 'driver-reports']
            }
        };
        
        // Get the list of modules to notify
        const modulesToNotify = notificationMap[sourceModuleId] && 
                               notificationMap[sourceModuleId][dataType] || [];
        
        // Send notifications
        modulesToNotify.forEach(targetModuleId => {
            // Map module ID to agent ID
            const agentMap = {
                'asset-map': 'AssetTracker',
                'driver-reports': 'DriverPipeline',
                'pm-allocation': 'BillingVerifier'
            };
            
            const targetAgent = agentMap[targetModuleId];
            if (!targetAgent) return;
            
            this.geniusCore.sendMessage(
                'ContinuityManager',
                targetAgent,
                'data-update',
                {
                    sourceModule: sourceModuleId,
                    dataType: dataType,
                    data: data
                }
            );
            
            console.log(`Notified ${targetAgent} about ${sourceModuleId}.${dataType} update`);
        });
    }
    
    checkDataConsistency(modules) {
        const results = {};
        const now = new Date();
        
        modules.forEach(moduleId => {
            if (!this.moduleData[moduleId]) {
                results[moduleId] = {
                    status: 'error',
                    message: `Unknown module: ${moduleId}`
                };
                return;
            }
            
            const lastUpdate = this.moduleData[moduleId].lastUpdate ? 
                new Date(this.moduleData[moduleId].lastUpdate) : null;
            
            results[moduleId] = {
                hasData: lastUpdate !== null,
                dataAge: lastUpdate ? (now - lastUpdate) / 1000 : null,
                dataStatus: lastUpdate ? 
                    (now - lastUpdate < 300000 ? 'current' : 'outdated') : 
                    'missing'
            };
        });
        
        return results;
    }
    
    crossValidate(sourceModule, targetModule, entity, options = {}) {
        // Get the appropriate validator based on the modules
        const validatorKey = `${sourceModule}-to-${targetModule}`;
        
        const validators = {
            'driver-reports-to-pm-allocation': this.validateDriverToPm.bind(this),
            'asset-map-to-driver-reports': this.validateAssetToDriver.bind(this),
            'asset-map-to-pm-allocation': this.validateAssetToPm.bind(this),
            'pm-allocation-to-driver-reports': this.validatePmToDriver.bind(this),
            'pm-allocation-to-asset-map': this.validatePmToAsset.bind(this)
        };
        
        const validator = validators[validatorKey];
        if (!validator) {
            return {
                status: 'error',
                message: `No validator available for ${validatorKey}`
            };
        }
        
        return validator(entity, options);
    }
    
    registerDriverToPmValidator() {
        // This validator checks if driver job assignments are consistent with PM allocations
        this.validateDriverToPm = (driver, options = {}) => {
            // If we don't have the necessary data, return inconclusive
            if (!this.moduleData['driver-reports'].classifications || 
                !this.moduleData['pm-allocation'].jobAssignments) {
                return {
                    status: 'inconclusive',
                    message: 'Insufficient data for validation'
                };
            }
            
            // Get driver's assigned job
            const driverData = this.moduleData['driver-reports'].classifications[driver];
            if (!driverData || !driverData.jobNumber) {
                return {
                    status: 'inconclusive',
                    message: 'Driver has no job assignment'
                };
            }
            
            // Check if job exists in PM allocations
            const jobNumber = driverData.jobNumber;
            const pmJobAssignments = this.moduleData['pm-allocation'].jobAssignments;
            
            if (!pmJobAssignments[jobNumber]) {
                return {
                    status: 'warning',
                    message: `Job ${jobNumber} not found in PM allocations`,
                    details: {
                        jobNumber: jobNumber,
                        driver: driver,
                        recommendation: 'Verify job number or update PM allocations'
                    }
                };
            }
            
            // Job exists, check details
            return {
                status: 'valid',
                message: `Driver ${driver} validated against PM allocations`,
                details: {
                    jobNumber: jobNumber,
                    driver: driver,
                    pmCode: pmJobAssignments[jobNumber].pmCode,
                    allocation: pmJobAssignments[jobNumber].allocation
                }
            };
        };
    }
    
    registerAssetToDriverValidator() {
        // This validator checks if asset location matches driver assignments
        this.validateAssetToDriver = (assetId, options = {}) => {
            // If we don't have the necessary data, return inconclusive
            if (!this.moduleData['asset-map'].assets || 
                !this.moduleData['driver-reports'].drivers) {
                return {
                    status: 'inconclusive',
                    message: 'Insufficient data for validation'
                };
            }
            
            // Find asset
            const assets = this.moduleData['asset-map'].assets;
            const asset = assets.find(a => a.id === assetId || a.asset_id === assetId);
            if (!asset) {
                return {
                    status: 'error',
                    message: `Asset ${assetId} not found`
                };
            }
            
            // Check if asset has a driver
            if (!asset.driver) {
                return {
                    status: 'inconclusive',
                    message: 'Asset has no assigned driver'
                };
            }
            
            // Check if driver exists in driver reports
            const driverName = asset.driver;
            const driversList = this.moduleData['driver-reports'].drivers;
            const driver = driversList.find(d => d === driverName);
            
            if (!driver) {
                return {
                    status: 'warning',
                    message: `Driver ${driverName} not found in driver reports`,
                    details: {
                        assetId: assetId,
                        driver: driverName,
                        recommendation: 'Update driver records or correct asset assignment'
                    }
                };
            }
            
            // Check if driver location matches asset location
            const driverClassifications = this.moduleData['driver-reports'].classifications;
            if (!driverClassifications[driverName]) {
                return {
                    status: 'warning',
                    message: `Driver ${driverName} has no classification data`,
                    details: {
                        assetId: assetId,
                        driver: driverName,
                        recommendation: 'Process driver reports to get classification'
                    }
                };
            }
            
            const driverJobNumber = driverClassifications[driverName].jobNumber;
            const assetLocation = asset.location;
            
            // Simple location check - a more sophisticated check would use geofencing
            if (driverJobNumber && assetLocation && 
                !assetLocation.includes(driverJobNumber)) {
                return {
                    status: 'warning',
                    message: `Asset location doesn't match driver's job`,
                    details: {
                        assetId: assetId,
                        driver: driverName,
                        driverJob: driverJobNumber,
                        assetLocation: assetLocation,
                        recommendation: 'Verify asset location or update driver assignment'
                    }
                };
            }
            
            return {
                status: 'valid',
                message: `Asset ${assetId} validated against driver ${driverName}`,
                details: {
                    assetId: assetId,
                    driver: driverName,
                    location: assetLocation
                }
            };
        };
    }
    
    registerAssetToPmValidator() {
        // This validator checks if asset job site is properly allocated in PM
        this.validateAssetToPm = (assetId, options = {}) => {
            // If we don't have the necessary data, return inconclusive
            if (!this.moduleData['asset-map'].assets || 
                !this.moduleData['pm-allocation'].jobAssignments) {
                return {
                    status: 'inconclusive',
                    message: 'Insufficient data for validation'
                };
            }
            
            // Find asset
            const assets = this.moduleData['asset-map'].assets;
            const asset = assets.find(a => a.id === assetId || a.asset_id === assetId);
            if (!asset) {
                return {
                    status: 'error',
                    message: `Asset ${assetId} not found`
                };
            }
            
            // Extract job number from location if possible
            if (!asset.location) {
                return {
                    status: 'inconclusive',
                    message: 'Asset has no location data'
                };
            }
            
            // Try to extract job number from location
            // This is a simple approach - real implementation would be more sophisticated
            const jobNumberRegex = /(\d{4}-\d{3}|\w+-YARD)/i;
            const match = asset.location.match(jobNumberRegex);
            const jobNumber = match ? match[1] : null;
            
            if (!jobNumber) {
                return {
                    status: 'inconclusive',
                    message: 'Could not determine job number from asset location'
                };
            }
            
            // Check if job exists in PM allocations
            const pmJobAssignments = this.moduleData['pm-allocation'].jobAssignments;
            
            if (!pmJobAssignments[jobNumber]) {
                return {
                    status: 'warning',
                    message: `Job ${jobNumber} not found in PM allocations`,
                    details: {
                        assetId: assetId,
                        jobNumber: jobNumber,
                        location: asset.location,
                        recommendation: 'Update PM allocations to include this job'
                    }
                };
            }
            
            // Job exists, check details
            return {
                status: 'valid',
                message: `Asset ${assetId} validated against PM allocations`,
                details: {
                    assetId: assetId,
                    jobNumber: jobNumber,
                    pmCode: pmJobAssignments[jobNumber].pmCode,
                    allocation: pmJobAssignments[jobNumber].allocation
                }
            };
        };
    }
    
    validatePmToDriver(jobNumber, options = {}) {
        // This is the reverse of validateDriverToPm
        // Check if PM job has corresponding drivers
        
        // If we don't have the necessary data, return inconclusive
        if (!this.moduleData['pm-allocation'].jobAssignments || 
            !this.moduleData['driver-reports'].classifications) {
            return {
                status: 'inconclusive',
                message: 'Insufficient data for validation'
            };
        }
        
        // Check if job exists in PM allocations
        const pmJobAssignments = this.moduleData['pm-allocation'].jobAssignments;
        if (!pmJobAssignments[jobNumber]) {
            return {
                status: 'error',
                message: `Job ${jobNumber} not found in PM allocations`
            };
        }
        
        // Find drivers assigned to this job
        const classifications = this.moduleData['driver-reports'].classifications;
        const driversOnJob = Object.entries(classifications)
            .filter(([driver, data]) => data.jobNumber === jobNumber)
            .map(([driver]) => driver);
        
        if (driversOnJob.length === 0) {
            return {
                status: 'warning',
                message: `No drivers found for job ${jobNumber}`,
                details: {
                    jobNumber: jobNumber,
                    pmCode: pmJobAssignments[jobNumber].pmCode,
                    recommendation: 'Check if this job is active or update driver assignments'
                }
            };
        }
        
        return {
            status: 'valid',
            message: `Job ${jobNumber} has ${driversOnJob.length} assigned drivers`,
            details: {
                jobNumber: jobNumber,
                pmCode: pmJobAssignments[jobNumber].pmCode,
                allocation: pmJobAssignments[jobNumber].allocation,
                drivers: driversOnJob
            }
        };
    }
    
    validatePmToAsset(jobNumber, options = {}) {
        // This is the reverse of validateAssetToPm
        // Check if PM job has corresponding assets
        
        // If we don't have the necessary data, return inconclusive
        if (!this.moduleData['pm-allocation'].jobAssignments || 
            !this.moduleData['asset-map'].assets) {
            return {
                status: 'inconclusive',
                message: 'Insufficient data for validation'
            };
        }
        
        // Check if job exists in PM allocations
        const pmJobAssignments = this.moduleData['pm-allocation'].jobAssignments;
        if (!pmJobAssignments[jobNumber]) {
            return {
                status: 'error',
                message: `Job ${jobNumber} not found in PM allocations`
            };
        }
        
        // Find assets assigned to this job
        const assets = this.moduleData['asset-map'].assets;
        const assetsOnJob = assets.filter(asset => 
            asset.location && asset.location.includes(jobNumber)
        );
        
        if (assetsOnJob.length === 0) {
            return {
                status: 'warning',
                message: `No assets found for job ${jobNumber}`,
                details: {
                    jobNumber: jobNumber,
                    pmCode: pmJobAssignments[jobNumber].pmCode,
                    recommendation: 'Check if this job is active or update asset locations'
                }
            };
        }
        
        return {
            status: 'valid',
            message: `Job ${jobNumber} has ${assetsOnJob.length} assigned assets`,
            details: {
                jobNumber: jobNumber,
                pmCode: pmJobAssignments[jobNumber].pmCode,
                allocation: pmJobAssignments[jobNumber].allocation,
                assets: assetsOnJob.map(a => a.id || a.asset_id)
            }
        };
    }
    
    performContinuityCheck() {
        console.log('Performing system-wide continuity check...');
        
        // Check if we have all necessary modules
        const moduleStatuses = this.checkDataConsistency([
            'asset-map', 
            'driver-reports', 
            'pm-allocation'
        ]);
        
        // Count valid jobs with assets and drivers
        const validationResults = {
            jobs: {},
            assets: {},
            drivers: {},
            summary: {
                jobCount: 0,
                assetCount: 0,
                driverCount: 0,
                validJobs: 0,
                jobsWithAssets: 0,
                jobsWithDrivers: 0,
                assetsWithDrivers: 0
            }
        };
        
        // If we have PM data, check each job
        if (this.moduleData['pm-allocation'].jobAssignments) {
            const jobs = Object.keys(this.moduleData['pm-allocation'].jobAssignments);
            validationResults.summary.jobCount = jobs.length;
            
            jobs.forEach(jobNumber => {
                const pmToAsset = this.validatePmToAsset(jobNumber);
                const pmToDriver = this.validatePmToDriver(jobNumber);
                
                validationResults.jobs[jobNumber] = {
                    assetValidation: pmToAsset,
                    driverValidation: pmToDriver,
                    isValid: 
                        pmToAsset.status === 'valid' && 
                        pmToDriver.status === 'valid'
                };
                
                if (validationResults.jobs[jobNumber].isValid) {
                    validationResults.summary.validJobs++;
                }
                
                if (pmToAsset.status === 'valid') {
                    validationResults.summary.jobsWithAssets++;
                }
                
                if (pmToDriver.status === 'valid') {
                    validationResults.summary.jobsWithDrivers++;
                }
            });
        }
        
        // If we have asset data, check assets with drivers
        if (this.moduleData['asset-map'].assets) {
            const assets = this.moduleData['asset-map'].assets;
            validationResults.summary.assetCount = assets.length;
            
            let assetsWithDrivers = 0;
            assets.forEach(asset => {
                const assetId = asset.id || asset.asset_id;
                if (asset.driver) {
                    const assetToDriver = this.validateAssetToDriver(assetId);
                    validationResults.assets[assetId] = {
                        driverValidation: assetToDriver,
                        isValid: assetToDriver.status === 'valid'
                    };
                    
                    if (assetToDriver.status === 'valid') {
                        assetsWithDrivers++;
                    }
                }
            });
            
            validationResults.summary.assetsWithDrivers = assetsWithDrivers;
        }
        
        // If we have driver data, count drivers
        if (this.moduleData['driver-reports'].drivers) {
            validationResults.summary.driverCount = 
                this.moduleData['driver-reports'].drivers.length;
        }
        
        // Store results in the manifest if available
        if (window.CoreManifest) {
            this.geniusCore.sendMessage(
                'ContinuityManager',
                'SystemManifest',
                'update-system-state',
                {
                    continuityCheck: validationResults.summary
                }
            );
        }
        
        console.log('Continuity check complete');
        return validationResults;
    }
    
    initiateHandshake() {
        console.log('Initiating cross-module handshake...');
        
        // Register module data watchers for each module
        this.setupDataWatchers();
        
        // See if we have the main agents available
        if (window.AssetTracker) {
            // Register assets
            const demoAssets = [
                {
                    id: 'EX-30',
                    asset_id: 'EX-30',
                    name: 'EX-30 CAT 320D L 2011 Excavator +',
                    type: 'Excavator',
                    make: 'CAT',
                    model: '320D L',
                    location: '2024-019 (15) Tarrant VA Bridge Rehab',
                    driver: 'R. Martinez',
                    status: 'active',
                    latitude: 32.38489,
                    longitude: -97.33166,
                    last_update: '5/21/2025 3:18:29 PM CT'
                },
                {
                    id: 'TH-02',
                    asset_id: 'TH-02',
                    name: 'TH-02 JLG G12-55A 2013 Telehandler +',
                    type: 'Telehandler',
                    make: 'JLG',
                    model: 'G12-55A',
                    location: 'HOU YARD/SHOP',
                    driver: null,
                    status: 'active',
                    latitude: 29.64284,
                    longitude: -95.34801,
                    last_update: '5/21/2025 4:30:32 AM CT'
                }
            ];
            
            this.registerModuleData('asset-map', 'assets', demoAssets);
        }
        
        if (window.DriverPipeline) {
            // Register driver data
            const demoDrivers = ['R. Martinez', 'J. Smith', 'A. Johnson'];
            const demoClassifications = {
                'R. Martinez': {
                    jobNumber: '2024-019',
                    status: 'active',
                    startTime: '7:30 AM',
                    endTime: '4:30 PM',
                    hours: 8.5
                },
                'J. Smith': {
                    jobNumber: '2023-032',
                    status: 'active',
                    startTime: '8:00 AM',
                    endTime: '5:00 PM',
                    hours: 8.0
                }
            };
            
            this.registerModuleData('driver-reports', 'drivers', demoDrivers);
            this.registerModuleData('driver-reports', 'classifications', demoClassifications);
        }
        
        if (window.BillingVerifier) {
            // Register PM data
            const demoPmCodes = ['HARDIMAN', 'KOCMICK', 'MORALES'];
            const demoJobAssignments = {
                '2024-019': {
                    pmCode: 'HARDIMAN',
                    allocation: 0.65,
                    description: '(15) Tarrant VA Bridge Rehab'
                },
                '2023-032': {
                    pmCode: 'KOCMICK',
                    allocation: 0.8,
                    description: 'SH 345 Bridge Rehabilitation'
                },
                'DFW-YARD': {
                    pmCode: 'MORALES',
                    allocation: 1.0,
                    description: 'DFW Yard'
                },
                'HOU-YARD': {
                    pmCode: 'MORALES',
                    allocation: 1.0,
                    description: 'HOU Yard/Shop'
                }
            };
            
            this.registerModuleData('pm-allocation', 'pmCodes', demoPmCodes);
            this.registerModuleData('pm-allocation', 'jobAssignments', demoJobAssignments);
        }
        
        // Run initial continuity check
        setTimeout(() => this.performContinuityCheck(), 1000);
    }
    
    setupDataWatchers() {
        // DriverPipeline to BillingVerifier handshake
        if (window.DriverPipeline && window.BillingVerifier) {
            console.log('Setting up Driver → PM allocation handshake');
            
            // Watch for driver updates from DriverPipeline
            this.geniusCore.sendMessage(
                'ContinuityManager',
                'DriverPipeline',
                'register-data-watcher',
                {
                    notifyOnUpdate: true,
                    shareData: true
                }
            );
            
            // Watch for PM updates from BillingVerifier
            this.geniusCore.sendMessage(
                'ContinuityManager',
                'BillingVerifier',
                'register-data-watcher',
                {
                    notifyOnUpdate: true,
                    shareData: true
                }
            );
        }
        
        // AssetTracker to DriverPipeline handshake
        if (window.AssetTracker && window.DriverPipeline) {
            console.log('Setting up Asset → Driver handshake');
            
            // Watch for asset updates from AssetTracker
            this.geniusCore.sendMessage(
                'ContinuityManager',
                'AssetTracker',
                'register-data-watcher',
                {
                    notifyOnUpdate: true,
                    shareData: true
                }
            );
        }
    }
    
    validateAll() {
        // Run a full validation across all entities
        console.log('Running full cross-module validation...');
        
        // Perform job validations
        let jobResults = {};
        if (this.moduleData['pm-allocation'].jobAssignments) {
            const jobs = Object.keys(this.moduleData['pm-allocation'].jobAssignments);
            
            jobs.forEach(jobNumber => {
                jobResults[jobNumber] = {
                    pmToAsset: this.validatePmToAsset(jobNumber),
                    pmToDriver: this.validatePmToDriver(jobNumber)
                };
            });
        }
        
        // Perform asset validations
        let assetResults = {};
        if (this.moduleData['asset-map'].assets) {
            const assets = this.moduleData['asset-map'].assets;
            
            assets.forEach(asset => {
                const assetId = asset.id || asset.asset_id;
                assetResults[assetId] = {
                    assetToDriver: asset.driver ? this.validateAssetToDriver(assetId) : null,
                    assetToPm: this.validateAssetToPm(assetId)
                };
            });
        }
        
        // Perform driver validations
        let driverResults = {};
        if (this.moduleData['driver-reports'].classifications) {
            const drivers = Object.keys(this.moduleData['driver-reports'].classifications);
            
            drivers.forEach(driver => {
                driverResults[driver] = {
                    driverToPm: this.validateDriverToPm(driver)
                };
            });
        }
        
        return {
            jobs: jobResults,
            assets: assetResults,
            drivers: driverResults,
            timestamp: new Date().toISOString()
        };
    }
}

// Wait for GENIUS CORE to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if GENIUS CORE is loaded every 100ms
    const checkGeniusCore = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkGeniusCore);
            window.ContinuityManager = new ContinuityManager();
            console.log('Continuity Manager connected to GENIUS CORE');
        }
    }, 100);
});

console.log('GENIUS CORE Continuity Manager Loaded');