* TRAXORA GENIUS CORE | Direct Map Enhancements
*
* This module applies direct DOM and CSS changes to ensure enhancements
* are immediately visible in the preview.
*/
class DirectMapEnhancements {
constructor() {
document.addEventListener('DOMContentLoaded', () => {
this.init();
});
}
init() {
console.log('Initializing Direct Map Enhancements');
this.addMapLegend();
this.enhanceAssetMarkers();
this.addClusterVisualization();
this.addHeatMap();
this.addMeasurementTool();
this.makeSidebarSticky();
this.createFilterShortcuts();
this.enhancePopupTemplate();
this.addOfflineIndicator();
this.addJobProximityDetection();
this.addMapControls();
}
addMapLegend() {
const legendHTML = `
<div id="map-legend" class="map-legend">
<div class="legend-header">
<h6>Map Legend</h6>
<button class="legend-toggle-button">
<i class="bi bi-chevron-up"></i>
</button>
</div>
<div class="legend-content">
<div class="legend-section">
<h6>Division Colors</h6>
<div class="color-item">
<span class="color-swatch" style="background-color: #3366FF;"></span>
<span class="color-label">DFW (DIV 2)</span>
</div>
<div class="color-item">
<span class="color-swatch" style="background-color: #FF3333;"></span>
<span class="color-label">HOU (DIV 4)</span>
</div>
<div class="color-item">
<span class="color-swatch" style="background-color: #33CC33;"></span>
<span class="color-label">WT (DIV 3)</span>
</div>
<div class="color-item">
<span class="color-swatch" style="background-color: #FFCC00;"></span>
<span class="color-label">TEXDIST (DIV 8)</span>
</div>
<div class="color-item">
<span class="color-swatch" style="background-color: #999999;"></span>
<span class="color-label">Unassigned</span>
</div>
</div>
<div class="legend-section">
<h6>Asset Types</h6>
<div class="icon-item">
<i class="bi bi-truck icon-swatch"></i>
<span class="icon-label">Truck</span>
</div>
<div class="icon-item">
<i class="bi bi-bullseye icon-swatch"></i>
<span class="icon-label">Heavy Equipment</span>
</div>
<div class="icon-item">
<i class="bi bi-cone-striped icon-swatch"></i>
<span class="icon-label">Safety Equipment</span>
</div>
</div>
</div>
</div>
`;
const legendStyle = document.createElement('style');
legendStyle.textContent = `
.map-legend {
position: absolute;
bottom: 20px;
right: 10px;
background: rgba(40, 40, 40, 0.85);
border-radius: 5px;
box-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
max-width: 300px;
width: calc(100% - 20px);
z-index: 1000;
transition: all 0.3s ease;
overflow: hidden;
font-size: 13px;
}
.map-legend.collapsed {
max-height: 40px;
}
.legend-header {
display: flex;
justify-content: space-between;
align-items: center;
padding: 8px 12px;
background: rgba(30, 30, 30, 0.5);
cursor: pointer;
}
.legend-header h6 {
margin: 0;
font-size: 14px;
font-weight: 600;
color: #fff;
border-bottom: none;
}
.legend-toggle-button {
background: none;
border: none;
color: #fff;
cursor: pointer;
padding: 0;
transition: transform 0.3s ease;
}
.map-legend.collapsed .legend-toggle-button i {
transform: rotate(180deg);
}
.legend-content {
padding: 10px;
overflow-y: auto;
max-height: calc(80vh - 40px);
}
.legend-section {
margin-bottom: 12px;
}
.legend-section h6 {
margin: 0 0 8px 0;
font-size: 13px;
font-weight: 500;
color: #ccc;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
padding-bottom: 5px;
}
.color-item, .icon-item {
display: flex;
align-items: center;
margin-bottom: 5px;
}
.color-swatch {
width: 16px;
height: 16px;
border-radius: 3px;
margin-right: 8px;
}
.icon-swatch {
width: 16px;
height: 16px;
margin-right: 8px;
text-align: center;
}
.color-label, .icon-label {
font-size: 12px;
color: #ddd;
}
`;
document.head.appendChild(legendStyle);
const mapContainer = document.querySelector('.map-container');
if (mapContainer) {
const legendDiv = document.createElement('div');
legendDiv.innerHTML = legendHTML;
mapContainer.appendChild(legendDiv.firstElementChild);
const legend = document.getElementById('map-legend');
const legendToggle = document.querySelector('.legend-toggle-button');
if (legend && legendToggle) {
legendToggle.addEventListener('click', () => {
legend.classList.toggle('collapsed');
});
}
}
}
enhanceAssetMarkers() {
if (window.createAssetIcon) {
const originalCreateAssetIcon = window.createAssetIcon;
window.createAssetIcon = function(status, division) {
let color = "#3366FF"; // Default: DIV 2 (DFW)
if (division === "DIV 4") {
color = "#FF3333"; // HOU
} else if (division === "DIV 3") {
color = "#33CC33"; // WT
} else if (division === "DIV 8") {
color = "#FFCC00"; // TEXDIST
} else if (division === "UNASSIGNED") {
color = "#999999"; // Unassigned
}
return L.divIcon({
className: 'asset-marker-icon',
html: `<div class="asset-marker" style="background-color:${color};width:24px;height:24px;border-radius:50%;border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);display:flex;justify-content:center;align-items:center;color:white;font-size:12px;"><i class="bi bi-geo-alt-fill"></i></div>`,
iconSize: [24, 24],
iconAnchor: [12, 12]
});
};
const markerStyle = document.createElement('style');
markerStyle.textContent = `
.asset-marker {
transition: all 0.3s ease;
}
.asset-marker:hover {
transform: scale(1.2);
}
.asset-marker.pulsating {
animation: pulse 1.5s infinite;
}
@keyframes pulse {
0% { transform: scale(1); }
50% { transform: scale(1.2); }
100% { transform: scale(1); }
}
`;
document.head.appendChild(markerStyle);
}
}
addClusterVisualization() {
const clusterCssLink = document.createElement('link');
clusterCssLink.rel = 'stylesheet';
clusterCssLink.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css';
document.head.appendChild(clusterCssLink);
const clusterDefaultCssLink = document.createElement('link');
clusterDefaultCssLink.rel = 'stylesheet';
clusterDefaultCssLink.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css';
document.head.appendChild(clusterDefaultCssLink);
const clusterScript = document.createElement('script');
clusterScript.src = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js';
document.head.appendChild(clusterScript);
clusterScript.onload = () => {
if (window.map && window.assetOverlay) {
const markers = L.markerClusterGroup({
showCoverageOnHover: false,
maxClusterRadius: 40,
iconCreateFunction: function(cluster) {
const count = cluster.getChildCount();
return L.divIcon({
html: `<div class="cluster-marker" style="background-color: rgba(51, 122, 183, 0.8); color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; font-weight: bold; border: 2px solid white;">${count}</div>`,
className: 'custom-cluster-icon',
iconSize: L.point(30, 30)
});
}
});
window.map.removeLayer(window.assetOverlay);
window.assetClusterLayer = markers;
window.map.addLayer(markers);
if (window.overlays) {
window.overlays["Clustered Assets"] = markers;
window.overlays["Individual Assets"] = window.assetOverlay;
}
}
};
}
addHeatMap() {
const heatScript = document.createElement('script');
heatScript.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
document.head.appendChild(heatScript);
heatScript.onload = () => {
if (window.map && window.loadAssets) {
const originalLoadAssets = window.loadAssets;
window.loadAssets = function() {
originalLoadAssets.apply(this, arguments);
fetch('/map/api/assets')
.then(response => response.json())
.then(data => {
const heatData = data
.filter(asset => asset.latitude && asset.longitude)
.map(asset => [asset.latitude, asset.longitude, 0.5]);
if (window.heatLayer) {
window.map.removeLayer(window.heatLayer);
}
window.heatLayer = L.heatLayer(heatData, {
radius: 25,
blur: 15,
maxZoom: 17,
gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}
});
if (window.overlays) {
window.overlays["Asset Heat Map"] = window.heatLayer;
}
});
};
}
};
}
addMeasurementTool() {
const drawCssLink = document.createElement('link');
drawCssLink.rel = 'stylesheet';
drawCssLink.href = 'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css';
document.head.appendChild(drawCssLink);
const drawScript = document.createElement('script');
drawScript.src = 'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js';
document.head.appendChild(drawScript);
drawScript.onload = () => {
if (window.map) {
const drawnItems = new L.FeatureGroup();
window.map.addLayer(drawnItems);
const drawControl = new L.Control.Draw({
draw: {
marker: false,
circlemarker: false,
polyline: {
shapeOptions: {
color: '#3388ff',
weight: 3
},
metric: true,
showLength: true
},
polygon: {
shapeOptions: {
color: '#3388ff'
},
allowIntersection: false,
showArea: true
},
rectangle: {
shapeOptions: {
color: '#3388ff'
}
},
circle: {
shapeOptions: {
color: '#3388ff'
}
}
},
edit: {
featureGroup: drawnItems
}
});
window.map.addControl(drawControl);
window.map.on(L.Draw.Event.CREATED, function(event) {
const layer = event.layer;
if (event.layerType === 'polyline') {
const latlngs = layer.getLatLngs();
let totalDistance = 0;
for (let i = 1; i < latlngs.length; i++) {
totalDistance += latlngs[i-1].distanceTo(latlngs[i]);
}
const distanceInMiles = (totalDistance / 1609.34).toFixed(2);
layer.bindTooltip(`Distance: ${distanceInMiles} miles`, {
permanent: true,
direction: 'center',
className: 'distance-tooltip'
});
}
drawnItems.addLayer(layer);
});
const tooltipStyle = document.createElement('style');
tooltipStyle.textContent = `
.distance-tooltip {
background: rgba(40, 40, 40, 0.85);
border: 1px solid rgba(255, 255, 255, 0.3);
color: white;
font-size: 12px;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
`;
document.head.appendChild(tooltipStyle);
}
};
}
makeSidebarSticky() {
const sidebar = document.querySelector('.sidebar');
if (sidebar) {
const stickyStyle = document.createElement('style');
stickyStyle.textContent = `
.sidebar.sticky {
position: sticky;
top: 0;
height: 100vh;
overflow-y: auto;
}
.sticky-toggle {
position: absolute;
top: 10px;
right: 10px;
background: rgba(40, 40, 40, 0.7);
color: white;
border: none;
border-radius: 3px;
width: 30px;
height: 30px;
font-size: 14px;
display: flex;
justify-content: center;
align-items: center;
cursor: pointer;
transition: all 0.2s ease;
z-index: 100;
}
.sticky-toggle:hover {
background: rgba(40, 40, 40, 0.9);
}
@media (max-width: 768px) {
.sidebar.sticky {
position: relative;
top: 0;
height: auto;
overflow-y: visible;
}
.sticky-toggle {
display: none;
}
}
`;
document.head.appendChild(stickyStyle);
const toggleButton = document.createElement('button');
toggleButton.className = 'sticky-toggle';
toggleButton.innerHTML = '<i class="bi bi-pin-angle"></i>';
toggleButton.title = 'Toggle Sticky Sidebar';
sidebar.appendChild(toggleButton);
toggleButton.addEventListener('click', () => {
sidebar.classList.toggle('sticky');
toggleButton.innerHTML = sidebar.classList.contains('sticky') ?
'<i class="bi bi-pin-angle-fill"></i>' :
'<i class="bi bi-pin-angle"></i>';
});
sidebar.classList.add('sticky');
toggleButton.innerHTML = '<i class="bi bi-pin-angle-fill"></i>';
}
}
createFilterShortcuts() {
const filtersSection = document.querySelector('.section:first-of-type');
if (filtersSection) {
const shortcutsDiv = document.createElement('div');
shortcutsDiv.className = 'filter-shortcuts';
shortcutsDiv.innerHTML = `
<div class="d-flex flex-wrap gap-2 mt-3">
<button class="btn btn-sm btn-outline-secondary shortcut-btn" data-type="Truck">Trucks</button>
<button class="btn btn-sm btn-outline-secondary shortcut-btn" data-type="Excavator">Excavators</button>
<button class="btn btn-sm btn-outline-secondary shortcut-btn" data-type="Crane">Cranes</button>
<button class="btn btn-sm btn-outline-secondary shortcut-btn" data-type="Loader">Loaders</button>
</div>
<div class="d-flex flex-wrap gap-2 mt-2">
<button class="btn btn-sm btn-outline-primary shortcut-job" data-job="2023-032">SH 345</button>
<button class="btn btn-sm btn-outline-primary shortcut-job" data-job="DFW-YARD">DFW Yard</button>
<button class="btn btn-sm btn-outline-primary shortcut-job" data-job="2023-007">Ector</button>
</div>
`;
filtersSection.appendChild(shortcutsDiv);
const typeFilter = document.getElementById('type-filter');
const jobSiteFilter = document.getElementById('job-site-filter');
const refreshButton = document.getElementById('refresh-map');
if (typeFilter && refreshButton) {
shortcutsDiv.querySelectorAll('.shortcut-btn').forEach(btn => {
btn.addEventListener('click', () => {
typeFilter.value = btn.dataset.type;
refreshButton.click();
});
});
}
if (jobSiteFilter && refreshButton) {
shortcutsDiv.querySelectorAll('.shortcut-job').forEach(btn => {
btn.addEventListener('click', () => {
const jobOptions = Array.from(jobSiteFilter.options);
const option = jobOptions.find(opt => opt.text.includes(btn.dataset.job));
if (option) {
jobSiteFilter.value = option.value;
refreshButton.click();
}
});
});
}
}
}
enhancePopupTemplate() {
const popupStyle = document.createElement('style');
popupStyle.textContent = `
.custom-popup {
padding: 0;
}
.custom-popup .leaflet-popup-content-wrapper {
background-color: rgba(40, 40, 40, 0.9);
border-radius: 5px;
color: #fff;
padding: 0;
}
.custom-popup .leaflet-popup-content {
margin: 0;
width: 250px !important;
overflow: hidden;
}
.custom-popup .leaflet-popup-tip {
background-color: rgba(40, 40, 40, 0.9);
}
.asset-popup-header {
padding: 10px;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
background-color: rgba(30, 30, 30, 0.5);
}
.asset-popup-title {
margin: 0;
font-size: 14px;
font-weight: 600;
color: #fff;
}
.asset-popup-subtitle {
font-size: 12px;
color: #33d4ff;
margin: 0;
}
.asset-popup-content {
padding: 10px;
}
.asset-popup-detail {
display: flex;
justify-content: space-between;
margin-bottom: 5px;
font-size: 12px;
}
.asset-popup-label {
color: #aaa;
margin-right: 10px;
}
.asset-popup-value {
color: #fff;
text-align: right;
}
.popup-actions {
display: flex;
flex-wrap: wrap;
gap: 5px;
margin-top: 10px;
padding: 10px;
border-top: 1px solid rgba(255, 255, 255, 0.1);
background-color: rgba(30, 30, 30, 0.5);
}
.asset-action-button {
flex: 1;
min-width: 80px;
background: rgba(40, 40, 40, 0.7);
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 3px;
color: #fff;
padding: 4px 8px;
font-size: 11px;
cursor: pointer;
text-align: center;
transition: background 0.2s ease;
}
.asset-action-button:hover {
background: rgba(60, 60, 60, 0.8);
}
.asset-action-button.primary {
background: rgba(51, 122, 183, 0.7);
}
.asset-action-button.primary:hover {
background: rgba(51, 122, 183, 0.8);
}
.job-selector {
width: 100%;
margin-top: 5px;
display: none;
}
.job-selector.visible {
display: block;
}
`;
document.head.appendChild(popupStyle);
if (window.loadAssets) {
window.createEnhancedPopupContent = function(asset) {
let division = "DIV 2"; // Default
const location = asset.location?.toUpperCase() || '';
if (location.includes('HOU')) {
division = "DIV 4";
} else if (location.includes('ECTOR') || location.includes('MIDLAND')) {
division = "DIV 3";
} else if (location.includes('TEX')) {
division = "DIV 8";
}
let divisionColor = "#3366FF"; // Default: DIV 2 (DFW)
if (division === "DIV 4") {
divisionColor = "#FF3333"; // HOU
} else if (division === "DIV 3") {
divisionColor = "#33CC33"; // WT
} else if (division === "DIV 8") {
divisionColor = "#FFCC00"; // TEXDIST
}
return `
<div class="asset-popup-container">
<div class="asset-popup-header" style="border-left: 4px solid ${divisionColor};">
<h3 class="asset-popup-title">${asset.name}</h3>
<p class="asset-popup-subtitle">${asset.asset_id || asset.id} | ${division}</p>
</div>
<div class="asset-popup-content">
<div class="asset-popup-detail">
<span class="asset-popup-label">Status:</span>
<span class="asset-popup-value">${asset.status || 'Active'}</span>
</div>
<div class="asset-popup-detail">
<span class="asset-popup-label">Location:</span>
<span class="asset-popup-value">${asset.location || 'Unknown'}</span>
</div>
<div class="asset-popup-detail">
<span class="asset-popup-label">Last Update:</span>
<span class="asset-popup-value">${asset.last_update || 'Unknown'}</span>
</div>
<div class="asset-popup-detail">
<span class="asset-popup-label">Type:</span>
<span class="asset-popup-value">${asset.type || 'Unknown'}</span>
</div>
<div class="asset-popup-detail">
<span class="asset-popup-label">Make/Model:</span>
<span class="asset-popup-value">${asset.make || ''} ${asset.model || ''}</span>
</div>
<div class="asset-popup-detail">
<span class="asset-popup-label">Driver:</span>
<span class="asset-popup-value">${asset.driver || 'Unassigned'}</span>
</div>
</div>
<div class="popup-actions">
<button class="asset-action-button reassign-job-button primary" data-asset-id="${asset.asset_id || asset.id}">
<i class="bi bi-arrow-repeat"></i> Reassign Job
</button>
<button class="asset-action-button mark-billable-button" data-asset-id="${asset.asset_id || asset.id}">
<i class="bi bi-receipt"></i> Mark Billable
</button>
<button class="asset-action-button flag-review-button" data-asset-id="${asset.asset_id || asset.id}">
<i class="bi bi-flag"></i> Flag for Review
</button>
<div class="job-selector" id="job-selector-${asset.asset_id || asset.id}">
<div class="selector-header">Select New Job Site:</div>
<select class="job-select form-select form-select-sm" id="job-select-${asset.asset_id || asset.id}">
<option value="">-- Select Job --</option>
<option value="2023-032">2023-032 SH 345 Bridge Rehabilitation</option>
<option value="2024-019">2024-019 (15) Tarrant VA Bridge Rehab</option>
<option value="DFW-YARD">DFW Yard</option>
<option value="HOU-YARD">HOU Yard/Shop</option>
<option value="2023-007">2023-007 Ector BI 20E Rehab Roadway</option>
<option value="2024-012">2024-012 Dal IH635 U-Turn Bridge</option>
</select>
<div class="d-flex gap-2 mt-2">
<button class="btn btn-sm btn-success confirm-btn w-50" data-asset-id="${asset.asset_id || asset.id}">Confirm</button>
<button class="btn btn-sm btn-danger cancel-btn w-50" data-asset-id="${asset.asset_id || asset.id}">Cancel</button>
</div>
</div>
</div>
</div>
`;
};
const originalLoadAssets = window.loadAssets;
window.loadAssets = function() {
originalLoadAssets.apply(this, arguments);
window.createAssetMarkerWithPopup = function(asset) {
let division = "DIV 2"; // Default
const location = asset.location?.toUpperCase() || '';
if (location.includes('HOU')) {
division = "DIV 4";
} else if (location.includes('ECTOR') || location.includes('MIDLAND')) {
division = "DIV 3";
} else if (location.includes('TEX')) {
division = "DIV 8";
}
const marker = L.marker([asset.latitude, asset.longitude], {
icon: window.createAssetIcon(asset.status, division)
});
const popup = L.popup({
className: 'custom-popup',
closeButton: true,
autoClose: true,
closeOnClick: true
}).setContent(window.createEnhancedPopupContent(asset));
marker.bindPopup(popup);
marker.on('popupopen', function() {
setTimeout(() => {
const reassignBtn = document.querySelector('.reassign-job-button');
if (reassignBtn) {
reassignBtn.addEventListener('click', function() {
const assetId = this.getAttribute('data-asset-id');
const selector = document.getElementById(`job-selector-${assetId}`);
if (selector) {
selector.classList.add('visible');
}
});
}
const confirmBtn = document.querySelector('.confirm-btn');
if (confirmBtn) {
confirmBtn.addEventListener('click', function() {
const assetId = this.getAttribute('data-asset-id');
const jobSelect = document.getElementById(`job-select-${assetId}`);
const selector = document.getElementById(`job-selector-${assetId}`);
if (jobSelect && selector) {
const selectedJob = jobSelect.value;
if (selectedJob) {
console.log(`[PASSIVE] Would reassign asset ${assetId} to job ${selectedJob}`);
const actionsDiv = selector.parentElement;
const confirmationDiv = document.createElement('div');
confirmationDiv.className = 'alert alert-success mt-2 p-2 small';
confirmationDiv.innerHTML = '<i class="bi bi-check-circle"></i> Reassignment request logged (passive mode)';
actionsDiv.appendChild(confirmationDiv);
selector.classList.remove('visible');
setTimeout(() => {
if (confirmationDiv.parentElement) {
confirmationDiv.parentElement.removeChild(confirmationDiv);
}
}, 3000);
}
}
});
}
const cancelBtn = document.querySelector('.cancel-btn');
if (cancelBtn) {
cancelBtn.addEventListener('click', function() {
const assetId = this.getAttribute('data-asset-id');
const selector = document.getElementById(`job-selector-${assetId}`);
if (selector) {
selector.classList.remove('visible');
}
});
}
}, 100);
});
return marker;
};
};
}
}
addOfflineIndicator() {
const indicator = document.createElement('div');
indicator.id = 'offline-indicator';
indicator.className = 'offline-indicator hidden';
indicator.innerHTML = `
<div class="offline-message">
<i class="bi bi-wifi-off"></i>
<span class="offline-text">Using offline asset data</span>
</div>
<button class="offline-close" title="Dismiss">&times;</button>
`;
document.body.appendChild(indicator);
const indicatorStyle = document.createElement('style');
indicatorStyle.textContent = `
.offline-indicator {
position: fixed;
top: 0;
left: 0;
right: 0;
background-color: rgba(243, 156, 18, 0.9);
color: #fff;
padding: 8px 15px;
text-align: center;
font-size: 13px;
z-index: 9999;
display: flex;
justify-content: space-between;
align-items: center;
}
.offline-indicator.hidden {
display: none;
}
.offline-message {
flex: 1;
}
.offline-close {
background: none;
border: none;
color: white;
cursor: pointer;
font-size: 16px;
padding: 0 0 0 10px;
}
`;
document.head.appendChild(indicatorStyle);
const closeBtn = indicator.querySelector('.offline-close');
if (closeBtn) {
closeBtn.addEventListener('click', () => {
indicator.classList.add('hidden');
});
}
setTimeout(() => {
indicator.classList.remove('hidden');
}, 10000); // Show after 10 seconds
}
addJobProximityDetection() {
if (window.map) {
const highlightStyle = document.createElement('style');
highlightStyle.textContent = `
.distance-circle {
stroke-dasharray: 10, 10;
animation: dash 15s linear infinite;
stroke: rgba(51, 212, 255, 0.6);
fill: rgba(51, 212, 255, 0.1);
}
@keyframes dash {
to {
stroke-dashoffset: -200;
}
}
`;
document.head.appendChild(highlightStyle);
window.showJobProximity = function(jobId) {
if (window.proximityCircle) {
window.map.removeLayer(window.proximityCircle);
}
const jobSite = window.jobSites.find(site => site.job_number === jobId);
if (jobSite) {
window.proximityCircle = L.circle([jobSite.latitude, jobSite.longitude], {
radius: jobSite.radius || 1000,
className: 'distance-circle'
}).addTo(window.map);
window.map.setView([jobSite.latitude, jobSite.longitude], 14);
}
};
const sidebarContent = document.querySelector('.sidebar-content');
if (sidebarContent) {
const proximityHeader = document.createElement('div');
proximityHeader.className = 'mt-4 mb-2';
proximityHeader.innerHTML = '<h5>Job Proximity</h5>';
const proximityContent = document.createElement('div');
proximityContent.innerHTML = `
<div class="mb-2 small">Show assets within job radius:</div>
<div class="d-flex flex-wrap gap-2">
<button class="btn btn-sm btn-outline-info proximity-btn" data-job="2023-032">SH 345</button>
<button class="btn btn-sm btn-outline-info proximity-btn" data-job="DFW-YARD">DFW Yard</button>
<button class="btn btn-sm btn-outline-info proximity-btn" data-job="2023-007">Ector</button>
</div>
`;
sidebarContent.appendChild(proximityHeader);
sidebarContent.appendChild(proximityContent);
proximityContent.querySelectorAll('.proximity-btn').forEach(btn => {
btn.addEventListener('click', () => {
window.showJobProximity(btn.dataset.job);
});
});
}
}
}
addMapControls() {
if (window.map) {
class HomeButton extends L.Control {
onAdd(map) {
const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
const button = L.DomUtil.create('a', 'home-button', container);
button.innerHTML = '<i class="bi bi-house-door"></i>';
button.title = 'Zoom to Home';
button.href = '#';
L.DomEvent.on(button, 'click', function(e) {
L.DomEvent.preventDefault(e);
map.setView([32.7767, -96.7970], 8);
});
return container;
}
}
class ShowAllButton extends L.Control {
onAdd(map) {
const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
const button = L.DomUtil.create('a', 'show-all-button', container);
button.innerHTML = '<i class="bi bi-eye"></i>';
button.title = 'Show All Assets';
button.href = '#';
L.DomEvent.on(button, 'click', function(e) {
L.DomEvent.preventDefault(e);
document.getElementById('type-filter').value = '';
document.getElementById('job-site-filter').value = '';
document.getElementById('refresh-map').click();
});
return container;
}
}
new HomeButton({ position: 'topleft' }).addTo(window.map);
new ShowAllButton({ position: 'topleft' }).addTo(window.map);
}
}
}
const directEnhancements = new DirectMapEnhancements();
console.log('GENIUS CORE Direct Map Enhancements Loaded');