/**
 * TRAXORA User Preferences System
 * 
 * This module tracks and applies user preferences across the application,
 * creating a personalized experience based on past behavior.
 */

class UserPreferences {
    constructor() {
        this.preferences = this.loadPreferences();
        this.fieldHistory = this.loadFieldHistory();
        this.currentPage = window.location.pathname;
        this.initializeFormTracking();
    }
    
    loadPreferences() {
        const savedPrefs = localStorage.getItem('traxora_preferences');
        return savedPrefs ? JSON.parse(savedPrefs) : {
            filters: {},
            columns: {},
            sorts: {},
            pageSize: {},
            viewMode: {},
            recentSearches: {},
            lastAccessed: {}
        };
    }
    
    savePreferences() {
        localStorage.setItem('traxora_preferences', JSON.stringify(this.preferences));
    }
    
    loadFieldHistory() {
        const savedHistory = localStorage.getItem('traxora_field_history');
        return savedHistory ? JSON.parse(savedHistory) : {};
    }
    
    saveFieldHistory() {
        localStorage.setItem('traxora_field_history', JSON.stringify(this.fieldHistory));
    }
    
    // Apply saved preferences to the current page
    applyPreferencesToPage() {
        this.applyFilterPreferences();
        this.applyColumnPreferences();
        this.applySortPreferences();
        this.applyViewModePreferences();
        this.setupFieldAutoComplete();
        this.updateLastAccessed();
    }
    
    // Track when this page was last accessed
    updateLastAccessed() {
        this.preferences.lastAccessed[this.currentPage] = new Date().toISOString();
        this.savePreferences();
    }
    
    // Apply saved filter values
    applyFilterPreferences() {
        const pageFilters = this.preferences.filters[this.currentPage];
        
        if (!pageFilters) return;
        
        // Apply each saved filter value
        Object.keys(pageFilters).forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (!filterElement) return;
            
            const savedValue = pageFilters[filterId];
            
            // Handle different input types
            if (filterElement.tagName === 'SELECT') {
                filterElement.value = savedValue;
                // Trigger change event for any dependent components
                filterElement.dispatchEvent(new Event('change'));
            } 
            else if (filterElement.tagName === 'INPUT') {
                if (filterElement.type === 'checkbox') {
                    filterElement.checked = savedValue === 'true' || savedValue === true;
                } else if (filterElement.type === 'radio') {
                    const radio = document.querySelector(`input[name="${filterElement.name}"][value="${savedValue}"]`);
                    if (radio) radio.checked = true;
                } else {
                    filterElement.value = savedValue;
                }
            }
        });
    }
    
    // Apply saved column visibility settings
    applyColumnPreferences() {
        const pageColumns = this.preferences.columns[this.currentPage];
        
        if (!pageColumns) return;
        
        // Apply column visibility
        Object.keys(pageColumns).forEach(columnId => {
            const isVisible = pageColumns[columnId];
            const columnToggle = document.querySelector(`[data-column-toggle="${columnId}"]`);
            
            if (columnToggle) {
                // Update toggle state
                if (columnToggle.type === 'checkbox') {
                    columnToggle.checked = isVisible;
                }
                
                // Update column visibility
                document.querySelectorAll(`[data-column="${columnId}"], .${columnId}-column`).forEach(col => {
                    col.style.display = isVisible ? '' : 'none';
                });
            }
        });
    }
    
    // Apply saved sort preferences
    applySortPreferences() {
        const pageSorts = this.preferences.sorts[this.currentPage];
        
        if (!pageSorts) return;
        
        // Find sort controls and apply saved values
        Object.keys(pageSorts).forEach(tableId => {
            const sortInfo = pageSorts[tableId];
            const sortSelect = document.querySelector(`#${tableId}-sort-field, [data-sort-table="${tableId}"]`);
            const directionSelect = document.querySelector(`#${tableId}-sort-direction, [data-sort-direction="${tableId}"]`);
            
            if (sortSelect && sortInfo.field) {
                sortSelect.value = sortInfo.field;
                sortSelect.dispatchEvent(new Event('change'));
            }
            
            if (directionSelect && sortInfo.direction) {
                directionSelect.value = sortInfo.direction;
                directionSelect.dispatchEvent(new Event('change'));
            }
        });
    }
    
    // Apply saved view mode (cards vs table, etc)
    applyViewModePreferences() {
        const viewMode = this.preferences.viewMode[this.currentPage];
        
        if (!viewMode) return;
        
        // Find and click the correct view mode button
        const viewButton = document.querySelector(`[data-view-mode="${viewMode}"]`);
        if (viewButton) {
            viewButton.click();
        }
    }
    
    // Setup autocomplete for form fields based on user's past inputs
    setupFieldAutoComplete() {
        document.querySelectorAll('input[type="text"], input[type="email"], textarea').forEach(field => {
            if (field.classList.contains('no-autocomplete') || field.autocomplete === 'off') return;
            
            const fieldId = field.id || field.name;
            if (!fieldId) return;
            
            // Add event listener to save input history
            field.addEventListener('change', () => {
                this.saveFieldInputHistory(fieldId, field.value);
            });
            
            // For input-list type autocomplete
            if (this.fieldHistory[fieldId] && this.fieldHistory[fieldId].length > 0) {
                const datalistId = `history-${fieldId}`;
                let datalist = document.getElementById(datalistId);
                
                // Create datalist if it doesn't exist
                if (!datalist) {
                    datalist = document.createElement('datalist');
                    datalist.id = datalistId;
                    document.body.appendChild(datalist);
                    field.setAttribute('list', datalistId);
                }
                
                // Clear existing options
                datalist.innerHTML = '';
                
                // Add history options
                this.fieldHistory[fieldId].forEach(value => {
                    const option = document.createElement('option');
                    option.value = value;
                    datalist.appendChild(option);
                });
            }
        });
    }
    
    // Initialize tracking of form inputs and filters
    initializeFormTracking() {
        // Track filter changes
        document.querySelectorAll('.data-filter, [data-filter="true"]').forEach(filter => {
            const filterId = filter.id;
            if (!filterId) return;
            
            filter.addEventListener('change', () => {
                this.saveFilterPreference(filterId, filter.type === 'checkbox' ? filter.checked : filter.value);
            });
        });
        
        // Track column toggling
        document.querySelectorAll('[data-column-toggle]').forEach(toggle => {
            const columnId = toggle.dataset.columnToggle;
            
            toggle.addEventListener('change', () => {
                const isVisible = toggle.type === 'checkbox' ? toggle.checked : toggle.value === 'true';
                this.saveColumnPreference(columnId, isVisible);
                
                // Update column visibility in the UI
                document.querySelectorAll(`[data-column="${columnId}"], .${columnId}-column`).forEach(col => {
                    col.style.display = isVisible ? '' : 'none';
                });
            });
        });
        
        // Track sort changes
        document.querySelectorAll('[data-sort-table]').forEach(sortSelect => {
            const tableId = sortSelect.dataset.sortTable;
            
            sortSelect.addEventListener('change', () => {
                const directionSelect = document.querySelector(`[data-sort-direction="${tableId}"]`);
                const direction = directionSelect ? directionSelect.value : 'asc';
                
                this.saveSortPreference(tableId, {
                    field: sortSelect.value,
                    direction: direction
                });
            });
        });
        
        // Track sort direction changes
        document.querySelectorAll('[data-sort-direction]').forEach(directionSelect => {
            const tableId = directionSelect.dataset.sortDirection;
            
            directionSelect.addEventListener('change', () => {
                const sortSelect = document.querySelector(`[data-sort-table="${tableId}"]`);
                const field = sortSelect ? sortSelect.value : null;
                
                if (field) {
                    this.saveSortPreference(tableId, {
                        field: field,
                        direction: directionSelect.value
                    });
                }
            });
        });
        
        // Track view mode changes
        document.querySelectorAll('[data-view-mode]').forEach(viewButton => {
            const viewMode = viewButton.dataset.viewMode;
            
            viewButton.addEventListener('click', () => {
                this.saveViewModePreference(viewMode);
            });
        });
        
        // Track search queries
        document.querySelectorAll('.search-form, [data-search="true"]').forEach(searchForm => {
            searchForm.addEventListener('submit', (e) => {
                const searchInput = searchForm.querySelector('input[type="search"], input[type="text"]');
                if (searchInput && searchInput.value.trim()) {
                    this.saveSearchQuery(searchInput.value.trim());
                }
            });
        });
    }
    
    // Save a filter preference
    saveFilterPreference(filterId, value) {
        if (!this.preferences.filters[this.currentPage]) {
            this.preferences.filters[this.currentPage] = {};
        }
        
        this.preferences.filters[this.currentPage][filterId] = value;
        this.savePreferences();
    }
    
    // Save column visibility preference
    saveColumnPreference(columnId, isVisible) {
        if (!this.preferences.columns[this.currentPage]) {
            this.preferences.columns[this.currentPage] = {};
        }
        
        this.preferences.columns[this.currentPage][columnId] = isVisible;
        this.savePreferences();
    }
    
    // Save sort preference
    saveSortPreference(tableId, sortInfo) {
        if (!this.preferences.sorts[this.currentPage]) {
            this.preferences.sorts[this.currentPage] = {};
        }
        
        this.preferences.sorts[this.currentPage][tableId] = sortInfo;
        this.savePreferences();
    }
    
    // Save view mode preference
    saveViewModePreference(viewMode) {
        this.preferences.viewMode[this.currentPage] = viewMode;
        this.savePreferences();
    }
    
    // Save search query history
    saveSearchQuery(query) {
        if (!this.preferences.recentSearches[this.currentPage]) {
            this.preferences.recentSearches[this.currentPage] = [];
        }
        
        // Remove the query if it already exists (to avoid duplicates)
        this.preferences.recentSearches[this.currentPage] = 
            this.preferences.recentSearches[this.currentPage].filter(q => q !== query);
        
        // Add to the front of the array
        this.preferences.recentSearches[this.currentPage].unshift(query);
        
        // Limit to 10 recent searches
        if (this.preferences.recentSearches[this.currentPage].length > 10) {
            this.preferences.recentSearches[this.currentPage].pop();
        }
        
        this.savePreferences();
    }
    
    // Save field input history for autocomplete
    saveFieldInputHistory(fieldId, value) {
        if (!value.trim()) return;
        
        if (!this.fieldHistory[fieldId]) {
            this.fieldHistory[fieldId] = [];
        }
        
        // Remove the value if it already exists (to avoid duplicates)
        this.fieldHistory[fieldId] = this.fieldHistory[fieldId].filter(v => v !== value);
        
        // Add to the front of the array
        this.fieldHistory[fieldId].unshift(value);
        
        // Limit to 10 entries per field
        if (this.fieldHistory[fieldId].length > 10) {
            this.fieldHistory[fieldId].pop();
        }
        
        this.saveFieldHistory();
    }
    
    // Get recent searches for the current page
    getRecentSearches() {
        return this.preferences.recentSearches[this.currentPage] || [];
    }
    
    // Get frequently accessed pages
    getFrequentPages(limit = 5) {
        const pages = Object.keys(this.preferences.lastAccessed)
            .map(page => ({
                url: page,
                lastAccessed: new Date(this.preferences.lastAccessed[page])
            }))
            .sort((a, b) => b.lastAccessed - a.lastAccessed);
            
        return pages.slice(0, limit);
    }
    
    // Clear all saved preferences (for testing or privacy)
    clearAllPreferences() {
        localStorage.removeItem('traxora_preferences');
        localStorage.removeItem('traxora_field_history');
        this.preferences = this.loadPreferences();
        this.fieldHistory = this.loadFieldHistory();
    }
}

// Initialize the preferences system when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize user preferences
    window.userPreferences = new UserPreferences();
    
    // Apply preferences to the current page
    window.userPreferences.applyPreferencesToPage();
    
    // Update recent searches dropdown if it exists
    const recentSearchesContainer = document.querySelector('.recent-searches-container');
    if (recentSearchesContainer) {
        const recentSearches = window.userPreferences.getRecentSearches();
        
        if (recentSearches.length > 0) {
            let html = '<h6 class="dropdown-header">Recent Searches</h6>';
            
            recentSearches.forEach(search => {
                html += `<a class="dropdown-item" href="?search=${encodeURIComponent(search)}">${search}</a>`;
            });
            
            recentSearchesContainer.innerHTML = html;
        }
    }
});