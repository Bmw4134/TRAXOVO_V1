/**
 * TRAXOVO Quantum Asset Intelligence Map
 * Custom quantum-style visualization for fleet operations
 */

class QuantumAssetMap {
    constructor() {
        this.zones = {
            zone_580: {
                name: "Zone 580 - North Fort Worth Operations",
                coverage: "5km radius",
                jobsites: 52,
                alerts: 0,
                assets: {
                    active: 48,
                    maintenance: 3,
                    offline: 1
                },
                description: "Primary operations hub for north Fort Worth corridor with high-density construction projects"
            },
            zone_581: {
                name: "Zone 581 - Central Fort Worth Hub",
                coverage: "3km radius", 
                jobsites: 58,
                alerts: 1,
                assets: {
                    active: 52,
                    maintenance: 4,
                    offline: 2
                },
                description: "Central dispatch and coordination center with rapid response capabilities"
            },
            zone_582: {
                name: "Zone 582 - South Fort Worth Projects",
                coverage: "8km radius",
                jobsites: 42,
                alerts: 0,
                assets: {
                    active: 38,
                    maintenance: 3,
                    offline: 1
                },
                description: "Extended coverage zone for major infrastructure and commercial developments"
            }
        };
        this.initializeMap();
        this.startQuantumUpdates();
    }

    initializeMap() {
        console.log('🚀 Quantum Asset Intelligence Map initialized');
        this.updateAssetCounters();
        this.addHoverEffects();
        this.addQuantumAnimations();
    }

    showZoneDetails(zoneId) {
        const zone = this.zones[zoneId];
        if (!zone) return;

        // Create quantum modal
        const modal = document.createElement('div');
        modal.id = 'quantumZoneModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: quantumFadeIn 0.3s ease;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: linear-gradient(135deg, #1a1f2e 0%, #0d0d17 100%);
            border: 2px solid rgba(0,255,159,0.3);
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            color: white;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            position: relative;
        `;

        modalContent.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="width: 12px; height: 12px; background: ${this.getZoneColor(zoneId)}; border-radius: 50%; margin-right: 12px; animation: quantumPulse 2s infinite;"></div>
                <h2 style="margin: 0; color: #00ff9f; font-size: 20px; font-weight: 700;">${zone.name}</h2>
            </div>
            
            <div style="margin-bottom: 25px;">
                <p style="color: rgba(255,255,255,0.8); font-size: 14px; line-height: 1.6; margin: 0;">
                    ${zone.description}
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 25px;">
                <div style="background: rgba(0,255,159,0.1); border: 1px solid rgba(0,255,159,0.3); border-radius: 12px; padding: 15px;">
                    <div style="font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 5px;">COVERAGE</div>
                    <div style="font-size: 18px; font-weight: 700; color: #00ff9f;">${zone.coverage}</div>
                </div>
                <div style="background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.3); border-radius: 12px; padding: 15px;">
                    <div style="font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 5px;">JOBSITES</div>
                    <div style="font-size: 18px; font-weight: 700; color: #00d4ff;">${zone.jobsites}</div>
                </div>
            </div>
            
            <div style="background: rgba(26,31,46,0.8); border-radius: 12px; padding: 20px; margin-bottom: 25px;">
                <div style="font-size: 14px; font-weight: 600; color: #00ff9f; margin-bottom: 15px;">Asset Distribution</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #00ff9f;">● Active:</span>
                    <span style="color: white; font-weight: 600;">${zone.assets.active}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #ffa500;">● Maintenance:</span>
                    <span style="color: white; font-weight: 600;">${zone.assets.maintenance}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #ff6b6b;">● Offline:</span>
                    <span style="color: white; font-weight: 600;">${zone.assets.offline}</span>
                </div>
            </div>
            
            ${zone.alerts > 0 ? `
            <div style="background: rgba(255,107,107,0.1); border: 1px solid rgba(255,107,107,0.3); border-radius: 12px; padding: 15px; margin-bottom: 25px;">
                <div style="color: #ff6b6b; font-weight: 600; font-size: 14px;">⚠ ${zone.alerts} Active Alert${zone.alerts > 1 ? 's' : ''}</div>
                <div style="color: rgba(255,255,255,0.7); font-size: 12px; margin-top: 5px;">Equipment requires attention</div>
            </div>
            ` : ''}
            
            <div style="display: flex; gap: 15px; justify-content: flex-end;">
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        style="padding: 12px 24px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">
                    Close
                </button>
                <button onclick="viewZoneAssets('${zoneId}')"
                        style="padding: 12px 24px; background: linear-gradient(45deg, #00ff9f, #00d4ff); border: none; border-radius: 8px; color: #000; font-weight: 700; cursor: pointer; transition: all 0.3s ease;">
                    View Assets
                </button>
            </div>
        `;

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // Add quantum fade in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes quantumFadeIn {
                from { opacity: 0; transform: scale(0.8); }
                to { opacity: 1; transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }

    getZoneColor(zoneId) {
        const colors = {
            zone_580: '#00ff9f',
            zone_581: '#00d4ff', 
            zone_582: '#ff6b6b'
        };
        return colors[zoneId] || '#00ff9f';
    }

    updateAssetCounters() {
        // Calculate totals from all zones
        let totalActive = 0;
        let totalMaintenance = 0;
        let totalAlerts = 0;

        Object.values(this.zones).forEach(zone => {
            totalActive += zone.assets.active;
            totalMaintenance += zone.assets.maintenance;
            totalAlerts += zone.alerts;
        });

        // Update counters if elements exist
        const activeCount = document.getElementById('activeAssetCount');
        const maintenanceCount = document.getElementById('maintenanceAssetCount');
        const alertCount = document.getElementById('alertAssetCount');

        if (activeCount) activeCount.textContent = totalActive;
        if (maintenanceCount) maintenanceCount.textContent = totalMaintenance;
        if (alertCount) alertCount.textContent = totalAlerts;
    }

    addHoverEffects() {
        const zones = document.querySelectorAll('.geofence-zone');
        zones.forEach(zone => {
            zone.addEventListener('mouseenter', () => {
                zone.style.transform = 'scale(1.05)';
                zone.style.boxShadow = '0 10px 30px rgba(0,255,159,0.3)';
                zone.style.transition = 'all 0.3s ease';
            });

            zone.addEventListener('mouseleave', () => {
                zone.style.transform = 'scale(1)';
                zone.style.boxShadow = 'none';
            });
        });
    }

    addQuantumAnimations() {
        // Add floating animation to asset dots
        const assetDots = document.querySelectorAll('.asset-dot');
        assetDots.forEach((dot, index) => {
            if (dot.classList.contains('active')) {
                dot.style.animation = `quantumFloat ${2 + (index % 3)}s ease-in-out infinite`;
            }
        });

        // Add quantum grid animation
        const grid = document.querySelector('.quantum-grid-overlay');
        if (grid) {
            grid.style.animation = 'quantumGrid 10s linear infinite';
        }
    }

    startQuantumUpdates() {
        // Simulate real-time data updates
        setInterval(() => {
            this.updateQuantumMetrics();
        }, 30000); // Update every 30 seconds
    }

    updateQuantumMetrics() {
        // Simulate minor metric fluctuations for realism
        Object.keys(this.zones).forEach(zoneId => {
            const zone = this.zones[zoneId];
            
            // Small random variations in active assets (±2)
            const variation = Math.floor(Math.random() * 5) - 2;
            const baseActive = zone.assets.active;
            zone.assets.active = Math.max(baseActive + variation, baseActive - 2);
        });

        this.updateAssetCounters();
        console.log('🔄 Quantum metrics updated');
    }
}

// Global functions for zone interactions
function showZoneDetails(zoneId) {
    if (window.quantumAssetMap) {
        window.quantumAssetMap.showZoneDetails(zoneId);
    }
}

function viewZoneAssets(zoneId) {
    // Navigate to detailed asset view for the zone
    console.log(`Viewing assets for ${zoneId}`);
    // Could integrate with existing asset drill-down modals
}

// Initialize quantum asset map when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for the map container to be available
    setTimeout(() => {
        if (document.getElementById('quantumAssetMap')) {
            window.quantumAssetMap = new QuantumAssetMap();
            console.log('✓ Quantum Asset Map intelligence activated');
        }
    }, 500);
});

// Add quantum CSS animations
const quantumStyles = document.createElement('style');
quantumStyles.textContent = `
    @keyframes quantumFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }
    
    @keyframes quantumGrid {
        0% { background-position: 0 0; }
        100% { background-position: 40px 40px; }
    }
    
    .geofence-zone {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .geofence-zone:hover {
        z-index: 10;
    }
    
    .asset-dot {
        box-shadow: 0 0 10px currentColor;
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(quantumStyles);