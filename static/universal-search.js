/**
 * TRAXOVO Universal Search System
 * Instant access to assets, financials, and operational data
 */

class UniversalSearch {
    constructor() {
        this.searchInput = null;
        this.resultsContainer = null;
        this.searchTimeout = null;
        this.isVisible = false;
        this.init();
    }

    init() {
        this.createSearchInterface();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
    }

    createSearchInterface() {
        // Create search bar if it doesn't exist
        let searchContainer = document.querySelector('.universal-search-container');
        if (!searchContainer) {
            searchContainer = document.createElement('div');
            searchContainer.className = 'universal-search-container';
            searchContainer.innerHTML = `
                <div class="search-wrapper">
                    <input type="text" 
                           id="universal-search" 
                           placeholder="Search assets, financials, categories... (Ctrl+K)" 
                           autocomplete="off">
                    <div class="search-icon">🔍</div>
                    <div class="search-loading" id="search-loading" style="display: none;">⏳</div>
                </div>
                <div class="search-results" id="search-results"></div>
                <div class="search-shortcuts">
                    <span>Press <kbd>Ctrl+K</kbd> to search anywhere</span>
                </div>
            `;
            
            // Insert at top of body or in header
            const header = document.querySelector('.top-bar') || document.querySelector('header');
            if (header) {
                header.appendChild(searchContainer);
            } else {
                document.body.insertBefore(searchContainer, document.body.firstChild);
            }
        }

        this.searchInput = document.getElementById('universal-search');
        this.resultsContainer = document.getElementById('search-results');
        this.loadingIndicator = document.getElementById('search-loading');
    }

    setupEventListeners() {
        if (!this.searchInput) return;

        // Search input events
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            this.handleSearch(query);
        });

        this.searchInput.addEventListener('focus', () => {
            this.showSearchInterface();
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.universal-search-container')) {
                this.hideSearchInterface();
            }
        });

        // Escape key to close
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideSearchInterface();
                this.searchInput.blur();
            }
        });
    }

    setupKeyboardShortcuts() {
        // Ctrl+K to focus search
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.focusSearch();
            }
        });
    }

    handleSearch(query) {
        clearTimeout(this.searchTimeout);
        
        if (query.length < 2) {
            this.hideResults();
            return;
        }

        this.showLoading();
        
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    async performSearch(query) {
        try {
            const response = await fetch(`/api/fleet/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.hideLoading();
            
            if (data.status === 'success') {
                this.displayResults(data.results, query);
            } else {
                this.displayError('Search failed. Please try again.');
            }
        } catch (error) {
            this.hideLoading();
            this.displayError('Network error. Please check your connection.');
        }
    }

    displayResults(results, query) {
        if (!results || results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">🔍</div>
                    <div>No results found for "${query}"</div>
                    <div class="search-tips">Try searching for asset IDs, categories, or financial terms</div>
                </div>
            `;
            this.showResults();
            return;
        }

        const resultsByCategory = this.groupResultsByCategory(results);
        let html = '';

        for (const [category, items] of Object.entries(resultsByCategory)) {
            html += `
                <div class="result-category">
                    <div class="category-header">${category}</div>
                    <div class="category-results">
            `;
            
            items.forEach(result => {
                html += `
                    <div class="search-result-item" onclick="window.location.href='${result.url}'">
                        <div class="result-main">
                            <div class="result-title">${this.highlightQuery(result.title, query)}</div>
                            <div class="result-subtitle">${this.highlightQuery(result.subtitle, query)}</div>
                        </div>
                        <div class="result-meta">
                            <span class="result-category-tag">${result.category}</span>
                            <span class="result-relevance">${Math.round(result.relevance * 100)}%</span>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }

        this.resultsContainer.innerHTML = html;
        this.showResults();
    }

    groupResultsByCategory(results) {
        const grouped = {};
        results.forEach(result => {
            if (!grouped[result.category]) {
                grouped[result.category] = [];
            }
            grouped[result.category].push(result);
        });
        return grouped;
    }

    highlightQuery(text, query) {
        if (!text || !query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    displayError(message) {
        this.resultsContainer.innerHTML = `
            <div class="search-error">
                <div class="error-icon">⚠️</div>
                <div>${message}</div>
            </div>
        `;
        this.showResults();
    }

    showSearchInterface() {
        this.isVisible = true;
        document.querySelector('.universal-search-container').classList.add('active');
    }

    hideSearchInterface() {
        this.isVisible = false;
        document.querySelector('.universal-search-container').classList.remove('active');
        this.hideResults();
    }

    showResults() {
        this.resultsContainer.style.display = 'block';
    }

    hideResults() {
        this.resultsContainer.style.display = 'none';
    }

    showLoading() {
        this.loadingIndicator.style.display = 'block';
        document.querySelector('.search-icon').style.display = 'none';
    }

    hideLoading() {
        this.loadingIndicator.style.display = 'none';
        document.querySelector('.search-icon').style.display = 'block';
    }

    focusSearch() {
        this.searchInput.focus();
        this.showSearchInterface();
    }

    // Quick access methods for common searches
    searchAssets(assetId) {
        this.searchInput.value = assetId;
        this.handleSearch(assetId);
        this.focusSearch();
    }

    searchFinancials() {
        this.searchInput.value = 'revenue';
        this.handleSearch('revenue');
        this.focusSearch();
    }

    searchCategory(category) {
        this.searchInput.value = category;
        this.handleSearch(category);
        this.focusSearch();
    }
}

// Initialize universal search when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.universalSearch = new UniversalSearch();
});

// Expose global search functions
window.searchAssets = (assetId) => window.universalSearch?.searchAssets(assetId);
window.searchFinancials = () => window.universalSearch?.searchFinancials();
window.searchCategory = (category) => window.universalSearch?.searchCategory(category);