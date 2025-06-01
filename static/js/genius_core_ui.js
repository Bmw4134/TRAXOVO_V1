* TRAXORA GENIUS CORE | UI Manager
*
* This module creates and manages the UI components for the GENIUS CORE system.
*/
document.addEventListener('DOMContentLoaded', function() {
setTimeout(createUIComponents, 1000);
});
function createUIComponents() {
console.log('Creating GENIUS CORE UI components...');
createModuleStatusPanel();
createSystemManifestButton();
addGlobalStyles();
console.log('GENIUS CORE UI components created');
}
function createModuleStatusPanel() {
if (document.getElementById('genius-module-status')) {
return;
}
const statusPanel = document.createElement('div');
statusPanel.id = 'genius-module-status';
statusPanel.className = 'genius-ui genius-module-status';
statusPanel.innerHTML = `
<div class="genius-ui-header">
<h6>System Status</h6>
<button class="genius-ui-toggle">−</button>
</div>
<div class="genius-ui-content">
<div class="genius-module-item">
<span class="module-name">Asset Map</span>
<span class="module-status operational">Operational</span>
<div class="progress">
<div class="progress-bar" style="width: 100%"></div>
</div>
</div>
<div class="genius-module-item">
<span class="module-name">Driver Reports</span>
<span class="module-status waiting">Waiting for files</span>
<div class="progress">
<div class="progress-bar" style="width: 40%"></div>
</div>
</div>
<div class="genius-module-item">
<span class="module-name">PM Allocation</span>
<span class="module-status waiting">Waiting for verification</span>
<div class="progress">
<div class="progress-bar" style="width: 40%"></div>
</div>
</div>
<div class="genius-module-item">
<span class="module-name">GENIUS CORE</span>
<span class="module-status operational">Continuity Mode Active</span>
<div class="progress">
<div class="progress-bar genius" style="width: 100%"></div>
</div>
</div>
</div>
`;
document.body.appendChild(statusPanel);
const header = statusPanel.querySelector('.genius-ui-header');
const toggleBtn = statusPanel.querySelector('.genius-ui-toggle');
header.addEventListener('click', function() {
statusPanel.classList.toggle('collapsed');
toggleBtn.textContent = statusPanel.classList.contains('collapsed') ? '+' : '−';
});
}
function createSystemManifestButton() {
if (document.getElementById('genius-manifest-button')) {
return;
}
const manifestButton = document.createElement('div');
manifestButton.id = 'genius-manifest-button';
manifestButton.className = 'genius-ui genius-manifest-button';
manifestButton.innerHTML = `
<button class="genius-manifest-toggle">
<span>GENIUS CORE</span>
<span class="status-indicator active"></span>
</button>
<div class="genius-manifest-panel">
<div class="genius-ui-header">
<h6>System Manifest</h6>
<button class="genius-ui-close">×</button>
</div>
<div class="genius-ui-content">
<div class="genius-manifest-item">
<div class="agent-header">
<span class="agent-name">AssetTracker</span>
<span class="agent-status active">Active</span>
</div>
<div class="agent-description">Tracking 656 assets across 42 job sites</div>
</div>
<div class="genius-manifest-item">
<div class="agent-header">
<span class="agent-name">DriverPipeline</span>
<span class="agent-status waiting">Waiting</span>
</div>
<div class="agent-description">Ready to process driver data for 05/21/2025</div>
</div>
<div class="genius-manifest-item">
<div class="agent-header">
<span class="agent-name">BillingVerifier</span>
<span class="agent-status waiting">Waiting</span>
</div>
<div class="agent-description">Ready to verify April 2025 allocations</div>
</div>
<div class="genius-manifest-item">
<div class="agent-header">
<span class="agent-name">ModuleStatus</span>
<span class="agent-status active">Active</span>
</div>
<div class="agent-description">Monitoring system health and module performance</div>
</div>
<div class="genius-manifest-item">
<div class="agent-header">
<span class="agent-name">SystemManifest</span>
<span class="agent-status active">Active</span>
</div>
<div class="agent-description">Managing core continuity across all modules</div>
</div>
</div>
</div>
`;
document.body.appendChild(manifestButton);
const toggleBtn = manifestButton.querySelector('.genius-manifest-toggle');
const panel = manifestButton.querySelector('.genius-manifest-panel');
const closeBtn = manifestButton.querySelector('.genius-ui-close');
toggleBtn.addEventListener('click', function() {
panel.classList.toggle('visible');
});
closeBtn.addEventListener('click', function() {
panel.classList.remove('visible');
});
}
function createDriverUploadPane() {
if (document.getElementById('genius-driver-upload')) {
return;
}
const uploadPane = document.createElement('div');
uploadPane.id = 'genius-driver-upload';
uploadPane.className = 'genius-ui genius-driver-upload';
uploadPane.innerHTML = `
<div class="genius-ui-header">
<h6>Driver Reports Pipeline</h6>
<button class="genius-ui-toggle">−</button>
</div>
<div class="genius-ui-content">
<div class="file-status-list">
<div class="file-status-item">
<span class="file-label">Driving History:</span>
<span class="file-value uploaded">Uploaded</span>
</div>
<div class="file-status-item">
<span class="file-label">Activity Detail:</span>
<span class="file-value uploaded">Uploaded</span>
</div>
<div class="file-status-item">
<span class="file-label">Asset List:</span>
<span class="file-value uploaded">Uploaded</span>
</div>
</div>
<div class="genius-ui-actions">
<button class="genius-action-button">Run Pipeline</button>
<button class="genius-action-button secondary">Clear Files</button>
</div>
<div class="pipeline-results">
<div>Date: 2025-05-21</div>
<div>Drivers: 125</div>
<div>Classified: 118</div>
<div>Unclassified: 7</div>
</div>
</div>
`;
document.body.appendChild(uploadPane);
const header = uploadPane.querySelector('.genius-ui-header');
const toggleBtn = uploadPane.querySelector('.genius-ui-toggle');
header.addEventListener('click', function() {
uploadPane.classList.toggle('collapsed');
toggleBtn.textContent = uploadPane.classList.contains('collapsed') ? '+' : '−';
});
}
function createBillingUploadPane() {
if (document.getElementById('genius-billing-upload')) {
return;
}
const uploadPane = document.createElement('div');
uploadPane.id = 'genius-billing-upload';
uploadPane.className = 'genius-ui genius-billing-upload';
uploadPane.innerHTML = `
<div class="genius-ui-header">
<h6>PM Allocation Verifier</h6>
<button class="genius-ui-toggle">−</button>
</div>
<div class="genius-ui-content">
<div class="file-status-list">
<div class="file-status-item">
<span class="file-label">Base File:</span>
<span class="file-value uploaded">Uploaded</span>
</div>
<div class="file-status-item">
<span class="file-label">PM Files:</span>
<span class="file-value uploaded">3 uploaded</span>
</div>
</div>
<div class="month-selection">
<label for="billing-month">Month:</label>
<select id="billing-month">
<option value="2025-04">April 2025</option>
<option value="2025-03">March 2025</option>
</select>
</div>
<div class="genius-ui-actions">
<button class="genius-action-button">Verify Allocation</button>
<button class="genius-action-button secondary">Clear Files</button>
</div>
</div>
`;
document.body.appendChild(uploadPane);
const header = uploadPane.querySelector('.genius-ui-header');
const toggleBtn = uploadPane.querySelector('.genius-ui-toggle');
header.addEventListener('click', function() {
uploadPane.classList.toggle('collapsed');
toggleBtn.textContent = uploadPane.classList.contains('collapsed') ? '+' : '−';
});
}
function addGlobalStyles() {
const style = document.createElement('style');
style.textContent = `
.genius-ui {
position: fixed;
background: rgba(33, 37, 41, 0.9);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
color: white;
font-family: sans-serif;
z-index: 1000;
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.genius-ui-header {
display: flex;
justify-content: space-between;
align-items: center;
padding: 10px 15px;
background: rgba(0, 0, 0, 0.2);
cursor: pointer;
}
.genius-ui-header h6 {
margin: 0;
color: #33d4ff;
}
.genius-ui-toggle, .genius-ui-close {
background: none;
border: none;
color: white;
font-size: 16px;
cursor: pointer;
padding: 0 5px;
}
.genius-ui-content {
padding: 15px;
display: flex;
flex-direction: column;
gap: 10px;
}
.genius-ui.collapsed .genius-ui-content {
display: none;
}
.genius-module-status {
bottom: 20px;
right: 20px;
width: 300px;
}
.genius-module-item {
display: flex;
flex-direction: column;
gap: 5px;
}
.module-name {
font-weight: bold;
}
.module-status {
font-size: 12px;
}
.module-status.operational {
color: #28a745;
}
.module-status.waiting {
color: #ffc107;
}
.module-status.error {
color: #dc3545;
}
.progress {
height: 5px;
background: rgba(255, 255, 255, 0.1);
border-radius: 2px;
overflow: hidden;
}
.progress-bar {
height: 100%;
background: #28a745;
}
.progress-bar.genius {
background: #33d4ff;
}
.genius-manifest-button {
top: 20px;
right: 20px;
}
.genius-manifest-toggle {
display: flex;
align-items: center;
gap: 10px;
background: rgba(33, 37, 41, 0.9);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 20px;
color: #33d4ff;
font-weight: bold;
padding: 8px 15px;
cursor: pointer;
}
.status-indicator {
width: 10px;
height: 10px;
border-radius: 50%;
background: #dc3545;
}
.status-indicator.active {
background: #28a745;
}
.genius-manifest-panel {
position: absolute;
top: 100%;
right: 0;
width: 350px;
margin-top: 10px;
background: rgba(33, 37, 41, 0.9);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
display: none;
}
.genius-manifest-panel.visible {
display: block;
}
.genius-manifest-item {
padding: 10px;
border-radius: 4px;
background: rgba(255, 255, 255, 0.1);
margin-bottom: 10px;
}
.agent-header {
display: flex;
justify-content: space-between;
margin-bottom: 5px;
}
.agent-name {
font-weight: bold;
}
.agent-status {
font-size: 12px;
padding: 2px 6px;
border-radius: 10px;
}
.agent-status.active {
background: rgba(40, 167, 69, 0.2);
color: #28a745;
}
.agent-status.waiting {
background: rgba(255, 193, 7, 0.2);
color: #ffc107;
}
.agent-description {
font-size: 12px;
color: #ccc;
}
.genius-driver-upload {
bottom: 20px;
left: 20px;
width: 300px;
}
.genius-billing-upload {
bottom: 20px;
left: 340px;
width: 300px;
}
.file-status-list {
display: flex;
flex-direction: column;
gap: 5px;
}
.file-status-item {
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
.month-selection {
display: flex;
align-items: center;
justify-content: space-between;
margin-top: 5px;
}
.month-selection select {
background: #444;
color: white;
border: none;
border-radius: 4px;
padding: 5px;
}
.genius-ui-actions {
display: flex;
gap: 10px;
margin-top: 5px;
}
.genius-action-button {
flex: 1;
padding: 5px 10px;
background: #33d4ff;
color: #111;
border: none;
border-radius: 4px;
cursor: pointer;
font-weight: bold;
}
.genius-action-button.secondary {
background: #444;
color: white;
}
.genius-action-button:hover {
filter: brightness(1.1);
}
.pipeline-results {
font-size: 12px;
color: #ccc;
margin-top: 10px;
padding-top: 10px;
border-top: 1px solid rgba(255, 255, 255, 0.1);
}
`;
document.head.appendChild(style);
setTimeout(() => {
createDriverUploadPane();
createBillingUploadPane();
}, 500);
}
console.log('GENIUS CORE UI Manager Loaded');