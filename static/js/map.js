let map;
let markers = [];
let assetMarkers = {};
function initializeMap(assets) {
const mapContainer = document.getElementById('map-container');
if (!mapContainer) return;
map = L.map('map-container').setView([32.7767, -96.7970], 10); // Dallas area
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
maxZoom: 18
}).addTo(map);
if (assets && assets.length > 0) {
addAssetsToMap(assets);
} else {
fetch('/api/assets')
.then(response => response.json())
.then(data => {
addAssetsToMap(data);
})
.catch(error => console.error('Error fetching asset data:', error));
}
}
function initializeAssetMap(asset) {
const assetMapContainer = document.getElementById('asset-detail-map');
if (!assetMapContainer || !asset) return;
if (!asset.Latitude || !asset.Longitude) {
assetMapContainer.innerHTML = '<div class="alert alert-warning">No location data available for this asset</div>';
return;
}
const assetMap = L.map('asset-detail-map').setView([asset.Latitude, asset.Longitude], 14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
maxZoom: 18
}).addTo(assetMap);
const markerIcon = L.divIcon({
html: `<div class="marker-icon ${asset.Active ? 'active' : 'inactive'}">${asset.AssetIdentifier}</div>`,
className: '',
iconSize: [40, 40]
});
const marker = L.marker([asset.Latitude, asset.Longitude], {icon: markerIcon})
.addTo(assetMap)
.bindPopup(`
<strong>${asset.Label || asset.AssetIdentifier}</strong><br>
Status: ${asset.Active ? 'Active' : 'Inactive'}<br>
Location: ${asset.Location || 'Unknown'}<br>
Last Updated: ${asset.EventDateTimeString || 'Unknown'}
`);
marker.openPopup();
}
function addAssetsToMap(assets) {
if (markers.length > 0) {
markers.forEach(marker => map.removeLayer(marker));
markers = [];
}
const assetsByLocation = {};
assets.forEach(asset => {
if (!asset.Latitude || !asset.Longitude) return;
const locationKey = `${asset.Latitude.toFixed(4)},${asset.Longitude.toFixed(4)}`;
if (!assetsByLocation[locationKey]) {
assetsByLocation[locationKey] = [];
}
assetsByLocation[locationKey].push(asset);
});
for (const locationKey in assetsByLocation) {
const [lat, lng] = locationKey.split(',').map(coord => parseFloat(coord));
const assetsAtLocation = assetsByLocation[locationKey];
let popupContent = '<div class="map-popup">';
popupContent += `<h6>${assetsAtLocation[0].Location || 'Unknown Location'}</h6>`;
popupContent += `<div class="map-popup-content">`;
assetsAtLocation.forEach(asset => {
const statusClass = asset.Active ? 'text-success' : 'text-danger';
popupContent += `
<div class="mb-2">
<strong class="${statusClass}">${asset.AssetIdentifier}</strong>:
${asset.Label ? asset.Label.split(' ').slice(1).join(' ') : 'Unknown'}
<br>
<small>${asset.AssetCategory || 'Unknown'} - ${asset.AssetMake || ''} ${asset.AssetModel || ''}</small>
<br>
<a href="/asset/${asset.AssetIdentifier}" class="btn btn-sm btn-outline-primary mt-1">Details</a>
</div>
`;
});
popupContent += '</div></div>';
const size = Math.max(8, Math.min(15, 8 + assetsAtLocation.length));
const hasActiveAssets = assetsAtLocation.some(asset => asset.Active);
const marker = L.circleMarker([lat, lng], {
radius: size,
fillColor: hasActiveAssets ? '#28a745' : '#dc3545',
color: '#fff',
weight: 2,
opacity: 1,
fillOpacity: 0.8
}).addTo(map);
if (assetsAtLocation.length > 1) {
const label = L.divIcon({
html: `<div class="map-marker-label">${assetsAtLocation.length}</div>`,
className: '',
iconSize: [20, 20]
});
L.marker([lat, lng], {icon: label}).addTo(map);
}
marker.bindPopup(popupContent);
markers.push(marker);
assetsAtLocation.forEach(asset => {
assetMarkers[asset.AssetIdentifier] = marker;
});
}
if (markers.length > 0) {
const group = new L.featureGroup(markers);
map.fitBounds(group.getBounds().pad(0.1));
}
}
function filterMapMarkers(status, category, location) {
fetch(`/api/assets?status=${status}&category=${category}&location=${location}`)
.then(response => response.json())
.then(data => {
if (map) {
addAssetsToMap(data);
}
})
.catch(error => console.error('Error fetching filtered asset data:', error));
}
document.head.insertAdjacentHTML('beforeend', `
<style>
.marker-icon {
display: flex;
align-items: center;
justify-content: center;
color: white;
font-weight: bold;
width: 30px;
height: 30px;
border-radius: 50%;
background-color: #007bff;
}
.marker-icon.active {
background-color: #28a745;
}
.marker-icon.inactive {
background-color: #dc3545;
}
.map-popup {
min-width: 200px;
max-height: 300px;
overflow-y: auto;
}
.map-popup h6 {
border-bottom: 1px solid #ccc;
padding-bottom: 5px;
margin-bottom: 10px;
}
.map-marker-label {
display: flex;
align-items: center;
justify-content: center;
color: white;
font-weight: bold;
font-size: 10px;
}
</style>
`);