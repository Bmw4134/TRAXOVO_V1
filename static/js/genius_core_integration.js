* TRAXORA GENIUS CORE | Data Integration Manager
*
* This module connects the GENIUS CORE agent architecture to real data from
* the asset map and other system modules.
*/
class GeniusCoreIntegration {
constructor() {
if (!window.GeniusCore) {
console.error('GENIUS CORE not available. Integration aborted.');
return;
}
this.geniusCore = window.GeniusCore;
this.assetData = {};
this.jobSiteData = {};
this.setupMapIntegration();
this.setupAssetDataListener();
this.setupJobSiteListener();
this.integrationAgent = {
id: 'IntegrationManager',
handleMessage(message) {
switch (message.type) {
case 'sync-status':
return {
status: 'sync-status',
assetCount: Object.keys(window.Integration.assetData).length,
jobSiteCount: Object.keys(window.Integration.jobSiteData).length,
lastSync: new Date().toISOString()
};
default:
return { status: 'unknown-message-type' };
}
}
};
this.geniusCore.registerAgent('IntegrationManager', this.integrationAgent);
if (window.ModuleStatus) {
window.ModuleStatus.updateModuleStatus('asset-map', 'connected', 95, {
assetsLoaded: true,
jobSitesLoaded: true,
recommendationsActive: true
});
}
console.log('GENIUS CORE Integration Manager initialized');
}
setupMapIntegration() {
const originalLoadAssets = window.loadAssets;
if (originalLoadAssets) {
window.loadAssets = function() {
const result = originalLoadAssets.apply(this, arguments);
if (window.Integration && window.assetData) {
window.Integration.captureAssetData(window.assetData);
}
return result;
};
}
const originalLoadJobSites = window.loadJobSites;
if (originalLoadJobSites) {
window.loadJobSites = function() {
const result = originalLoadJobSites.apply(this, arguments);
if (window.Integration && window.jobSites) {
window.Integration.captureJobSiteData(window.jobSites);
}
return result;
};
}
}
setupAssetDataListener() {
const observer = new MutationObserver((mutations) => {
for (const mutation of mutations) {
if (mutation.type === 'childList' &&
mutation.target.id === 'map-container' &&
window.assetData) {
this.captureAssetData(window.assetData);
}
}
});
observer.observe(document.body, { childList: true, subtree: true });
}
setupJobSiteListener() {
const observer = new MutationObserver((mutations) => {
for (const mutation of mutations) {
if (mutation.type === 'childList' &&
mutation.target.id === 'map-container' &&
window.jobSites) {
this.captureJobSiteData(window.jobSites);
}
}
});
observer.observe(document.body, { childList: true, subtree: true });
}
captureAssetData(assetData) {
if (!Array.isArray(assetData)) return;
console.log(`Capturing ${assetData.length} assets for GENIUS CORE`);
assetData.forEach(asset => {
this.assetData[asset.id] = asset;
this.geniusCore.sendMessage(
'IntegrationManager',
'AssetTracker',
'asset-update',
asset
);
if (asset.last_update) {
const lastUpdateDate = new Date(asset.last_update);
const currentDate = new Date();
const diffTime = Math.abs(currentDate - lastUpdateDate);
const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
if (diffDays > 30) {
this.geniusCore.sendMessage(
'IntegrationManager',
'AnomalyDetector',
'check-anomaly',
{
type: 'asset-inactive',
assetId: asset.id,
inactiveDays: diffDays,
assetType: asset.type
}
);
}
}
if (asset.latitude && asset.longitude && Object.keys(this.jobSiteData).length > 0) {
this.checkForSiteConflicts(asset);
}
});
if (window.ModuleStatus) {
window.ModuleStatus.updateModuleStatus('asset-map', 'operational', 100, {
assetsLoaded: true,
assetCount: Object.keys(this.assetData).length,
lastUpdate: new Date().toISOString()
});
}
}
captureJobSiteData(jobSiteData) {
if (!Array.isArray(jobSiteData)) return;
console.log(`Capturing ${jobSiteData.length} job sites for GENIUS CORE`);
jobSiteData.forEach(site => {
this.jobSiteData[site.id] = site;
this.geniusCore.sendMessage(
'IntegrationManager',
'JobSiteMonitor',
'site-update',
site
);
});
Object.values(this.assetData).forEach(asset => {
if (asset.latitude && asset.longitude) {
this.checkForSiteConflicts(asset);
}
});
}
checkForSiteConflicts(asset) {
const matchingSites = [];
Object.values(this.jobSiteData).forEach(site => {
if (!site.latitude || !site.longitude || !site.radius) return;
const distance = this.calculateDistance(
asset.latitude, asset.longitude,
site.latitude, site.longitude
);
if (distance <= site.radius) {
matchingSites.push({
site: site,
distance: distance
});
this.geniusCore.sendMessage(
'IntegrationManager',
'JobSiteMonitor',
'asset-at-site',
{
assetId: asset.id,
siteId: site.id
}
);
}
});
if (matchingSites.length > 1) {
matchingSites.sort((a, b) => a.distance - b.distance);
this.geniusCore.sendMessage(
'IntegrationManager',
'RecommendationEngine',
'request-recommendation',
{
assetId: asset.id,
assetType: asset.type,
sites: matchingSites.map(match => match.site)
}
);
this.geniusCore.sendMessage(
'IntegrationManager',
'AnomalyDetector',
'check-anomaly',
{
type: 'site-conflict',
assetId: asset.id,
sites: matchingSites.map(match => match.site.id),
timestamp: new Date().toISOString()
}
);
}
}
calculateDistance(lat1, lon1, lat2, lon2) {
const R = 6371000; // Radius of the earth in meters
const dLat = this.deg2rad(lat2 - lat1);
const dLon = this.deg2rad(lon2 - lon1);
const a =
Math.sin(dLat/2) * Math.sin(dLat/2) +
Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) *
Math.sin(dLon/2) * Math.sin(dLon/2);
const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
const distance = R * c; // Distance in meters
return distance;
}
deg2rad(deg) {
return deg * (Math.PI/180);
}
}
document.addEventListener('DOMContentLoaded', function() {
const checkInterval = setInterval(() => {
if (window.GeniusCore) {
clearInterval(checkInterval);
window.Integration = new GeniusCoreIntegration();
console.log('GENIUS CORE Integration initialized');
}
}, 100);
});
console.log('GENIUS CORE Integration Manager Loaded');