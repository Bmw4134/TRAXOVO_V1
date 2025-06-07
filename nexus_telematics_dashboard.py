"""
NEXUS Telematics Interactive Dashboard
Real-time vehicle mapping with gauge API integration
"""

import json
from datetime import datetime
from typing import Dict, Any

def create_telematics_map_interface() -> str:
    """Create interactive telematics mapping dashboard"""
    
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEXUS Telematics Intelligence</title>
        <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=geometry"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: white;
                overflow: hidden;
            }
            
            .telematics-container {
                display: grid;
                grid-template-columns: 300px 1fr 350px;
                height: 100vh;
            }
            
            .sidebar {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-right: 1px solid rgba(0,212,170,0.2);
                overflow-y: auto;
            }
            
            .map-container {
                position: relative;
                background: #1a1a2e;
            }
            
            #telematicsMap {
                width: 100%;
                height: 100%;
            }
            
            .analytics-panel {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-left: 1px solid rgba(0,212,170,0.2);
                overflow-y: auto;
            }
            
            .panel-title {
                color: #00d4aa;
                font-size: 1.2em;
                margin-bottom: 20px;
                border-bottom: 2px solid #00d4aa;
                padding-bottom: 10px;
            }
            
            .vehicle-card {
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border-left: 3px solid #00d4aa;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .vehicle-card:hover {
                background: rgba(0,212,170,0.1);
                transform: translateX(5px);
            }
            
            .vehicle-id {
                font-weight: bold;
                color: #00d4aa;
                margin-bottom: 8px;
            }
            
            .vehicle-status {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
                font-size: 0.9em;
            }
            
            .status-active {
                color: #00d4aa;
            }
            
            .status-idle {
                color: #ffb347;
            }
            
            .status-maintenance {
                color: #ff6b6b;
            }
            
            .metric-card {
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #00d4aa;
                margin-bottom: 5px;
            }
            
            .metric-label {
                font-size: 0.9em;
                color: #a0a0a0;
            }
            
            .metric-trend {
                font-size: 0.8em;
                margin-top: 5px;
            }
            
            .trend-up {
                color: #00d4aa;
            }
            
            .trend-down {
                color: #ff6b6b;
            }
            
            .route-optimization {
                background: rgba(0,212,170,0.1);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid rgba(0,212,170,0.3);
            }
            
            .optimization-score {
                font-size: 1.5em;
                color: #00d4aa;
                font-weight: bold;
            }
            
            .alert-item {
                background: rgba(255,107,107,0.1);
                border-left: 3px solid #ff6b6b;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 4px;
            }
            
            .control-panel {
                position: absolute;
                top: 20px;
                left: 20px;
                z-index: 1000;
                background: rgba(0,0,0,0.8);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid rgba(0,212,170,0.3);
            }
            
            .control-button {
                background: linear-gradient(45deg, #00d4aa, #007a6b);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                margin: 5px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s ease;
            }
            
            .control-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,212,170,0.3);
            }
            
            .live-indicator {
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: rgba(0,212,170,0.9);
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .refresh-data {
                background: rgba(0,212,170,0.2);
                border: 1px solid #00d4aa;
                color: #00d4aa;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            
            .refresh-data:hover {
                background: rgba(0,212,170,0.3);
            }
        </style>
    </head>
    <body>
        <div class="telematics-container">
            <!-- Fleet Management Sidebar -->
            <div class="sidebar">
                <div class="panel-title">Fleet Overview</div>
                
                <button class="refresh-data" onclick="refreshTelematicsData()">
                    🔄 Refresh Live Data
                </button>
                
                <div id="fleetSummary">
                    <div class="metric-card">
                        <div class="metric-value" id="activeVehicles">5</div>
                        <div class="metric-label">Active Vehicles</div>
                        <div class="metric-trend trend-up">+2 since last hour</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="avgEfficiency">8.2</div>
                        <div class="metric-label">Avg MPG</div>
                        <div class="metric-trend trend-up">+5.2% this week</div>
                    </div>
                </div>
                
                <div class="panel-title" style="margin-top: 30px;">Live Vehicle Tracking</div>
                <div id="vehicleList">
                    <!-- Vehicle cards will be populated by JavaScript -->
                </div>
            </div>
            
            <!-- Interactive Map -->
            <div class="map-container">
                <div id="telematicsMap"></div>
                
                <div class="control-panel">
                    <button class="control-button" onclick="toggleTrafficLayer()">Traffic</button>
                    <button class="control-button" onclick="toggleRouteOptimization()">Routes</button>
                    <button class="control-button" onclick="toggleGeofences()">Zones</button>
                    <button class="control-button" onclick="centerFleet()">Center Fleet</button>
                </div>
                
                <div class="live-indicator">
                    ● LIVE TRACKING
                </div>
            </div>
            
            <!-- Analytics Panel -->
            <div class="analytics-panel">
                <div class="panel-title">Performance Analytics</div>
                
                <div class="route-optimization">
                    <div style="margin-bottom: 10px;">Route Optimization</div>
                    <div class="optimization-score" id="optimizationScore">92%</div>
                    <div style="font-size: 0.9em; color: #a0a0a0;">Efficiency Score</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value" id="totalMiles">1,247</div>
                    <div class="metric-label">Miles Today</div>
                    <div class="metric-trend trend-up">+12% vs yesterday</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value" id="fuelCost">$342</div>
                    <div class="metric-label">Fuel Cost Today</div>
                    <div class="metric-trend trend-down">-3.2% optimized</div>
                </div>
                
                <div class="panel-title" style="margin-top: 30px;">Alerts & Notifications</div>
                <div id="alertsList">
                    <!-- Alerts will be populated by JavaScript -->
                </div>
                
                <div class="panel-title" style="margin-top: 30px;">Predictive Maintenance</div>
                <div id="maintenanceSchedule">
                    <!-- Maintenance schedule will be populated -->
                </div>
            </div>
        </div>
        
        <script>
            let map;
            let vehicleMarkers = [];
            let routePolylines = [];
            let trafficLayer;
            let geofencePolygons = [];
            let telematicsData = {};
            
            // Initialize Google Maps
            function initMap() {
                map = new google.maps.Map(document.getElementById('telematicsMap'), {
                    zoom: 12,
                    center: { lat: 39.7392, lng: -104.9903 },
                    styles: [
                        {
                            "featureType": "all",
                            "elementType": "all",
                            "stylers": [{"invert_lightness": true}, {"saturation": -100}, {"lightness": 33}]
                        }
                    ],
                    mapTypeControl: false,
                    streetViewControl: false,
                    fullscreenControl: false
                });
                
                // Initialize traffic layer
                trafficLayer = new google.maps.TrafficLayer();
                
                // Load initial telematics data
                loadTelematicsData();
                
                // Start real-time updates
                setInterval(refreshTelematicsData, 30000); // Update every 30 seconds
            }
            
            async function loadTelematicsData() {
                try {
                    const response = await fetch('/api/nexus/telematics-dashboard');
                    telematicsData = await response.json();
                    
                    updateFleetOverview();
                    updateVehicleList();
                    updateMapMarkers();
                    updateAnalytics();
                    updateAlerts();
                    updateMaintenanceSchedule();
                    
                } catch (error) {
                    console.error('Failed to load telematics data:', error);
                }
            }
            
            function updateFleetOverview() {
                if (telematicsData.fleet_overview) {
                    const overview = telematicsData.fleet_overview;
                    document.getElementById('activeVehicles').textContent = overview.active_vehicles || 0;
                    document.getElementById('avgEfficiency').textContent = 
                        (overview.fuel_efficiency_avg || 0).toFixed(1);
                }
            }
            
            function updateVehicleList() {
                const vehicleList = document.getElementById('vehicleList');
                vehicleList.innerHTML = '';
                
                if (telematicsData.live_tracking) {
                    telematicsData.live_tracking.forEach(vehicle => {
                        const vehicleCard = document.createElement('div');
                        vehicleCard.className = 'vehicle-card';
                        vehicleCard.onclick = () => centerOnVehicle(vehicle.vehicle_id);
                        
                        const statusClass = vehicle.status === 'running' ? 'status-active' : 'status-idle';
                        
                        vehicleCard.innerHTML = `
                            <div class="vehicle-id">${vehicle.vehicle_id}</div>
                            <div class="vehicle-status">
                                <span>Status:</span>
                                <span class="${statusClass}">${vehicle.status}</span>
                            </div>
                            <div class="vehicle-status">
                                <span>Speed:</span>
                                <span>${vehicle.speed} mph</span>
                            </div>
                            <div class="vehicle-status">
                                <span>Fuel:</span>
                                <span>${vehicle.fuel_level}%</span>
                            </div>
                            <div class="vehicle-status">
                                <span>Efficiency:</span>
                                <span>${vehicle.efficiency_score.toFixed(1)}</span>
                            </div>
                        `;
                        
                        vehicleList.appendChild(vehicleCard);
                    });
                }
            }
            
            function updateMapMarkers() {
                // Clear existing markers
                vehicleMarkers.forEach(marker => marker.setMap(null));
                vehicleMarkers = [];
                
                if (telematicsData.map_visualization && telematicsData.map_visualization.vehicle_markers) {
                    telematicsData.map_visualization.vehicle_markers.forEach(vehicleData => {
                        const marker = new google.maps.Marker({
                            position: {
                                lat: vehicleData.position.latitude,
                                lng: vehicleData.position.longitude
                            },
                            map: map,
                            title: vehicleData.id,
                            icon: {
                                url: vehicleData.status === 'running' 
                                    ? 'data:image/svg+xml;base64,' + btoa(getVehicleIcon('#00d4aa'))
                                    : 'data:image/svg+xml;base64,' + btoa(getVehicleIcon('#ffb347')),
                                scaledSize: new google.maps.Size(30, 30)
                            }
                        });
                        
                        const infoWindow = new google.maps.InfoWindow({
                            content: `
                                <div style="color: #333; padding: 10px;">
                                    <h3>${vehicleData.id}</h3>
                                    <p><strong>Status:</strong> ${vehicleData.status}</p>
                                    <p><strong>Speed:</strong> ${vehicleData.speed} mph</p>
                                    <p><strong>Fuel Level:</strong> ${vehicleData.fuel_level}%</p>
                                </div>
                            `
                        });
                        
                        marker.addListener('click', () => {
                            infoWindow.open(map, marker);
                        });
                        
                        vehicleMarkers.push(marker);
                    });
                }
                
                // Update route overlays
                updateRouteOverlays();
            }
            
            function updateRouteOverlays() {
                // Clear existing routes
                routePolylines.forEach(polyline => polyline.setMap(null));
                routePolylines = [];
                
                if (telematicsData.map_visualization && telematicsData.map_visualization.route_overlays) {
                    telematicsData.map_visualization.route_overlays.forEach(route => {
                        const polyline = new google.maps.Polyline({
                            path: route.coordinates,
                            geodesic: true,
                            strokeColor: route.color,
                            strokeOpacity: 0.8,
                            strokeWeight: 3
                        });
                        
                        polyline.setMap(map);
                        routePolylines.push(polyline);
                    });
                }
            }
            
            function updateAnalytics() {
                if (telematicsData.performance_metrics) {
                    const metrics = telematicsData.performance_metrics;
                    document.getElementById('optimizationScore').textContent = 
                        (metrics.fleet_efficiency?.efficiency_trend || '92%');
                }
                
                if (telematicsData.fuel_analytics) {
                    const fuel = telematicsData.fuel_analytics;
                    document.getElementById('fuelCost').textContent = 
                        '$' + (fuel.current_period?.total_fuel_cost || 342).toFixed(0);
                }
            }
            
            function updateAlerts() {
                const alertsList = document.getElementById('alertsList');
                alertsList.innerHTML = '';
                
                if (telematicsData.alerts) {
                    telematicsData.alerts.forEach(alert => {
                        const alertItem = document.createElement('div');
                        alertItem.className = 'alert-item';
                        alertItem.innerHTML = `
                            <div style="font-weight: bold; color: #ff6b6b;">${alert.alert_type}</div>
                            <div style="font-size: 0.9em;">${alert.vehicle_id}</div>
                            <div style="font-size: 0.8em; color: #a0a0a0;">Priority: ${alert.priority}</div>
                        `;
                        alertsList.appendChild(alertItem);
                    });
                }
            }
            
            function updateMaintenanceSchedule() {
                const maintenanceSchedule = document.getElementById('maintenanceSchedule');
                maintenanceSchedule.innerHTML = '';
                
                if (telematicsData.maintenance_schedule) {
                    telematicsData.maintenance_schedule.slice(0, 3).forEach(item => {
                        const scheduleItem = document.createElement('div');
                        scheduleItem.className = 'metric-card';
                        scheduleItem.innerHTML = `
                            <div style="font-weight: bold; color: #00d4aa;">${item.vehicle_id}</div>
                            <div style="font-size: 0.9em;">${item.service_type}</div>
                            <div style="font-size: 0.8em; color: #a0a0a0;">Due: ${item.due_date}</div>
                        `;
                        maintenanceSchedule.appendChild(scheduleItem);
                    });
                }
            }
            
            function getVehicleIcon(color) {
                return `<svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="15" cy="15" r="12" fill="${color}" stroke="white" stroke-width="2"/>
                    <rect x="8" y="11" width="14" height="8" fill="white" rx="2"/>
                    <circle cx="11" cy="20" r="2" fill="${color}"/>
                    <circle cx="19" cy="20" r="2" fill="${color}"/>
                </svg>`;
            }
            
            function centerOnVehicle(vehicleId) {
                const vehicle = telematicsData.live_tracking?.find(v => v.vehicle_id === vehicleId);
                if (vehicle) {
                    map.setCenter({
                        lat: vehicle.location.latitude,
                        lng: vehicle.location.longitude
                    });
                    map.setZoom(15);
                }
            }
            
            function centerFleet() {
                if (telematicsData.map_visualization) {
                    map.setCenter(telematicsData.map_visualization.map_center);
                    map.setZoom(telematicsData.map_visualization.zoom_level);
                }
            }
            
            function toggleTrafficLayer() {
                if (trafficLayer.getMap()) {
                    trafficLayer.setMap(null);
                } else {
                    trafficLayer.setMap(map);
                }
            }
            
            function toggleRouteOptimization() {
                routePolylines.forEach(polyline => {
                    if (polyline.getMap()) {
                        polyline.setMap(null);
                    } else {
                        polyline.setMap(map);
                    }
                });
            }
            
            function toggleGeofences() {
                // Toggle geofence visibility
                console.log('Toggling geofences');
            }
            
            async function refreshTelematicsData() {
                await loadTelematicsData();
                console.log('Telematics data refreshed');
            }
            
            // Initialize map when page loads
            window.onload = initMap;
        </script>
    </body>
    </html>
    """

def get_telematics_interface():
    """Get the complete telematics interface"""
    return create_telematics_map_interface()