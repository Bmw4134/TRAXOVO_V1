
// QQ Enhanced Asset Map with Zone Integration
class QQAssetZoneMap {
    constructor() {
        this.map = null;
        this.assetMarkers = {};
        this.zoneCircles = {};
        this.fortWorthZones = {"fort_worth_main": {"name": "Fort Worth Main Yard", "center_lat": 32.7767, "center_lng": -97.097, "radius_meters": 500, "payroll_rate": 28.5, "zone_color": "#3498db"}, "downtown_construction": {"name": "Downtown Construction Site", "center_lat": 32.7555, "center_lng": -97.3308, "radius_meters": 300, "payroll_rate": 32.75, "zone_color": "#e74c3c"}, "trinity_river": {"name": "Trinity River Project", "center_lat": 32.7915, "center_lng": -97.4019, "radius_meters": 750, "payroll_rate": 35.25, "zone_color": "#27ae60"}, "alliance_depot": {"name": "Alliance Equipment Depot", "center_lat": 33.0013, "center_lng": -97.203, "radius_meters": 400, "payroll_rate": 29.8, "zone_color": "#f39c12"}};
        this.activeAssets = [{"AssetIdentifier": "D-26", "Label": "CAT 330 Excavator D-26", "AssetCategory": "Excavator", "AssetMake": "Caterpillar", "AssetModel": "330", "Active": true, "Latitude": 32.7767, "Longitude": -97.097, "Location": "Fort Worth Main Yard", "assigned_zone": "fort_worth_main", "zone_status": "in_zone", "operator": "Bob Johnson", "hourly_rate": 28.5}, {"AssetIdentifier": "EX-81", "Label": "Komatsu PC400 EX-81", "AssetCategory": "Excavator", "AssetMake": "Komatsu", "AssetModel": "PC400", "Active": true, "Latitude": 32.7555, "Longitude": -97.3308, "Location": "Downtown Construction Site", "assigned_zone": "downtown_construction", "zone_status": "in_zone", "operator": "Carlos Martinez", "hourly_rate": 32.75}, {"AssetIdentifier": "PT-252", "Label": "Ford F-350 PT-252", "AssetCategory": "Pickup Truck", "AssetMake": "Ford", "AssetModel": "F-350", "Active": true, "Latitude": 32.7915, "Longitude": -97.4019, "Location": "Trinity River Project", "assigned_zone": "trinity_river", "zone_status": "in_zone", "operator": "Diana Smith", "hourly_rate": 35.25}, {"AssetIdentifier": "ET-35", "Label": "CAT D8R Dozer ET-35", "AssetCategory": "Dozer", "AssetMake": "Caterpillar", "AssetModel": "D8R", "Active": true, "Latitude": 33.0013, "Longitude": -97.203, "Location": "Alliance Equipment Depot", "assigned_zone": "alliance_depot", "zone_status": "in_zone", "operator": "Eric Wilson", "hourly_rate": 29.8}, {"AssetIdentifier": "F150-01", "Label": "Ford F-150 F150-01", "AssetCategory": "Pickup Truck", "AssetMake": "Ford", "AssetModel": "F-150", "Active": false, "Latitude": 32.79, "Longitude": -97.12, "Location": "En Route - Trinity River", "assigned_zone": "trinity_river", "zone_status": "out_of_zone", "operator": "Alice Rodriguez", "hourly_rate": 35.25}];
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.addZoneOverlays();
        this.addAssetMarkers();
        this.setupRealTimeUpdates();
        console.log('QQ Asset Zone Map: INITIALIZED');
    }
    
    initializeMap() {
        // Initialize with Fort Worth center
        this.map = L.map('map-container', {
            center: [32.7767, -97.1970],
            zoom: 11,
            zoomControl: true,
            attributionControl: true
        });
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add scale control
        L.control.scale().addTo(this.map);
    }
    
    addZoneOverlays() {
        Object.entries(this.fortWorthZones).forEach(([zoneId, zone]) => {
            // Create zone circle
            const circle = L.circle([zone.center_lat, zone.center_lng], {
                radius: zone.radius_meters,
                fillColor: zone.zone_color,
                color: zone.zone_color,
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.2
            }).addTo(this.map);
            
            // Zone popup with payroll information
            const popupContent = `
                <div class="zone-popup">
                    <h6>${zone.name}</h6>
                    <p><strong>Payroll Rate:</strong> ${zone.payroll_rate}/hour</p>
                    <p><strong>Zone Radius:</strong> ${zone.radius_meters}m</p>
                    <div class="zone-assets" id="zone-assets-${zoneId}">
                        <p>Loading assets...</p>
                    </div>
                </div>
            `;
            
            circle.bindPopup(popupContent);
            this.zoneCircles[zoneId] = circle;
            
            // Update zone assets when popup opens
            circle.on('popupopen', () => {
                this.updateZoneAssetsList(zoneId);
            });
        });
    }
    
    addAssetMarkers() {
        this.activeAssets.forEach(asset => {
            const zone = this.fortWorthZones[asset.assigned_zone];
            const isInZone = asset.zone_status === 'in_zone';
            
            // Create custom marker icon based on zone status
            const iconColor = isInZone ? zone.zone_color : '#95a5a6';
            const markerIcon = L.divIcon({
                html: `
                    <div class="asset-marker" style="background-color: ${iconColor}">
                        <span>${asset.AssetIdentifier}</span>
                        <div class="zone-indicator ${isInZone ? 'in-zone' : 'out-zone'}"></div>
                    </div>
                `,
                className: 'custom-asset-marker',
                iconSize: [50, 50],
                iconAnchor: [25, 25]
            });
            
            const marker = L.marker([asset.Latitude, asset.Longitude], {
                icon: markerIcon
            }).addTo(this.map);
            
            // Asset popup with zone and payroll information
            const popupContent = `
                <div class="asset-popup">
                    <h6>${asset.Label}</h6>
                    <p><strong>Status:</strong> <span class="${asset.Active ? 'status-active' : 'status-inactive'}">${asset.Active ? 'Active' : 'Inactive'}</span></p>
                    <p><strong>Operator:</strong> ${asset.operator}</p>
                    <p><strong>Zone:</strong> ${zone.name}</p>
                    <p><strong>Zone Status:</strong> <span class="zone-status-${asset.zone_status}">${asset.zone_status.replace('_', ' ').toUpperCase()}</span></p>
                    <p><strong>Hourly Rate:</strong> $$${asset.hourly_rate}/hour</p>
                    <p><strong>Location:</strong> ${asset.Location}</p>
                    <div class="asset-actions">
                        <button onclick="qqAssetMap.centerOnAsset('${asset.AssetIdentifier}')" class="btn-small">Center</button>
                        <button onclick="qqAssetMap.viewAssetDetails('${asset.AssetIdentifier}')" class="btn-small">Details</button>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            this.assetMarkers[asset.AssetIdentifier] = marker;
        });
    }
    
    updateZoneAssetsList(zoneId) {
        const zoneAssets = this.activeAssets.filter(asset => asset.assigned_zone === zoneId);
        const container = document.getElementById(`zone-assets-${zoneId}`);
        
        if (container && zoneAssets.length > 0) {
            const assetsHtml = zoneAssets.map(asset => `
                <div class="zone-asset-item">
                    <span class="asset-id">${asset.AssetIdentifier}</span>
                    <span class="asset-operator">${asset.operator}</span>
                    <span class="asset-status ${asset.Active ? 'active' : 'inactive'}">${asset.Active ? 'Active' : 'Inactive'}</span>
                </div>
            `).join('');
            
            container.innerHTML = `
                <h6>Assets in Zone (${zoneAssets.length})</h6>
                ${assetsHtml}
            `;
        }
    }
    
    centerOnAsset(assetId) {
        const asset = this.activeAssets.find(a => a.AssetIdentifier === assetId);
        if (asset && this.assetMarkers[assetId]) {
            this.map.setView([asset.Latitude, asset.Longitude], 15);
            this.assetMarkers[assetId].openPopup();
        }
    }
    
    viewAssetDetails(assetId) {
        const asset = this.activeAssets.find(a => a.AssetIdentifier === assetId);
        if (asset) {
            // Open asset details in new window or modal
            window.open(`/asset/${assetId}`, '_blank');
        }
    }
    
    setupRealTimeUpdates() {
        // Update asset positions every 30 seconds
        setInterval(() => {
            this.refreshAssetData();
        }, 30000);
    }
    
    refreshAssetData() {
        fetch('/api/fort-worth-assets')
            .then(response => response.json())
            .then(data => {
                this.updateAssetPositions(data);
            })
            .catch(error => console.error('Asset update error:', error));
    }
    
    updateAssetPositions(newAssetData) {
        newAssetData.forEach(asset => {
            if (this.assetMarkers[asset.AssetIdentifier]) {
                // Update marker position
                const marker = this.assetMarkers[asset.AssetIdentifier];
                marker.setLatLng([asset.Latitude, asset.Longitude]);
                
                // Update zone status if changed
                if (asset.zone_status !== this.activeAssets.find(a => a.AssetIdentifier === asset.AssetIdentifier)?.zone_status) {
                    this.updateAssetMarkerStyle(asset);
                }
            }
        });
        
        // Update internal asset data
        this.activeAssets = newAssetData;
    }
    
    updateAssetMarkerStyle(asset) {
        const zone = this.fortWorthZones[asset.assigned_zone];
        const isInZone = asset.zone_status === 'in_zone';
        const iconColor = isInZone ? zone.zone_color : '#95a5a6';
        
        const newIcon = L.divIcon({
            html: `
                <div class="asset-marker" style="background-color: ${iconColor}">
                    <span>${asset.AssetIdentifier}</span>
                    <div class="zone-indicator ${isInZone ? 'in-zone' : 'out-zone'}"></div>
                </div>
            `,
            className: 'custom-asset-marker',
            iconSize: [50, 50],
            iconAnchor: [25, 25]
        });
        
        this.assetMarkers[asset.AssetIdentifier].setIcon(newIcon);
    }
}

// Initialize QQ Asset Zone Map when map container exists
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('map-container')) {
        window.qqAssetMap = new QQAssetZoneMap();
    }
});

// CSS for enhanced styling
const mapStyles = `
<style>
.asset-marker {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    border: 3px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 10px;
    position: relative;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.zone-indicator {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid white;
}

.zone-indicator.in-zone {
    background-color: #27ae60;
}

.zone-indicator.out-zone {
    background-color: #e74c3c;
}

.asset-popup, .zone-popup {
    min-width: 200px;
}

.asset-popup h6, .zone-popup h6 {
    margin: 0 0 10px 0;
    color: #2c3e50;
    border-bottom: 1px solid #ecf0f1;
    padding-bottom: 5px;
}

.status-active {
    color: #27ae60;
    font-weight: bold;
}

.status-inactive {
    color: #e74c3c;
    font-weight: bold;
}

.zone-status-in_zone {
    color: #27ae60;
    font-weight: bold;
}

.zone-status-out_of_zone {
    color: #e74c3c;
    font-weight: bold;
}

.asset-actions {
    margin-top: 10px;
    display: flex;
    gap: 5px;
}

.btn-small {
    padding: 4px 8px;
    font-size: 12px;
    border: none;
    border-radius: 4px;
    background: #3498db;
    color: white;
    cursor: pointer;
}

.btn-small:hover {
    background: #2980b9;
}

.zone-asset-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid #ecf0f1;
    font-size: 12px;
}

.asset-id {
    font-weight: bold;
    color: #2c3e50;
}

.asset-status.active {
    color: #27ae60;
}

.asset-status.inactive {
    color: #e74c3c;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', mapStyles);
