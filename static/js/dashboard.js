// dashboard.js - Scripts for the main dashboard page

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize filter form submission
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }

    // Clear filters button
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            document.getElementById('status-filter').value = 'all';
            document.getElementById('category-filter').value = 'all';
            document.getElementById('location-filter').value = 'all';
            applyFilters();
        });
    }

    // Initialize search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const assetCards = document.querySelectorAll('.asset-card');
            
            assetCards.forEach(function(card) {
                const assetText = card.textContent.toLowerCase();
                if (assetText.includes(searchValue)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});

// Apply filters function
function applyFilters() {
    const statusFilter = document.getElementById('status-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const locationFilter = document.getElementById('location-filter').value;
    
    // Redirect to the same page with filter parameters
    window.location.href = `/?status=${statusFilter}&category=${categoryFilter}&location=${locationFilter}`;
}

// Function to toggle details section
function toggleDetails(assetId) {
    const detailsElement = document.getElementById(`details-${assetId}`);
    if (detailsElement) {
        if (detailsElement.style.display === 'none' || !detailsElement.style.display) {
            detailsElement.style.display = 'block';
        } else {
            detailsElement.style.display = 'none';
        }
    }
}
