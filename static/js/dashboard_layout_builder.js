/**
 * TRAXOVO Dashboard Layout Builder
 * Drag-and-drop personalized dashboard with dynamic hover animations
 */

class DashboardLayoutBuilder {
    constructor() {
        this.widgets = [];
        this.currentLayout = {};
        this.isEditMode = false;
        this.draggedElement = null;
        
        this.init();
    }
    
    init() {
        this.setupEditModeToggle();
        this.setupDragAndDrop();
        this.setupWidgetCatalog();
        this.loadSavedLayout();
        this.setupHoverAnimations();
    }
    
    setupEditModeToggle() {
        // Add edit mode toggle button to the dashboard
        const editButton = document.createElement('button');
        editButton.className = 'btn btn-outline-primary position-fixed';
        editButton.style.cssText = 'top: 20px; right: 20px; z-index: 1050; border-radius: 50px;';
        editButton.innerHTML = '<i class="fas fa-edit me-2"></i>Customize Dashboard';
        editButton.onclick = () => this.toggleEditMode();
        document.body.appendChild(editButton);
    }
    
    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        const body = document.body;
        
        if (this.isEditMode) {
            body.classList.add('dashboard-edit-mode');
            this.showWidgetCatalog();
            this.enableDragAndDrop();
        } else {
            body.classList.remove('dashboard-edit-mode');
            this.hideWidgetCatalog();
            this.disableDragAndDrop();
            this.saveLayout();
        }
    }
    
    setupWidgetCatalog() {
        const catalog = document.createElement('div');
        catalog.id = 'widget-catalog';
        catalog.className = 'widget-catalog position-fixed bg-white shadow-lg rounded';
        catalog.style.cssText = `
            left: 20px; top: 80px; width: 300px; max-height: 80vh; 
            overflow-y: auto; z-index: 1040; display: none; 
            border: 2px solid #007bff; padding: 20px;
        `;
        
        catalog.innerHTML = `
            <h5 class="mb-3"><i class="fas fa-puzzle-piece me-2"></i>Widget Catalog</h5>
            <div class="widget-list">
                ${this.getAvailableWidgets().map(widget => `
                    <div class="widget-item mb-2 p-3 border rounded cursor-pointer hover-lift" 
                         draggable="true" data-widget-type="${widget.type}">
                        <div class="d-flex align-items-center">
                            <i class="${widget.icon} me-2 text-primary"></i>
                            <div>
                                <strong>${widget.name}</strong>
                                <small class="d-block text-muted">${widget.description}</small>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <hr>
            <button class="btn btn-success btn-sm w-100" onclick="dashboardBuilder.saveLayout()">
                <i class="fas fa-save me-2"></i>Save Layout
            </button>
        `;
        
        document.body.appendChild(catalog);
    }
    
    getAvailableWidgets() {
        return [
            {
                type: 'asset-metrics',
                name: 'Asset Metrics',
                icon: 'fas fa-truck',
                description: 'Total and active asset counts'
            },
            {
                type: 'revenue-chart',
                name: 'Revenue Chart',
                icon: 'fas fa-chart-line',
                description: 'Monthly revenue tracking'
            },
            {
                type: 'driver-status',
                name: 'Driver Status',
                icon: 'fas fa-users',
                description: 'Active driver dashboard'
            },
            {
                type: 'alert-feed',
                name: 'Live Alerts',
                icon: 'fas fa-bell',
                description: 'Real-time system alerts'
            },
            {
                type: 'utilization-gauge',
                name: 'Utilization Gauge',
                icon: 'fas fa-tachometer-alt',
                description: 'Fleet utilization percentage'
            },
            {
                type: 'quick-actions',
                name: 'Quick Actions',
                icon: 'fas fa-bolt',
                description: 'Common task shortcuts'
            },
            {
                type: 'gps-map',
                name: 'GPS Mini Map',
                icon: 'fas fa-map',
                description: 'Live asset locations'
            },
            {
                type: 'maintenance-alerts',
                name: 'Maintenance Alerts',
                icon: 'fas fa-wrench',
                description: 'Upcoming maintenance'
            }
        ];
    }
    
    setupDragAndDrop() {
        document.addEventListener('dragstart', (e) => {
            if (this.isEditMode && e.target.classList.contains('widget-item')) {
                this.draggedElement = e.target;
                e.dataTransfer.effectAllowed = 'copy';
            }
        });
        
        document.addEventListener('dragover', (e) => {
            if (this.isEditMode) {
                e.preventDefault();
                this.highlightDropZone(e.target);
            }
        });
        
        document.addEventListener('drop', (e) => {
            if (this.isEditMode && this.draggedElement) {
                e.preventDefault();
                this.handleDrop(e);
            }
        });
    }
    
    enableDragAndDrop() {
        // Make existing dashboard widgets draggable
        document.querySelectorAll('.card, .metric-card, .widget').forEach(element => {
            element.draggable = true;
            element.classList.add('draggable-widget');
            element.addEventListener('dragstart', (e) => {
                this.draggedElement = e.target;
            });
        });
    }
    
    disableDragAndDrop() {
        document.querySelectorAll('.draggable-widget').forEach(element => {
            element.draggable = false;
            element.classList.remove('draggable-widget');
        });
    }
    
    handleDrop(event) {
        const dropZone = this.findDropZone(event.target);
        if (dropZone && this.draggedElement) {
            const widgetType = this.draggedElement.dataset.widgetType;
            
            if (widgetType) {
                // Creating new widget from catalog
                this.createWidget(widgetType, dropZone);
            } else {
                // Moving existing widget
                this.moveWidget(this.draggedElement, dropZone);
            }
            
            this.draggedElement = null;
            this.clearDropZoneHighlights();
        }
    }
    
    createWidget(type, container) {
        const widget = this.generateWidgetHTML(type);
        const widgetElement = document.createElement('div');
        widgetElement.className = 'col-xl-3 col-md-6 mb-4 dashboard-widget';
        widgetElement.innerHTML = widget;
        
        // Add widget with animation
        widgetElement.style.opacity = '0';
        widgetElement.style.transform = 'scale(0.8)';
        container.appendChild(widgetElement);
        
        // Animate in
        setTimeout(() => {
            widgetElement.style.transition = 'all 0.3s ease';
            widgetElement.style.opacity = '1';
            widgetElement.style.transform = 'scale(1)';
        }, 50);
        
        this.setupWidgetAnimations(widgetElement);
    }
    
    generateWidgetHTML(type) {
        const widgets = {
            'asset-metrics': `
                <div class="card border-start border-primary border-4 hover-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h4 class="mb-0">${window.dashboardData?.total_assets || '717'}</h4>
                                <p class="text-muted mb-0">Total Assets</p>
                            </div>
                            <div class="flex-shrink-0">
                                <i class="fas fa-truck fa-2x text-primary"></i>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            'revenue-chart': `
                <div class="card hover-card">
                    <div class="card-header bg-success text-white">
                        <i class="fas fa-chart-line me-2"></i>Revenue Trend
                    </div>
                    <div class="card-body">
                        <canvas id="revenue-mini-chart" width="100" height="60"></canvas>
                        <h5 class="mt-2 mb-0 text-success">$142.8K</h5>
                        <small class="text-muted">Monthly Revenue</small>
                    </div>
                </div>
            `,
            'driver-status': `
                <div class="card border-start border-warning border-4 hover-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h4 class="mb-0">12</h4>
                                <p class="text-muted mb-0">Active Drivers</p>
                                <small class="text-success">3 clocked in</small>
                            </div>
                            <div class="flex-shrink-0">
                                <i class="fas fa-users fa-2x text-warning"></i>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            'utilization-gauge': `
                <div class="card hover-card">
                    <div class="card-body text-center">
                        <div class="utilization-gauge mb-3">
                            <div class="gauge-circle">
                                <span class="gauge-text">85.6%</span>
                            </div>
                        </div>
                        <h6 class="mb-0">Fleet Utilization</h6>
                    </div>
                </div>
            `,
            'quick-actions': `
                <div class="card hover-card">
                    <div class="card-header">
                        <i class="fas fa-bolt me-2"></i>Quick Actions
                    </div>
                    <div class="card-body p-2">
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-outline-primary">Add Asset</button>
                            <button class="btn btn-sm btn-outline-success">View Reports</button>
                            <button class="btn btn-sm btn-outline-info">GPS Tracking</button>
                        </div>
                    </div>
                </div>
            `
        };
        
        return widgets[type] || '<div class="card"><div class="card-body">Widget not found</div></div>';
    }
    
    setupHoverAnimations() {
        // Dynamic hover animations for all dashboard elements
        const style = document.createElement('style');
        style.textContent = `
            .hover-card {
                transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                cursor: pointer;
            }
            
            .hover-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                border-color: var(--bs-primary) !important;
            }
            
            .hover-lift {
                transition: all 0.2s ease;
            }
            
            .hover-lift:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .dashboard-edit-mode .hover-card {
                border: 2px dashed #007bff;
                position: relative;
            }
            
            .dashboard-edit-mode .hover-card::after {
                content: "⋮⋮";
                position: absolute;
                top: 10px;
                right: 10px;
                color: #007bff;
                font-size: 18px;
                font-weight: bold;
            }
            
            .widget-item:hover {
                background: #f8f9fa;
                border-color: #007bff !important;
            }
            
            .drop-zone-highlight {
                background: rgba(0,123,255,0.1) !important;
                border: 2px dashed #007bff !important;
            }
            
            .utilization-gauge .gauge-circle {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: conic-gradient(#28a745 0deg 308deg, #e9ecef 308deg 360deg);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
                position: relative;
            }
            
            .utilization-gauge .gauge-circle::before {
                content: '';
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: white;
                position: absolute;
            }
            
            .gauge-text {
                font-weight: bold;
                font-size: 14px;
                z-index: 1;
            }
            
            .draggable-widget {
                opacity: 0.8;
                cursor: move;
            }
            
            .draggable-widget:hover {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
        
        // Apply hover animations to existing elements
        this.applyHoverAnimations();
    }
    
    applyHoverAnimations() {
        // Add hover classes to dashboard cards
        document.querySelectorAll('.card:not(.hover-card)').forEach(card => {
            card.classList.add('hover-card');
        });
        
        // Add ripple effect to buttons
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', this.createRippleEffect);
        });
    }
    
    createRippleEffect(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.6);
            transform: scale(0);
            animation: ripple 0.6s linear;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        // Add ripple animation if not exists
        if (!document.querySelector('#ripple-animation')) {
            const rippleStyle = document.createElement('style');
            rippleStyle.id = 'ripple-animation';
            rippleStyle.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(rippleStyle);
        }
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
    
    findDropZone(element) {
        // Find the nearest container that can accept widgets
        let current = element;
        while (current && current !== document.body) {
            if (current.classList.contains('row') || 
                current.classList.contains('container') ||
                current.classList.contains('main-content')) {
                return current;
            }
            current = current.parentElement;
        }
        return null;
    }
    
    highlightDropZone(element) {
        this.clearDropZoneHighlights();
        const dropZone = this.findDropZone(element);
        if (dropZone) {
            dropZone.classList.add('drop-zone-highlight');
        }
    }
    
    clearDropZoneHighlights() {
        document.querySelectorAll('.drop-zone-highlight').forEach(el => {
            el.classList.remove('drop-zone-highlight');
        });
    }
    
    showWidgetCatalog() {
        document.getElementById('widget-catalog').style.display = 'block';
    }
    
    hideWidgetCatalog() {
        document.getElementById('widget-catalog').style.display = 'none';
    }
    
    saveLayout() {
        const layout = this.captureCurrentLayout();
        localStorage.setItem('traxovo_dashboard_layout', JSON.stringify(layout));
        
        // Show save confirmation
        this.showNotification('Dashboard layout saved successfully!', 'success');
    }
    
    loadSavedLayout() {
        const saved = localStorage.getItem('traxovo_dashboard_layout');
        if (saved) {
            try {
                this.currentLayout = JSON.parse(saved);
                // Apply saved layout logic here
            } catch (e) {
                console.warn('Failed to load saved layout:', e);
            }
        }
    }
    
    captureCurrentLayout() {
        // Capture current widget positions and types
        const widgets = [];
        document.querySelectorAll('.dashboard-widget').forEach((widget, index) => {
            widgets.push({
                type: widget.dataset.widgetType || 'unknown',
                position: index,
                size: widget.className.includes('col-xl-6') ? 'large' : 'small'
            });
        });
        
        return {
            widgets,
            timestamp: new Date().toISOString()
        };
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible position-fixed`;
        notification.style.cssText = 'top: 20px; left: 50%; transform: translateX(-50%); z-index: 1060; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }
    
    setupWidgetAnimations(widget) {
        // Add specific animations for individual widgets
        widget.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
        });
        
        widget.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
}

// Initialize dashboard layout builder when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardBuilder = new DashboardLayoutBuilder();
});

// Export for global access
window.DashboardLayoutBuilder = DashboardLayoutBuilder;