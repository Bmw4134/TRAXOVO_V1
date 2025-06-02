// TRAXOVO Dashboard Customization - Enterprise Fleet Management
class DashboardCustomizer {
    constructor() {
        this.widgets = [];
        this.layout = 'default';
        this.init();
    }
    
    init() {
        this.loadSavedLayout();
        this.setupDragAndDrop();
        this.bindEvents();
    }
    
    loadSavedLayout() {
        const saved = localStorage.getItem('traxovo_dashboard_layout');
        if (saved) {
            this.layout = JSON.parse(saved);
            this.applyLayout();
        }
    }
    
    applyLayout() {
        // Apply saved dashboard layout
        const widgets = document.querySelectorAll('.widget, .metric-card');
        widgets.forEach((widget, index) => {
            if (this.layout.widgets && this.layout.widgets[index]) {
                const config = this.layout.widgets[index];
                widget.style.order = config.order || index;
                widget.style.display = config.visible !== false ? 'block' : 'none';
            }
        });
    }
    
    setupDragAndDrop() {
        const widgets = document.querySelectorAll('.widget, .metric-card');
        widgets.forEach(widget => {
            widget.setAttribute('draggable', 'true');
            widget.addEventListener('dragstart', this.handleDragStart.bind(this));
            widget.addEventListener('dragover', this.handleDragOver.bind(this));
            widget.addEventListener('drop', this.handleDrop.bind(this));
        });
    }
    
    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.id || 'widget');
    }
    
    handleDragOver(e) {
        e.preventDefault();
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.saveLayout();
    }
    
    bindEvents() {
        // Add customization controls
        const controls = document.createElement('div');
        controls.className = 'dashboard-controls';
        controls.innerHTML = `
            <button class="btn btn-sm btn-outline-primary" onclick="dashboardCustomizer.resetLayout()">
                <i class="bi bi-arrow-clockwise"></i> Reset Layout
            </button>
        `;
        controls.style.cssText = 'position: fixed; top: 10px; right: 100px; z-index: 1000;';
        document.body.appendChild(controls);
    }
    
    saveLayout() {
        const widgets = document.querySelectorAll('.widget, .metric-card');
        const layout = {
            widgets: Array.from(widgets).map((widget, index) => ({
                id: widget.id || `widget-${index}`,
                order: widget.style.order || index,
                visible: widget.style.display !== 'none'
            }))
        };
        localStorage.setItem('traxovo_dashboard_layout', JSON.stringify(layout));
    }
    
    resetLayout() {
        localStorage.removeItem('traxovo_dashboard_layout');
        location.reload();
    }
}

const dashboardCustomizer = new DashboardCustomizer();