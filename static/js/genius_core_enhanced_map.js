* TRAXORA GENIUS CORE | Enhanced Map Integration
*
* This module enhances the map with interactive elements, action buttons,
* and advanced job scoring visualization integrated with the GENIUS CORE system.
*/
class EnhancedMapSystem {
constructor() {
if (!window.GeniusCore) {
console.error('GENIUS CORE not available. Enhanced Map initialization aborted.');
return;
}
this.geniusCore = window.GeniusCore;
this.map = null;
this.markers = {};
this.jobSites = [];
this.activePopup = null;
this.mapAgent = {
id: 'EnhancedMap',
handleMessage(message) {
switch (message.type) {
case 'assign-to-job':
return window.EnhancedMap.assignAssetToJob(
message.payload.assetId,
message.payload.jobNumber,
message.payload.driverId
);
case 'mark-billable':
return window.EnhancedMap.markAssetAsBillable(
message.payload.assetId,
message.payload.jobNumber,
message.payload.isPMBillable
);
case 'flag-for-review':
return window.EnhancedMap.flagAssetForReview(
message.payload.assetId,
message.payload.reason,
message.payload.priority
);
case 'get-job-score':
return {
status: 'job-score',
score: window.EnhancedMap.getJobScore(
message.payload.assetId,
message.payload.jobNumber
)
};
case 'highlight-asset':
return window.EnhancedMap.highlightAsset(
message.payload.assetId,
message.payload.style
);
default:
return { status: 'unknown-message-type' };
}
}
};
this.geniusCore.registerAgent('EnhancedMap', this.mapAgent);
setTimeout(() => this.initializeMapEnhancements(), 1000);
console.log('Enhanced Map System initialized');
}
initializeMapEnhancements() {
this.map = window.map;
if (!this.map) {
console.error('Map not found, cannot enhance.');
return;
}
this.createCustomPopupTemplate();
this.setupMarkerListeners();
this.enhanceJobSiteVisualization();
console.log('Map enhancements initialized');
if (window.ContinuityManager) {
setTimeout(() => {
this.registerMapData();
}, 3000);
}
}
createCustomPopupTemplate() {
this.popupTemplate = (asset) => {
const container = document.createElement('div');
container.className = 'genius-map-popup';
container.id = `popup-${asset.id || asset.asset_id}`;
const details = document.createElement('div');
details.className = 'popup-details';
details.innerHTML = `
<div class="popup-header">
<h6>${asset.name || asset.id || asset.asset_id}</h6>
<span class="asset-type">${asset.type || 'Asset'}</span>
</div>
<div class="popup-info">
<div class="info-item">
<span class="info-label">Make:</span>
<span class="info-value">${asset.make || 'Unknown'}</span>
</div>
<div class="info-item">
<span class="info-label">Model:</span>
<span class="info-value">${asset.model || 'Unknown'}</span>
</div>
<div class="info-item">
<span class="info-label">Status:</span>
<span class="info-value ${asset.status === 'active' ? 'active' : 'inactive'}">${asset.status || 'Unknown'}</span>
</div>
<div class="info-item">
<span class="info-label">Location:</span>
<span class="info-value">${asset.location || 'Unknown'}</span>
</div>
<div class="info-item">
<span class="info-label">Last Update:</span>
<span class="info-value">${asset.last_update || 'Unknown'}</span>
</div>
</div>
`;
if (asset.location) {
let jobNumber = null;
const jobMatch = asset.location.match(/(\d{4}-\d{3}|\w+-YARD)/i);
if (jobMatch) {
jobNumber = jobMatch[1];
}
const scoringSection = document.createElement('div');
scoringSection.className = 'job-scoring-section';
scoringSection.innerHTML = '<h6>Job Site Assessment</h6>';
const scoreContainer = document.createElement('div');
scoreContainer.className = 'job-score-container';
scoringSection.appendChild(scoreContainer);
if (jobNumber) {
this.updateJobScoreDisplay(scoreContainer, asset.id || asset.asset_id, jobNumber);
} else {
scoreContainer.innerHTML = `
<div class="no-job-message">No job number detected in location</div>
`;
}
const actionsSection = document.createElement('div');
actionsSection.className = 'popup-actions';
const assignButton = document.createElement('button');
assignButton.className = 'popup-action-btn assign';
assignButton.textContent = 'Assign to Job';
assignButton.dataset.assetId = asset.id || asset.asset_id;
assignButton.addEventListener('click', (e) => {
this.showAssignJobDialog(asset.id || asset.asset_id, asset.location);
e.stopPropagation();
});
const billableButton = document.createElement('button');
billableButton.className = 'popup-action-btn billable';
billableButton.textContent = 'Mark as Billable';
billableButton.dataset.assetId = asset.id || asset.asset_id;
billableButton.addEventListener('click', (e) => {
this.markAssetAsBillable(asset.id || asset.asset_id, jobNumber, true);
this.showConfirmation(billableButton, 'Marked billable!');
e.stopPropagation();
});
const flagButton = document.createElement('button');
flagButton.className = 'popup-action-btn flag';
flagButton.textContent = 'Flag for Review';
flagButton.dataset.assetId = asset.id || asset.asset_id;
flagButton.addEventListener('click', (e) => {
this.showFlagDialog(asset.id || asset.asset_id, asset.location);
e.stopPropagation();
});
actionsSection.appendChild(assignButton);
actionsSection.appendChild(billableButton);
actionsSection.appendChild(flagButton);
scoringSection.appendChild(actionsSection);
details.appendChild(scoringSection);
}
container.appendChild(details);
const styleElement = document.createElement('style');
styleElement.textContent = `
.genius-map-popup {
width: 300px;
}
.popup-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 8px;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
padding-bottom: 8px;
}
.popup-header h6 {
margin: 0;
font-weight: bold;
font-size: 14px;
color: #33d4ff;
}
.asset-type {
font-size: 12px;
background: rgba(51, 212, 255, 0.2);
color: #33d4ff;
padding: 2px 6px;
border-radius: 10px;
}
.popup-info {
display: flex;
flex-direction: column;
gap: 5px;
margin-bottom: 15px;
}
.info-item {
display: flex;
justify-content: space-between;
font-size: 12px;
}
.info-label {
font-weight: bold;
color: #ccc;
}
.info-value {
text-align: right;
}
.info-value.active {
color: #28a745;
}
.info-value.inactive {
color: #dc3545;
}
.job-scoring-section {
margin-top: 15px;
padding-top: 10px;
border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.job-scoring-section h6 {
margin: 0 0 10px 0;
font-size: 13px;
font-weight: bold;
}
.job-score-container {
margin-bottom: 10px;
}
.job-score {
display: flex;
align-items: center;
justify-content: space-between;
margin-bottom: 8px;
}
.job-score-label {
font-weight: bold;
font-size: 12px;
}
.job-score-value {
display: flex;
align-items: center;
gap: 5px;
}
.score-bar {
width: 80px;
height: 6px;
background: rgba(255, 255, 255, 0.1);
border-radius: 3px;
overflow: hidden;
}
.score-bar-fill {
height: 100%;
}
.score-bar-fill.high {
background: #28a745;
}
.score-bar-fill.medium {
background: #ffc107;
}
.score-bar-fill.low {
background: #dc3545;
}
.score-percentage {
font-size: 12px;
font-weight: bold;
min-width: 40px;
text-align: right;
}
.score-factors {
font-size: 11px;
margin-top: 5px;
color: #ccc;
}
.no-job-message {
font-size: 12px;
font-style: italic;
color: #999;
margin: 5px 0;
}
.popup-actions {
display: flex;
flex-wrap: wrap;
gap: 5px;
margin-top: 10px;
}
.popup-action-btn {
flex: 1;
background: #333;
border: none;
color: white;
padding: 5px 10px;
font-size: 12px;
border-radius: 4px;
cursor: pointer;
position: relative;
transition: all 0.2s ease;
}
.popup-action-btn:hover {
background: #444;
}
.popup-action-btn.assign {
background: #33d4ff;
color: #000;
}
.popup-action-btn.assign:hover {
background: #20c0eb;
}
.popup-action-btn.billable {
background: #28a745;
color: white;
}
.popup-action-btn.billable:hover {
background: #218838;
}
.popup-action-btn.flag {
background: #dc3545;
color: white;
}
.popup-action-btn.flag:hover {
background: #c82333;
}
.confirmation-message {
position: absolute;
top: -30px;
left: 50%;
transform: translateX(-50%);
background: rgba(40, 167, 69, 0.9);
color: white;
padding: 5px 10px;
border-radius: 4px;
font-size: 12px;
pointer-events: none;
opacity: 0;
transition: opacity 0.3s ease;
white-space: nowrap;
}
.confirmation-message.visible {
opacity: 1;
}
.popup-dialog {
position: fixed;
top: 50%;
left: 50%;
transform: translate(-50%, -50%);
background: #343a40;
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
padding: 20px;
min-width: 300px;
z-index: 2000;
box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
}
.popup-dialog-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 15px;
padding-bottom: 10px;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.popup-dialog-title {
margin: 0;
font-size: 16px;
color: #33d4ff;
}
.popup-dialog-close {
background: none;
border: none;
color: #ccc;
font-size: 18px;
cursor: pointer;
}
.popup-dialog-content {
margin-bottom: 20px;
}
.popup-form-group {
margin-bottom: 15px;
}
.popup-form-group label {
display: block;
margin-bottom: 5px;
font-weight: bold;
font-size: 13px;
}
.popup-form-group input,
.popup-form-group textarea,
.popup-form-group select {
width: 100%;
padding: 8px;
background: #495057;
border: 1px solid #6c757d;
border-radius: 4px;
color: white;
}
.popup-form-group select {
height: 36px;
}
.popup-dialog-actions {
display: flex;
justify-content: flex-end;
gap: 10px;
}
.popup-dialog-btn {
padding: 8px 15px;
border: none;
border-radius: 4px;
cursor: pointer;
font-weight: bold;
}
.popup-dialog-btn.cancel {
background: #6c757d;
color: white;
}
.popup-dialog-btn.primary {
background: #33d4ff;
color: #000;
}
.popup-dialog-btn.danger {
background: #dc3545;
color: white;
}
.popup-dialog-backdrop {
position: fixed;
top: 0;
left: 0;
right: 0;
bottom: 0;
background: rgba(0, 0, 0, 0.5);
z-index: 1999;
}
`;
container.appendChild(styleElement);
return container;
};
}
setupMarkerListeners() {
const mapContainer = document.getElementById('map');
if (!mapContainer) return;
const observer = new MutationObserver((mutations) => {
mutations.forEach((mutation) => {
if (mutation.type === 'childList') {
const markers = mapContainer.querySelectorAll('.leaflet-marker-icon');
markers.forEach((marker) => {
if (!marker.dataset.enhanced) {
marker.dataset.enhanced = 'true';
marker.addEventListener('click', (e) => {
const assetId = marker.alt;
if (assetId) {
this.handleMarkerClick(assetId);
}
});
}
});
}
});
});
observer.observe(mapContainer, {
childList: true,
subtree: true
});
}
handleMarkerClick(assetId) {
console.log('Marker clicked:', assetId);
}
enhanceJobSiteVisualization() {
console.log('Job site visualization would be enhanced here');
}
registerMapData() {
if (window.assets && Array.isArray(window.assets)) {
this.geniusCore.sendMessage(
'EnhancedMap',
'ContinuityManager',
'register-module-data',
{
moduleId: 'asset-map',
dataType: 'assets',
data: window.assets
}
);
console.log('Registered asset data with Continuity Manager');
}
if (window.jobSites && Array.isArray(window.jobSites)) {
this.geniusCore.sendMessage(
'EnhancedMap',
'ContinuityManager',
'register-module-data',
{
moduleId: 'asset-map',
dataType: 'jobSites',
data: window.jobSites
}
);
console.log('Registered job site data with Continuity Manager');
}
}
updateJobScoreDisplay(container, assetId, jobNumber) {
let score = this.getJobScore(assetId, jobNumber);
if (score) {
const scoreLevel = this.getScoreLevel(score.overallScore);
let factorsHtml = '';
for (const [factor, value] of Object.entries(score.factors)) {
let factorName = factor;
factorName = factorName.replace(/([A-Z])/g, ' $1')
.replace(/^./, (str) => str.toUpperCase());
factorsHtml += `${factorName}: ${value}%, `;
}
if (factorsHtml) {
factorsHtml = factorsHtml.slice(0, -2); // Remove trailing comma and space
}
container.innerHTML = `
<div class="job-score">
<span class="job-score-label">Job Fit (${jobNumber}):</span>
<div class="job-score-value">
<div class="score-bar">
<div class="score-bar-fill ${scoreLevel}" style="width: ${score.overallScore}%"></div>
</div>
<span class="score-percentage">${score.overallScore}%</span>
</div>
</div>
<div class="score-factors">
Factors: ${factorsHtml}
</div>
`;
} else {
container.innerHTML = `
<div class="no-job-message">Job scoring not available</div>
`;
}
}
getJobScore(assetId, jobNumber) {
if (window.VisualDiagnostics && window.VisualDiagnostics.getTelemetryScore) {
return window.VisualDiagnostics.getTelemetryScore(assetId, jobNumber);
}
return {
assetId: assetId,
jobNumber: jobNumber,
overallScore: 75,
factors: {
distance: 80,
timeAtJob: 70,
historicalPattern: 85,
driverMatch: 65
},
confidenceLevel: 'Medium',
analysisTime: new Date().toISOString()
};
}
getScoreLevel(score) {
if (score >= 80) {
return 'high';
} else if (score >= 60) {
return 'medium';
} else {
return 'low';
}
}
showConfirmation(button, message) {
let confirmation = button.querySelector('.confirmation-message');
if (!confirmation) {
confirmation = document.createElement('div');
confirmation.className = 'confirmation-message';
button.appendChild(confirmation);
}
confirmation.textContent = message;
confirmation.classList.add('visible');
setTimeout(() => {
confirmation.classList.remove('visible');
}, 2000);
}
showAssignJobDialog(assetId, currentLocation) {
const dialog = document.createElement('div');
dialog.className = 'popup-dialog';
const backdrop = document.createElement('div');
backdrop.className = 'popup-dialog-backdrop';
dialog.innerHTML = `
<div class="popup-dialog-header">
<h5 class="popup-dialog-title">Assign Asset to Job</h5>
<button class="popup-dialog-close">&times;</button>
</div>
<div class="popup-dialog-content">
<div class="popup-form-group">
<label for="asset-id">Asset ID:</label>
<input type="text" id="asset-id" value="${assetId}" readonly>
</div>
<div class="popup-form-group">
<label for="current-location">Current Location:</label>
<input type="text" id="current-location" value="${currentLocation || 'Unknown'}" readonly>
</div>
<div class="popup-form-group">
<label for="job-number">Job Number:</label>
<input type="text" id="job-number" placeholder="Enter job number (e.g. 2023-032)">
</div>
<div class="popup-form-group">
<label for="driver-id">Assign Driver (optional):</label>
<input type="text" id="driver-id" placeholder="Enter driver name">
</div>
</div>
<div class="popup-dialog-actions">
<button class="popup-dialog-btn cancel">Cancel</button>
<button class="popup-dialog-btn primary">Assign</button>
</div>
`;
document.body.appendChild(backdrop);
document.body.appendChild(dialog);
const closeBtn = dialog.querySelector('.popup-dialog-close');
const cancelBtn = dialog.querySelector('.popup-dialog-btn.cancel');
const assignBtn = dialog.querySelector('.popup-dialog-btn.primary');
closeBtn.addEventListener('click', () => {
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
cancelBtn.addEventListener('click', () => {
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
assignBtn.addEventListener('click', () => {
const jobNumber = dialog.querySelector('#job-number').value;
const driverId = dialog.querySelector('#driver-id').value;
if (!jobNumber) {
alert('Please enter a job number');
return;
}
this.assignAssetToJob(assetId, jobNumber, driverId || null);
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
}
showFlagDialog(assetId, currentLocation) {
const dialog = document.createElement('div');
dialog.className = 'popup-dialog';
const backdrop = document.createElement('div');
backdrop.className = 'popup-dialog-backdrop';
dialog.innerHTML = `
<div class="popup-dialog-header">
<h5 class="popup-dialog-title">Flag Asset for Review</h5>
<button class="popup-dialog-close">&times;</button>
</div>
<div class="popup-dialog-content">
<div class="popup-form-group">
<label for="asset-id">Asset ID:</label>
<input type="text" id="asset-id" value="${assetId}" readonly>
</div>
<div class="popup-form-group">
<label for="current-location">Current Location:</label>
<input type="text" id="current-location" value="${currentLocation || 'Unknown'}" readonly>
</div>
<div class="popup-form-group">
<label for="flag-reason">Reason:</label>
<textarea id="flag-reason" rows="3" placeholder="Enter reason for review"></textarea>
</div>
<div class="popup-form-group">
<label for="flag-priority">Priority:</label>
<select id="flag-priority">
<option value="low">Low</option>
<option value="medium" selected>Medium</option>
<option value="high">High</option>
</select>
</div>
</div>
<div class="popup-dialog-actions">
<button class="popup-dialog-btn cancel">Cancel</button>
<button class="popup-dialog-btn danger">Flag</button>
</div>
`;
document.body.appendChild(backdrop);
document.body.appendChild(dialog);
const closeBtn = dialog.querySelector('.popup-dialog-close');
const cancelBtn = dialog.querySelector('.popup-dialog-btn.cancel');
const flagBtn = dialog.querySelector('.popup-dialog-btn.danger');
closeBtn.addEventListener('click', () => {
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
cancelBtn.addEventListener('click', () => {
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
flagBtn.addEventListener('click', () => {
const reason = dialog.querySelector('#flag-reason').value;
const priority = dialog.querySelector('#flag-priority').value;
if (!reason) {
alert('Please enter a reason');
return;
}
this.flagAssetForReview(assetId, reason, priority);
document.body.removeChild(dialog);
document.body.removeChild(backdrop);
});
}
assignAssetToJob(assetId, jobNumber, driverId = null) {
console.log(`Assigning asset ${assetId} to job ${jobNumber}${driverId ? ` with driver ${driverId}` : ''}`);
if (window.VisualDiagnostics) {
window.VisualDiagnostics.logEvent('EnhancedMap', 'asset-assigned', {
assetId: assetId,
jobNumber: jobNumber,
driverId: driverId,
message: `Asset ${assetId} assigned to job ${jobNumber}${driverId ? ` with driver ${driverId}` : ''}`
});
}
if (window.ContinuityManager) {
console.log('Asset assignment would update continuity data');
}
return {
status: 'asset-assigned',
assetId: assetId,
jobNumber: jobNumber,
driverId: driverId
};
}
markAssetAsBillable(assetId, jobNumber, isPMBillable = true) {
console.log(`Marking asset ${assetId} on job ${jobNumber} as ${isPMBillable ? 'PM billable' : 'not PM billable'}`);
if (window.VisualDiagnostics) {
window.VisualDiagnostics.logEvent('EnhancedMap', 'asset-billable-status', {
assetId: assetId,
jobNumber: jobNumber,
isPMBillable: isPMBillable,
message: `Asset ${assetId} marked as ${isPMBillable ? 'billable' : 'not billable'} on job ${jobNumber}`
});
}
if (window.BillingVerifier) {
this.geniusCore.sendMessage(
'EnhancedMap',
'BillingVerifier',
'update-asset-billing',
{
assetId: assetId,
jobNumber: jobNumber,
isPMBillable: isPMBillable
}
);
}
return {
status: 'asset-billable-updated',
assetId: assetId,
jobNumber: jobNumber,
isPMBillable: isPMBillable
};
}
flagAssetForReview(assetId, reason, priority = 'medium') {
console.log(`Flagging asset ${assetId} for review with priority ${priority}: ${reason}`);
if (window.VisualDiagnostics) {
window.VisualDiagnostics.logEvent('EnhancedMap', 'asset-flagged', {
assetId: assetId,
reason: reason,
priority: priority,
message: `Asset ${assetId} flagged for review: ${reason}`
});
}
if (window.VisualDiagnostics) {
window.VisualDiagnostics.registerConflict(
'asset-review',
{ assetId: assetId },
{
message: reason,
severity: priority,
recommendedAction: 'Review asset and address flagged issue'
}
);
}
return {
status: 'asset-flagged',
assetId: assetId,
reason: reason,
priority: priority
};
}
highlightAsset(assetId, style = 'default') {
console.log(`Highlighting asset ${assetId} with style ${style}`);
return {
status: 'asset-highlighted',
assetId: assetId,
style: style
};
}
}
document.addEventListener('DOMContentLoaded', function() {
const checkGeniusCore = setInterval(() => {
if (window.GeniusCore) {
clearInterval(checkGeniusCore);
window.EnhancedMap = new EnhancedMapSystem();
console.log('Enhanced Map System connected to GENIUS CORE');
}
}, 100);
});
console.log('GENIUS CORE Enhanced Map System Loaded');