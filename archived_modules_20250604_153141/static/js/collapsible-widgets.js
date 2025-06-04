// Collapsible Widgets System - Clean and Minimalist
class CollapsibleWidgets {
    constructor() {
        this.isExpanded = false;
        this.widgets = [];
        this.notifications = 0;
        this.init();
    }
    
    init() {
        this.createWidgetContainer();
        this.loadWidgets();
        this.setupEventListeners();
        console.log('Collapsible Widgets: INITIALIZED');
    }
    
    createWidgetContainer() {
        // Remove existing widget containers that are in-your-face
        const existingContainers = document.querySelectorAll('.nudges-container, .widget-grid, .dashboard-widgets');
        existingContainers.forEach(container => {
            if (container.style.position !== 'fixed' || !container.classList.contains('collapsible')) {
                container.style.display = 'none';
            }
        });
        
        // Create clean, minimalist widget container
        const container = document.createElement('div');
        container.className = 'widget-container collapsible';
        container.innerHTML = `
            <button class="widget-toggle" id="widget-toggle">
                <i class="fas fa-layer-group"></i>
                <span class="widget-badge" id="widget-badge" style="display: none;">0</span>
            </button>
            <div class="widget-panel" id="widget-panel">
                <div class="widget-header">
                    <h6>Smart Insights</h6>
                </div>
                <div class="widget-content" id="widget-content">
                    <div class="widget-item">
                        <div class="widget-item-title">Loading insights...</div>
                        <div class="widget-item-desc">Analyzing operational data</div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    setupEventListeners() {
        const toggle = document.getElementById('widget-toggle');
        const container = document.querySelector('.widget-container');
        
        toggle.addEventListener('click', () => {
            this.isExpanded = !this.isExpanded;
            
            if (this.isExpanded) {
                container.classList.add('expanded');
                this.loadWidgets();
            } else {
                container.classList.remove('expanded');
            }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target) && this.isExpanded) {
                this.isExpanded = false;
                container.classList.remove('expanded');
            }
        });
    }
    
    loadWidgets() {
        // Load productivity nudges
        fetch('/api/contextual-nudges')
            .then(response => response.json())
            .then(data => {
                this.renderProductivityNudges(data.nudges);
            })
            .catch(error => console.error('Widget loading error:', error));
            
        // Load system insights
        this.loadSystemInsights();
    }
    
    renderProductivityNudges(nudges) {
        const content = document.getElementById('widget-content');
        let html = '';
        
        if (nudges && Object.keys(nudges).length > 0) {
            Object.entries(nudges).forEach(([key, nudge], index) => {
                const priority = index === 0 ? 'high-priority' : index === 1 ? 'medium-priority' : 'low-priority';
                
                html += `
                    <div class="widget-item nudge ${priority}">
                        <div class="widget-item-title">${this.formatNudgeTitle(key)}</div>
                        <div class="widget-item-desc">${nudge}</div>
                        <div class="widget-item-meta">
                            <span class="widget-savings">Potential Savings</span>
                            <span style="font-size: 10px; color: #95a5a6;">Just now</span>
                        </div>
                        <div class="widget-actions">
                            <button class="widget-btn primary" onclick="this.applyNudge('${key}')">Apply</button>
                            <button class="widget-btn secondary" onclick="this.dismissNudge('${key}')">Later</button>
                        </div>
                    </div>
                `;
            });
            
            this.notifications = Object.keys(nudges).length;
        } else {
            html = `
                <div class="widget-item insight">
                    <div class="widget-item-title">All systems optimized</div>
                    <div class="widget-item-desc">No immediate actions required</div>
                </div>
            `;
            this.notifications = 0;
        }
        
        content.innerHTML = html;
        this.updateNotificationBadge();
    }
    
    loadSystemInsights() {
        // Add UI/UX validation insights
        fetch('/api/ui-ux-validation')
            .then(response => response.json())
            .then(data => {
                this.addSystemInsight({
                    title: 'UI/UX Optimization',
                    desc: `${data.improvement_score}% consistency achieved`,
                    type: 'insight',
                    priority: 'low'
                });
            })
            .catch(error => console.log('UI validation unavailable'));
    }
    
    addSystemInsight(insight) {
        const content = document.getElementById('widget-content');
        const insightHtml = `
            <div class="widget-item ${insight.type} ${insight.priority}-priority">
                <div class="widget-item-title">${insight.title}</div>
                <div class="widget-item-desc">${insight.desc}</div>
            </div>
        `;
        
        content.insertAdjacentHTML('beforeend', insightHtml);
    }
    
    formatNudgeTitle(key) {
        return key.replace(/_/g, ' ')
                 .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    updateNotificationBadge() {
        const badge = document.getElementById('widget-badge');
        const toggle = document.getElementById('widget-toggle');
        
        if (this.notifications > 0) {
            badge.textContent = this.notifications;
            badge.style.display = 'flex';
            toggle.classList.add('has-notifications');
        } else {
            badge.style.display = 'none';
            toggle.classList.remove('has-notifications');
        }
    }
    
    applyNudge(nudgeKey) {
        // Apply the nudge action
        fetch('/api/qq/patch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nudge: nudgeKey, action: 'apply' })
        }).then(response => response.json())
          .then(data => {
              this.showFeedback('Applied: ' + this.formatNudgeTitle(nudgeKey));
              this.loadWidgets(); // Refresh
          });
    }
    
    dismissNudge(nudgeKey) {
        // Dismiss the nudge
        this.showFeedback('Dismissed: ' + this.formatNudgeTitle(nudgeKey));
        this.loadWidgets(); // Refresh
    }
    
    showFeedback(message) {
        // Simple feedback toast
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #27ae60;
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 13px;
            z-index: 9999;
            animation: fadeInOut 3s ease;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Auto-hide existing widgets and initialize collapsible system
document.addEventListener('DOMContentLoaded', function() {
    // Hide aggressive widget displays
    const aggressiveWidgets = document.querySelectorAll(
        '.nudges-container:not(.collapsible), ' +
        '.widget-grid:not(.collapsible), ' +
        '.dashboard-widgets:not(.collapsible), ' +
        '.productivity-nudges:not(.collapsible)'
    );
    
    aggressiveWidgets.forEach(widget => {
        widget.style.opacity = '0';
        widget.style.pointerEvents = 'none';
        widget.style.position = 'absolute';
        widget.style.left = '-9999px';
    });
    
    // Initialize clean collapsible widgets
    window.collapsibleWidgets = new CollapsibleWidgets();
});

// CSS Animation for feedback toast
const toastStyle = document.createElement('style');
toastStyle.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-20px); }
        15% { opacity: 1; transform: translateY(0); }
        85% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-20px); }
    }
`;
document.head.appendChild(toastStyle);