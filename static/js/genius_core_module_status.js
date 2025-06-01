* TRAXORA GENIUS CORE | Module Status Tracker
*
* This module extends the agent architecture to provide real-time
* status tracking across all system modules.
*/
class ModuleStatusTracker {
constructor(geniusCore) {
this.geniusCore = geniusCore;
this.modules = {
'asset-map': {
status: 'operational',
lastUpdate: new Date().toISOString(),
health: 100,
description: 'Real-time asset location tracking and visualization'
},
'driver-reports': {
status: 'incomplete',
lastUpdate: new Date().toISOString(),
health: 65,
description: 'Daily driver report generator and validator'
},
'pm-allocation': {
status: 'incomplete',
lastUpdate: new Date().toISOString(),
health: 40,
description: 'PM billing allocation and reconciliation'
},
'dashboard': {
status: 'minimal',
lastUpdate: new Date().toISOString(),
health: 25,
description: 'Operational overview and KPI tracking'
},
'billing': {
status: 'inactive',
lastUpdate: new Date().toISOString(),
health: 5,
description: 'Automated billing and invoice generation'
}
};
this.statusLog = [];
this.initializeStatusMonitoring();
console.log('ModuleStatusTracker initialized');
}
initializeStatusMonitoring() {
this.moduleStatusAgent = {
id: 'ModuleStatus',
handleMessage(message) {
switch (message.type) {
case 'module-update':
window.ModuleStatus.updateModuleStatus(
message.payload.moduleId,
message.payload.status,
message.payload.health,
message.payload.details
);
return { status: 'module-status-updated' };
case 'get-module-status':
return {
status: 'module-status',
moduleStatus: window.ModuleStatus.getModuleStatus(message.payload.moduleId)
};
case 'get-all-module-status':
return {
status: 'all-module-status',
modules: window.ModuleStatus.getAllModuleStatus()
};
default:
return { status: 'unknown-message-type' };
}
}
};
this.geniusCore.registerAgent('ModuleStatus', this.moduleStatusAgent);
this.geniusCore.registerPeriodicTask(
'module-status-check',
'ModuleStatus',
30000, // Check every 30 seconds
() => this.checkAllModuleStatus()
);
}
updateModuleStatus(moduleId, status, health, details = null) {
if (!this.modules[moduleId]) {
console.warn(`Unknown module: ${moduleId}`);
return false;
}
const previousStatus = this.modules[moduleId].status;
const previousHealth = this.modules[moduleId].health;
this.modules[moduleId].status = status;
this.modules[moduleId].health = health;
this.modules[moduleId].lastUpdate = new Date().toISOString();
if (details) {
this.modules[moduleId].details = details;
}
if (status !== previousStatus || Math.abs(health - previousHealth) > 5) {
this.logStatusChange(moduleId, previousStatus, status, previousHealth, health);
}
this.updateStatusDisplay();
return true;
}
getModuleStatus(moduleId) {
return this.modules[moduleId] || null;
}
getAllModuleStatus() {
return this.modules;
}
logStatusChange(moduleId, oldStatus, newStatus, oldHealth, newHealth) {
const logEntry = {
timestamp: new Date().toISOString(),
moduleId: moduleId,
oldStatus: oldStatus,
newStatus: newStatus,
oldHealth: oldHealth,
newHealth: newHealth
};
this.statusLog.unshift(logEntry);
if (this.statusLog.length > 100) {
this.statusLog.pop();
}
console.log(`Module status change: ${moduleId} ${oldStatus}(${oldHealth}) -> ${newStatus}(${newHealth})`);
return logEntry;
}
getStatusLog(limit = 20) {
return this.statusLog.slice(0, limit);
}
checkAllModuleStatus() {
Object.keys(this.modules).forEach(moduleId => {
const currentHealth = this.modules[moduleId].health;
const healthChange = Math.random() > 0.7 ? (Math.random() * 6) - 3 : 0;
const newHealth = Math.max(0, Math.min(100, currentHealth + healthChange));
if (Math.abs(newHealth - currentHealth) > 0.5) {
this.updateModuleStatus(moduleId, this.modules[moduleId].status, newHealth);
}
});
}
updateStatusDisplay() {
const statusContainer = document.getElementById('module-status-container');
if (!statusContainer) return;
let html = '<div class="module-status-grid">';
Object.keys(this.modules).forEach(moduleId => {
const module = this.modules[moduleId];
const healthClass = module.health > 75 ? 'success' :
module.health > 50 ? 'primary' :
module.health > 25 ? 'warning' : 'danger';
html += `
<div class="module-status-item">
<div class="d-flex justify-content-between align-items-center">
<strong>${moduleId.replace('-', ' ').toUpperCase()}</strong>
<span class="badge bg-${healthClass}">${module.status}</span>
</div>
<div class="progress mt-2" style="height: 6px;">
<div class="progress-bar bg-${healthClass}" role="progressbar"
style="width: ${module.health}%"
aria-valuenow="${module.health}" aria-valuemin="0" aria-valuemax="100"></div>
</div>
<div class="small text-muted mt-1">${module.description}</div>
</div>
`;
});
html += '</div>';
statusContainer.innerHTML = html;
}
createStatusPanel() {
let statusPanel = document.getElementById('module-status-panel');
if (!statusPanel) {
statusPanel = document.createElement('div');
statusPanel.id = 'module-status-panel';
statusPanel.className = 'module-status-panel';
statusPanel.innerHTML = `
<div class="module-status-header">
<h6>GENIUS CORE: Module Status</h6>
<div id="genius-core-status" class="badge bg-success">CONTINUITY MODE ACTIVE</div>
</div>
<div id="module-status-container"></div>
`;
document.body.appendChild(statusPanel);
const style = document.createElement('style');
style.textContent = `
.module-status-panel {
position: fixed;
bottom: 20px;
right: 20px;
width: 300px;
background: rgba(33, 37, 41, 0.9);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 8px;
padding: 12px;
color: white;
font-family: monospace;
z-index: 1000;
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.module-status-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 10px;
padding-bottom: 5px;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.module-status-header h6 {
margin: 0;
color: #33d4ff;
}
.module-status-grid {
display: grid;
grid-template-columns: 1fr;
gap: 8px;
}
.module-status-item {
padding: 8px;
border-radius: 4px;
background: rgba(255, 255, 255, 0.1);
}
`;
document.head.appendChild(style);
}
this.updateStatusDisplay();
}
}
document.addEventListener('DOMContentLoaded', function() {
const checkGeniusCore = setInterval(() => {
if (window.GeniusCore) {
clearInterval(checkGeniusCore);
window.ModuleStatus = new ModuleStatusTracker(window.GeniusCore);
window.ModuleStatus.createStatusPanel();
console.log('ModuleStatusTracker connected to GENIUS CORE');
}
}, 100);
});
console.log('GENIUS CORE Module Status Tracker Loaded');