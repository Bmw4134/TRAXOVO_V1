/**
 * Regional Billing Exports JavaScript
 * 
 * This script handles the generation of regional billing exports
 * through API endpoints and displays success/error messages.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners for regional export buttons
    const dfwButton = document.getElementById('generate-dfw-export');
    const houstonButton = document.getElementById('generate-houston-export');
    const westTexasButton = document.getElementById('generate-west-texas-export');
    
    // Add event listeners if buttons exist
    if (dfwButton) {
        dfwButton.addEventListener('click', function() {
            generateRegionalExport('dfw');
        });
    }
    
    if (houstonButton) {
        houstonButton.addEventListener('click', function() {
            generateRegionalExport('houston');
        });
    }
    
    if (westTexasButton) {
        westTexasButton.addEventListener('click', function() {
            generateRegionalExport('west_texas');
        });
    }
    
    /**
     * Function to generate regional billing export via API call
     * @param {string} region - The region to generate export for (dfw, houston, west_texas)
     */
    function generateRegionalExport(region) {
        // Show loading state
        const button = document.getElementById(`generate-${region}-export`);
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        
        // Make API call to generate the export
        fetch(`/api/generate-regional-billing/${region}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            button.disabled = false;
            button.innerHTML = originalText;
            
            // Create alert container if it doesn't exist
            const alertsContainer = document.getElementById('alerts-container');
            
            // Display success or error message
            if (data.success) {
                // Create success alert
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Success!</strong> ${data.message}
                    <a href="${data.download_url}" class="btn btn-sm btn-primary ms-3">Download Export</a>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Add to alerts container
                alertsContainer.appendChild(alert);
                
                // Initialize dismissible alert
                new bootstrap.Alert(alert);
            } else {
                // Create error alert
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Error!</strong> ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Add to alerts container
                alertsContainer.appendChild(alert);
                
                // Initialize dismissible alert
                new bootstrap.Alert(alert);
            }
        })
        .catch(error => {
            // Reset button state
            button.disabled = false;
            button.innerHTML = originalText;
            
            // Create alert container if it doesn't exist
            const alertsContainer = document.getElementById('alerts-container');
            
            // Create error alert
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                <strong>Error!</strong> An unexpected error occurred while generating the export.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            // Add to alerts container
            alertsContainer.appendChild(alert);
            
            // Initialize dismissible alert
            new bootstrap.Alert(alert);
            
            console.error('Export error:', error);
        });
    }
});