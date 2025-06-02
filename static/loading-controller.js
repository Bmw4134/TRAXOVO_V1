/** TRAXOVO Dynamic Loading Controller
* Manages loading states and animations across the platform
*/
class LoadingController {
constructor() {
this.activeLoaders = new Set();
this.loadingStates = new Map();
this.init();
}
init() {
this.detectInitialLoading();
this.setupEventListeners();
}
detectInitialLoading() {
const fleetMap = document.querySelector('#fleet-map');
if (fleetMap && !fleetMap.dataset.loaded) {
this.showMapLoading('fleet-map');
}
const kpiContainer = document.querySelector('.kpi-metrics');
if (kpiContainer && !kpiContainer.dataset.loaded) {
this.showKPILoading('kpi-metrics');
}
const assetGrid = document.querySelector('.asset-grid');
if (assetGrid && !assetGrid.dataset.loaded) {
this.showAssetGridLoading('asset-grid');
}
}
setupEventListeners() {
document.addEventListener('click', (e) => {
const target = e.target.parentElement&&.parentElement.querySelector('[data-loading-trigger]');
if (target) {
const loadingType = target.dataset.loadingTrigger;
const targetId = target.dataset.loadingTarget;
this.showLoading(loadingType, targetId);
}
});
document.addEventListener('traxovo:loading:start', (e) => {
this.showLoading(e.detail.type, e.detail.target, e.detail.message);
});
document.addEventListener('traxovo:loading:complete', (e) => {
this.hideLoading(e.detail.target);
});
}
showLoading(type, targetId, message = null) {
const container = document.getElementById(targetId);
if (!container) return;
this.activeLoaders.add(targetId);
this.loadingStates.set(targetId, { type, startTime: Date.now() });
switch (type) {
case 'fleet-map':
this.showMapLoading(targetId, message);
break;
case 'kpi':
this.showKPILoading(targetId, message);
break;
case 'asset-grid':
this.showAssetGridLoading(targetId, message);
break;
case 'table':
this.showTableLoading(targetId, message);
break;
case 'general':
this.showGeneralLoading(targetId, message);
break;
default:
this.showGeneralLoading(targetId, message);
}
}
showMapLoading(targetId, message = 'Loading fleet data...') {
const container = document.getElementById(targetId);
container.innerHTML = `
<div class="map-loading">
<div class="map-loading-content">
<div class="fleet-spinner"></div>
<div class="loading-text">${message}</div>
<div class="loading-subtext">Connecting to GAUGE API and processing 701 assets</div>
</div>
</div>
`;
}
showKPILoading(targetId, message = 'Calculating metrics...') {
const container = document.getElementById(targetId);
container.innerHTML = `
<div class="kpi-loading">
<div class="kpi-loading-card">
<div class="kpi-loading-value"></div>
<div class="kpi-loading-label"></div>
</div>
<div class="kpi-loading-card">
<div class="kpi-loading-value"></div>
<div class="kpi-loading-label"></div>
</div>
<div class="kpi-loading-card">
<div class="kpi-loading-value"></div>
<div class="kpi-loading-label"></div>
</div>
<div class="kpi-loading-card">
<div class="kpi-loading-value"></div>
<div class="kpi-loading-label"></div>
</div>
</div>
`;
}
showAssetGridLoading(targetId, message = 'Loading assets...') {
const container = document.getElementById(targetId);
const loadingCards = Array(6).fill(null).map(() => `
<div class="asset-loading-card">
<div class="loading-bar medium"></div>
<div class="loading-bar short"></div>
<div class="loading-bar long"></div>
<div class="loading-bar medium"></div>
</div>
`).join('');
container.innerHTML = `
<div class="fleet-loading">
<div class="loading-text">${message}</div>
<div class="progress-loading">
<div class="progress-bar"></div>
</div>
</div>
<div class="asset-loading-grid">
${loadingCards}
</div>
`;
}
showTableLoading(targetId, message = 'Loading data...') {
const container = document.getElementById(targetId);
const loadingRows = Array(8).fill(null).map(() => `
<tr>
<td><div class="table-loading-cell"></div></td>
<td><div class="table-loading-cell"></div></td>
<td><div class="table-loading-cell"></div></td>
<td><div class="table-loading-cell"></div></td>
<td><div class="table-loading-cell"></div></td>
</tr>
`).join('');
container.innerHTML = `
<div class="fleet-loading">
<div class="loading-text">${message}</div>
</div>
<table class="table-loading">
${loadingRows}
</table>
`;
}
showGeneralLoading(targetId, message = 'Loading...') {
const container = document.getElementById(targetId);
container.innerHTML = `
<div class="fleet-loading">
<div class="fleet-spinner"></div>
<div class="loading-text">${message}</div>
<div class="loading-subtext">Processing authentic fleet data</div>
</div>
`;
}
hideLoading(targetId) {
this.activeLoaders.delete(targetId);
this.loadingStates.delete(targetId);
const container = document.getElementById(targetId);
if (container) {
container.dataset.loaded = 'true';
const loadingElements = container.querySelectorAll('[class*="loading"]');
loadingElements.forEach(el => el.remove());
}
}
showFleetMapLoading(message) {
this.showLoading('fleet-map', 'fleet-map', message);
}
showDashboardLoading() {
this.showLoading('kpi', 'dashboard-metrics');
this.showLoading('general', 'recent-activity');
}
simulateDataLoading(targetId, duration = 2000) {
setTimeout(() => {
this.hideLoading(targetId);
this.dispatchLoadingComplete(targetId);
}, duration);
}
dispatchLoadingComplete(targetId) {
document.dispatchEvent(new CustomEvent('traxovo:loading:complete', {
detail: { target: targetId }
}));
}
getLoadingDuration(targetId) {
const state = this.loadingStates.get(targetId);
return state ? Date.now() - state.startTime : 0;
}
isLoading(targetId) {
return this.activeLoaders.has(targetId);
}
getActiveLoaders() {
return Array.from(this.activeLoaders);
}
}
const traxovoLoading = new LoadingController();
window.showFleetLoading = (message) => traxovoLoading.showFleetMapLoading(message);
window.hideFleetLoading = () => traxovoLoading.hideLoading('fleet-map');
window.showDashboardLoading = () => traxovoLoading.showDashboardLoading();
document.addEventListener('DOMContentLoaded', () => {
document.querySelectorAll('[data-auto-loading]').forEach(element => {
const loadingType = element.dataset.autoLoading;
const loadingMessage = element.dataset.loadingMessage;
traxovoLoading.showLoading(loadingType, element.id, loadingMessage);
});
});