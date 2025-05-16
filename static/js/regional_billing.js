/**
 * Regional Billing Generation functionality
 * This script handles the generation of regional billing exports
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners for regional billing buttons
    const dfwButton = document.getElementById('generate-dfw');
    const houButton = document.getElementById('generate-hou');
    const wtxButton = document.getElementById('generate-wtx');
    
    if (dfwButton) {
        dfwButton.addEventListener('click', function() {
            generateRegionalBilling('dfw');
        });
    }
    
    if (houButton) {
        houButton.addEventListener('click', function() {
            generateRegionalBilling('hou');
        });
    }
    
    if (wtxButton) {
        wtxButton.addEventListener('click', function() {
            generateRegionalBilling('wtx');
        });
    }
});

/**
 * Generate a regional billing export
 * @param {string} region - The region code (dfw, hou, wtx)
 */
function generateRegionalBilling(region) {
    // Show loading state
    const button = document.getElementById(`generate-${region}`);
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
    
    // Make AJAX request to generate the regional billing export
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
        button.textContent = originalText;
        
        // Handle response
        if (data.success) {
            // Show success message
            showAlert('success', data.message);
            
            // Add download link if provided
            if (data.download_link) {
                const alertsContainer = document.getElementById('alerts-container');
                if (alertsContainer) {
                    const downloadAlert = document.createElement('div');
                    downloadAlert.className = 'alert alert-success';
                    downloadAlert.innerHTML = data.download_link;
                    alertsContainer.appendChild(downloadAlert);
                    
                    // Scroll to the alerts container
                    alertsContainer.scrollIntoView({ behavior: 'smooth' });
                }
            }
        } else {
            // Show error message
            showAlert('danger', data.message || 'An error occurred while generating the export.');
        }
    })
    .catch(error => {
        // Reset button state
        button.disabled = false;
        button.textContent = originalText;
        
        // Show error message
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while generating the export. Please try again.');
    });
}

/**
 * Show an alert message
 * @param {string} type - The alert type (success, danger, warning, info)
 * @param {string} message - The message to display
 */
function showAlert(type, message) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) {
        console.error('Alerts container not found');
        return;
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000);
}