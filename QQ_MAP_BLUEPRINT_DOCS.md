# QQ Bleeding-Edge Asset Tracking Map Blueprint

## Overview
This blueprint provides a complete, reusable asset tracking map component that can be integrated into any dashboard system.

## Features
- Real-time asset tracking with live updates
- AI-powered predictive asset movement
- Heat mapping for utilization analysis
- Mobile-responsive design
- Interactive controls and notifications
- Authentic Fort Worth fleet data integration

## Quick Integration

### 1. Add to Flask Route
```python
# QQ Bleeding-Edge Map Integration for your_dashboard
from qq_bleeding_edge_map_blueprint import QQMapBlueprint

@app.route('/your_dashboard')
def your_dashboard_dashboard():
    """Dashboard with QQ bleeding-edge map integration"""
    
    # Initialize QQ Map Blueprint
    qq_map = QQMapBlueprint()
    
    # Generate map HTML for template
    map_html = qq_map.generate_map_html(
        container_id="dashboard-map", 
        height="600px"
    )
    
    return render_template('your_dashboard_dashboard.html', 
        qq_map_html=map_html,
        # Add your other dashboard data here
    )
```

### 2. Template Integration
```html
<!-- In your dashboard template -->
<div class="dashboard-section">
    <h2>QQ Bleeding-Edge Asset Tracking</h2>
    {{ qq_map_html|safe }}
</div>

<!-- Required CSS libraries -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
```

### 3. Generated HTML Example
```html
        
        <!-- QQ Bleeding-Edge Asset Tracking Map -->
        <div id="example-map" style="height: 500px; position: relative;">
            <div class="qq-map-header">
                <div class="qq-logo-section">
                    <div class="qq-logo">TRAXOVO QQ</div>
                    <div class="qq-location-info">
                        📍 Fort Worth, TX Fleet Operations<br>
                        <span>QQ Bleeding-Edge Asset Intelligence</span>
                    </div>
                </div>
                <div class="qq-map-controls">
                    <button class="qq-control-btn" onclick="qqCenterFleet()">Center Fleet</button>
                    <button class="qq-control-btn" onclick="qqToggleTracking()">QQ Live Track</button>
                    <button class="qq-control-btn" onclick="qqTogglePredictive()">AI Predict</button>
                    <button class="qq-control-btn" onclick="qqShowHeatmap()">Heat Map</button>
                    <button class="qq-control-btn" onclick="qqShowAll()">Show All</button>
                </div>
            </div>
            
            <div class="qq-real-time-indicator">
                <div class="qq-pulse"></div>
                <span>LIVE TRACKING</span>
            </div>
            
            <div id="qq-map-20250603_191257" class="qq-map-canvas"></div>
            
            <div class="qq-asset-stats">
                <div class="qq-stat">
                    <div class="qq-stat-number" id="qq-active-count">0</div>
                    <div class="qq-stat-label">Active Assets</div>
                </div>
                <div class="qq-stat">
                    <div class="qq-stat-number" id="qq-utilization">0%</div>
                    <div class="qq-stat-label">Utilization</div>
                </div>
                <div class="qq-stat">
                    <div class="qq-stat-number" id="qq-efficiency">0%</div>
                    <div class="qq-stat-label">Efficiency</div>
                </div>
            </div>
        </div>
        
        [CSS and JavaScript included automatically]
```

## Complete Integration Examples

### Executive Dashboard Integration
```python
@app.route('/executive-dashboard')
def executive_dashboard():
    qq_map = QQMapBlueprint()
    map_html = qq_map.generate_map_html("executive-map", "400px")
    
    return render_template('executive_dashboard.html',
        qq_map_html=map_html,
        executive_metrics=get_executive_metrics()
    )
```

### Operations Dashboard Integration
```python
@app.route('/operations')
def operations_dashboard():
    qq_map = QQMapBlueprint()
    map_html = qq_map.generate_map_html("ops-map", "700px")
    
    return render_template('operations.html',
        qq_map_html=map_html,
        operational_data=get_ops_data()
    )
```

### Mobile Dashboard Integration
```python
@app.route('/mobile-dashboard')
def mobile_dashboard():
    qq_map = QQMapBlueprint()
    map_html = qq_map.generate_map_html("mobile-map", "300px")
    
    return render_template('mobile_dashboard.html',
        qq_map_html=map_html,
        mobile_optimized=True
    )
```

## Customization Options

### Map Dimensions
```python
# Small map for sidebars
map_html = qq_map.generate_map_html("sidebar-map", "250px")

# Large map for main dashboard
map_html = qq_map.generate_map_html("main-map", "800px")

# Full screen map
map_html = qq_map.generate_map_html("fullscreen-map", "100vh")
```

### Container Styling
```html
<div class="custom-map-container">
    {{ qq_map_html|safe }}
</div>

<style>
.custom-map-container {
    border: 2px solid #3498db;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
</style>
```

## API Data Integration

### Connect to Your Asset API
```javascript
// Modify the loadAssets() function in the generated JavaScript
function loadAssets() {
    fetch('/api/your-assets-endpoint')
        .then(response => response.json())
        .then(data => {
            assetsData = data.assets;
            updateMapMarkers();
            updateStats();
        })
        .catch(error => {
            console.error('Asset data error:', error);
            // Fallback to demo data
            loadDemoAssets();
        });
}
```

### Custom Asset Types
```javascript
function createAssetIcon(status, type) {
    const iconMap = {
        'Excavator': '🚜',
        'Truck': '🚛',
        'Dozer': '🏗️',
        'Crane': '🏗️',
        'Loader': '🚜'
    };
    
    let color = status === 'Active' ? '#27ae60' : '#e74c3c';
    let icon = iconMap[type] || '📍';
    
    return L.divIcon({
        className: 'asset-marker',
        html: `<div style="background: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold;">${icon}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
}
```

## Advanced Features

### Real-Time Updates
The map automatically updates every 60 seconds and includes live tracking capabilities when enabled.

### AI Predictive Mode
- Generates predicted asset locations based on movement patterns
- Shows confidence levels and estimated arrival times
- Visual prediction markers with pulsing animations

### Heat Mapping
- Displays asset activity zones
- Color-coded by utilization intensity
- Interactive toggle on/off functionality

### Mobile Optimization
- Responsive design for all screen sizes
- Touch-friendly controls
- Optimized performance for mobile devices

## Troubleshooting

### Map Not Loading
1. Ensure Leaflet CSS and JS libraries are loaded
2. Check container height is set (not 0px)
3. Verify container ID is unique

### Asset Data Issues
1. Check API endpoint connectivity
2. Verify data format matches expected structure
3. Review browser console for error messages

### Performance Issues
1. Limit number of assets displayed (use clustering)
2. Reduce update frequency for mobile devices
3. Optimize marker clustering settings

## Support
This blueprint is part of the TRAXOVO QQ system and includes bleeding-edge asset intelligence capabilities.

Files included:
- `qq_bleeding_edge_map_blueprint.py` - Main blueprint class
- `QQ_MAP_BLUEPRINT_DOCS.md` - This documentation
- `templates/enhanced_fleet_map.html` - Reference implementation