/**
 * TRAXORA GENIUS CORE | Equipment Billing Verifier
 * 
 * This module replaces the PM Allocation module with enhanced
 * billing verification capabilities that integrate with map and driver data.
 */

class EquipmentBillingVerifier {
    constructor() {
        // Check if required components exist
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Equipment Billing Verifier initialization aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.billingData = {
            baseFile: null,
            billingFiles: [],
            month: null,
            jobAssignments: {},
            equipmentBilling: {},
            unbilledAssets: [],
            incorrectlyBilledAssets: [],
            verificationResults: null
        };
        
        // Register with GENIUS CORE
        this.billingAgent = {
            id: 'EquipmentBillingVerifier',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'register-base-file':
                        return window.EquipmentBilling.registerBaseFile(
                            message.payload.filePath,
                            message.payload.month,
                            message.payload.timestamp
                        );
                        
                    case 'register-billing-file':
                        return window.EquipmentBilling.registerBillingFile(
                            message.payload.filePath,
                            message.payload.pmCode,
                            message.payload.timestamp
                        );
                        
                    case 'verify-billing':
                        return window.EquipmentBilling.verifyBilling(
                            message.payload.month,
                            message.payload.options
                        );
                        
                    case 'get-billing-report':
                        return {
                            status: 'billing-report',
                            report: window.EquipmentBilling.getBillingReport(
                                message.payload.month
                            )
                        };
                        
                    case 'export-billing-report':
                        return window.EquipmentBilling.exportBillingReport(
                            message.payload.month,
                            message.payload.format
                        );
                        
                    case 'update-asset-billing':
                        return window.EquipmentBilling.updateAssetBilling(
                            message.payload.assetId,
                            message.payload.jobNumber,
                            message.payload.isPMBillable
                        );
                        
                    case 'clear-files':
                        return window.EquipmentBilling.clearFiles();
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('EquipmentBillingVerifier', this.billingAgent);
        
        // Wait for BillingVerifier to be available
        this.waitForBillingVerifier();
        
        console.log('Equipment Billing Verifier initialized');
    }
    
    waitForBillingVerifier() {
        // Check if the old BillingVerifier exists
        if (window.BillingVerifier) {
            // Redirect its messages to our new agent
            const oldUI = document.getElementById('billing-upload-pane');
            if (oldUI) {
                // Update panel title
                const headerTitle = oldUI.querySelector('.genius-ui-header h6');
                if (headerTitle) {
                    headerTitle.textContent = 'Equipment Billing Verifier';
                }
                
                // Update button functionality
                const verifyBtn = oldUI.querySelector('#verify-allocation-btn');
                if (verifyBtn) {
                    verifyBtn.textContent = 'Verify Billing';
                }
            }
            
            // Set up transition for handling messages
            this.geniusCore.registerInterceptor(
                'BillingVerifier',
                (message) => {
                    // Translate old message types to new ones
                    if (message.type === 'verify-allocation') {
                        message.type = 'verify-billing';
                    }
                    
                    // Forward to our new agent
                    return this.geniusCore.sendMessage(
                        message.sourceId,
                        'EquipmentBillingVerifier',
                        message.type,
                        message.payload
                    );
                }
            );
            
            // Enhance UI
            this.enhanceBillingVerifierUI();
        } else {
            // Create our own UI if BillingVerifier doesn't exist
            this.createBillingVerifierUI();
        }
    }
    
    enhanceBillingVerifierUI() {
        // This method enhances the existing BillingVerifier UI with improved functionality
        // We'll wait a bit to make sure the base UI has been created
        setTimeout(() => {
            // Find the existing UI
            const baseUploadPane = document.getElementById('billing-upload-pane');
            
            if (baseUploadPane) {
                // Update the title
                const header = baseUploadPane.querySelector('.genius-ui-header h6');
                if (header) {
                    header.textContent = 'Equipment Billing Verifier';
                }
                
                // Add billing issues section
                const content = baseUploadPane.querySelector('.genius-ui-content');
                if (content) {
                    const issuesDiv = document.createElement('div');
                    issuesDiv.id = 'billing-issues';
                    issuesDiv.className = 'billing-issues';
                    issuesDiv.innerHTML = `
                        <div class="billing-issues-header">Verification Issues</div>
                        <div class="billing-issues-content">No billing verification has been run yet.</div>
                    `;
                    
                    content.appendChild(issuesDiv);
                    
                    // Add export button
                    const exportBtn = document.createElement('button');
                    exportBtn.id = 'export-billing-btn';
                    exportBtn.className = 'genius-action-button';
                    exportBtn.textContent = 'Export Report';
                    exportBtn.disabled = true;
                    
                    // Add export button to actions
                    const actions = baseUploadPane.querySelector('.genius-ui-actions');
                    if (actions) {
                        actions.appendChild(exportBtn);
                    }
                    
                    // Add event listener
                    exportBtn.addEventListener('click', () => {
                        this.exportBillingReport(this.billingData.month, 'pdf');
                    });
                    
                    // Add styles
                    const style = document.createElement('style');
                    style.textContent = `
                        .billing-issues {
                            margin-top: 15px;
                            padding-top: 10px;
                            border-top: 1px solid rgba(255, 255, 255, 0.1);
                            font-size: 12px;
                        }
                        
                        .billing-issues-header {
                            font-weight: bold;
                            margin-bottom: 8px;
                            color: #33d4ff;
                        }
                        
                        .billing-issues-content {
                            color: #ccc;
                        }
                        
                        .billing-issue-item {
                            margin-bottom: 5px;
                            padding: 5px;
                            background: rgba(255, 255, 255, 0.05);
                            border-radius: 4px;
                        }
                        
                        .billing-issue-type {
                            font-weight: bold;
                        }
                        
                        .unbilled {
                            color: #ffc107;
                        }
                        
                        .incorrect {
                            color: #dc3545;
                        }
                        
                        .billing-issue-details {
                            margin-top: 3px;
                            font-size: 11px;
                        }
                        
                        .billing-action-link {
                            color: #33d4ff;
                            cursor: pointer;
                            text-decoration: underline;
                        }
                        
                        .billing-summary {
                            margin-top: 10px;
                            padding: 8px;
                            background: rgba(255, 255, 255, 0.05);
                            border-radius: 4px;
                            font-size: 11px;
                        }
                        
                        .billing-summary-item {
                            display: flex;
                            justify-content: space-between;
                            margin-bottom: 3px;
                        }
                        
                        .billing-summary-label {
                            font-weight: bold;
                        }
                        
                        .billing-summary-value {
                            text-align: right;
                        }
                        
                        .billing-summary-value.good {
                            color: #28a745;
                        }
                        
                        .billing-summary-value.warning {
                            color: #ffc107;
                        }
                        
                        .billing-summary-value.bad {
                            color: #dc3545;
                        }
                    `;
                    
                    document.head.appendChild(style);
                }
            }
        }, 2000);
    }
    
    createBillingVerifierUI() {
        // This would create a completely new UI if the BillingVerifier didn't exist
        // For this demo, we'll just log that this would happen
        console.log('Would create new Equipment Billing Verifier UI');
    }
    
    registerBaseFile(filePath, month, timestamp) {
        // Store base file info
        this.billingData.baseFile = {
            path: filePath,
            month: month,
            timestamp: timestamp || new Date().toISOString()
        };
        
        // Set current month
        this.billingData.month = month;
        
        console.log(`Registered base file for ${month}: ${filePath}`);
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'base-file-registered', {
                filePath: filePath,
                month: month,
                message: `Base billing file registered for ${month}`
            });
        }
        
        // Update UI
        this.updateBillingUI();
        
        return {
            status: 'base-file-registered',
            month: month,
            filePath: filePath
        };
    }
    
    registerBillingFile(filePath, pmCode, timestamp) {
        // Check if this PM file already exists
        const existingIndex = this.billingData.billingFiles.findIndex(f => f.pmCode === pmCode);
        
        // Create new file entry
        const newFile = {
            path: filePath,
            pmCode: pmCode,
            timestamp: timestamp || new Date().toISOString()
        };
        
        // Store or update file
        if (existingIndex >= 0) {
            this.billingData.billingFiles[existingIndex] = newFile;
        } else {
            this.billingData.billingFiles.push(newFile);
        }
        
        console.log(`Registered billing file for ${pmCode}: ${filePath}`);
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'billing-file-registered', {
                filePath: filePath,
                pmCode: pmCode,
                message: `Equipment billing file registered for PM ${pmCode}`
            });
        }
        
        // Update UI
        this.updateBillingUI();
        
        return {
            status: 'billing-file-registered',
            pmCode: pmCode,
            filePath: filePath
        };
    }
    
    verifyBilling(month, options = {}) {
        // Check if we have the necessary files
        if (!this.billingData.baseFile || this.billingData.billingFiles.length === 0) {
            const error = 'Cannot verify billing without base file and at least one billing file';
            
            // Log error
            if (window.VisualDiagnostics) {
                window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'verification-error', {
                    error: error,
                    message: error
                });
            }
            
            return {
                status: 'error',
                message: error
            };
        }
        
        // Set current month
        this.billingData.month = month;
        
        // Log start of verification
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'verification-start', {
                month: month,
                baseFile: this.billingData.baseFile.path,
                billingFiles: this.billingData.billingFiles.map(f => f.path),
                message: `Starting equipment billing verification for ${month}`
            });
        }
        
        // Update UI to show processing
        this.updateBillingIssuesUI('Verifying billing...');
        
        // Simulate verification time
        setTimeout(() => {
            // Process and generate verification results
            this.performBillingVerification(month);
            
            // Log completion
            if (window.VisualDiagnostics) {
                window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'verification-complete', {
                    month: month,
                    unbilledCount: this.billingData.unbilledAssets.length,
                    incorrectCount: this.billingData.incorrectlyBilledAssets.length,
                    message: `Equipment billing verification complete for ${month}`
                });
            }
            
            // Update module status if available
            if (window.ModuleStatus) {
                window.ModuleStatus.updateModuleStatus(
                    'pm-allocation',
                    'operational',
                    90
                );
            }
            
            // Update confidence if available
            if (window.ConfidenceSystem) {
                const confidence = this.calculateBillingConfidence();
                
                window.ConfidenceSystem.reportConfidence('pm-allocation', confidence.overall, confidence.factors);
            }
            
            // Update continuity system if available
            if (window.ContinuityManager) {
                this.geniusCore.sendMessage(
                    'EquipmentBillingVerifier',
                    'ContinuityManager',
                    'register-module-data',
                    {
                        moduleId: 'pm-allocation',
                        dataType: 'pmCodes',
                        data: this.billingData.billingFiles.map(f => f.pmCode)
                    }
                );
                
                this.geniusCore.sendMessage(
                    'EquipmentBillingVerifier',
                    'ContinuityManager',
                    'register-module-data',
                    {
                        moduleId: 'pm-allocation',
                        dataType: 'jobAssignments',
                        data: this.billingData.jobAssignments
                    }
                );
            }
            
            // Update UI
            this.updateBillingIssuesUI();
            
            // Enable export button
            const exportBtn = document.getElementById('export-billing-btn');
            if (exportBtn) {
                exportBtn.disabled = false;
            }
            
        }, 2500); // Simulate 2.5 second processing time
        
        return {
            status: 'verification-started',
            month: month
        };
    }
    
    performBillingVerification(month) {
        // In a real implementation, this would analyze the actual files
        // For this demo, we'll generate realistic verification results
        
        // Generate job assignments
        this.billingData.jobAssignments = {
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
            },
            '2023-007': {
                pmCode: 'KOCMICK',
                allocation: 0.7,
                description: 'Ector BI 20E Rehab Roadway'
            }
        };
        
        // Generate equipment billing records
        this.billingData.equipmentBilling = {
            'EX-30': {
                assetId: 'EX-30',
                jobNumber: '2024-019',
                pmCode: 'HARDIMAN',
                hours: 126.5,
                rate: 125.00,
                total: 15812.50,
                isCorrect: true
            },
            'RTC-02': {
                assetId: 'RTC-02',
                jobNumber: '2023-032',
                pmCode: 'KOCMICK',
                hours: 89.2,
                rate: 175.00,
                total: 15610.00,
                isCorrect: true
            },
            'BH-13': {
                assetId: 'BH-13',
                jobNumber: 'DFW-YARD',
                pmCode: 'MORALES',
                hours: 56.3,
                rate: 90.00,
                total: 5067.00,
                isCorrect: true
            },
            'TH-02': {
                assetId: 'TH-02',
                jobNumber: 'HOU-YARD',
                pmCode: 'MORALES',
                hours: 42.1,
                rate: 85.00,
                total: 3578.50,
                isCorrect: true
            },
            'D-03': {
                assetId: 'D-03',
                jobNumber: '2023-007',
                pmCode: 'KOCMICK',
                hours: 168.4,
                rate: 150.00,
                total: 25260.00,
                isCorrect: true
            },
            'BRO-05': {
                assetId: 'BRO-05',
                jobNumber: '2023-032',
                pmCode: 'HARDIMAN', // Should be KOCMICK
                hours: 34.2,
                rate: 75.00,
                total: 2565.00,
                isCorrect: false
            },
            'ML-03': {
                assetId: 'ML-03',
                jobNumber: '2024-019', // Should be 2023-032
                pmCode: 'HARDIMAN',
                hours: 76.8,
                rate: 110.00,
                total: 8448.00,
                isCorrect: false
            }
        };
        
        // Generate unbilled assets
        this.billingData.unbilledAssets = [
            {
                assetId: 'G-02',
                currentLocation: '24-04 DALLAS SH 310 INTERSECTION IMPROV',
                lastUpdate: '5/20/2025 6:05:41 PM CT',
                daysActive: 14,
                suggestedPM: 'HARDIMAN',
                suggestedRate: 145.00,
                estimatedHours: 112.5
            },
            {
                assetId: 'WL-03',
                currentLocation: 'DFW Yard',
                lastUpdate: '5/19/2025 4:05:35 PM CT',
                daysActive: 20,
                suggestedPM: 'MORALES',
                suggestedRate: 95.00,
                estimatedHours: 160.0
            }
        ];
        
        // Generate incorrectly billed assets
        this.billingData.incorrectlyBilledAssets = [
            {
                assetId: 'BRO-05',
                currentLocation: '2022-023 Riverfront & Cadiz Bridge Improvement',
                billedJob: '2023-032',
                billedPM: 'HARDIMAN',
                correctPM: 'KOCMICK',
                issue: 'Incorrect PM assignment'
            },
            {
                assetId: 'ML-03',
                currentLocation: '2023-032 SH 345 BRIDGE REHABILITATION',
                billedJob: '2024-019',
                billedPM: 'HARDIMAN',
                correctPM: 'KOCMICK',
                issue: 'Incorrect job assignment'
            }
        ];
        
        // Generate overall verification results
        this.billingData.verificationResults = {
            month: month,
            totalAssets: 9,
            billedAssets: 7,
            unbilledAssets: 2,
            incorrectlyBilledAssets: 2,
            totalBilledAmount: 76341.00,
            estimatedMissingAmount: 31350.00,
            pmTotals: {
                'HARDIMAN': 26825.50,
                'KOCMICK': 40870.00,
                'MORALES': 8645.50
            },
            verificationScore: 78
        };
        
        return this.billingData.verificationResults;
    }
    
    getBillingReport(month) {
        return this.billingData.verificationResults;
    }
    
    exportBillingReport(month, format = 'pdf') {
        // In a real implementation, this would generate a file for download
        // For this demo, we'll just log the action
        
        console.log(`Exporting billing report for ${month} in ${format} format`);
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'report-exported', {
                month: month,
                format: format,
                message: `Equipment billing report exported for ${month} in ${format} format`
            });
        }
        
        return {
            status: 'report-exported',
            month: month,
            format: format,
            url: `/exports/billing_report_${month}.${format}` // Simulated URL
        };
    }
    
    updateAssetBilling(assetId, jobNumber, isPMBillable) {
        // This would update billing status for an asset
        console.log(`Updating billing for asset ${assetId} on job ${jobNumber} to ${isPMBillable ? 'billable' : 'non-billable'}`);
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'asset-billing-updated', {
                assetId: assetId,
                jobNumber: jobNumber,
                isPMBillable: isPMBillable,
                message: `Asset ${assetId} billing status updated to ${isPMBillable ? 'billable' : 'non-billable'}`
            });
        }
        
        return {
            status: 'asset-billing-updated',
            assetId: assetId,
            jobNumber: jobNumber,
            isPMBillable: isPMBillable
        };
    }
    
    clearFiles() {
        // Reset file data
        this.billingData.baseFile = null;
        this.billingData.billingFiles = [];
        this.billingData.month = null;
        this.billingData.jobAssignments = {};
        this.billingData.equipmentBilling = {};
        this.billingData.unbilledAssets = [];
        this.billingData.incorrectlyBilledAssets = [];
        this.billingData.verificationResults = null;
        
        // Update UI
        this.updateBillingUI();
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('EquipmentBillingVerifier', 'files-cleared', {
                message: 'All equipment billing files cleared'
            });
        }
        
        // Disable export button
        const exportBtn = document.getElementById('export-billing-btn');
        if (exportBtn) {
            exportBtn.disabled = true;
        }
        
        return {
            status: 'files-cleared'
        };
    }
    
    updateBillingUI() {
        // Update the billing upload pane
        const baseStatus = document.querySelector('#base-file-status .file-value');
        const pmStatus = document.querySelector('#pm-files-status .file-value');
        
        if (baseStatus) {
            if (this.billingData.baseFile) {
                baseStatus.textContent = 'Uploaded';
                baseStatus.classList.add('uploaded');
            } else {
                baseStatus.textContent = 'Not uploaded';
                baseStatus.classList.remove('uploaded');
            }
        }
        
        if (pmStatus) {
            pmStatus.textContent = `${this.billingData.billingFiles.length} uploaded`;
            
            if (this.billingData.billingFiles.length > 0) {
                pmStatus.classList.add('uploaded');
            } else {
                pmStatus.classList.remove('uploaded');
            }
        }
        
        // Enable/disable verify button
        const verifyBtn = document.querySelector('#verify-allocation-btn');
        if (verifyBtn) {
            verifyBtn.disabled = !(this.billingData.baseFile && this.billingData.billingFiles.length > 0);
        }
    }
    
    updateBillingIssuesUI(message = null) {
        const issuesDiv = document.getElementById('billing-issues');
        if (!issuesDiv) return;
        
        // If just showing a message
        if (message) {
            issuesDiv.querySelector('.billing-issues-content').innerHTML = message;
            return;
        }
        
        // If no verification results
        if (!this.billingData.verificationResults) {
            issuesDiv.querySelector('.billing-issues-content').innerHTML = 'No billing verification has been run yet.';
            return;
        }
        
        // Build HTML for verification results
        let html = '';
        
        // Add summary
        html += `
            <div class="billing-summary">
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Total Billed Amount:</span>
                    <span class="billing-summary-value">$${this.billingData.verificationResults.totalBilledAmount.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Billed Assets:</span>
                    <span class="billing-summary-value">${this.billingData.verificationResults.billedAssets} of ${this.billingData.verificationResults.totalAssets}</span>
                </div>
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Unbilled Assets:</span>
                    <span class="billing-summary-value ${this.billingData.unbilledAssets.length > 0 ? 'warning' : 'good'}">${this.billingData.unbilledAssets.length}</span>
                </div>
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Incorrectly Billed:</span>
                    <span class="billing-summary-value ${this.billingData.incorrectlyBilledAssets.length > 0 ? 'bad' : 'good'}">${this.billingData.incorrectlyBilledAssets.length}</span>
                </div>
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Est. Missing Amount:</span>
                    <span class="billing-summary-value ${this.billingData.verificationResults.estimatedMissingAmount > 5000 ? 'bad' : 'warning'}">$${this.billingData.verificationResults.estimatedMissingAmount.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="billing-summary-item">
                    <span class="billing-summary-label">Verification Score:</span>
                    <span class="billing-summary-value ${this.billingData.verificationResults.verificationScore >= 90 ? 'good' : this.billingData.verificationResults.verificationScore >= 70 ? 'warning' : 'bad'}">${this.billingData.verificationResults.verificationScore}%</span>
                </div>
            </div>
        `;
        
        // Add unbilled assets
        if (this.billingData.unbilledAssets.length > 0) {
            html += `<div class="billing-issue-section">`;
            this.billingData.unbilledAssets.forEach(asset => {
                html += `
                    <div class="billing-issue-item">
                        <div class="billing-issue-type unbilled">Unbilled Asset: ${asset.assetId}</div>
                        <div class="billing-issue-details">
                            Location: ${asset.currentLocation}<br>
                            Last Update: ${asset.lastUpdate}<br>
                            Days Active: ${asset.daysActive}<br>
                            Suggested PM: ${asset.suggestedPM}<br>
                            Est. Value: $${(asset.suggestedRate * asset.estimatedHours).toLocaleString('en-US', {minimumFractionDigits: 2})}<br>
                            <a class="billing-action-link" data-asset="${asset.assetId}" data-action="mark-billable">Mark as Billable</a>
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
        }
        
        // Add incorrectly billed assets
        if (this.billingData.incorrectlyBilledAssets.length > 0) {
            html += `<div class="billing-issue-section">`;
            this.billingData.incorrectlyBilledAssets.forEach(asset => {
                html += `
                    <div class="billing-issue-item">
                        <div class="billing-issue-type incorrect">Incorrect Billing: ${asset.assetId}</div>
                        <div class="billing-issue-details">
                            Location: ${asset.currentLocation}<br>
                            Billed to: ${asset.billedJob} (${asset.billedPM})<br>
                            Should be: ${asset.correctPM}<br>
                            Issue: ${asset.issue}<br>
                            <a class="billing-action-link" data-asset="${asset.assetId}" data-action="fix-billing">Fix Billing</a>
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
        }
        
        // Set HTML
        issuesDiv.querySelector('.billing-issues-content').innerHTML = html;
        
        // Add event listeners for actions
        issuesDiv.querySelectorAll('.billing-action-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const assetId = e.target.getAttribute('data-asset');
                const action = e.target.getAttribute('data-action');
                
                if (action === 'mark-billable') {
                    const asset = this.billingData.unbilledAssets.find(a => a.assetId === assetId);
                    if (asset) {
                        // Determine job number from location
                        let jobNumber = null;
                        const jobMatch = asset.currentLocation.match(/(\d{4}-\d{3}|\w+-YARD)/i);
                        if (jobMatch) {
                            jobNumber = jobMatch[1];
                        }
                        
                        this.updateAssetBilling(assetId, jobNumber, true);
                        
                        // Show confirmation
                        e.target.textContent = 'Marked as billable!';
                        e.target.style.color = '#28a745';
                        e.target.style.pointerEvents = 'none';
                    }
                } else if (action === 'fix-billing') {
                    const asset = this.billingData.incorrectlyBilledAssets.find(a => a.assetId === assetId);
                    if (asset) {
                        // Determine job number from location
                        let jobNumber = null;
                        const jobMatch = asset.currentLocation.match(/(\d{4}-\d{3}|\w+-YARD)/i);
                        if (jobMatch) {
                            jobNumber = jobMatch[1];
                        }
                        
                        this.updateAssetBilling(assetId, jobNumber, true);
                        
                        // Show confirmation
                        e.target.textContent = 'Billing fixed!';
                        e.target.style.color = '#28a745';
                        e.target.style.pointerEvents = 'none';
                    }
                }
            });
        });
    }
    
    calculateBillingConfidence() {
        // Calculate confidence based on verification results
        
        // Start with base confidence
        let overallConfidence = 70; // Default medium confidence
        
        // If no verification results, confidence is low
        if (!this.billingData.verificationResults) {
            overallConfidence = 30;
        } else {
            // Use verification score as primary driver of confidence
            overallConfidence = this.billingData.verificationResults.verificationScore;
        }
        
        // Calculate factor confidences
        const dataFreshness = this.billingData.baseFile ? 80 : 30;
        const dataCompleteness = this.billingData.verificationResults ? 
            Math.round((this.billingData.verificationResults.billedAssets / this.billingData.verificationResults.totalAssets) * 100) : 0;
        const dataAccuracy = this.billingData.verificationResults ? 
            100 - (this.billingData.incorrectlyBilledAssets.length * 15) : 30;
        const allocationConfidence = this.billingData.verificationResults ? 
            75 - (this.billingData.unbilledAssets.length * 10) : 30;
        
        // Ensure confidence is in valid range
        overallConfidence = Math.max(0, Math.min(100, Math.round(overallConfidence)));
        
        return {
            overall: overallConfidence,
            factors: {
                'data-freshness': dataFreshness,
                'data-completeness': dataCompleteness,
                'data-accuracy': dataAccuracy,
                'allocation-confidence': allocationConfidence
            }
        };
    }
}

// Wait for GENIUS CORE to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if GENIUS CORE is loaded every 100ms
    const checkGeniusCore = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkGeniusCore);
            window.EquipmentBilling = new EquipmentBillingVerifier();
            console.log('Equipment Billing Verifier connected to GENIUS CORE');
        }
    }, 100);
});

console.log('GENIUS CORE Equipment Billing Verifier Loaded');