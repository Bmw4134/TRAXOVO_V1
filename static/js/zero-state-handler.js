/**
 * TRAXORA Zero-State Learning System
 * 
 * This module detects and responds to "zero-state" conditions in the application,
 * providing contextual guidance and tracking which areas cause confusion or stalling.
 * It builds a profile of how users interact with empty states to improve the UX.
 */

class ZeroStateHandler {
    constructor() {
        this.zeroStates = this.loadZeroStates();
        this.userInteractions = this.loadInteractions();
        this.showCount = this.loadShowCount();
        this.init();
    }
    
    init() {
        // Initialize zero state detection
        this.detectZeroStates();
        
        // Track user interactions with zero states
        this.setupInteractionTracking();
        
        // Track which zero states are dismissed/ignored vs interacted with
        window.addEventListener('beforeunload', () => {
            this.saveZeroStates();
            this.saveInteractions();
            this.saveShowCount();
        });
    }
    
    // Load saved zero states from localStorage
    loadZeroStates() {
        const savedStates = localStorage.getItem('traxora_zero_states');
        return savedStates ? JSON.parse(savedStates) : {
            assets: { encountered: false, dismissed: false },
            reports: { encountered: false, dismissed: false },
            drivers: { encountered: false, dismissed: false },
            billing: { encountered: false, dismissed: false },
            maintenance: { encountered: false, dismissed: false },
            alerts: { encountered: false, dismissed: false }
        };
    }
    
    // Save zero states to localStorage
    saveZeroStates() {
        localStorage.setItem('traxora_zero_states', JSON.stringify(this.zeroStates));
    }
    
    // Load saved interactions from localStorage
    loadInteractions() {
        const savedInteractions = localStorage.getItem('traxora_zero_interactions');
        return savedInteractions ? JSON.parse(savedInteractions) : {};
    }
    
    // Save interactions to localStorage
    saveInteractions() {
        localStorage.setItem('traxora_zero_interactions', JSON.stringify(this.userInteractions));
    }
    
    // Load show count from localStorage
    loadShowCount() {
        const savedCount = localStorage.getItem('traxora_zero_show_count');
        return savedCount ? JSON.parse(savedCount) : {};
    }
    
    // Save show count to localStorage
    saveShowCount() {
        localStorage.setItem('traxora_zero_show_count', JSON.stringify(this.showCount));
    }
    
    // Detect zero states on the current page
    detectZeroStates() {
        // Check for generic zero-state markers
        document.querySelectorAll('[data-zero-state]').forEach(element => {
            const stateType = element.dataset.zeroState;
            
            // Mark this zero state as encountered
            if (this.zeroStates[stateType]) {
                this.zeroStates[stateType].encountered = true;
                
                // Track how many times this zero state has been shown
                this.showCount[stateType] = (this.showCount[stateType] || 0) + 1;
                
                // Only show guidance if not previously dismissed
                if (!this.zeroStates[stateType].dismissed) {
                    this.showZeroStateGuidance(element, stateType);
                }
            }
        });
        
        // Detect empty tables
        document.querySelectorAll('table.table').forEach(table => {
            const tbody = table.querySelector('tbody');
            if (tbody && (!tbody.children.length || (tbody.children.length === 1 && tbody.textContent.trim().includes('No data')))) {
                const tableId = table.id || '';
                const stateType = this.inferZeroStateTypeFromTable(table);
                
                if (stateType && this.zeroStates[stateType]) {
                    this.zeroStates[stateType].encountered = true;
                    this.showCount[stateType] = (this.showCount[stateType] || 0) + 1;
                    
                    if (!this.zeroStates[stateType].dismissed) {
                        this.injectEmptyTableGuidance(table, stateType);
                    }
                }
            }
        });
        
        // Detect empty lists
        document.querySelectorAll('.list-group, .list-container').forEach(list => {
            if (!list.children.length || (list.children.length === 1 && list.textContent.trim().includes('No items'))) {
                const listId = list.id || '';
                const stateType = this.inferZeroStateTypeFromContainer(list);
                
                if (stateType && this.zeroStates[stateType]) {
                    this.zeroStates[stateType].encountered = true;
                    this.showCount[stateType] = (this.showCount[stateType] || 0) + 1;
                    
                    if (!this.zeroStates[stateType].dismissed) {
                        this.injectEmptyListGuidance(list, stateType);
                    }
                }
            }
        });
        
        // Detect empty dashboards
        document.querySelectorAll('.dashboard-container, .card-container').forEach(container => {
            const hasNoData = Array.from(container.querySelectorAll('.card, .dashboard-item')).every(item => 
                item.textContent.includes('No data') || 
                item.querySelector('.no-data') ||
                item.classList.contains('empty-state')
            );
            
            if (hasNoData) {
                const containerId = container.id || '';
                const stateType = this.inferZeroStateTypeFromContainer(container);
                
                if (stateType && this.zeroStates[stateType]) {
                    this.zeroStates[stateType].encountered = true;
                    this.showCount[stateType] = (this.showCount[stateType] || 0) + 1;
                    
                    if (!this.zeroStates[stateType].dismissed) {
                        this.injectEmptyDashboardGuidance(container, stateType);
                    }
                }
            }
        });
    }
    
    // Setup tracking of user interactions with zero states
    setupInteractionTracking() {
        // Track interactions with zero state guidance
        document.addEventListener('click', e => {
            const guidance = e.target.closest('.zero-state-guidance');
            if (!guidance) return;
            
            const stateType = guidance.dataset.zeroStateType;
            const actionType = e.target.dataset.zeroAction || 'general_click';
            
            // Record this interaction
            this.recordZeroStateInteraction(stateType, actionType, {
                element: e.target.textContent.trim(),
                timestamp: new Date().toISOString()
            });
            
            // If this is a dismiss action, mark the zero state as dismissed
            if (actionType === 'dismiss') {
                if (this.zeroStates[stateType]) {
                    this.zeroStates[stateType].dismissed = true;
                }
                
                // Remove the guidance
                guidance.classList.add('fade-out');
                setTimeout(() => {
                    guidance.remove();
                }, 300);
                
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
    
    // Record a user interaction with a zero state
    recordZeroStateInteraction(stateType, actionType, details = {}) {
        if (!this.userInteractions[stateType]) {
            this.userInteractions[stateType] = [];
        }
        
        this.userInteractions[stateType].push({
            action: actionType,
            details: details,
            count: this.showCount[stateType] || 1,
            timestamp: new Date().toISOString()
        });
    }
    
    // Show guidance for a generic zero state
    showZeroStateGuidance(element, stateType) {
        // Generate guidance content based on state type
        const guidance = this.getGuidanceContent(stateType);
        
        // Create guidance element
        const guidanceEl = document.createElement('div');
        guidanceEl.className = 'zero-state-guidance';
        guidanceEl.dataset.zeroStateType = stateType;
        guidanceEl.innerHTML = `
            <div class="card shadow-sm border-info">
                <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="${guidance.icon} me-2"></i>
                        ${guidance.title}
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-zero-action="dismiss" aria-label="Close"></button>
                </div>
                <div class="card-body">
                    <p>${guidance.message}</p>
                    <div class="d-flex gap-2">
                        ${guidance.actions.map(action => `
                            <a href="${action.url}" class="btn btn-${action.type}" data-zero-action="${action.action}">
                                <i class="${action.icon} me-1"></i> ${action.text}
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Insert guidance before or after the element based on position preference
        if (guidance.position === 'before') {
            element.parentNode.insertBefore(guidanceEl, element);
        } else {
            // Find next sibling
            const nextSibling = element.nextSibling;
            if (nextSibling) {
                element.parentNode.insertBefore(guidanceEl, nextSibling);
            } else {
                element.parentNode.appendChild(guidanceEl);
            }
        }
    }
    
    // Inject guidance for an empty table
    injectEmptyTableGuidance(table, stateType) {
        const guidance = this.getGuidanceContent(stateType);
        
        // Create guidance row
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Check if we already have a no-data row
        let existingRow = tbody.querySelector('.no-data-row, .empty-row');
        
        if (existingRow) {
            // Replace existing empty message with our guidance
            existingRow.innerHTML = `
                <td colspan="${this.getTableColumnCount(table)}" class="zero-state-guidance" data-zero-state-type="${stateType}">
                    <div class="alert alert-info mb-0">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0">
                                <i class="${guidance.icon} fs-3 me-3"></i>
                            </div>
                            <div class="flex-grow-1 ms-3">
                                <h5>${guidance.title}</h5>
                                <p class="mb-1">${guidance.message}</p>
                                <div class="d-flex gap-2 mt-2">
                                    ${guidance.actions.map(action => `
                                        <a href="${action.url}" class="btn btn-sm btn-${action.type}" data-zero-action="${action.action}">
                                            <i class="${action.icon} me-1"></i> ${action.text}
                                        </a>
                                    `).join('')}
                                    <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" data-zero-action="dismiss">
                                        <i class="bi bi-x-lg me-1"></i> Dismiss
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            `;
        } else {
            // Create new guidance row
            const row = document.createElement('tr');
            row.className = 'zero-state-row';
            row.innerHTML = `
                <td colspan="${this.getTableColumnCount(table)}" class="zero-state-guidance" data-zero-state-type="${stateType}">
                    <div class="alert alert-info mb-0">
                        <div class="d-flex align-items-center">
                            <div class="flex-shrink-0">
                                <i class="${guidance.icon} fs-3 me-3"></i>
                            </div>
                            <div class="flex-grow-1 ms-3">
                                <h5>${guidance.title}</h5>
                                <p class="mb-1">${guidance.message}</p>
                                <div class="d-flex gap-2 mt-2">
                                    ${guidance.actions.map(action => `
                                        <a href="${action.url}" class="btn btn-sm btn-${action.type}" data-zero-action="${action.action}">
                                            <i class="${action.icon} me-1"></i> ${action.text}
                                        </a>
                                    `).join('')}
                                    <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" data-zero-action="dismiss">
                                        <i class="bi bi-x-lg me-1"></i> Dismiss
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        }
    }
    
    // Inject guidance for an empty list
    injectEmptyListGuidance(list, stateType) {
        const guidance = this.getGuidanceContent(stateType);
        
        // Create guidance element
        const guidanceEl = document.createElement('div');
        guidanceEl.className = 'list-group-item zero-state-guidance';
        guidanceEl.dataset.zeroStateType = stateType;
        guidanceEl.innerHTML = `
            <div class="alert alert-info mb-0">
                <div class="d-flex align-items-center">
                    <div class="flex-shrink-0">
                        <i class="${guidance.icon} fs-3 me-3"></i>
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <h5>${guidance.title}</h5>
                        <p class="mb-1">${guidance.message}</p>
                        <div class="d-flex gap-2 mt-2">
                            ${guidance.actions.map(action => `
                                <a href="${action.url}" class="btn btn-sm btn-${action.type}" data-zero-action="${action.action}">
                                    <i class="${action.icon} me-1"></i> ${action.text}
                                </a>
                            `).join('')}
                            <button type="button" class="btn btn-sm btn-outline-secondary ms-auto" data-zero-action="dismiss">
                                <i class="bi bi-x-lg me-1"></i> Dismiss
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Check if there's already an empty state message
        const existingEmpty = list.querySelector('.empty-message, .no-items-message');
        if (existingEmpty) {
            // Replace existing message
            existingEmpty.replaceWith(guidanceEl);
        } else {
            // Add as first item
            if (list.firstChild) {
                list.insertBefore(guidanceEl, list.firstChild);
            } else {
                list.appendChild(guidanceEl);
            }
        }
    }
    
    // Inject guidance for an empty dashboard
    injectEmptyDashboardGuidance(container, stateType) {
        const guidance = this.getGuidanceContent(stateType);
        
        // Create guidance element
        const guidanceEl = document.createElement('div');
        guidanceEl.className = 'card shadow-sm mb-4 zero-state-guidance';
        guidanceEl.dataset.zeroStateType = stateType;
        guidanceEl.innerHTML = `
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="${guidance.icon} me-2"></i>
                    ${guidance.title}
                </h5>
                <button type="button" class="btn-close btn-close-white" data-zero-action="dismiss" aria-label="Close"></button>
            </div>
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <p class="lead">${guidance.message}</p>
                        <div class="d-flex gap-2 mt-3">
                            ${guidance.actions.map(action => `
                                <a href="${action.url}" class="btn btn-${action.type}" data-zero-action="${action.action}">
                                    <i class="${action.icon} me-1"></i> ${action.text}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                    <div class="col-md-4 text-center mt-3 mt-md-0">
                        <i class="bi bi-bar-chart-fill text-info" style="font-size: 5rem;"></i>
                    </div>
                </div>
            </div>
        `;
        
        // Insert at the top of container
        if (container.firstChild) {
            container.insertBefore(guidanceEl, container.firstChild);
        } else {
            container.appendChild(guidanceEl);
        }
    }
    
    // Get guidance content based on zero state type
    getGuidanceContent(stateType) {
        switch (stateType) {
            case 'assets':
                return {
                    title: 'No Assets Found',
                    message: 'It looks like you haven\'t added any assets yet. Assets represent vehicles, equipment, or other tracked items in your fleet.',
                    icon: 'bi bi-truck',
                    position: 'before',
                    actions: [
                        { text: 'Connect to API', url: '#api-connect', action: 'api_connect', icon: 'bi bi-cloud-arrow-down', type: 'primary' },
                        { text: 'Import Assets', url: '#import-assets', action: 'import_assets', icon: 'bi bi-upload', type: 'outline-primary' },
                        { text: 'Add Manually', url: '#add-asset', action: 'add_asset', icon: 'bi bi-plus-circle', type: 'outline-secondary' }
                    ]
                };
                
            case 'reports':
                return {
                    title: 'No Reports Available',
                    message: 'You haven\'t generated any reports yet. Reports provide insights into your fleet operations and help you make data-driven decisions.',
                    icon: 'bi bi-file-earmark-text',
                    position: 'before',
                    actions: [
                        { text: 'Generate Report', url: '#generate-report', action: 'generate_report', icon: 'bi bi-file-earmark-plus', type: 'primary' },
                        { text: 'View Templates', url: '#report-templates', action: 'view_templates', icon: 'bi bi-columns-gap', type: 'outline-secondary' }
                    ]
                };
                
            case 'drivers':
                return {
                    title: 'No Drivers Listed',
                    message: 'Your driver roster is empty. Drivers can be assigned to assets and tracked for performance and compliance.',
                    icon: 'bi bi-person-badge',
                    position: 'before',
                    actions: [
                        { text: 'Add Driver', url: '#add-driver', action: 'add_driver', icon: 'bi bi-person-plus', type: 'primary' },
                        { text: 'Import Drivers', url: '#import-drivers', action: 'import_drivers', icon: 'bi bi-upload', type: 'outline-primary' }
                    ]
                };
                
            case 'billing':
                return {
                    title: 'No Billing Data Found',
                    message: 'There is no billing data available. Upload your PM allocation files to track and reconcile billing information.',
                    icon: 'bi bi-calculator',
                    position: 'before',
                    actions: [
                        { text: 'Upload PM Files', url: '/pm_allocation', action: 'upload_pm', icon: 'bi bi-upload', type: 'primary' },
                        { text: 'Auto-Detect Files', url: '/auto_process_pm_allocation', action: 'auto_detect', icon: 'bi bi-magic', type: 'outline-secondary' }
                    ]
                };
                
            case 'maintenance':
                return {
                    title: 'No Maintenance Records',
                    message: 'You haven\'t added any maintenance records yet. Keep track of repairs, services, and regular maintenance for your assets.',
                    icon: 'bi bi-tools',
                    position: 'after',
                    actions: [
                        { text: 'Schedule Maintenance', url: '#schedule-maintenance', action: 'schedule_maintenance', icon: 'bi bi-calendar-plus', type: 'primary' },
                        { text: 'View History', url: '#maintenance-history', action: 'view_history', icon: 'bi bi-clock-history', type: 'outline-secondary' }
                    ]
                };
                
            case 'alerts':
                return {
                    title: 'No Active Alerts',
                    message: 'There are currently no alerts in the system. Alerts notify you of important events or issues that require attention.',
                    icon: 'bi bi-bell',
                    position: 'after',
                    actions: [
                        { text: 'Set Up Notifications', url: '#notification-settings', action: 'setup_notifications', icon: 'bi bi-gear', type: 'primary' },
                        { text: 'View History', url: '#alert-history', action: 'view_history', icon: 'bi bi-clock-history', type: 'outline-secondary' }
                    ]
                };
                
            default:
                return {
                    title: 'No Data Available',
                    message: 'There\'s no data to display at the moment. Get started by adding some information or importing data.',
                    icon: 'bi bi-info-circle',
                    position: 'before',
                    actions: [
                        { text: 'Get Started', url: '#', action: 'get_started', icon: 'bi bi-play-fill', type: 'primary' },
                        { text: 'Learn More', url: '#', action: 'learn_more', icon: 'bi bi-book', type: 'outline-secondary' }
                    ]
                };
        }
    }
    
    // Infer zero state type from a table
    inferZeroStateTypeFromTable(table) {
        const tableId = table.id || '';
        const tableClass = table.className || '';
        const tableCaption = table.querySelector('caption')?.textContent || '';
        const tableHeader = table.querySelector('thead')?.textContent || '';
        
        // Combine all text for better inference
        const combinedText = `${tableId} ${tableClass} ${tableCaption} ${tableHeader}`.toLowerCase();
        
        if (combinedText.includes('asset') || combinedText.includes('vehicle') || combinedText.includes('equipment')) {
            return 'assets';
        }
        
        if (combinedText.includes('report') || combinedText.includes('export')) {
            return 'reports';
        }
        
        if (combinedText.includes('driver') || combinedText.includes('employee') || combinedText.includes('staff')) {
            return 'drivers';
        }
        
        if (combinedText.includes('bill') || combinedText.includes('invoice') || combinedText.includes('payment') || combinedText.includes('allocation')) {
            return 'billing';
        }
        
        if (combinedText.includes('maintenance') || combinedText.includes('repair') || combinedText.includes('service')) {
            return 'maintenance';
        }
        
        if (combinedText.includes('alert') || combinedText.includes('notification') || combinedText.includes('warning')) {
            return 'alerts';
        }
        
        // Check the current URL path for clues
        const path = window.location.pathname.toLowerCase();
        
        if (path.includes('asset')) return 'assets';
        if (path.includes('report')) return 'reports';
        if (path.includes('driver')) return 'drivers';
        if (path.includes('bill') || path.includes('pm') || path.includes('allocation')) return 'billing';
        if (path.includes('maintenance')) return 'maintenance';
        if (path.includes('alert')) return 'alerts';
        
        return 'general';
    }
    
    // Infer zero state type from a container
    inferZeroStateTypeFromContainer(container) {
        const id = container.id || '';
        const className = container.className || '';
        const heading = container.querySelector('h1, h2, h3, h4, h5, h6')?.textContent || '';
        
        // Combine all text for better inference
        const combinedText = `${id} ${className} ${heading}`.toLowerCase();
        
        if (combinedText.includes('asset') || combinedText.includes('vehicle') || combinedText.includes('equipment')) {
            return 'assets';
        }
        
        if (combinedText.includes('report') || combinedText.includes('export')) {
            return 'reports';
        }
        
        if (combinedText.includes('driver') || combinedText.includes('employee') || combinedText.includes('staff')) {
            return 'drivers';
        }
        
        if (combinedText.includes('bill') || combinedText.includes('invoice') || combinedText.includes('payment') || combinedText.includes('allocation')) {
            return 'billing';
        }
        
        if (combinedText.includes('maintenance') || combinedText.includes('repair') || combinedText.includes('service')) {
            return 'maintenance';
        }
        
        if (combinedText.includes('alert') || combinedText.includes('notification') || combinedText.includes('warning')) {
            return 'alerts';
        }
        
        // Check the current URL path for clues
        const path = window.location.pathname.toLowerCase();
        
        if (path.includes('asset')) return 'assets';
        if (path.includes('report')) return 'reports';
        if (path.includes('driver')) return 'drivers';
        if (path.includes('bill') || path.includes('pm') || path.includes('allocation')) return 'billing';
        if (path.includes('maintenance')) return 'maintenance';
        if (path.includes('alert')) return 'alerts';
        
        return 'general';
    }
    
    // Get the column count for a table
    getTableColumnCount(table) {
        const headerRow = table.querySelector('thead tr');
        if (headerRow) {
            return headerRow.cells.length;
        }
        
        // Fallback to first row if no header
        const firstRow = table.querySelector('tbody tr');
        if (firstRow) {
            return firstRow.cells.length;
        }
        
        return 3; // Default if we can't determine
    }
    
    // Get zero state metrics for analysis
    getZeroStateMetrics() {
        const metrics = {};
        
        // Calculate metrics for each zero state type
        Object.keys(this.zeroStates).forEach(stateType => {
            const stateData = this.zeroStates[stateType];
            const interactions = this.userInteractions[stateType] || [];
            const showCount = this.showCount[stateType] || 0;
            
            // Calculate interaction rate
            const interactionRate = showCount > 0 ? interactions.length / showCount : 0;
            
            // Count specific actions
            const actionCounts = {};
            interactions.forEach(interaction => {
                const action = interaction.action;
                actionCounts[action] = (actionCounts[action] || 0) + 1;
            });
            
            metrics[stateType] = {
                encountered: stateData.encountered,
                dismissed: stateData.dismissed,
                showCount: showCount,
                interactionCount: interactions.length,
                interactionRate: interactionRate,
                actionCounts: actionCounts
            };
        });
        
        return metrics;
    }
    
    // Reset a specific zero state (for testing or after data added)
    resetZeroState(stateType) {
        if (this.zeroStates[stateType]) {
            this.zeroStates[stateType].dismissed = false;
        }
        this.saveZeroStates();
    }
    
    // Reset all zero states
    resetAllZeroStates() {
        Object.keys(this.zeroStates).forEach(stateType => {
            this.zeroStates[stateType].dismissed = false;
        });
        this.saveZeroStates();
    }
}

// Initialize the zero state handler when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize zero state handler
    window.zeroStateHandler = new ZeroStateHandler();
    
    // Add custom styles for zero state guidance
    const style = document.createElement('style');
    style.textContent = `
        .zero-state-guidance {
            animation: fadeIn 0.3s ease-in-out;
        }
        
        .fade-out {
            animation: fadeOut 0.3s ease-in-out;
            opacity: 0;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(style);
});