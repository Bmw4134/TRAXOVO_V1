// Leaflet map with asset updates
const map = L.map('map').setView([32.7357, -97.1081], 12);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
const assets = new Map();
function updateAsset(data) {
  let marker = assets.get(data.assetId);
  if (!marker) {
    marker = L.marker([data.lat, data.lng]).addTo(map);
    assets.set(data.assetId, marker);
  }
  marker.setLatLng([data.lat, data.lng]);
  marker.bindPopup(`<strong>${data.assetId}</strong><br/>Speed: ${data.speed} mph`);
}
const ws = new WebSocket('wss://your-server/telemetry');
ws.onmessage = e => updateAsset(JSON.parse(e.data));
