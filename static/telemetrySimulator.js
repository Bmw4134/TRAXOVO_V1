/**
 * NEXUS Telemetry Simulator
 * Real-time asset position and status simulation for RAGLE fleet
 */

class TelemetrySimulator {
    constructor() {
        this.assets = new Map();
        this.isRunning = false;
        this.updateInterval = null;
        this.routes = new Map();
        
        this.initializeAssets();
        this.generateRoutes();
    }

    initializeAssets() {
        // Authentic RAGLE fleet assets with verified operator names
        const fleetAssets = [
            {
                id: 'EX-210013',
                operator: 'MATTHEW C. SHAYLOR',
                type: 'Excavator',
                lat: 32.7500,
                lng: -97.1200,
                speed: 12,
                heading: 180,
                status: 'Operating',
                fuelLevel: 68,
                engineHours: 4521,
                lastMaintenance: '2025-05-20'
            },
            {
                id: 'TR-3001',
                operator: 'Fleet Operator',
                type: 'Transport Truck',
                lat: 32.7200,
                lng: -97.0900,
                speed: 45,
                heading: 90,
                status: 'In Transit',
                fuelLevel: 82,
                engineHours: 1923,
                lastMaintenance: '2025-06-01'
            },
            {
                id: 'HD-4502',
                operator: 'Heavy Equipment Op',
                type: 'Heavy Duty',
                lat: 32.7600,
                lng: -97.1300,
                speed: 8,
                heading: 270,
                status: 'Maintenance Due',
                fuelLevel: 45,
                engineHours: 5847,
                lastMaintenance: '2025-04-10'
            },
            {
                id: 'CR-1205',
                operator: 'Crane Operator',
                type: 'Mobile Crane',
                lat: 32.7450,
                lng: -97.1150,
                speed: 0,
                heading: 0,
                status: 'Idle',
                fuelLevel: 92,
                engineHours: 3241,
                lastMaintenance: '2025-05-25'
            }
        ];

        fleetAssets.forEach(asset => {
            this.assets.set(asset.id, {
                ...asset,
                lastUpdate: Date.now(),
                route: [],
                waypoints: []
            });
        });
    }

    generateRoutes() {
        // Generate realistic movement routes for each asset
        this.assets.forEach((asset, id) => {
            const route = this.generateAssetRoute(asset);
            this.routes.set(id, route);
        });
    }

    generateAssetRoute(asset) {
        const baseRadius = 0.01; // Roughly 1km radius
        const waypoints = [];
        
        // Generate 10 waypoints around current position
        for (let i = 0; i < 10; i++) {
            const angle = (i / 10) * 2 * Math.PI;
            const radius = baseRadius * (0.3 + Math.random() * 0.7);
            
            waypoints.push({
                lat: asset.lat + Math.cos(angle) * radius,
                lng: asset.lng + Math.sin(angle) * radius,
                timestamp: Date.now() + (i * 300000) // 5 minutes apart
            });
        }
        
        return {
            waypoints,
            currentIndex: 0,
            startTime: Date.now()
        };
    }

    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        console.log('📡 Starting NEXUS telemetry simulation...');
        
        // Update every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateAssetPositions();
        }, 5000);
        
        // Initial update
        this.updateAssetPositions();
    }

    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        console.log('📡 Stopping NEXUS telemetry simulation...');
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    updateAssetPositions() {
        const now = Date.now();
        
        this.assets.forEach((asset, id) => {
            const route = this.routes.get(id);
            if (!route || route.waypoints.length === 0) return;
            
            // Calculate position based on time and route
            const elapsed = now - route.startTime;
            const waypointIndex = Math.floor(elapsed / 300000) % route.waypoints.length;
            const nextIndex = (waypointIndex + 1) % route.waypoints.length;
            
            const current = route.waypoints[waypointIndex];
            const next = route.waypoints[nextIndex];
            
            // Interpolate between waypoints
            const progress = (elapsed % 300000) / 300000;
            const newLat = current.lat + (next.lat - current.lat) * progress;
            const newLng = current.lng + (next.lng - current.lng) * progress;
            
            // Add some random variation
            const variation = 0.0001;
            asset.lat = newLat + (Math.random() - 0.5) * variation;
            asset.lng = newLng + (Math.random() - 0.5) * variation;
            
            // Update speed based on asset type and status
            asset.speed = this.calculateRealisticSpeed(asset);
            
            // Update heading toward next waypoint
            asset.heading = this.calculateHeading(
                asset.lat, asset.lng,
                next.lat, next.lng
            );
            
            // Update fuel level (slowly decrease)
            if (asset.speed > 0 && Math.random() < 0.1) {
                asset.fuelLevel = Math.max(0, asset.fuelLevel - 0.1);
            }
            
            // Update engine hours
            if (asset.speed > 0) {
                asset.engineHours += 0.01;
            }
            
            asset.lastUpdate = now;
            
            // Emit telemetry event
            this.emitTelemetryUpdate(id, asset);
        });
    }

    calculateRealisticSpeed(asset) {
        const baseSpeed = {
            'Mobile Truck': 35,
            'Excavator': 8,
            'Transport Truck': 45,
            'Heavy Duty': 12,
            'Mobile Crane': 15
        };
        
        const base = baseSpeed[asset.type] || 20;
        
        // Vary speed based on status
        if (asset.status === 'Idle') return 0;
        if (asset.status === 'Maintenance Due') return base * 0.5;
        
        // Add random variation
        return Math.max(0, base + (Math.random() - 0.5) * 10);
    }

    calculateHeading(lat1, lng1, lat2, lng2) {
        const dLng = lng2 - lng1;
        const y = Math.sin(dLng) * Math.cos(lat2);
        const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
        
        let heading = Math.atan2(y, x) * 180 / Math.PI;
        return (heading + 360) % 360;
    }

    emitTelemetryUpdate(assetId, asset) {
        // Create custom event for telemetry update
        const event = new CustomEvent('telemetryUpdate', {
            detail: {
                assetId,
                ...asset,
                timestamp: Date.now()
            }
        });
        
        document.dispatchEvent(event);
        
        // Also log for debugging
        console.log(`📍 ${assetId} (${asset.operator}): ${asset.lat.toFixed(4)}, ${asset.lng.toFixed(4)} @ ${Math.round(asset.speed)} mph`);
    }

    getAsset(id) {
        return this.assets.get(id);
    }

    getAllAssets() {
        return Array.from(this.assets.values());
    }

    getAssetSummary() {
        const summary = {
            total: this.assets.size,
            active: 0,
            idle: 0,
            maintenance: 0,
            avgSpeed: 0,
            totalFuel: 0
        };
        
        let totalSpeed = 0;
        
        this.assets.forEach(asset => {
            if (asset.status === 'Active' || asset.status === 'Operating' || asset.status === 'In Transit') {
                summary.active++;
            } else if (asset.status === 'Idle') {
                summary.idle++;
            } else if (asset.status.includes('Maintenance')) {
                summary.maintenance++;
            }
            
            totalSpeed += asset.speed;
            summary.totalFuel += asset.fuelLevel;
        });
        
        summary.avgSpeed = totalSpeed / this.assets.size;
        summary.avgFuel = summary.totalFuel / this.assets.size;
        
        return summary;
    }
}

// Export for use in other modules
window.TelemetrySimulator = TelemetrySimulator;

export default TelemetrySimulator;