* TRAXORA GENIUS CORE | System Manifest and Continuity Mode Controller
*
* This module locks in the core logic for the Asset Map and other modules,
* and establishes the system manifest for tracking agent status.
*/
class GeniusCoreManifest {
constructor() {
if (!window.GeniusCore) {
console.error('GENIUS CORE not available. Manifest initialization aborted.');
return;
}
this.geniusCore = window.GeniusCore;
this.systemManifest = {};
this.taskQueue = [];
this.continuityMode = true;
this.lastBroadcast = null;
this.initializeManifest();
this.manifestAgent = {
id: 'SystemManifest',
handleMessage(message) {
switch (message.type) {
case 'register-module':
return window.CoreManifest.registerModule(
message.payload.name,
message.payload.path,
message.payload.dataSource
);
case 'update-status':
return window.CoreManifest.updateModuleStatus(
message.payload.name,
message.payload.status,
message.payload.task,
message.payload.details
);
case 'get-manifest':
return {
status: 'manifest',
manifest: window.CoreManifest.getFullManifest()
};
case 'get-module-status':
return {
status: 'module-status',
moduleStatus: window.CoreManifest.getModuleStatus(message.payload.name)
};
default:
return { status: 'unknown-message-type' };
}
}
};
this.geniusCore.registerAgent('SystemManifest', this.manifestAgent);
this.registerWithBroadcaster();
setInterval(() => this.broadcastManifestStatus(), 5000);
console.log('GENIUS CORE Manifest initialized');
}
initializeManifest() {
this.registerModule('AssetTracker', '/asset-map/trackers/asset', 'gauge_api.AssetList');
this.registerModule('JobSiteMonitor', '/asset-map/trackers/job-site', 'map_standalone.job_sites');
this.registerModule('RecommendationEngine', '/asset-map/intelligence/recommendation', 'asset-tracker,job-site-monitor');
this.registerModule('AnomalyDetector', '/asset-map/intelligence/anomaly', 'asset-tracker,job-site-monitor');
this.registerModule('BillingVerifier', '/billing/verifiers/allocation', 'pm-allocation-files');
this.registerModule('DriverReports', '/driver-reports/pipeline/processor', 'uploaded-csv-files');
this.registerModule('SystemManifest', '/system/manifest', 'agent-broadcasts');
this.registerModule('ModuleStatus', '/system/status', 'agent-status-reports');
this.registerModule('IntegrationManager', '/system/integration', 'asset-map-ui');
}
registerModule(name, path, dataSource) {
this.systemManifest[name] = {
name: name,
path: path,
dataSource: dataSource,
status: 'initializing',
health: 50,
lastTask: null,
lastUpdate: new Date().toISOString(),
details: {}
};
console.log(`Module registered: ${name} at ${path}`);
return { status: 'module-registered', name: name };
}
updateModuleStatus(name, status, currentTask = null, details = null) {
if (!this.systemManifest[name]) {
console.warn(`Unknown module in manifest: ${name}`);
return { status: 'error', message: 'Unknown module' };
}
this.systemManifest[name].status = status;
this.systemManifest[name].lastUpdate = new Date().toISOString();
if (currentTask) {
this.systemManifest[name].lastTask = currentTask;
}
if (details) {
this.systemManifest[name].details = {
...this.systemManifest[name].details,
...details
};
}
switch (status) {
case 'operational':
this.systemManifest[name].health = 100;
break;
case 'connected':
this.systemManifest[name].health = 90;
break;
case 'processing':
this.systemManifest[name].health = 80;
break;
case 'waiting':
this.systemManifest[name].health = 70;
break;
case 'partial':
this.systemManifest[name].health = 60;
break;
case 'incomplete':
this.systemManifest[name].health = 40;
break;
case 'error':
this.systemManifest[name].health = 20;
break;
case 'inactive':
this.systemManifest[name].health = 10;
break;
default:
break;
}
return {
status: 'module-status-updated',
name: name,
currentStatus: status,
health: this.systemManifest[name].health
};
}
getModuleStatus(name) {
return this.systemManifest[name] || null;
}
getFullManifest() {
return {
modules: this.systemManifest,
continuityMode: this.continuityMode,
taskQueueDepth: this.taskQueue.length,
lastBroadcast: this.lastBroadcast
};
}
registerWithBroadcaster() {
window.addEventListener('message', (event) => {
if (event.data && event.data.type === 'genius-core-broadcast') {
this.handleBroadcast(event.data.payload);
}
});
}
handleBroadcast(payload) {
if (payload.type === 'agent-status') {
this.updateModuleStatus(
payload.agent,
payload.status,
payload.currentTask,
payload.details
);
} else if (payload.type === 'task-queue-update') {
this.taskQueue = payload.tasks;
}
}
broadcastManifestStatus() {
const manifest = this.getFullManifest();
this.lastBroadcast = new Date().toISOString();
window.postMessage({
type: 'genius-core-broadcast',
payload: {
type: 'manifest-update',
manifest: manifest,
timestamp: this.lastBroadcast
}
}, '*');
this.updateManifestDisplay();
}
updateManifestDisplay() {
const manifestContainer = document.getElementById('system-manifest-container');
if (!manifestContainer) return;
let html = '<div class="system-manifest">';
html += '<h6>GENIUS CORE SYSTEM MANIFEST</h6>';
html += '<div class="manifest-list">';
Object.values(this.systemManifest).forEach(module => {
const healthClass = module.health > 75 ? 'success' :
module.health > 50 ? 'primary' :
module.health > 25 ? 'warning' : 'danger';
html += `
<div class="manifest-item">
<div class="d-flex justify-content-between">
<strong>${module.name}</strong>
<span class="badge bg-${healthClass}">${module.status}</span>
</div>
<div class="small text-muted">${module.path}</div>
<div class="small">Source: ${module.dataSource}</div>
${module.lastTask ?
`<div class="small">Task: ${module.lastTask}</div>` : ''}
<div class="small">Last event: ${new Date(module.lastUpdate).toLocaleTimeString()}</div>
</div>
`;
});
html += '</div>';
html += `<div class="manifest-footer">Continuity Mode: ${this.continuityMode ? 'ACTIVE' : 'INACTIVE'}</div>`;
html += '</div>';
manifestContainer.innerHTML = html;
}
createManifestDisplay() {
let manifestDiv = document.getElementById('system-manifest-container');
if (!manifestDiv) {
manifestDiv = document.createElement('div');
manifestDiv.id = 'system-manifest-container';
manifestDiv.className = 'system-manifest-container';
const toggleButton = document.createElement('button');
toggleButton.id = 'manifest-toggle';
toggleButton.className = 'manifest-toggle';
toggleButton.textContent = 'GENIUS CORE MANIFEST';
document.body.appendChild(toggleButton);
document.body.appendChild(manifestDiv);
toggleButton.addEventListener('click', function() {
manifestDiv.classList.toggle('expanded');
toggleButton.classList.toggle('active');
});
const style = document.createElement('style');
style.textContent = `
.system-manifest-container {
position: fixed;
top: 20px;
right: -340px;
width: 320px;
max-height: 80vh;
background: rgba(33, 37, 41, 0.95);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
padding: 12px;
color: white;
font-family: monospace;
z-index: 2000;
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
transition: right 0.3s ease-in-out;
overflow-y: auto;
}
.system-manifest-container.expanded {
right: 20px;
}
.manifest-toggle {
position: fixed;
top: 20px;
right: 20px;
background: #333;
color: #33d4ff;
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 4px;
padding: 5px 10px;
font-family: monospace;
font-size: 12px;
cursor: pointer;
z-index: 2001;
}
.manifest-toggle.active {
background: #33d4ff;
color: #333;
}
.system-manifest h6 {
color: #33d4ff;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
padding-bottom: 8px;
margin-bottom: 12px;
}
.manifest-list {
display: grid;
grid-template-columns: 1fr;
gap: 10px;
}
.manifest-item {
padding: 8px;
border-radius: 4px;
background: rgba(255, 255, 255, 0.1);
}
.manifest-footer {
margin-top: 12px;
padding-top: 8px;
border-top: 1px solid rgba(255, 255, 255, 0.1);
text-align: center;
font-weight: bold;
color: #33d4ff;
}
`;
document.head.appendChild(style);
}
this.updateManifestDisplay();
}
}
document.addEventListener('DOMContentLoaded', function() {
const checkGeniusCore = setInterval(() => {
if (window.GeniusCore) {
clearInterval(checkGeniusCore);
window.CoreManifest = new GeniusCoreManifest();
window.CoreManifest.createManifestDisplay();
console.log('GENIUS CORE Manifest connected');
}
}, 100);
});
console.log('GENIUS CORE Manifest System Loaded');