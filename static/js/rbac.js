/** TRAXORA Role-Based Access Control
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
    this.applyRoleBasedVisibility();
    document.addEventListener("roleChanged", (e) => {
      this.userRole = e.detail.role;
      this.applyRoleBasedVisibility();
    });
  }
  getUserRole() {
    const storedRole = localStorage.getItem("traxora_user_role");
    if (storedRole) {
      return storedRole;
    }
    if (document.body.classList.contains("role-admin")) {
      return "admin";
    }
    if (document.body.classList.contains("role-manager")) {
      return "manager";
    }
    return "user";
  }
  applyRoleBasedVisibility() {
    document.querySelectorAll("[data-role-access]").forEach((element) => {
      const allowedRoles = element.dataset.roleAccess
        .split(",")
        .map((r) => r.trim());
      const hasAccess = this.checkRoleAccess(allowedRoles);
      if (hasAccess) {
        element.style.display = "";
        element.classList.remove("d-none");
      } else {
        element.style.display = "none";
        element.classList.add("d-none");
      }
    });
    this.updateOrganizationContext();
  }
  checkRoleAccess(allowedRoles) {
    if (allowedRoles.includes("all")) {
      return true;
    }
    if (this.userRole === "admin") {
      return true;
    }
    return allowedRoles.includes(this.userRole);
  }
  updateOrganizationContext() {
    const orgSelector = document.getElementById("organization-select");
    if (!orgSelector) return;
    const selectedOrg = orgSelector.value;
    const selectedOrgText =
      orgSelector.options[orgSelector.selectedIndex]?.text ||
      "All Organizations";
    const orgContextContainer = document.querySelector(".organization-context");
    if (orgContextContainer) {
      if (selectedOrg && selectedOrg !== "all") {
        orgContextContainer.innerHTML = `<i class="bi bi-building me-1"></i> ${selectedOrgText}`;
        orgContextContainer.classList.remove("d-none");
      } else {
        orgContextContainer.classList.add("d-none");
      }
    }
  }
  setUserRole(role) {
    this.userRole = role;
    localStorage.setItem("traxora_user_role", role);
    this.applyRoleBasedVisibility();
    document.dispatchEvent(
      new CustomEvent("roleChanged", {
        detail: { role: role },
      }),
    );
  }
}
document.addEventListener("DOMContentLoaded", function () {
  window.rbac = new RoleBasedAccessControl();
  const orgSelector = document.getElementById("organization-select");
  if (orgSelector) {
    orgSelector.addEventListener("change", () => {
      window.rbac.updateOrganizationContext();
    });
  }
});
