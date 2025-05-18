/**
 * TRAXORA Quick Actions System
 * 
 * This module manages the floating quick action button tray
 * that provides context-sensitive shortcuts based on user role and behavior.
 */

class QuickActionsManager {
    constructor() {
        this.container = null;
        this.trigger = null;
        this.menu = null;
        this.isOpen = false;
        this.userRole = this.getUserRole();
        this.recentActions = this.loadRecentActions() || [];
        this.currentContext = this.determineContext();
        
        this.actionDefinitions = {
            'daily_report': {
                icon: 'bi-calendar-day',
                label: 'Daily Driver Report',
                url: '/daily_report',
                color: 'action-primary',
                roles: ['all']
            },
            'upload_pm': {
                icon: 'bi-upload',
                label: 'Upload PM Files',
                url: '/pm_allocation',
                color: 'action-success',
                roles: ['all']
            },
            'asset_map': {
                icon: 'bi-geo-alt',
                label: 'Asset Map',
                url: '/assets/map',
                color: 'action-info',
                roles: ['all']
            },
            'add_asset': {
                icon: 'bi-plus-circle',
                label: 'Add New Asset',
                url: '#add-asset-modal',
                color: 'action-primary',
                roles: ['admin', 'manager'],
                isModal: true
            },
            'schedule_maintenance': {
                icon: 'bi-tools',
                label: 'Schedule Maintenance',
                url: '#schedule-maintenance',
                color: 'action-warning',
                roles: ['admin', 'manager']
            },
            'export_report': {
                icon: 'bi-file-earmark-arrow-down',
                label: 'Export Report',
                url: '#export-report-modal',
                color: 'action-info',
                roles: ['all'],
                isModal: true
            },
            'view_alerts': {
                icon: 'bi-bell',
                label: 'View Alerts',
                url: '#alerts',
                color: 'action-danger',
                roles: ['all'],
                badge: true
            },
            'ocr_tool': {
                icon: 'bi-file-text',
                label: 'OCR Tool',
                url: '/ocr_tool',
                color: 'action-primary',
                roles: ['all']
            }
        };
        
        this.init();
    }
    
    init() {
        this.createQuickActionsUI();
        this.setupEventListeners();
        this.updateQuickActions();
    }
    
    // Create the Quick Actions UI elements
    createQuickActionsUI() {
        // Create container
        this.container = document.createElement('div');
        this.container.className = 'quick-actions-container';
        
        // Create main trigger button
        this.trigger = document.createElement('div');
        this.trigger.className = 'quick-actions-trigger';
        this.trigger.innerHTML = '<i class="bi bi-plus-lg fs-4"></i>';
        
        // Create menu
        this.menu = document.createElement('div');
        this.menu.className = 'quick-actions-menu';
        
        // Add to DOM
        this.container.appendChild(this.menu);
        this.container.appendChild(this.trigger);
        document.body.appendChild(this.container);
    }
    
    // Set up event listeners
    setupEventListeners() {
        // Toggle menu on trigger click
        this.trigger.addEventListener('click', () => {
            this.toggleMenu();
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.container.contains(e.target)) {
                this.closeMenu();
            }
        });
        
        // Track action usage for priority adjustment
        document.addEventListener('click', (e) => {
            const actionLink = e.target.closest('[data-quick-action]');
            if (actionLink) {
                const actionId = actionLink.dataset.quickAction;
                this.recordActionUsage(actionId);
            }
        });
        
        // Listen for context changes
        document.addEventListener('contextChanged', (e) => {
            this.currentContext = e.detail.context;
            this.updateQuickActions();
        });
    }
    
    // Toggle the quick actions menu
    toggleMenu() {
        if (this.isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }
    
    // Open the quick actions menu
    openMenu() {
        this.isOpen = true;
        this.trigger.classList.add('is-active');
        this.menu.classList.add('is-active');
    }
    
    // Close the quick actions menu
    closeMenu() {
        this.isOpen = false;
        this.trigger.classList.remove('is-active');
        this.menu.classList.remove('is-active');
    }
    
    // Update the quick actions based on current context and user role
    updateQuickActions() {
        // Clear existing actions
        this.menu.innerHTML = '';
        
        // Get priority actions for current context and user role
        const priorityActions = this.getPriorityActions();
        
        // Create action items in the menu
        priorityActions.forEach(actionId => {
            const action = this.actionDefinitions[actionId];
            if (!action) return;
            
            // Check if user has permission for this action
            if (this.hasPermission(action.roles)) {
                const actionItem = this.createActionItem(actionId, action);
                this.menu.appendChild(actionItem);
            }
        });
    }
    
    // Create an individual quick action item
    createActionItem(actionId, action) {
        const actionItem = document.createElement('div');
        actionItem.className = 'quick-action-item';
        
        const actionBtn = document.createElement('a');
        actionBtn.className = `quick-action-btn ${action.color}`;
        actionBtn.href = action.url;
        actionBtn.innerHTML = `<i class="bi ${action.icon}"></i>`;
        actionBtn.setAttribute('data-quick-action', actionId);
        
        // If it's a modal trigger
        if (action.isModal) {
            actionBtn.setAttribute('data-bs-toggle', 'modal');
            actionBtn.setAttribute('data-bs-target', action.url);
        }
        
        const actionLabel = document.createElement('div');
        actionLabel.className = 'quick-action-label';
        actionLabel.textContent = action.label;
        
        // Add badge if specified
        if (action.badge) {
            const badge = document.createElement('div');
            badge.className = 'quick-action-badge';
            badge.textContent = this.getBadgeCount(actionId);
            
            // Only show badge if there are items
            if (parseInt(badge.textContent) > 0) {
                actionBtn.appendChild(badge);
                actionBtn.classList.add('quick-action-pulse');
            }
        }
        
        actionItem.appendChild(actionBtn);
        actionItem.appendChild(actionLabel);
        
        return actionItem;
    }
    
    // Get the user's role (can be extended to use actual authentication)
    getUserRole() {
        // This would normally be determined from the authenticated user's information
        // For now, default to 'all' which is visible to everyone
        return 'all';
    }
    
    // Check if the user has permission for the specified roles
    hasPermission(requiredRoles) {
        if (requiredRoles.includes('all')) return true;
        
        // If user is admin, they can access everything
        if (this.userRole === 'admin') return true;
        
        // Check if user role is in the required roles
        return requiredRoles.includes(this.userRole);
    }
    
    // Determine the current application context based on URL and page elements
    determineContext() {
        const path = window.location.pathname.toLowerCase();
        
        if (path.includes('asset')) return 'assets';
        if (path.includes('pm_allocation') || path.includes('billing')) return 'billing';
        if (path.includes('daily_report') || path.includes('attendance')) return 'attendance';
        if (path.includes('maintenance')) return 'maintenance';
        if (path.includes('job') || path.includes('zone')) return 'jobzones';
        if (path.includes('admin')) return 'admin';
        if (path.includes('report')) return 'reports';
        
        // Default to dashboard context
        return 'dashboard';
    }
    
    // Get priority actions based on context, user role, and recent history
    getPriorityActions() {
        // Base priorities for each context
        const contextPriorities = {
            'dashboard': ['daily_report', 'asset_map', 'upload_pm', 'view_alerts'],
            'assets': ['asset_map', 'add_asset', 'daily_report', 'schedule_maintenance'],
            'billing': ['upload_pm', 'export_report', 'daily_report', 'ocr_tool'],
            'attendance': ['daily_report', 'export_report', 'asset_map', 'view_alerts'],
            'maintenance': ['schedule_maintenance', 'asset_map', 'export_report', 'daily_report'],
            'jobzones': ['asset_map', 'daily_report', 'view_alerts', 'export_report'],
            'admin': ['view_alerts', 'add_asset', 'export_report', 'upload_pm'],
            'reports': ['export_report', 'daily_report', 'asset_map', 'ocr_tool']
        };
        
        // Get base priorities for current context
        let priorities = contextPriorities[this.currentContext] || contextPriorities['dashboard'];
        
        // Adjust based on recent action history
        if (this.recentActions.length > 0) {
            // Get the most used actions
            const actionCounts = {};
            this.recentActions.forEach(action => {
                actionCounts[action] = (actionCounts[action] || 0) + 1;
            });
            
            // Sort by count
            const sortedActions = Object.keys(actionCounts)
                .sort((a, b) => actionCounts[b] - actionCounts[a])
                .filter(action => this.actionDefinitions[action]); // Filter out unknown actions
            
            // Promote most used action to the top if it's not already
            if (sortedActions.length > 0 && !priorities.slice(0, 2).includes(sortedActions[0])) {
                // Add to beginning and remove from later in the array if it exists
                const topAction = sortedActions[0];
                priorities = [topAction, ...priorities.filter(a => a !== topAction)].slice(0, 4);
            }
        }
        
        return priorities;
    }
    
    // Record action usage for priority adjustment
    recordActionUsage(actionId) {
        if (!this.actionDefinitions[actionId]) return;
        
        // Add to recent actions
        this.recentActions.unshift(actionId);
        
        // Limit to last 20 actions
        if (this.recentActions.length > 20) {
            this.recentActions = this.recentActions.slice(0, 20);
        }
        
        // Save to localStorage
        localStorage.setItem('traxora_recent_actions', JSON.stringify(this.recentActions));
    }
    
    // Load recent actions from localStorage
    loadRecentActions() {
        const savedActions = localStorage.getItem('traxora_recent_actions');
        return savedActions ? JSON.parse(savedActions) : [];
    }
    
    // Get badge count for notifications
    getBadgeCount(actionId) {
        // This would normally be populated from API data
        // For demonstration, we'll use a placeholder count
        if (actionId === 'view_alerts') {
            // Check for alert count in localStorage for demo purposes
            const alertCount = localStorage.getItem('traxora_alert_count');
            return alertCount || '0';
        }
        
        return '0';
    }
    
    // Programmatically set the alert count (for demo/testing)
    setAlertCount(count) {
        localStorage.setItem('traxora_alert_count', count.toString());
        this.updateQuickActions();
    }
}

// Initialize the quick actions when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add link to quick-actions.css
    const styleLink = document.createElement('link');
    styleLink.rel = 'stylesheet';
    styleLink.href = '/static/css/quick-actions.css';
    document.head.appendChild(styleLink);
    
    // Initialize quick actions
    window.quickActions = new QuickActionsManager();
    
    // Demo: Set a random alert count every 30 seconds
    setInterval(() => {
        const randomCount = Math.floor(Math.random() * 5);
        window.quickActions.setAlertCount(randomCount);
    }, 30000);
});