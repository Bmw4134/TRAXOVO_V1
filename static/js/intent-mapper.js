/**
 * TRAXORA Intent Mapping System
 * 
 * This module analyzes user behavior to determine likely intents and usage patterns.
 * It creates invisible tags for user actions and maps them to higher-level intents
 * that can be used for personalization and adaptive UI.
 */

class IntentMapper {
    constructor() {
        this.actions = this.loadActions();
        this.intents = {
            reporting: {
                score: 0,
                threshold: 3,
                actions: ['view_report', 'export_report', 'filter_report']
            },
            monitoring: {
                score: 0,
                threshold: 3,
                actions: ['view_dashboard', 'check_status', 'view_alerts']
            },
            managing: {
                score: 0,
                threshold: 4,
                actions: ['edit_record', 'create_record', 'assign_task', 'update_settings']
            },
            analyzing: {
                score: 0,
                threshold: 3,
                actions: ['filter_data', 'sort_data', 'search_records', 'view_details']
            },
            planning: {
                score: 0,
                threshold: 3,
                actions: ['view_calendar', 'schedule_event', 'view_forecast']
            }
        };
        
        this.currentIntent = this.loadCurrentIntent();
        this.sessionStart = new Date();
        this.lastActivity = new Date();
        this.pageViews = {};
        
        this.init();
    }
    
    init() {
        // Set up action tracking
        this.setupActionTracking();
        
        // Start session tracking
        this.trackSession();
        
        // Load previous intents and update scores
        this.analyzeActions();
        
        // Initial UI adaptation based on current intent
        this.adaptUIToIntent();
    }
    
    // Load saved actions from localStorage
    loadActions() {
        const savedActions = localStorage.getItem('traxora_user_actions');
        return savedActions ? JSON.parse(savedActions) : [];
    }
    
    // Save actions to localStorage
    saveActions() {
        // Keep only the most recent 100 actions to avoid storage issues
        if (this.actions.length > 100) {
            this.actions = this.actions.slice(-100);
        }
        
        localStorage.setItem('traxora_user_actions', JSON.stringify(this.actions));
    }
    
    // Load current intent from localStorage
    loadCurrentIntent() {
        const savedIntent = localStorage.getItem('traxora_current_intent');
        return savedIntent || 'general';
    }
    
    // Save current intent to localStorage
    saveCurrentIntent() {
        localStorage.setItem('traxora_current_intent', this.currentIntent);
    }
    
    // Set up tracking for user actions
    setupActionTracking() {
        // Track page views
        this.trackAction('page_view', {
            url: window.location.pathname,
            title: document.title
        });
        
        // Track main navigation clicks
        document.querySelectorAll('.navbar-nav .nav-link, .nav-item .dropdown-item').forEach(link => {
            link.addEventListener('click', () => {
                const action = this.inferActionFromNavigation(link);
                
                this.trackAction(action, {
                    element: link.textContent.trim(),
                    url: link.getAttribute('href')
                });
            });
        });
        
        // Track button clicks
        document.querySelectorAll('button:not([data-bs-dismiss]), .btn:not([data-bs-dismiss])').forEach(button => {
            button.addEventListener('click', () => {
                // Skip close buttons for modals, alerts, etc.
                if (button.classList.contains('btn-close') || button.classList.contains('close')) {
                    return;
                }
                
                const action = button.dataset.action || this.inferActionFromButton(button);
                
                this.trackAction(action, {
                    element: button.textContent.trim(),
                    id: button.id || null,
                    class: button.className
                });
            });
        });
        
        // Track form submissions
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => {
                const action = form.dataset.action || this.inferActionFromForm(form);
                
                this.trackAction(action, {
                    form: form.id || form.className,
                    action: form.getAttribute('action')
                });
            });
        });
        
        // Track modal openings
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(trigger => {
            trigger.addEventListener('click', () => {
                const targetId = trigger.getAttribute('data-bs-target');
                const modal = document.querySelector(targetId);
                
                if (modal) {
                    const action = 'view_modal';
                    const modalTitle = modal.querySelector('.modal-title')?.textContent.trim() || '';
                    
                    this.trackAction(action, {
                        modal: targetId,
                        title: modalTitle
                    });
                }
            });
        });
        
        // Track tab selection
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const action = 'select_tab';
                
                this.trackAction(action, {
                    tab: e.target.textContent.trim(),
                    previousTab: e.relatedTarget ? e.relatedTarget.textContent.trim() : null
                });
            });
        });
        
        // Track search actions
        document.querySelectorAll('input[type="search"], .search-form input[type="text"]').forEach(search => {
            search.form?.addEventListener('submit', () => {
                if (search.value.trim()) {
                    this.trackAction('search_records', {
                        query: search.value.trim(),
                        searchField: search.name || search.id
                    });
                }
            });
        });
        
        // Track filter changes
        document.querySelectorAll('select.filter-select, input.filter-input, [data-filter="true"]').forEach(filter => {
            filter.addEventListener('change', () => {
                this.trackAction('filter_data', {
                    filter: filter.name || filter.id,
                    value: filter.type === 'checkbox' ? filter.checked : filter.value
                });
            });
        });
        
        // Track sort changes
        document.querySelectorAll('[data-sort="true"], .sort-select').forEach(sort => {
            sort.addEventListener('change', () => {
                this.trackAction('sort_data', {
                    column: sort.value,
                    element: sort.name || sort.id
                });
            });
        });
        
        // Track Export/Download actions
        document.querySelectorAll('a[href*="export"], a[href*="download"], button[data-action="export"]').forEach(link => {
            link.addEventListener('click', () => {
                let format = 'unknown';
                
                // Try to determine export format
                if (link.href) {
                    if (link.href.includes('pdf')) format = 'pdf';
                    else if (link.href.includes('csv')) format = 'csv';
                    else if (link.href.includes('excel') || link.href.includes('xlsx')) format = 'excel';
                }
                
                this.trackAction('export_report', {
                    format: format,
                    element: link.textContent.trim()
                });
            });
        });
    }
    
    // Infer action type from navigation element
    inferActionFromNavigation(element) {
        const text = element.textContent.toLowerCase().trim();
        const url = element.getAttribute('href') || '';
        
        if (url === '/' || url === '#' || url.includes('dashboard')) {
            return 'view_dashboard';
        }
        
        if (text.includes('report') || url.includes('report')) {
            return 'view_report';
        }
        
        if (text.includes('setting') || url.includes('setting')) {
            return 'update_settings';
        }
        
        if (text.includes('alert') || url.includes('alert')) {
            return 'view_alerts';
        }
        
        // Default navigation action
        return 'navigate';
    }
    
    // Infer action type from button element
    inferActionFromButton(button) {
        const text = button.textContent.toLowerCase().trim();
        
        // Check for common action indicators in button text
        if (text.includes('add') || text.includes('create') || text.includes('new')) {
            return 'create_record';
        }
        
        if (text.includes('edit') || text.includes('update')) {
            return 'edit_record';
        }
        
        if (text.includes('delete') || text.includes('remove')) {
            return 'delete_record';
        }
        
        if (text.includes('save')) {
            return 'save_record';
        }
        
        if (text.includes('export') || text.includes('download')) {
            return 'export_report';
        }
        
        if (text.includes('filter') || text.includes('apply')) {
            return 'filter_data';
        }
        
        if (text.includes('search')) {
            return 'search_records';
        }
        
        if (text.includes('assign')) {
            return 'assign_task';
        }
        
        // Check button classes for clues
        if (button.classList.contains('btn-primary')) {
            return 'primary_action';
        }
        
        // Default button action
        return 'button_click';
    }
    
    // Infer action type from form element
    inferActionFromForm(form) {
        const formId = form.id || '';
        const formAction = form.getAttribute('action') || '';
        
        if (formId.includes('search') || formAction.includes('search')) {
            return 'search_records';
        }
        
        if (formId.includes('filter') || formAction.includes('filter')) {
            return 'filter_data';
        }
        
        if (formId.includes('create') || formAction.includes('create') || formAction.includes('new')) {
            return 'create_record';
        }
        
        if (formId.includes('edit') || formAction.includes('edit') || formAction.includes('update')) {
            return 'edit_record';
        }
        
        if (formId.includes('login')) {
            return 'user_login';
        }
        
        // Look for submit button text as a clue
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            const buttonText = submitButton.value || submitButton.textContent || '';
            if (buttonText.toLowerCase().includes('search')) {
                return 'search_records';
            }
            if (buttonText.toLowerCase().includes('filter')) {
                return 'filter_data';
            }
            if (buttonText.toLowerCase().includes('create') || buttonText.toLowerCase().includes('add')) {
                return 'create_record';
            }
            if (buttonText.toLowerCase().includes('update') || buttonText.toLowerCase().includes('save')) {
                return 'edit_record';
            }
        }
        
        // Default form action
        return 'form_submit';
    }
    
    // Track a user action
    trackAction(action, details = {}) {
        // Update last activity time
        this.lastActivity = new Date();
        
        // Add basic metadata
        const actionData = {
            action: action,
            details: details,
            timestamp: new Date().toISOString(),
            page: window.location.pathname,
            sessionTime: Math.floor((this.lastActivity - this.sessionStart) / 1000)
        };
        
        // Add to actions history
        this.actions.push(actionData);
        
        // Track page view counts
        if (action === 'page_view') {
            const page = details.url || window.location.pathname;
            this.pageViews[page] = (this.pageViews[page] || 0) + 1;
        }
        
        // Save actions
        this.saveActions();
        
        // Analyze new action and update intents
        this.analyzeAction(actionData);
        
        // Check if intent should be changed based on new action
        this.checkIntent();
    }
    
    // Track user session information
    trackSession() {
        // Track time on page when leaving
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Math.floor((new Date() - this.lastActivity) / 1000);
            
            if (timeOnPage > 5) {  // Only track if spent more than 5 seconds
                this.trackAction('page_exit', {
                    timeOnPage: timeOnPage,
                    url: window.location.pathname
                });
            }
        });
        
        // Check for session inactivity
        setInterval(() => {
            const now = new Date();
            const inactiveTime = Math.floor((now - this.lastActivity) / 1000);
            
            // If inactive for more than 5 minutes, consider it a new session
            if (inactiveTime > 300) {
                this.sessionStart = now;
                this.lastActivity = now;
                
                // Track new session start
                this.trackAction('session_resume', {
                    inactiveTime: inactiveTime
                });
            }
        }, 60000);  // Check every minute
    }
    
    // Analyze a single action for intent signals
    analyzeAction(actionData) {
        const action = actionData.action;
        
        // Update intent scores based on the action
        Object.keys(this.intents).forEach(intent => {
            const intentData = this.intents[intent];
            
            if (intentData.actions.includes(action)) {
                // Increase score for this intent
                intentData.score += 1;
                
                // Apply decay to old score (gradually reduce over time)
                // This ensures recent actions have more weight
                intentData.score *= 0.95;
            }
        });
    }
    
    // Analyze all tracked actions to determine intent patterns
    analyzeActions() {
        // Reset scores
        Object.keys(this.intents).forEach(intent => {
            this.intents[intent].score = 0;
        });
        
        // Get recent actions (last 20)
        const recentActions = this.actions.slice(-20);
        
        // Count action types
        const actionCounts = {};
        recentActions.forEach(actionData => {
            const action = actionData.action;
            actionCounts[action] = (actionCounts[action] || 0) + 1;
        });
        
        // Update intent scores based on action counts
        Object.keys(this.intents).forEach(intent => {
            const intentData = this.intents[intent];
            
            // Calculate score based on relevant actions
            intentData.actions.forEach(action => {
                if (actionCounts[action]) {
                    intentData.score += actionCounts[action];
                }
            });
        });
        
        // Check if we should update the current intent
        this.checkIntent();
    }
    
    // Check if current intent should be updated
    checkIntent() {
        let highestScore = 0;
        let highestIntent = 'general';
        
        // Find intent with highest score above threshold
        Object.keys(this.intents).forEach(intent => {
            const intentData = this.intents[intent];
            
            if (intentData.score > highestScore && intentData.score >= intentData.threshold) {
                highestScore = intentData.score;
                highestIntent = intent;
            }
        });
        
        // Update current intent if changed
        if (this.currentIntent !== highestIntent) {
            this.currentIntent = highestIntent;
            this.saveCurrentIntent();
            
            // Adapt UI to new intent
            this.adaptUIToIntent();
        }
    }
    
    // Adapt the UI based on detected user intent
    adaptUIToIntent() {
        // Skip if no UI adaptation elements exist
        if (!document.querySelector('[data-intent-adapt]')) {
            return;
        }
        
        // Show elements that match current intent
        document.querySelectorAll('[data-intent-adapt]').forEach(element => {
            const intents = element.dataset.intentAdapt.split(',').map(i => i.trim());
            
            if (intents.includes(this.currentIntent) || intents.includes('all')) {
                element.style.display = '';  // Show this element
                element.classList.remove('d-none');
            } else {
                element.style.display = 'none';  // Hide this element
                element.classList.add('d-none');
            }
        });
        
        // Update navigation emphasis based on intent
        document.querySelectorAll('[data-intent-nav]').forEach(navItem => {
            const intents = navItem.dataset.intentNav.split(',').map(i => i.trim());
            
            if (intents.includes(this.currentIntent)) {
                navItem.classList.add('intent-highlight');  // Highlight this nav item
            } else {
                navItem.classList.remove('intent-highlight');
            }
        });
        
        // Update content emphasis based on intent
        document.querySelectorAll('[data-intent-emphasis]').forEach(content => {
            const intentEmphasis = content.dataset.intentEmphasis;
            
            if (intentEmphasis === this.currentIntent) {
                content.classList.add('intent-emphasized');  // Emphasize this content
            } else {
                content.classList.remove('intent-emphasized');
            }
        });
        
        // Trigger any custom handlers for the intent
        this.triggerIntentHandlers();
    }
    
    // Trigger any custom intent handlers
    triggerIntentHandlers() {
        // Dispatch custom event for intent change
        const event = new CustomEvent('intentChanged', {
            detail: {
                intent: this.currentIntent,
                intents: this.intents
            }
        });
        
        document.dispatchEvent(event);
        
        // Call specific intent handlers
        if (typeof window[`on${this.currentIntent}Intent`] === 'function') {
            window[`on${this.currentIntent}Intent`](this.intents[this.currentIntent]);
        }
    }
    
    // Get the current detected user intent
    getCurrentIntent() {
        return this.currentIntent;
    }
    
    // Get intent scores for all intents
    getIntentScores() {
        const scores = {};
        
        Object.keys(this.intents).forEach(intent => {
            scores[intent] = this.intents[intent].score;
        });
        
        return scores;
    }
    
    // Get the most frequently visited pages
    getFrequentPages(limit = 5) {
        return Object.entries(this.pageViews)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(entry => ({
                url: entry[0],
                count: entry[1]
            }));
    }
    
    // Get the recent actions of a specific type
    getRecentActionsByType(actionType, limit = 5) {
        return this.actions
            .filter(action => action.action === actionType)
            .slice(-limit)
            .reverse();
    }
    
    // Export user behavior data (for potential server-side analysis)
    exportBehaviorData() {
        return {
            currentIntent: this.currentIntent,
            intents: this.intents,
            pageViews: this.pageViews,
            recentActions: this.actions.slice(-20)
        };
    }
    
    // Clear all tracked data (for privacy or testing)
    clearAllData() {
        localStorage.removeItem('traxora_user_actions');
        localStorage.removeItem('traxora_current_intent');
        
        this.actions = [];
        this.pageViews = {};
        this.currentIntent = 'general';
        
        Object.keys(this.intents).forEach(intent => {
            this.intents[intent].score = 0;
        });
    }
}

// Initialize the intent mapping system when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize intent mapper
    window.intentMapper = new IntentMapper();
    
    // Expose high-level intent API for other scripts
    window.getCurrentUserIntent = function() {
        return window.intentMapper.getCurrentIntent();
    };
    
    window.getIntentScores = function() {
        return window.intentMapper.getIntentScores();
    };
    
    window.getTopVisitedPages = function() {
        return window.intentMapper.getFrequentPages();
    };
    
    // Dispatch ready event
    document.dispatchEvent(new Event('intentMapperReady'));
});

// CSS for intent-based UI adaptation
const style = document.createElement('style');
style.textContent = `
    .intent-highlight {
        font-weight: bold !important;
        position: relative;
    }
    
    .intent-highlight::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 2px;
        background-color: var(--bs-primary);
        animation: pulse 2s infinite;
    }
    
    .intent-emphasized {
        border-left: 3px solid var(--bs-primary) !important;
        padding-left: 15px !important;
        background-color: rgba(var(--bs-primary-rgb), 0.05) !important;
    }
    
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
`;
document.head.appendChild(style);