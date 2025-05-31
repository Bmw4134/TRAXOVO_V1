/**
 * Elite Asset Tooltip System for TRAXOVO
 * Contextual hover tooltips showing authentic GAUGE asset metrics
 */

class AssetTooltipManager {
    constructor() {
        this.tooltip = null;
        this.tooltipData = {};
        this.isVisible = false;
        this.hideTimeout = null;
        this.init();
    }

    init() {
        this.createTooltip();
        this.loadTooltipData();
        this.bindEvents();
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'asset-tooltip';
        this.tooltip.id = 'asset-tooltip';
        document.body.appendChild(this.tooltip);
    }

    async loadTooltipData() {
        try {
            const response = await fetch('/api/fleet/assets');
            const data = await response.json();
            
            if (data.success && data.asset_tooltips) {
                this.tooltipData = data.asset_tooltips;
                console.log(`Loaded tooltips for ${Object.keys(this.tooltipData).length} authentic assets`);
            }
        } catch (error) {
            console.error('Failed to load tooltip data:', error);
        }
    }

    bindEvents() {
        // Bind to asset elements across the application
        document.addEventListener('mouseenter', (e) => {
            const assetElement = e.target.closest('[data-asset-id]');
            if (assetElement) {
                const assetId = assetElement.dataset.assetId;
                this.showTooltip(assetId, e);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            const assetElement = e.target.closest('[data-asset-id]');
            if (assetElement) {
                this.hideTooltip();
            }
        }, true);

        document.addEventListener('mousemove', (e) => {
            if (this.isVisible) {
                this.updateTooltipPosition(e);
            }
        });
    }

    showTooltip(assetId, event) {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }

        const tooltipInfo = this.tooltipData[assetId];
        if (!tooltipInfo) return;

        this.tooltip.innerHTML = this.generateTooltipHTML(tooltipInfo);
        this.updateTooltipPosition(event);
        
        this.tooltip.classList.add('visible');
        this.isVisible = true;
    }

    hideTooltip() {
        this.hideTimeout = setTimeout(() => {
            this.tooltip.classList.remove('visible');
            this.isVisible = false;
        }, 100);
    }

    updateTooltipPosition(event) {
        const tooltip = this.tooltip;
        const padding = 15;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let x = event.clientX + padding;
        let y = event.clientY + padding;

        // Adjust if tooltip would go off-screen
        const tooltipRect = tooltip.getBoundingClientRect();
        
        if (x + tooltipRect.width > viewportWidth) {
            x = event.clientX - tooltipRect.width - padding;
        }
        
        if (y + tooltipRect.height > viewportHeight) {
            y = event.clientY - tooltipRect.height - padding;
        }

        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
    }

    generateTooltipHTML(tooltipInfo) {
        const statusClass = tooltipInfo.status === 'Active' ? 'status-active' : 'status-inactive';
        const efficiencyScore = parseInt(tooltipInfo.metrics.efficiency_score);
        
        return `
            <div class="tooltip-header">
                <div class="tooltip-title">${tooltipInfo.header}</div>
                <div class="tooltip-category">${tooltipInfo.category}</div>
                <div class="tooltip-status ${statusClass}">${tooltipInfo.status}</div>
                <div style="clear: both;"></div>
            </div>

            <div class="tooltip-section">
                <div class="section-title">Location & Metrics</div>
                <div class="metric-row">
                    <span class="metric-label">Location:</span>
                    <span class="metric-value">${tooltipInfo.location}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Engine Hours:</span>
                    <span class="metric-value">${tooltipInfo.metrics.engine_hours}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Battery Level:</span>
                    <span class="metric-value">${tooltipInfo.metrics.battery_level}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Health Status:</span>
                    <span class="metric-value">${tooltipInfo.metrics.health_status}</span>
                </div>
            </div>

            <div class="tooltip-section">
                <div class="section-title">Efficiency Score</div>
                <div class="efficiency-bar">
                    <div class="efficiency-fill" style="width: ${efficiencyScore}%"></div>
                </div>
                <div style="text-align: center; margin-top: 4px; font-weight: 500; color: #1e293b;">
                    ${tooltipInfo.metrics.efficiency_score}
                </div>
            </div>

            <div class="tooltip-section">
                <div class="section-title">Utilization</div>
                <div class="metric-row">
                    <span class="metric-label">Status:</span>
                    <span class="metric-value">${tooltipInfo.utilization.status}</span>
                </div>
                ${tooltipInfo.utilization.idle_time ? `
                <div class="metric-row">
                    <span class="metric-label">Idle Time:</span>
                    <span class="metric-value">${tooltipInfo.utilization.idle_time}</span>
                </div>
                ` : ''}
                <div class="metric-row">
                    <span class="metric-label">Efficiency:</span>
                    <span class="metric-value">${tooltipInfo.utilization.efficiency}</span>
                </div>
            </div>

            <div class="tooltip-section">
                <div class="section-title">Maintenance</div>
                <div class="metric-row">
                    <span class="metric-label">Next Service:</span>
                    <span class="metric-value">${tooltipInfo.maintenance.next_service}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Priority:</span>
                    <span class="metric-value ${this.getPriorityClass(tooltipInfo.maintenance.priority)}">${tooltipInfo.maintenance.priority}</span>
                </div>
            </div>

            <div class="tooltip-section">
                <div class="section-title">Performance</div>
                <div class="performance-indicators">
                    <div class="performance-badge ${this.getPerformanceBadgeClass(tooltipInfo.performance_indicators.productivity)}">
                        Productivity: ${tooltipInfo.performance_indicators.productivity}
                    </div>
                    <div class="performance-badge ${this.getPerformanceBadgeClass(tooltipInfo.performance_indicators.reliability)}">
                        Reliability: ${tooltipInfo.performance_indicators.reliability}
                    </div>
                </div>
            </div>

            <div class="tooltip-footer">
                Authentic GAUGE Telematic Data
            </div>
        `;
    }

    getPriorityClass(priority) {
        switch (priority.toLowerCase()) {
            case 'high': return 'badge-high';
            case 'medium': return 'badge-medium';
            case 'low': return 'badge-low';
            default: return '';
        }
    }

    getPerformanceBadgeClass(performance) {
        switch (performance.toLowerCase()) {
            case 'excellent': return 'badge-excellent';
            case 'high': return 'badge-excellent';
            case 'good': return 'badge-good';
            case 'medium': return 'badge-medium';
            case 'fair': return 'badge-fair';
            case 'low': return 'badge-low';
            default: return 'badge-good';
        }
    }

    // Method to add tooltip support to new elements
    addTooltipToElement(element, assetId) {
        element.setAttribute('data-asset-id', assetId);
        element.style.cursor = 'pointer';
    }

    // Method to refresh tooltip data
    async refreshTooltipData() {
        await this.loadTooltipData();
    }
}

// Initialize the tooltip manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.assetTooltipManager = new AssetTooltipManager();
});

// Utility function to add tooltips to dynamically created elements
function addAssetTooltip(element, assetId) {
    if (window.assetTooltipManager) {
        window.assetTooltipManager.addTooltipToElement(element, assetId);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AssetTooltipManager, addAssetTooltip };
}