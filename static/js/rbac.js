/**
 * TRAXORA Role-Based Access Control
 * 
 * This module manages the visibility of navigation items and features
 * based on the user's role. It supports role-based permissions and
 * adapts the UI accordingly.
 */

class RoleBasedAccessControl {
    constructor() {
        this.userRole = this.getUserRole();
        this.init();
    }
    
    init() {
        // Apply role-based visibility to nav items
        this.applyRoleBasedVisibility();
        
        // Listen for role changes (if user switches roles)
        document.addEventListener('roleChanged', (e) => {
            this.userRole = e.detail.role;
            this.applyRoleBasedVisibility();
        });
    }
    
    // Get the current user's role
    getUserRole() {
        // In a real application, this would come from the server
        // For demonstration purposes, we'll check for admin class on body or use localStorage
        
        const storedRole = localStorage.getItem('traxora_user_role');
        if (storedRole) {
            return storedRole;
        }
        
        // Check if user has admin indicator in body class
        if (document.body.classList.contains('role-admin')) {
            return 'admin';
        }
        
        if (document.body.classList.contains('role-manager')) {
            return 'manager';
        }
        
        // Default role
        return 'user';
    }
    
    // Apply visibility rules based on user role
    applyRoleBasedVisibility() {
        // Process navigation items
        document.querySelectorAll('[data-role-access]').forEach(element => {
            const allowedRoles = element.dataset.roleAccess.split(',').map(r => r.trim());
            
            // Check if current role has access
            const hasAccess = this.checkRoleAccess(allowedRoles);
            
            // Apply visibility
            if (hasAccess) {
                element.style.display = '';
                element.classList.remove('d-none');
            } else {
                element.style.display = 'none';
                element.classList.add('d-none');
            }
        });
        
        // Store organization context in top navbar if available
        this.updateOrganizationContext();
    }
    
    // Check if the current role has access to a feature
    checkRoleAccess(allowedRoles) {
        // 'all' means everyone has access
        if (allowedRoles.includes('all')) {
            return true;
        }
        
        // Admin can access everything
        if (this.userRole === 'admin') {
            return true;
        }
        
        // Check specific role access
        return allowedRoles.includes(this.userRole);
    }
    
    // Update organization context in navbar
    updateOrganizationContext() {
        const orgSelector = document.getElementById('organization-select');
        if (!orgSelector) return;
        
        const selectedOrg = orgSelector.value;
        const selectedOrgText = orgSelector.options[orgSelector.selectedIndex]?.text || 'All Organizations';
        
        // Update org context in navbar if container exists
        const orgContextContainer = document.querySelector('.organization-context');
        if (orgContextContainer) {
            if (selectedOrg && selectedOrg !== 'all') {
                orgContextContainer.innerHTML = `<i class="bi bi-building me-1"></i> ${selectedOrgText}`;
                orgContextContainer.classList.remove('d-none');
            } else {
                orgContextContainer.classList.add('d-none');
            }
        }
    }
    
    // Set user role (for testing or role switching)
    setUserRole(role) {
        this.userRole = role;
        localStorage.setItem('traxora_user_role', role);
        
        // Apply updated visibility
        this.applyRoleBasedVisibility();
        
        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('roleChanged', {
            detail: { role: role }
        }));
    }
}

// Initialize RBAC when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize RBAC
    window.rbac = new RoleBasedAccessControl();
    
    // Listen for organization selection changes
    const orgSelector = document.getElementById('organization-select');
    if (orgSelector) {
        orgSelector.addEventListener('change', () => {
            window.rbac.updateOrganizationContext();
        });
    }
});