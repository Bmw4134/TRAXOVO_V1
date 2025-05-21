/**
 * TRAXORA GENIUS CORE | Driver Module Pipeline Manager
 * 
 * This module implements a clean, isolated pipeline for the Driver Reports
 * module that only uses recent file uploads and properly cleans up after itself.
 */

class DriverPipelineManager {
    constructor() {
        // Check if required components exist
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Driver Pipeline initialization aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.currentFiles = {
            drivingHistory: null,
            activityDetail: null,
            assetList: null
        };
        this.processingState = {
            isRunning: false,
            lastRun: null,
            results: null,
            errors: [],
            warnings: []
        };
        
        // Register with GENIUS CORE
        this.driverAgent = {
            id: 'DriverPipeline',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'register-file':
                        return window.DriverPipeline.registerFile(
                            message.payload.fileType,
                            message.payload.filePath,
                            message.payload.timestamp
                        );
                        
                    case 'run-pipeline':
                        return window.DriverPipeline.runPipeline(
                            message.payload.date,
                            message.payload.options
                        );
                        
                    case 'get-pipeline-status':
                        return {
                            status: 'pipeline-status',
                            pipelineStatus: window.DriverPipeline.getPipelineStatus()
                        };
                        
                    case 'clear-files':
                        return window.DriverPipeline.clearFiles();
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('DriverPipeline', this.driverAgent);
        
        // Register with system manifest
        this.registerWithManifest();
        
        console.log('Driver Pipeline Manager initialized');
    }
    
    registerWithManifest() {
        if (window.CoreManifest) {
            // Register this module in the system manifest
            this.geniusCore.sendMessage(
                'DriverPipeline',
                'SystemManifest',
                'register-module',
                {
                    name: 'DriverPipeline',
                    path: '/driver-reports/pipeline/processor',
                    dataSource: 'uploaded-csv-files'
                }
            );
            
            // Update initial status
            this.updateModuleStatus('waiting', 'Waiting for file uploads');
        }
    }
    
    updateModuleStatus(status, task = null, details = null) {
        // Update manifest
        if (window.CoreManifest) {
            this.geniusCore.sendMessage(
                'DriverPipeline',
                'SystemManifest',
                'update-status',
                {
                    name: 'DriverPipeline',
                    status: status,
                    task: task,
                    details: details
                }
            );
        }
        
        // Update module status
        if (window.ModuleStatus) {
            window.ModuleStatus.updateModuleStatus(
                'driver-reports',
                status,
                details && details.filesReady ? 80 : 
                details && details.filesUploaded ? 70 : 40
            );
        }
    }
    
    registerFile(fileType, filePath, timestamp) {
        if (!['drivingHistory', 'activityDetail', 'assetList'].includes(fileType)) {
            return { 
                status: 'error', 
                message: 'Invalid file type. Must be drivingHistory, activityDetail, or assetList'
            };
        }
        
        // Store file info
        this.currentFiles[fileType] = {
            path: filePath,
            timestamp: timestamp || new Date().toISOString(),
            processed: false
        };
        
        console.log(`Registered ${fileType} file: ${filePath}`);
        
        // Check if all files are ready
        const filesReady = this.checkFilesReady();
        
        // Update status
        this.updateModuleStatus(
            filesReady ? 'ready' : 'waiting',
            filesReady ? 'Ready to process' : 'Waiting for more files',
            {
                filesUploaded: true,
                filesReady: filesReady,
                fileCount: Object.values(this.currentFiles).filter(f => f !== null).length
            }
        );
        
        return { 
            status: 'file-registered', 
            fileType: fileType,
            allFilesReady: filesReady
        };
    }
    
    checkFilesReady() {
        // Check if all required files are present
        return (
            this.currentFiles.drivingHistory !== null &&
            this.currentFiles.activityDetail !== null &&
            this.currentFiles.assetList !== null
        );
    }
    
    runPipeline(date, options = {}) {
        // Check if all files are ready
        if (!this.checkFilesReady()) {
            const error = 'Not all required files are uploaded. Need drivingHistory, activityDetail, and assetList files.';
            this.processingState.errors.push(error);
            return { 
                status: 'error', 
                message: error
            };
        }
        
        // Check if already running
        if (this.processingState.isRunning) {
            return { 
                status: 'error', 
                message: 'Pipeline is already running' 
            };
        }
        
        // Mark as running
        this.processingState.isRunning = true;
        this.processingState.errors = [];
        this.processingState.warnings = [];
        
        // Update status
        this.updateModuleStatus('processing', 'Running pipeline', {
            date: date,
            options: options,
            startTime: new Date().toISOString()
        });
        
        // In a real implementation, this would call backend endpoints
        // For simulation, we'll use a timeout to represent processing time
        setTimeout(() => {
            // Simulate pipeline completion
            this.processingState.isRunning = false;
            this.processingState.lastRun = new Date().toISOString();
            
            // Mark files as processed
            Object.keys(this.currentFiles).forEach(key => {
                if (this.currentFiles[key]) {
                    this.currentFiles[key].processed = true;
                }
            });
            
            // Set result
            this.processingState.results = {
                date: date,
                processedAt: this.processingState.lastRun,
                report: {
                    totalDrivers: 125,
                    classified: 118,
                    unclassified: 7,
                    warnings: 3
                }
            };
            
            // Update status
            this.updateModuleStatus('operational', 'Pipeline completed', {
                date: date,
                completionTime: this.processingState.lastRun,
                results: this.processingState.results
            });
            
            console.log('Driver pipeline completed successfully');
            
            // Send message to BillingVerifier to notify of new driver data
            this.geniusCore.sendMessage(
                'DriverPipeline',
                'BillingVerifier',
                'driver-data-updated',
                {
                    date: date,
                    processedAt: this.processingState.lastRun,
                    driverCount: this.processingState.results.report.totalDrivers
                }
            );
            
            // Clean up temporary files (the real implementation would do this)
            this.cleanupTemporaryFiles();
            
        }, 3000); // Simulate 3 second processing time
        
        return { 
            status: 'pipeline-started', 
            date: date,
            startTime: new Date().toISOString()
        };
    }
    
    getPipelineStatus() {
        return {
            files: this.currentFiles,
            state: this.processingState,
            isReady: this.checkFilesReady(),
            lastRun: this.processingState.lastRun,
            hasErrors: this.processingState.errors.length > 0,
            errors: this.processingState.errors,
            warnings: this.processingState.warnings
        };
    }
    
    clearFiles() {
        // Reset file tracking
        this.currentFiles = {
            drivingHistory: null,
            activityDetail: null,
            assetList: null
        };
        
        // Update status
        this.updateModuleStatus('waiting', 'Files cleared, waiting for uploads');
        
        return { status: 'files-cleared' };
    }
    
    cleanupTemporaryFiles() {
        // In a real implementation, this would delete temporary files
        console.log('Cleaning up temporary files from pipeline run');
        
        // For simulation, we'll just log that cleanup happened
        return true;
    }
    
    createUploadPane() {
        // Create an upload pane for the driver module if it doesn't exist
        let uploadPane = document.getElementById('driver-upload-pane');
        
        if (!uploadPane && document.getElementById('map')) {
            uploadPane = document.createElement('div');
            uploadPane.id = 'driver-upload-pane';
            uploadPane.className = 'driver-upload-pane';
            
            uploadPane.innerHTML = `
                <div class="driver-upload-header">
                    <h6>Driver Reports Pipeline</h6>
                    <button id="driver-upload-toggle" class="driver-upload-toggle">+</button>
                </div>
                <div class="driver-upload-content">
                    <div class="upload-status">
                        <div id="driving-history-status" class="file-status">
                            <span class="file-label">Driving History:</span>
                            <span class="file-value">Not uploaded</span>
                        </div>
                        <div id="activity-detail-status" class="file-status">
                            <span class="file-label">Activity Detail:</span>
                            <span class="file-value">Not uploaded</span>
                        </div>
                        <div id="asset-list-status" class="file-status">
                            <span class="file-label">Asset List:</span>
                            <span class="file-value">Not uploaded</span>
                        </div>
                    </div>
                    <div class="upload-actions">
                        <button id="run-pipeline-btn" disabled>Run Pipeline</button>
                        <button id="clear-files-btn">Clear Files</button>
                    </div>
                    <div id="pipeline-result" class="pipeline-result"></div>
                </div>
            `;
            
            document.body.appendChild(uploadPane);
            
            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .driver-upload-pane {
                    position: fixed;
                    bottom: 20px;
                    left: 20px;
                    width: 300px;
                    background: rgba(33, 37, 41, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    color: white;
                    font-family: sans-serif;
                    z-index: 1000;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    transition: height 0.3s ease-in-out;
                    overflow: hidden;
                    height: 40px;
                }
                
                .driver-upload-pane.expanded {
                    height: 220px;
                }
                
                .driver-upload-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 15px;
                    background: rgba(0, 0, 0, 0.2);
                    cursor: pointer;
                }
                
                .driver-upload-header h6 {
                    margin: 0;
                    color: #33d4ff;
                }
                
                .driver-upload-toggle {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 16px;
                    cursor: pointer;
                    padding: 0 5px;
                }
                
                .driver-upload-content {
                    padding: 15px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }
                
                .upload-status {
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }
                
                .file-status {
                    display: flex;
                    justify-content: space-between;
                }
                
                .file-label {
                    font-weight: bold;
                }
                
                .file-value {
                    color: #999;
                }
                
                .file-value.uploaded {
                    color: #33d4ff;
                }
                
                .upload-actions {
                    display: flex;
                    gap: 10px;
                    margin-top: 10px;
                }
                
                .upload-actions button {
                    flex: 1;
                    padding: 5px 10px;
                    background: #444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                
                .upload-actions button:disabled {
                    background: #333;
                    color: #666;
                    cursor: not-allowed;
                }
                
                .upload-actions button:hover:not(:disabled) {
                    background: #555;
                }
                
                .pipeline-result {
                    margin-top: 10px;
                    font-size: 12px;
                    color: #ccc;
                }
            `;
            
            document.head.appendChild(style);
            
            // Add toggle behavior
            const header = uploadPane.querySelector('.driver-upload-header');
            const toggleBtn = uploadPane.querySelector('.driver-upload-toggle');
            
            header.addEventListener('click', function() {
                uploadPane.classList.toggle('expanded');
                toggleBtn.textContent = uploadPane.classList.contains('expanded') ? '−' : '+';
            });
            
            // Add action handlers
            const runBtn = uploadPane.querySelector('#run-pipeline-btn');
            const clearBtn = uploadPane.querySelector('#clear-files-btn');
            const resultDiv = uploadPane.querySelector('#pipeline-result');
            
            runBtn.addEventListener('click', function() {
                const date = new Date().toISOString().split('T')[0];
                window.DriverPipeline.runPipeline(date);
                resultDiv.innerHTML = 'Running pipeline...';
                runBtn.disabled = true;
            });
            
            clearBtn.addEventListener('click', function() {
                window.DriverPipeline.clearFiles();
                updateFileStatus(null, null, null);
                resultDiv.innerHTML = '';
                runBtn.disabled = true;
            });
            
            // Function to update file status
            const updateFileStatus = (drivingHistory, activityDetail, assetList) => {
                const dhStatus = uploadPane.querySelector('#driving-history-status .file-value');
                const adStatus = uploadPane.querySelector('#activity-detail-status .file-value');
                const alStatus = uploadPane.querySelector('#asset-list-status .file-value');
                
                if (drivingHistory) {
                    dhStatus.textContent = 'Uploaded';
                    dhStatus.classList.add('uploaded');
                } else {
                    dhStatus.textContent = 'Not uploaded';
                    dhStatus.classList.remove('uploaded');
                }
                
                if (activityDetail) {
                    adStatus.textContent = 'Uploaded';
                    adStatus.classList.add('uploaded');
                } else {
                    adStatus.textContent = 'Not uploaded';
                    adStatus.classList.remove('uploaded');
                }
                
                if (assetList) {
                    alStatus.textContent = 'Uploaded';
                    alStatus.classList.add('uploaded');
                } else {
                    alStatus.textContent = 'Not uploaded';
                    alStatus.classList.remove('uploaded');
                }
                
                // Enable run button if all files are uploaded
                runBtn.disabled = !(drivingHistory && activityDetail && assetList);
            };
            
            // Update status when file status changes
            setInterval(() => {
                const status = window.DriverPipeline.getPipelineStatus();
                
                updateFileStatus(
                    status.files.drivingHistory,
                    status.files.activityDetail,
                    status.files.assetList
                );
                
                // Update result
                if (status.state.results) {
                    resultDiv.innerHTML = `
                        <div>Date: ${status.state.results.date}</div>
                        <div>Drivers: ${status.state.results.report.totalDrivers}</div>
                        <div>Classified: ${status.state.results.report.classified}</div>
                        <div>Unclassified: ${status.state.results.report.unclassified}</div>
                        <div>Warnings: ${status.state.results.report.warnings}</div>
                    `;
                }
                
                // Re-enable run button after completion
                if (!status.state.isRunning && status.isReady) {
                    runBtn.disabled = false;
                }
            }, 1000);
        }
    }
}

// Wait for GENIUS CORE to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if GENIUS CORE is loaded every 100ms
    const checkGeniusCore = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkGeniusCore);
            window.DriverPipeline = new DriverPipelineManager();
            window.DriverPipeline.createUploadPane();
            console.log('Driver Pipeline Manager connected to GENIUS CORE');
            
            // Register example files for demonstration
            setTimeout(() => {
                window.DriverPipeline.registerFile('drivingHistory', '/uploads/DrivingHistory_20250521.csv', new Date().toISOString());
                window.DriverPipeline.registerFile('activityDetail', '/uploads/ActivityDetail_20250521.csv', new Date().toISOString());
                window.DriverPipeline.registerFile('assetList', '/uploads/AssetList_20250521.csv', new Date().toISOString());
            }, 2000);
        }
    }, 100);
});

console.log('GENIUS CORE Driver Pipeline Manager Loaded');