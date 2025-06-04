/**
 * TRAXOVO Intuitive Drag-and-Drop Dashboard Widgets
 * Advanced dashboard customization with persistent layouts
 */

class TRAXOVODragDropDashboard {
    constructor() {
        this.widgets = new Map();
        this.draggedElement = null;
        this.dropZones = [];
        this.layoutConfig = this.loadLayout();
        this.isDragging = false;
        this.touchOffset = { x: 0, y: 0 };
        
        this.initialize();
    }
    
    initialize() {
        this.createWidgetLibrary();
        this.setupDragAndDrop();
        this.loadSavedLayout();
        this.setupLayoutControls();
        
        console.log('TRAXOVO Drag-Drop Dashboard: INITIALIZED');
    }
    
    createWidgetLibrary() {
        const widgetLibrary = document.createElement('div');
        widgetLibrary.id = 'widget-library';
        widgetLibrary.className = 'widget-library';
        widgetLibrary.innerHTML = `
            <div class="widget-library-header">
                <h3>Available Widgets</h3>
                <button class="toggle-library" onclick="traxovoDragDrop.toggleLibrary()">
                    <i class="fas fa-chevron-up"></i>
                </button>
            </div>
            <div class="widget-library-content">
                <div class="widget-category">
                    <h4>Fleet Management</h4>
                    <div class="widget-items">
                        <div class="widget-item" data-widget-type="fleet-overview" draggable="true">
                            <i class="fas fa-truck"></i>
                            <span>Fleet Overview</span>
                        </div>
                        <div class="widget-item" data-widget-type="asset-tracking" draggable="true">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>Asset Tracking</span>
                        </div>
                        <div class="widget-item" data-widget-type="maintenance-alerts" draggable="true">
                            <i class="fas fa-wrench"></i>
                            <span>Maintenance Alerts</span>
                        </div>
                    </div>
                </div>
                
                <div class="widget-category">
                    <h4>Analytics</h4>
                    <div class="widget-items">
                        <div class="widget-item" data-widget-type="performance-chart" draggable="true">
                            <i class="fas fa-chart-line"></i>
                            <span>Performance Chart</span>
                        </div>
                        <div class="widget-item" data-widget-type="cost-analysis" draggable="true">
                            <i class="fas fa-dollar-sign"></i>
                            <span>Cost Analysis</span>
                        </div>
                        <div class="widget-item" data-widget-type="utilization-metrics" draggable="true">
                            <i class="fas fa-tachometer-alt"></i>
                            <span>Utilization Metrics</span>
                        </div>
                    </div>
                </div>
                
                <div class="widget-category">
                    <h4>Operations</h4>
                    <div class="widget-items">
                        <div class="widget-item" data-widget-type="attendance-matrix" draggable="true">
                            <i class="fas fa-users"></i>
                            <span>Attendance Matrix</span>
                        </div>
                        <div class="widget-item" data-widget-type="zone-payroll" draggable="true">
                            <i class="fas fa-money-check"></i>
                            <span>Zone Payroll</span>
                        </div>
                        <div class="widget-item" data-widget-type="project-status" draggable="true">
                            <i class="fas fa-tasks"></i>
                            <span>Project Status</span>
                        </div>
                    </div>
                </div>
                
                <div class="widget-category">
                    <h4>Productivity</h4>
                    <div class="widget-items">
                        <div class="widget-item" data-widget-type="smart-nudges" draggable="true">
                            <i class="fas fa-lightbulb"></i>
                            <span>Smart Nudges</span>
                        </div>
                        <div class="widget-item" data-widget-type="quick-actions" draggable="true">
                            <i class="fas fa-bolt"></i>
                            <span>Quick Actions</span>
                        </div>
                        <div class="widget-item" data-widget-type="weather-widget" draggable="true">
                            <i class="fas fa-cloud-sun"></i>
                            <span>Weather</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(widgetLibrary);
    }
    
    setupDragAndDrop() {
        // Setup drag events for widget library items
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('widget-item') || e.target.classList.contains('dashboard-widget')) {
                this.handleDragStart(e);
            }
        });
        
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.handleDragOver(e);
        });
        
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            this.handleDrop(e);
        });
        
        document.addEventListener('dragend', (e) => {
            this.handleDragEnd(e);
        });
        
        // Touch events for mobile support
        document.addEventListener('touchstart', (e) => {
            if (e.target.classList.contains('widget-item') || e.target.classList.contains('dashboard-widget')) {
                this.handleTouchStart(e);
            }
        }, { passive: false });
        
        document.addEventListener('touchmove', (e) => {
            if (this.isDragging) {
                e.preventDefault();
                this.handleTouchMove(e);
            }
        }, { passive: false });
        
        document.addEventListener('touchend', (e) => {
            if (this.isDragging) {
                this.handleTouchEnd(e);
            }
        });
        
        // Create drop zones
        this.createDropZones();
    }
    
    createDropZones() {
        const dashboardGrid = document.querySelector('.dashboard-grid') || document.querySelector('.metrics-grid');
        
        if (dashboardGrid) {
            dashboardGrid.classList.add('drop-zone');
            this.dropZones.push(dashboardGrid);
        }
        
        // Create additional drop zones if needed
        const mainContent = document.querySelector('.main-content') || document.querySelector('.dashboard-main');
        if (mainContent && !mainContent.querySelector('.drop-zone-container')) {
            const dropZoneContainer = document.createElement('div');
            dropZoneContainer.className = 'drop-zone-container';
            dropZoneContainer.innerHTML = `
                <div class="drop-zone primary-zone" data-zone="primary">
                    <div class="drop-zone-label">Primary Dashboard Area</div>
                </div>
                <div class="drop-zone secondary-zone" data-zone="secondary">
                    <div class="drop-zone-label">Secondary Widget Area</div>
                </div>
            `;
            mainContent.appendChild(dropZoneContainer);
            
            this.dropZones.push(...dropZoneContainer.querySelectorAll('.drop-zone'));
        }
    }
    
    handleDragStart(e) {
        this.draggedElement = e.target;
        this.isDragging = true;
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
        e.dataTransfer.setData('text/plain', e.target.dataset.widgetType || 'unknown');
        
        // Add dragging class for visual feedback
        e.target.classList.add('dragging');
        
        // Show drop zones
        this.showDropZones();
    }
    
    handleDragOver(e) {
        const dropZone = e.target.closest('.drop-zone');
        if (dropZone) {
            dropZone.classList.add('drag-over');
            this.clearOtherDropZoneHighlights(dropZone);
        }
    }
    
    handleDrop(e) {
        const dropZone = e.target.closest('.drop-zone');
        if (dropZone && this.draggedElement) {
            this.createWidget(this.draggedElement.dataset.widgetType, dropZone);
            this.saveLayout();
        }
        
        this.cleanupDrag();
    }
    
    handleDragEnd(e) {
        this.cleanupDrag();
    }
    
    handleTouchStart(e) {
        const touch = e.touches[0];
        this.draggedElement = e.target;
        this.isDragging = true;
        
        const rect = e.target.getBoundingClientRect();
        this.touchOffset = {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top
        };
        
        e.target.classList.add('dragging');
        this.showDropZones();
    }
    
    handleTouchMove(e) {
        if (!this.isDragging || !this.draggedElement) return;
        
        const touch = e.touches[0];
        const dragPreview = this.getDragPreview();
        
        dragPreview.style.left = (touch.clientX - this.touchOffset.x) + 'px';
        dragPreview.style.top = (touch.clientY - this.touchOffset.y) + 'px';
        
        // Check for drop zone under touch
        const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
        const dropZone = elementBelow?.closest('.drop-zone');
        
        this.clearAllDropZoneHighlights();
        if (dropZone) {
            dropZone.classList.add('drag-over');
        }
    }
    
    handleTouchEnd(e) {
        if (!this.isDragging) return;
        
        const touch = e.changedTouches[0];
        const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
        const dropZone = elementBelow?.closest('.drop-zone');
        
        if (dropZone && this.draggedElement) {
            this.createWidget(this.draggedElement.dataset.widgetType, dropZone);
            this.saveLayout();
        }
        
        this.cleanupDrag();
    }
    
    getDragPreview() {
        let preview = document.getElementById('drag-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'drag-preview';
            preview.className = 'drag-preview';
            document.body.appendChild(preview);
        }
        
        if (this.draggedElement) {
            preview.innerHTML = this.draggedElement.innerHTML;
            preview.style.display = 'block';
        }
        
        return preview;
    }
    
    createWidget(widgetType, dropZone) {
        const widgetId = `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const widget = document.createElement('div');
        widget.className = 'dashboard-widget';
        widget.id = widgetId;
        widget.dataset.widgetType = widgetType;
        widget.draggable = true;
        
        widget.innerHTML = this.getWidgetContent(widgetType, widgetId);
        
        dropZone.appendChild(widget);
        this.widgets.set(widgetId, {
            type: widgetType,
            zone: dropZone.dataset.zone || 'primary',
            position: dropZone.children.length - 1
        });
        
        // Initialize widget functionality
        this.initializeWidget(widget, widgetType);
        
        // Add widget controls
        this.addWidgetControls(widget);
    }
    
    getWidgetContent(widgetType, widgetId) {
        const widgetTemplates = {
            'fleet-overview': `
                <div class="widget-header">
                    <h4><i class="fas fa-truck"></i> Fleet Overview</h4>
                </div>
                <div class="widget-content">
                    <div class="fleet-stats">
                        <div class="stat-item">
                            <span class="stat-value">23</span>
                            <span class="stat-label">Active Vehicles</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">87%</span>
                            <span class="stat-label">Utilization</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">2</span>
                            <span class="stat-label">Maintenance Due</span>
                        </div>
                    </div>
                </div>
            `,
            'asset-tracking': `
                <div class="widget-header">
                    <h4><i class="fas fa-map-marker-alt"></i> Asset Tracking</h4>
                </div>
                <div class="widget-content">
                    <div class="asset-list">
                        <div class="asset-item">
                            <span class="asset-name">Excavator-001</span>
                            <span class="asset-status active">Active</span>
                        </div>
                        <div class="asset-item">
                            <span class="asset-name">Truck-045</span>
                            <span class="asset-status moving">In Transit</span>
                        </div>
                        <div class="asset-item">
                            <span class="asset-name">Crane-012</span>
                            <span class="asset-status idle">Idle</span>
                        </div>
                    </div>
                </div>
            `,
            'performance-chart': `
                <div class="widget-header">
                    <h4><i class="fas fa-chart-line"></i> Performance Chart</h4>
                </div>
                <div class="widget-content">
                    <canvas id="chart-${widgetId}" class="performance-chart"></canvas>
                </div>
            `,
            'maintenance-alerts': `
                <div class="widget-header">
                    <h4><i class="fas fa-wrench"></i> Maintenance Alerts</h4>
                </div>
                <div class="widget-content">
                    <div class="alert-list">
                        <div class="alert-item urgent">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span>Excavator-001: Oil change due</span>
                        </div>
                        <div class="alert-item warning">
                            <i class="fas fa-warning"></i>
                            <span>Truck-045: Tire inspection needed</span>
                        </div>
                    </div>
                </div>
            `,
            'attendance-matrix': `
                <div class="widget-header">
                    <h4><i class="fas fa-users"></i> Attendance Matrix</h4>
                </div>
                <div class="widget-content">
                    <div class="attendance-grid">
                        <div class="attendance-row">
                            <span class="employee-name">Alice Rodriguez</span>
                            <span class="attendance-status present">Present</span>
                        </div>
                        <div class="attendance-row">
                            <span class="employee-name">Bob Johnson</span>
                            <span class="attendance-status present">Present</span>
                        </div>
                        <div class="attendance-row">
                            <span class="employee-name">Carlos Martinez</span>
                            <span class="attendance-status absent">Absent</span>
                        </div>
                    </div>
                </div>
            `,
            'smart-nudges': `
                <div class="widget-header">
                    <h4><i class="fas fa-lightbulb"></i> Smart Nudges</h4>
                </div>
                <div class="widget-content">
                    <div class="nudge-item">
                        <i class="fas fa-info-circle"></i>
                        <span>Consider scheduling maintenance for high-usage vehicles</span>
                    </div>
                    <div class="nudge-item">
                        <i class="fas fa-chart-bar"></i>
                        <span>Review fuel efficiency reports for cost optimization</span>
                    </div>
                </div>
            `,
            'weather-widget': `
                <div class="widget-header">
                    <h4><i class="fas fa-cloud-sun"></i> Fort Worth Weather</h4>
                </div>
                <div class="widget-content">
                    <div class="weather-info">
                        <div class="weather-main">
                            <span class="temperature">72°F</span>
                            <span class="condition">Partly Cloudy</span>
                        </div>
                        <div class="weather-details">
                            <span>Humidity: 65%</span>
                            <span>Wind: 8 mph</span>
                        </div>
                    </div>
                </div>
            `
        };
        
        return widgetTemplates[widgetType] || `
            <div class="widget-header">
                <h4>Unknown Widget</h4>
            </div>
            <div class="widget-content">
                <p>Widget type: ${widgetType}</p>
            </div>
        `;
    }
    
    addWidgetControls(widget) {
        const controls = document.createElement('div');
        controls.className = 'widget-controls';
        controls.innerHTML = `
            <button class="widget-control refresh" onclick="traxovoDragDrop.refreshWidget('${widget.id}')" title="Refresh">
                <i class="fas fa-sync-alt"></i>
            </button>
            <button class="widget-control settings" onclick="traxovoDragDrop.configureWidget('${widget.id}')" title="Settings">
                <i class="fas fa-cog"></i>
            </button>
            <button class="widget-control remove" onclick="traxovoDragDrop.removeWidget('${widget.id}')" title="Remove">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        widget.appendChild(controls);
    }
    
    initializeWidget(widget, widgetType) {
        // Initialize specific widget functionality
        switch (widgetType) {
            case 'performance-chart':
                this.initializeChart(widget);
                break;
            case 'weather-widget':
                this.updateWeatherWidget(widget);
                break;
            default:
                // Basic initialization for other widgets
                break;
        }
    }
    
    initializeChart(widget) {
        const canvas = widget.querySelector('canvas');
        if (canvas && typeof Chart !== 'undefined') {
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    datasets: [{
                        label: 'Fleet Utilization',
                        data: [85, 92, 78, 96, 87],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    }
    
    updateWeatherWidget(widget) {
        // Simulate weather data update
        setTimeout(() => {
            const temperature = widget.querySelector('.temperature');
            const condition = widget.querySelector('.condition');
            
            if (temperature && condition) {
                const temps = ['68°F', '72°F', '75°F', '69°F', '71°F'];
                const conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Clear'];
                
                temperature.textContent = temps[Math.floor(Math.random() * temps.length)];
                condition.textContent = conditions[Math.floor(Math.random() * conditions.length)];
            }
        }, 1000);
    }
    
    refreshWidget(widgetId) {
        const widget = document.getElementById(widgetId);
        if (widget) {
            const widgetType = widget.dataset.widgetType;
            
            // Add refresh animation
            widget.classList.add('refreshing');
            
            setTimeout(() => {
                this.initializeWidget(widget, widgetType);
                widget.classList.remove('refreshing');
            }, 1000);
        }
    }
    
    configureWidget(widgetId) {
        const widget = document.getElementById(widgetId);
        if (widget) {
            // Create configuration modal
            this.showWidgetConfigModal(widget);
        }
    }
    
    removeWidget(widgetId) {
        const widget = document.getElementById(widgetId);
        if (widget) {
            widget.style.animation = 'fadeOut 0.3s ease-in-out';
            setTimeout(() => {
                widget.remove();
                this.widgets.delete(widgetId);
                this.saveLayout();
            }, 300);
        }
    }
    
    showWidgetConfigModal(widget) {
        const modal = document.createElement('div');
        modal.className = 'widget-config-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Configure Widget</h3>
                    <button class="close-modal" onclick="this.closest('.widget-config-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="config-option">
                        <label>Widget Title:</label>
                        <input type="text" value="${widget.querySelector('h4').textContent}" id="widget-title">
                    </div>
                    <div class="config-option">
                        <label>Refresh Interval:</label>
                        <select id="refresh-interval">
                            <option value="30">30 seconds</option>
                            <option value="60" selected>1 minute</option>
                            <option value="300">5 minutes</option>
                            <option value="600">10 minutes</option>
                        </select>
                    </div>
                    <div class="config-option">
                        <label>Widget Size:</label>
                        <select id="widget-size">
                            <option value="small">Small</option>
                            <option value="medium" selected>Medium</option>
                            <option value="large">Large</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-cancel" onclick="this.closest('.widget-config-modal').remove()">Cancel</button>
                    <button class="btn-save" onclick="traxovoDragDrop.saveWidgetConfig('${widget.id}', this.closest('.widget-config-modal'))">Save</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    saveWidgetConfig(widgetId, modal) {
        const widget = document.getElementById(widgetId);
        const title = modal.querySelector('#widget-title').value;
        const size = modal.querySelector('#widget-size').value;
        
        // Apply configuration
        widget.querySelector('h4').textContent = title;
        widget.className = `dashboard-widget ${size}`;
        
        // Update widget data
        const widgetData = this.widgets.get(widgetId);
        if (widgetData) {
            widgetData.title = title;
            widgetData.size = size;
            this.widgets.set(widgetId, widgetData);
        }
        
        this.saveLayout();
        modal.remove();
    }
    
    showDropZones() {
        this.dropZones.forEach(zone => {
            zone.classList.add('drop-zone-visible');
        });
    }
    
    hideDropZones() {
        this.dropZones.forEach(zone => {
            zone.classList.remove('drop-zone-visible', 'drag-over');
        });
    }
    
    clearAllDropZoneHighlights() {
        this.dropZones.forEach(zone => {
            zone.classList.remove('drag-over');
        });
    }
    
    clearOtherDropZoneHighlights(activeZone) {
        this.dropZones.forEach(zone => {
            if (zone !== activeZone) {
                zone.classList.remove('drag-over');
            }
        });
    }
    
    cleanupDrag() {
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
        }
        
        this.hideDropZones();
        this.isDragging = false;
        this.draggedElement = null;
        
        // Remove drag preview
        const preview = document.getElementById('drag-preview');
        if (preview) {
            preview.style.display = 'none';
        }
    }
    
    toggleLibrary() {
        const library = document.getElementById('widget-library');
        const content = library.querySelector('.widget-library-content');
        const toggle = library.querySelector('.toggle-library i');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.className = 'fas fa-chevron-up';
        } else {
            content.style.display = 'none';
            toggle.className = 'fas fa-chevron-down';
        }
    }
    
    setupLayoutControls() {
        const controls = document.createElement('div');
        controls.className = 'layout-controls';
        controls.innerHTML = `
            <button class="layout-btn" onclick="traxovoDragDrop.saveCurrentLayout()" title="Save Layout">
                <i class="fas fa-save"></i> Save Layout
            </button>
            <button class="layout-btn" onclick="traxovoDragDrop.resetLayout()" title="Reset Layout">
                <i class="fas fa-undo"></i> Reset
            </button>
            <button class="layout-btn" onclick="traxovoDragDrop.exportLayout()" title="Export Layout">
                <i class="fas fa-download"></i> Export
            </button>
            <button class="layout-btn" onclick="traxovoDragDrop.importLayout()" title="Import Layout">
                <i class="fas fa-upload"></i> Import
            </button>
        `;
        
        document.body.appendChild(controls);
    }
    
    saveLayout() {
        const layout = {
            widgets: Array.from(this.widgets.entries()).map(([id, data]) => ({
                id,
                ...data
            })),
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('traxovo-dashboard-layout', JSON.stringify(layout));
    }
    
    loadLayout() {
        const saved = localStorage.getItem('traxovo-dashboard-layout');
        return saved ? JSON.parse(saved) : { widgets: [] };
    }
    
    loadSavedLayout() {
        if (this.layoutConfig.widgets) {
            this.layoutConfig.widgets.forEach(widgetData => {
                const zone = document.querySelector(`[data-zone="${widgetData.zone}"]`);
                if (zone) {
                    this.createWidget(widgetData.type, zone);
                }
            });
        }
    }
    
    saveCurrentLayout() {
        this.saveLayout();
        
        // Show confirmation
        const notification = document.createElement('div');
        notification.className = 'layout-notification';
        notification.textContent = 'Layout saved successfully!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    resetLayout() {
        if (confirm('Are you sure you want to reset the dashboard layout?')) {
            // Remove all widgets
            document.querySelectorAll('.dashboard-widget').forEach(widget => {
                widget.remove();
            });
            
            this.widgets.clear();
            localStorage.removeItem('traxovo-dashboard-layout');
            
            // Show confirmation
            const notification = document.createElement('div');
            notification.className = 'layout-notification';
            notification.textContent = 'Layout reset successfully!';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
    
    exportLayout() {
        const layout = {
            widgets: Array.from(this.widgets.entries()).map(([id, data]) => ({
                id,
                ...data
            })),
            timestamp: new Date().toISOString(),
            version: '1.0.0'
        };
        
        const dataStr = JSON.stringify(layout, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `traxovo-layout-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
    
    importLayout() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const layout = JSON.parse(event.target.result);
                        this.applyImportedLayout(layout);
                    } catch (error) {
                        alert('Invalid layout file format');
                    }
                };
                reader.readAsText(file);
            }
        };
        
        input.click();
    }
    
    applyImportedLayout(layout) {
        // Clear current layout
        document.querySelectorAll('.dashboard-widget').forEach(widget => {
            widget.remove();
        });
        this.widgets.clear();
        
        // Apply imported layout
        if (layout.widgets) {
            layout.widgets.forEach(widgetData => {
                const zone = document.querySelector(`[data-zone="${widgetData.zone}"]`);
                if (zone) {
                    this.createWidget(widgetData.type, zone);
                }
            });
        }
        
        this.saveLayout();
        
        // Show confirmation
        const notification = document.createElement('div');
        notification.className = 'layout-notification';
        notification.textContent = 'Layout imported successfully!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready
let traxovoDragDrop;

function initializeDragDropDashboard() {
    traxovoDragDrop = new TRAXOVODragDropDashboard();
    window.traxovoDragDrop = traxovoDragDrop;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDragDropDashboard);
} else {
    initializeDragDropDashboard();
}