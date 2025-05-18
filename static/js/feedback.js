/**
 * TRAXORA Event-Driven Feedback System
 * 
 * This module provides smart, contextual feedback to users based on their actions.
 * It tracks user interactions, displays appropriate feedback, and helps build
 * a foundation for adaptive UX behavior.
 */

// Main Feedback Handler class
class SmartFeedback {
    constructor() {
        this.toastContainer = null;
        this.userPrefs = this.loadUserPreferences();
        this.actionHistory = [];
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.toastContainer = document.createElement('div');
            this.toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(this.toastContainer);
        } else {
            this.toastContainer = document.querySelector('.toast-container');
        }

        // Set up event listeners
        this.setupEventListeners();
        
        // Apply saved preferences
        this.applyUserPreferences();
    }

    setupEventListeners() {
        // Listen for form submissions
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', e => {
                // Skip login form and search forms
                if (form.classList.contains('login-form') || form.classList.contains('search-form')) return;
                
                // Get form purpose from data attribute or infer from action
                const formPurpose = form.dataset.purpose || this.inferFormPurpose(form);
                const formAction = form.getAttribute('action') || '';
                
                // Record action for behavioral analysis
                this.recordAction('form_submit', {
                    purpose: formPurpose,
                    action: formAction,
                    timestamp: new Date().toISOString()
                });
            });
        });

        // Track table column visibility toggles
        document.querySelectorAll('.column-toggle').forEach(toggle => {
            toggle.addEventListener('change', e => {
                const columnName = e.target.dataset.column;
                const isVisible = e.target.checked;
                
                // Save column preference
                this.saveColumnPreference(columnName, isVisible);
                
                // Record action
                this.recordAction('column_toggle', {
                    column: columnName,
                    visible: isVisible,
                    timestamp: new Date().toISOString()
                });
            });
        });

        // Track filter selections
        document.querySelectorAll('.filter-select, .filter-input').forEach(filter => {
            filter.addEventListener('change', e => {
                const filterName = e.target.name || e.target.id;
                const filterValue = e.target.value;
                
                // Save filter preference
                this.saveFilterPreference(filterName, filterValue);
                
                // Record action
                this.recordAction('filter_change', {
                    filter: filterName,
                    value: filterValue,
                    timestamp: new Date().toISOString()
                });
            });
        });

        // Track tab selections
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', e => {
                const tabId = e.target.getAttribute('href');
                
                // Save tab preference for this page
                const pagePath = window.location.pathname;
                this.saveTabPreference(pagePath, tabId);
                
                // Record action
                this.recordAction('tab_select', {
                    tab: tabId,
                    page: pagePath,
                    timestamp: new Date().toISOString()
                });
            });
        });

        // Track exports and downloads
        document.querySelectorAll('a[href*="export"], a[href*="download"]').forEach(link => {
            link.addEventListener('click', e => {
                const href = link.getAttribute('href');
                const format = this.inferExportFormat(href);
                
                // Show feedback
                this.showToast('Export Started', `Preparing ${format} export...`, 'info');
                
                // Record action
                this.recordAction('export_click', {
                    format: format,
                    url: href,
                    timestamp: new Date().toISOString()
                });
            });
        });
    }

    // Show a toast notification
    showToast(title, message, type = 'success', autohide = true, delay = 3000) {
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <i class="bi ${this.getIconForType(type)} me-2"></i>
                    <strong class="me-auto">${title}</strong>
                    <small>${this.getTimeString()}</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        this.toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: autohide,
            delay: delay
        });
        
        toast.show();
        
        // Auto-remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
        
        return toast;
    }

    // Show a banner notification (more prominent than toast)
    showBanner(message, type = 'info', dismissible = true, autoHide = true, delay = 5000) {
        const bannerId = 'banner-' + Date.now();
        const bannerHtml = `
            <div id="${bannerId}" class="alert alert-${type} alert-dismissible fade show mb-0 banner-notification" role="alert">
                <div class="container d-flex align-items-center">
                    <i class="bi ${this.getIconForType(type)} me-2 fs-5"></i>
                    <div>${message}</div>
                    ${dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}
                </div>
            </div>
        `;
        
        // Insert at the top of main content
        const mainElement = document.querySelector('main');
        if (mainElement) {
            mainElement.insertAdjacentHTML('afterbegin', bannerHtml);
            const bannerElement = document.getElementById(bannerId);
            
            if (autoHide) {
                setTimeout(() => {
                    const banner = new bootstrap.Alert(bannerElement);
                    banner.close();
                }, delay);
            }
            
            return bannerElement;
        }
        
        return null;
    }

    // Helper to get icon based on notification type
    getIconForType(type) {
        switch (type) {
            case 'success': return 'bi-check-circle-fill';
            case 'danger': return 'bi-exclamation-triangle-fill';
            case 'warning': return 'bi-exclamation-circle-fill';
            case 'info': return 'bi-info-circle-fill';
            default: return 'bi-bell-fill';
        }
    }

    // Helper to get current time string
    getTimeString() {
        const now = new Date();
        return `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
    }

    // Infer the purpose of a form from its action or contents
    inferFormPurpose(form) {
        const action = form.getAttribute('action') || '';
        const id = form.getAttribute('id') || '';
        
        if (action.includes('upload') || form.querySelector('input[type="file"]')) {
            return 'upload';
        } else if (action.includes('filter') || id.includes('filter')) {
            return 'filter';
        } else if (action.includes('create') || id.includes('create')) {
            return 'create';
        } else if (action.includes('edit') || id.includes('edit')) {
            return 'edit';
        } else if (action.includes('delete') || id.includes('delete')) {
            return 'delete';
        } else if (action.includes('search') || id.includes('search')) {
            return 'search';
        }
        
        return 'form_submission';
    }

    // Infer export format from URL
    inferExportFormat(url) {
        if (url.includes('pdf')) return 'PDF';
        if (url.includes('csv')) return 'CSV';
        if (url.includes('excel') || url.includes('xlsx') || url.includes('xls')) return 'Excel';
        if (url.includes('json')) return 'JSON';
        return 'file';
    }

    // Record user action for analysis
    recordAction(action, details) {
        // Add to local history
        this.actionHistory.push({
            action,
            details,
            timestamp: new Date().toISOString()
        });
        
        // Limit history size
        if (this.actionHistory.length > 100) {
            this.actionHistory.shift();
        }
        
        // Save to localStorage
        localStorage.setItem('traxora_action_history', JSON.stringify(this.actionHistory));
        
        // Optional: Send to server for analytics
        // this.sendActionToServer(action, details);
    }

    // Send action to server (placeholder for future implementation)
    sendActionToServer(action, details) {
        /* 
        fetch('/api/log-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action,
                details
            })
        });
        */
    }

    // Load user preferences from localStorage
    loadUserPreferences() {
        const prefs = localStorage.getItem('traxora_user_prefs');
        return prefs ? JSON.parse(prefs) : {
            columns: {},
            filters: {},
            tabs: {},
            theme: 'dark',
            densityLevel: 'default'
        };
    }

    // Save user preferences to localStorage
    saveUserPreferences() {
        localStorage.setItem('traxora_user_prefs', JSON.stringify(this.userPrefs));
    }

    // Save column visibility preference
    saveColumnPreference(columnName, isVisible) {
        if (!this.userPrefs.columns) {
            this.userPrefs.columns = {};
        }
        this.userPrefs.columns[columnName] = isVisible;
        this.saveUserPreferences();
    }

    // Save filter preference
    saveFilterPreference(filterName, value) {
        if (!this.userPrefs.filters) {
            this.userPrefs.filters = {};
        }
        this.userPrefs.filters[filterName] = value;
        this.saveUserPreferences();
    }

    // Save tab preference
    saveTabPreference(pagePath, tabId) {
        if (!this.userPrefs.tabs) {
            this.userPrefs.tabs = {};
        }
        this.userPrefs.tabs[pagePath] = tabId;
        this.saveUserPreferences();
    }

    // Apply user preferences to current page
    applyUserPreferences() {
        // Apply column preferences
        if (this.userPrefs.columns) {
            Object.entries(this.userPrefs.columns).forEach(([column, visible]) => {
                const toggle = document.querySelector(`.column-toggle[data-column="${column}"]`);
                if (toggle) {
                    toggle.checked = visible;
                    
                    // Also update column visibility
                    const tableColumn = document.querySelectorAll(`.${column}-column, [data-column="${column}"]`);
                    tableColumn.forEach(el => {
                        el.style.display = visible ? '' : 'none';
                    });
                }
            });
        }
        
        // Apply filter preferences
        if (this.userPrefs.filters) {
            Object.entries(this.userPrefs.filters).forEach(([filter, value]) => {
                const filterElement = document.querySelector(`#${filter}, [name="${filter}"]`);
                if (filterElement && filterElement.value !== value) {
                    filterElement.value = value;
                    
                    // Dispatch change event to trigger any attached handlers
                    filterElement.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }
        
        // Apply tab preferences
        if (this.userPrefs.tabs) {
            const pagePath = window.location.pathname;
            const activeTabId = this.userPrefs.tabs[pagePath];
            
            if (activeTabId) {
                const tabLink = document.querySelector(`[data-bs-toggle="tab"][href="${activeTabId}"]`);
                if (tabLink) {
                    const tab = new bootstrap.Tab(tabLink);
                    tab.show();
                }
            }
        }
    }

    // Analyze recent actions for intent patterns
    analyzeUserIntent() {
        // This is a placeholder for more sophisticated intent analysis
        const recentActions = this.actionHistory.slice(-10);
        
        // Example: Detect reporting intent
        const hasViewedReports = recentActions.some(a => a.action === 'tab_select' && a.details.tab.includes('report'));
        const hasExported = recentActions.some(a => a.action === 'export_click');
        
        if (hasViewedReports && hasExported) {
            return 'reporting';
        }
        
        // Example: Detect data entry intent
        const hasFormsSubmitted = recentActions.filter(a => a.action === 'form_submit').length > 2;
        if (hasFormsSubmitted) {
            return 'data_entry';
        }
        
        return 'browsing';
    }

    // Generate recommendations based on user behavior
    generateRecommendations() {
        const intent = this.analyzeUserIntent();
        
        switch (intent) {
            case 'reporting':
                return [
                    { text: 'View Driver Attendance Trends', url: '/attendance_dashboard', priority: 'high' },
                    { text: 'Set up automated exports', url: '#', priority: 'medium' }
                ];
                
            case 'data_entry':
                return [
                    { text: 'Use bulk import for faster entry', url: '#', priority: 'high' },
                    { text: 'View recently added data', url: '#', priority: 'medium' }
                ];
                
            default:
                return [];
        }
    }
}

// Initialize the feedback system when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.traxoraFeedback = new SmartFeedback();
    
    // Hook feedback to form submissions
    document.querySelectorAll('form:not(.login-form):not(.search-form)').forEach(form => {
        form.addEventListener('submit', function(e) {
            const formType = form.dataset.formType || 'form';
            const actionText = form.dataset.actionText || 'Processing...';
            const successText = form.dataset.successText || 'Success!';
            
            // Show processing toast
            window.traxoraFeedback.showToast('Action in Progress', actionText, 'info');
            
            // This would normally be handled server-side with proper result handling
            // For demo purposes, we'll simulate success after a short delay
            if (form.classList.contains('demo-form')) {
                e.preventDefault();
                setTimeout(() => {
                    window.traxoraFeedback.showToast('Success', successText, 'success');
                }, 1500);
            }
        });
    });
    
    // Process any data-feedback elements
    document.querySelectorAll('[data-feedback]').forEach(el => {
        el.addEventListener('click', function(e) {
            const feedbackType = this.dataset.feedback;
            const message = this.dataset.message || 'Action completed';
            
            if (feedbackType === 'toast') {
                const title = this.dataset.title || 'Notification';
                const type = this.dataset.type || 'info';
                window.traxoraFeedback.showToast(title, message, type);
            } else if (feedbackType === 'banner') {
                const type = this.dataset.type || 'info';
                window.traxoraFeedback.showBanner(message, type);
            }
            
            if (!this.dataset.allowDefault) {
                e.preventDefault();
            }
        });
    });
});

// Utility function to show toast from anywhere
function showFeedback(title, message, type = 'success') {
    if (window.traxoraFeedback) {
        window.traxoraFeedback.showToast(title, message, type);
    } else {
        console.warn('Feedback system not initialized');
    }
}

// Utility function to record action from anywhere
function recordUserAction(action, details) {
    if (window.traxoraFeedback) {
        window.traxoraFeedback.recordAction(action, details);
    } else {
        console.warn('Feedback system not initialized');
    }
}