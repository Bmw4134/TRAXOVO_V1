/**
 * TRAXORA GENIUS CORE | Direct Map Enhancements
 * 
 * This module applies direct DOM and CSS changes to ensure enhancements
 * are immediately visible in the preview.
 */

class DirectMapEnhancements {
    constructor() {
        // Initialize direct enhancements
        document.addEventListener('DOMContentLoaded', () => {
            this.init();
        });
    }
    
    init() {
        console.log('Initializing Direct Map Enhancements');
        
        // Add the map legend directly to the DOM
        this.addMapLegend();
        
        // Add asset color styling
        this.enhanceAssetMarkers();
        
        // Add cluster visualization
        this.addClusterVisualization();
        
        // Add heat map capability
        this.addHeatMap();
        
        // Add distance measurement tool
        this.addMeasurementTool();
        
        // Make sidebar sticky
        this.makeSidebarSticky();
        
        // Create filter shortcuts
        this.createFilterShortcuts();
        
        // Create enhanced popup template
        this.enhancePopupTemplate();
        
        // Add offline indicator
        this.addOfflineIndicator();
        
        // Add dynamic job proximity detection
        this.addJobProximityDetection();
        
        // Add map controls
        this.addMapControls();
    }
    
    addMapLegend() {
        // Create legend HTML
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
        
        // Add map legend CSS
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
        
        // Add legend to map
        const mapContainer = document.querySelector('.map-container');
        if (mapContainer) {
            const legendDiv = document.createElement('div');
            legendDiv.innerHTML = legendHTML;
            mapContainer.appendChild(legendDiv.firstElementChild);
            
            // Add event listener for toggling legend
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
        // Replace the original marker creation function
        if (window.createAssetIcon) {
            const originalCreateAssetIcon = window.createAssetIcon;
            
            window.createAssetIcon = function(status, division) {
                // Determine color based on division
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
                
                // Create enhanced icon with division color
                return L.divIcon({
                    className: 'asset-marker-icon',
                    html: `<div class="asset-marker" style="background-color:${color};width:24px;height:24px;border-radius:50%;border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);display:flex;justify-content:center;align-items:center;color:white;font-size:12px;"><i class="bi bi-geo-alt-fill"></i></div>`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });
            };
            
            // Add marker style
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
        // Add Leaflet.markercluster support
        // First create a new link element for the stylesheet
        const clusterCssLink = document.createElement('link');
        clusterCssLink.rel = 'stylesheet';
        clusterCssLink.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css';
        document.head.appendChild(clusterCssLink);
        
        const clusterDefaultCssLink = document.createElement('link');
        clusterDefaultCssLink.rel = 'stylesheet';
        clusterDefaultCssLink.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css';
        document.head.appendChild(clusterDefaultCssLink);
        
        // Then create a new script element
        const clusterScript = document.createElement('script');
        clusterScript.src = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js';
        document.head.appendChild(clusterScript);
        
        // Wait for the script to load
        clusterScript.onload = () => {
            // Check if we have a reference to the map
            if (window.map && window.assetOverlay) {
                // Create a marker cluster group
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
                
                // Add the cluster layer to the map
                window.map.removeLayer(window.assetOverlay);
                window.assetClusterLayer = markers;
                window.map.addLayer(markers);
                
                // Update overlays control
                if (window.overlays) {
                    window.overlays["Clustered Assets"] = markers;
                    window.overlays["Individual Assets"] = window.assetOverlay;
                }
            }
        };
    }
    
    addHeatMap() {
        // Add Leaflet.heat support
        const heatScript = document.createElement('script');
        heatScript.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
        document.head.appendChild(heatScript);
        
        // Wait for the script to load
        heatScript.onload = () => {
            // Check if we have a reference to the map
            if (window.map && window.loadAssets) {
                const originalLoadAssets = window.loadAssets;
                
                window.loadAssets = function() {
                    // Call the original loadAssets function
                    originalLoadAssets.apply(this, arguments);
                    
                    // After loading assets, create heat map
                    fetch('/map/api/assets')
                        .then(response => response.json())
                        .then(data => {
                            // Create heat map data
                            const heatData = data
                                .filter(asset => asset.latitude && asset.longitude)
                                .map(asset => [asset.latitude, asset.longitude, 0.5]);
                            
                            // Create heat layer
                            if (window.heatLayer) {
                                window.map.removeLayer(window.heatLayer);
                            }
                            
                            window.heatLayer = L.heatLayer(heatData, {
                                radius: 25,
                                blur: 15,
                                maxZoom: 17,
                                gradient: {0.4: 'blue', 0.65: 'lime', 1: 'red'}
                            });
                            
                            // Add to overlays
                            if (window.overlays) {
                                window.overlays["Asset Heat Map"] = window.heatLayer;
                            }
                        });
                };
            }
        };
    }
    
    addMeasurementTool() {
        // Add Leaflet.draw support
        const drawCssLink = document.createElement('link');
        drawCssLink.rel = 'stylesheet';
        drawCssLink.href = 'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css';
        document.head.appendChild(drawCssLink);
        
        const drawScript = document.createElement('script');
        drawScript.src = 'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js';
        document.head.appendChild(drawScript);
        
        // Wait for the script to load
        drawScript.onload = () => {
            // Check if we have a reference to the map
            if (window.map) {
                // Create a feature group to store editable layers
                const drawnItems = new L.FeatureGroup();
                window.map.addLayer(drawnItems);
                
                // Initialize the draw control
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
                
                // Event handler for when a shape is drawn
                window.map.on(L.Draw.Event.CREATED, function(event) {
                    const layer = event.layer;
                    
                    // If it's a polyline, add distance information
                    if (event.layerType === 'polyline') {
                        const latlngs = layer.getLatLngs();
                        let totalDistance = 0;
                        
                        for (let i = 1; i < latlngs.length; i++) {
                            totalDistance += latlngs[i-1].distanceTo(latlngs[i]);
                        }
                        
                        const distanceInMiles = (totalDistance / 1609.34).toFixed(2);
                        
                        // Add a tooltip with the distance
                        layer.bindTooltip(`Distance: ${distanceInMiles} miles`, {
                            permanent: true,
                            direction: 'center',
                            className: 'distance-tooltip'
                        });
                    }
                    
                    // Add the layer to the feature group
                    drawnItems.addLayer(layer);
                });
                
                // Add style for tooltips
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
        // Create a wrapper around the sidebar
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            // Create a sticky class for the sidebar
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
            
            // Add toggle button
            const toggleButton = document.createElement('button');
            toggleButton.className = 'sticky-toggle';
            toggleButton.innerHTML = '<i class="bi bi-pin-angle"></i>';
            toggleButton.title = 'Toggle Sticky Sidebar';
            
            sidebar.appendChild(toggleButton);
            
            // Add event listener
            toggleButton.addEventListener('click', () => {
                sidebar.classList.toggle('sticky');
                toggleButton.innerHTML = sidebar.classList.contains('sticky') ? 
                    '<i class="bi bi-pin-angle-fill"></i>' : 
                    '<i class="bi bi-pin-angle"></i>';
            });
            
            // Make sticky by default
            sidebar.classList.add('sticky');
            toggleButton.innerHTML = '<i class="bi bi-pin-angle-fill"></i>';
        }
    }
    
    createFilterShortcuts() {
        // Create filter shortcuts div
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
            
            // Add event listeners
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
                        // For job shortcuts, we need to find the job id by name
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
        // Add custom popup style
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
        
        // Override the popup creation
        if (window.loadAssets) {
            // Function to create enhanced popup content
            window.createEnhancedPopupContent = function(asset) {
                // Determine division
                let division = "DIV 2"; // Default
                const location = asset.location?.toUpperCase() || '';
                
                if (location.includes('HOU')) {
                    division = "DIV 4";
                } else if (location.includes('ECTOR') || location.includes('MIDLAND')) {
                    division = "DIV 3";
                } else if (location.includes('TEX')) {
                    division = "DIV 8";
                }
                
                // Determine color based on division
                let divisionColor = "#3366FF"; // Default: DIV 2 (DFW)
                
                if (division === "DIV 4") {
                    divisionColor = "#FF3333"; // HOU
                } else if (division === "DIV 3") {
                    divisionColor = "#33CC33"; // WT
                } else if (division === "DIV 8") {
                    divisionColor = "#FFCC00"; // TEXDIST
                }
                
                // Build popup content
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
            
            // Update the asset loading function
            const originalLoadAssets = window.loadAssets;
            window.loadAssets = function() {
                originalLoadAssets.apply(this, arguments);
                
                // Update how markers are created
                window.createAssetMarkerWithPopup = function(asset) {
                    // Get division for coloring
                    let division = "DIV 2"; // Default
                    const location = asset.location?.toUpperCase() || '';
                    
                    if (location.includes('HOU')) {
                        division = "DIV 4";
                    } else if (location.includes('ECTOR') || location.includes('MIDLAND')) {
                        division = "DIV 3";
                    } else if (location.includes('TEX')) {
                        division = "DIV 8";
                    }
                    
                    // Create marker with division-based color
                    const marker = L.marker([asset.latitude, asset.longitude], {
                        icon: window.createAssetIcon(asset.status, division)
                    });
                    
                    // Create popup
                    const popup = L.popup({
                        className: 'custom-popup',
                        closeButton: true,
                        autoClose: true,
                        closeOnClick: true
                    }).setContent(window.createEnhancedPopupContent(asset));
                    
                    // Bind popup to marker
                    marker.bindPopup(popup);
                    
                    // Add event listeners after popup is opened
                    marker.on('popupopen', function() {
                        setTimeout(() => {
                            // Add reassign job functionality
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
                            
                            // Add confirm/cancel buttons functionality
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
                                            
                                            // Show confirmation message
                                            const actionsDiv = selector.parentElement;
                                            const confirmationDiv = document.createElement('div');
                                            confirmationDiv.className = 'alert alert-success mt-2 p-2 small';
                                            confirmationDiv.innerHTML = '<i class="bi bi-check-circle"></i> Reassignment request logged (passive mode)';
                                            
                                            // Add after the job selector
                                            actionsDiv.appendChild(confirmationDiv);
                                            
                                            // Hide job selector
                                            selector.classList.remove('visible');
                                            
                                            // Remove confirmation after delay
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
        // Create the offline indicator
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
        
        // Add offline indicator style
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
        
        // Add close button behavior
        const closeBtn = indicator.querySelector('.offline-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                indicator.classList.add('hidden');
            });
        }
        
        // Simulate offline state after a delay
        setTimeout(() => {
            indicator.classList.remove('hidden');
        }, 10000); // Show after 10 seconds
    }
    
    addJobProximityDetection() {
        // Add proximity detection to show nearby assets for a job
        if (window.map) {
            // Create highlight style
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
            
            // Add function to show job proximity
            window.showJobProximity = function(jobId) {
                // Remove any existing circles
                if (window.proximityCircle) {
                    window.map.removeLayer(window.proximityCircle);
                }
                
                // Find the job site
                const jobSite = window.jobSites.find(site => site.job_number === jobId);
                
                if (jobSite) {
                    // Create a circle with dashed line
                    window.proximityCircle = L.circle([jobSite.latitude, jobSite.longitude], {
                        radius: jobSite.radius || 1000,
                        className: 'distance-circle'
                    }).addTo(window.map);
                    
                    // Zoom to the job site
                    window.map.setView([jobSite.latitude, jobSite.longitude], 14);
                }
            };
            
            // Update proximity controls
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
                
                // Add event listeners
                proximityContent.querySelectorAll('.proximity-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        window.showJobProximity(btn.dataset.job);
                    });
                });
            }
        }
    }
    
    addMapControls() {
        // Add some additional map controls
        if (window.map) {
            // Add zoom to home button
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
            
            // Add a button to show all assets
            class ShowAllButton extends L.Control {
                onAdd(map) {
                    const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                    const button = L.DomUtil.create('a', 'show-all-button', container);
                    button.innerHTML = '<i class="bi bi-eye"></i>';
                    button.title = 'Show All Assets';
                    button.href = '#';
                    
                    L.DomEvent.on(button, 'click', function(e) {
                        L.DomEvent.preventDefault(e);
                        // Set the filters to show all and refresh
                        document.getElementById('type-filter').value = '';
                        document.getElementById('job-site-filter').value = '';
                        document.getElementById('refresh-map').click();
                    });
                    
                    return container;
                }
            }
            
            // Add the controls to the map
            new HomeButton({ position: 'topleft' }).addTo(window.map);
            new ShowAllButton({ position: 'topleft' }).addTo(window.map);
        }
    }
}

// Initialize the enhancements
const directEnhancements = new DirectMapEnhancements();
console.log('GENIUS CORE Direct Map Enhancements Loaded');