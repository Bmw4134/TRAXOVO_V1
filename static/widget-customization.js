/**
 * TRAXOVO Personalized Dashboard Widget Customization
 * Allows users to customize dashboard layout and widget preferences
 */
(function () {
  "use strict";

  class WidgetCustomizer {
    constructor() {
      this.widgets = new Map();
      this.userPreferences = this.loadUserPreferences();
      this.availableWidgets = [
        { id: "fleet-status", name: "Fleet Status", category: "operations" },
        {
          id: "revenue-metrics",
          name: "Revenue Metrics",
          category: "financial",
        },
        {
          id: "asset-utilization",
          name: "Asset Utilization",
          category: "analytics",
        },
        {
          id: "driver-performance",
          name: "Driver Performance",
          category: "operations",
        },
        {
          id: "maintenance-alerts",
          name: "Maintenance Alerts",
          category: "operations",
        },
        {
          id: "billing-summary",
          name: "Billing Summary",
          category: "financial",
        },
        {
          id: "efficiency-trends",
          name: "Efficiency Trends",
          category: "analytics",
        },
        {
          id: "weather-overview",
          name: "Weather Overview",
          category: "external",
        },
      ];
      this.initializeCustomization();
    }

    loadUserPreferences() {
      const stored = localStorage.getItem("traxovo_widget_preferences");
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch (e) {
          console.warn("Failed to parse widget preferences, using defaults");
        }
      }

      return {
        layout: "grid-4x2",
        enabledWidgets: [
          "fleet-status",
          "revenue-metrics",
          "asset-utilization",
          "driver-performance",
        ],
        widgetOrder: [],
        theme: "professional-blue",
        autoRefresh: true,
        refreshInterval: 30000,
      };
    }

    saveUserPreferences() {
      localStorage.setItem(
        "traxovo_widget_preferences",
        JSON.stringify(this.userPreferences),
      );

      // Save to server for persistence across devices
      fetch("/api/user/widget-preferences", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.getCSRFToken(),
        },
        body: JSON.stringify(this.userPreferences),
      }).catch((e) => console.warn("Failed to sync preferences to server:", e));
    }

    getCSRFToken() {
      const meta = document.querySelector('meta[name="csrf-token"]');
      return meta ? meta.getAttribute("content") : "";
    }

    initializeCustomization() {
      this.createCustomizationUI();
      this.applyUserPreferences();
      this.setupEventListeners();
    }

    createCustomizationUI() {
      const customizeBtn = document.createElement("button");
      customizeBtn.id = "customize-dashboard-btn";
      customizeBtn.innerHTML = "⚙️ Customize";
      customizeBtn.className = "customize-btn";
      customizeBtn.onclick = () => this.showCustomizationPanel();

      const header = document.querySelector(".header");
      if (header) {
        header.appendChild(customizeBtn);
      }

      this.createCustomizationPanel();
    }

    createCustomizationPanel() {
      const panel = document.createElement("div");
      panel.id = "customization-panel";
      panel.className = "customization-panel hidden";

      panel.innerHTML = `
                <div class="customization-content">
                    <div class="customization-header">
                        <h3>Customize Your Dashboard</h3>
                        <button class="close-btn" onclick="window.widgetCustomizer.hideCustomizationPanel()">×</button>
                    </div>
                    
                    <div class="customization-body">
                        <div class="customization-section">
                            <h4>Layout</h4>
                            <div class="layout-options">
                                <div class="layout-option" data-layout="grid-4x2">
                                    <div class="layout-preview grid-4x2-preview"></div>
                                    <span>4x2 Grid</span>
                                </div>
                                <div class="layout-option" data-layout="grid-3x3">
                                    <div class="layout-preview grid-3x3-preview"></div>
                                    <span>3x3 Grid</span>
                                </div>
                                <div class="layout-option" data-layout="single-column">
                                    <div class="layout-preview single-column-preview"></div>
                                    <span>Single Column</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="customization-section">
                            <h4>Widgets</h4>
                            <div class="widget-selection">
                                ${this.generateWidgetSelectionHTML()}
                            </div>
                        </div>
                        
                        <div class="customization-section">
                            <h4>Settings</h4>
                            <div class="settings-options">
                                <label>
                                    <input type="checkbox" id="auto-refresh-toggle"> 
                                    Auto-refresh data
                                </label>
                                <label>
                                    Refresh interval: 
                                    <select id="refresh-interval">
                                        <option value="15000">15 seconds</option>
                                        <option value="30000">30 seconds</option>
                                        <option value="60000">1 minute</option>
                                        <option value="300000">5 minutes</option>
                                    </select>
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="customization-footer">
                        <button class="btn-secondary" onclick="window.widgetCustomizer.resetToDefaults()">Reset to Defaults</button>
                        <button class="btn-primary" onclick="window.widgetCustomizer.applyChanges()">Apply Changes</button>
                    </div>
                </div>
            `;

      document.body.appendChild(panel);
    }

    generateWidgetSelectionHTML() {
      const categories = [
        ...new Set(this.availableWidgets.map((w) => w.category)),
      ];

      return categories
        .map(
          (category) => `
                <div class="widget-category">
                    <h5>${this.capitalize(category)}</h5>
                    <div class="widget-list">
                        ${this.availableWidgets
                          .filter((w) => w.category === category)
                          .map(
                            (widget) => `
                                <label class="widget-item">
                                    <input type="checkbox" 
                                           data-widget-id="${widget.id}" 
                                           ${this.userPreferences.enabledWidgets.includes(widget.id) ? "checked" : ""}>
                                    <span>${widget.name}</span>
                                </label>
                            `,
                          )
                          .join("")}
                    </div>
                </div>
            `,
        )
        .join("");
    }

    capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }

    showCustomizationPanel() {
      const panel = document.getElementById("customization-panel");
      panel.classList.remove("hidden");

      // Set current values
      document
        .querySelector(`[data-layout="${this.userPreferences.layout}"]`)
        ?.classList.add("selected");
      document.getElementById("auto-refresh-toggle").checked =
        this.userPreferences.autoRefresh;
      document.getElementById("refresh-interval").value =
        this.userPreferences.refreshInterval;
    }

    hideCustomizationPanel() {
      const panel = document.getElementById("customization-panel");
      panel.classList.add("hidden");
    }

    setupEventListeners() {
      document.addEventListener("click", (e) => {
        if (e.target.matches(".layout-option")) {
          document
            .querySelectorAll(".layout-option")
            .forEach((opt) => opt.classList.remove("selected"));
          e.target.classList.add("selected");
        }
      });
    }

    applyUserPreferences() {
      this.applyLayout();
      this.applyWidgetVisibility();
      this.setupAutoRefresh();
    }

    applyLayout() {
      const dashboardContainer =
        document.querySelector(".main-content") ||
        document.querySelector(".dashboard-container");
      if (dashboardContainer) {
        dashboardContainer.className = `main-content layout-${this.userPreferences.layout}`;
      }
    }

    applyWidgetVisibility() {
      this.availableWidgets.forEach((widget) => {
        const element = document.querySelector(`[data-widget="${widget.id}"]`);
        if (element) {
          element.style.display = this.userPreferences.enabledWidgets.includes(
            widget.id,
          )
            ? "block"
            : "none";
        }
      });
    }

    setupAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
      }

      if (this.userPreferences.autoRefresh) {
        this.refreshTimer = setInterval(() => {
          this.refreshDashboardData();
        }, this.userPreferences.refreshInterval);
      }
    }

    refreshDashboardData() {
      // Trigger refresh of authentic data
      if (window.loadMetrics) {
        window.loadMetrics();
      }

      // Update last refresh time
      const refreshIndicator = document.querySelector(".last-refresh");
      if (refreshIndicator) {
        refreshIndicator.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
      }
    }

    applyChanges() {
      // Get selected layout
      const selectedLayout = document.querySelector(".layout-option.selected");
      if (selectedLayout) {
        this.userPreferences.layout = selectedLayout.dataset.layout;
      }

      // Get enabled widgets
      const enabledWidgets = [];
      document
        .querySelectorAll("[data-widget-id]:checked")
        .forEach((checkbox) => {
          enabledWidgets.push(checkbox.dataset.widgetId);
        });
      this.userPreferences.enabledWidgets = enabledWidgets;

      // Get settings
      this.userPreferences.autoRefresh = document.getElementById(
        "auto-refresh-toggle",
      ).checked;
      this.userPreferences.refreshInterval = parseInt(
        document.getElementById("refresh-interval").value,
      );

      this.saveUserPreferences();
      this.applyUserPreferences();
      this.hideCustomizationPanel();

      // Show success message
      this.showNotification("Dashboard customization applied successfully!");
    }

    resetToDefaults() {
      this.userPreferences = {
        layout: "grid-4x2",
        enabledWidgets: [
          "fleet-status",
          "revenue-metrics",
          "asset-utilization",
          "driver-performance",
        ],
        widgetOrder: [],
        theme: "professional-blue",
        autoRefresh: true,
        refreshInterval: 30000,
      };

      this.saveUserPreferences();
      this.applyUserPreferences();
      this.hideCustomizationPanel();

      // Reload to show changes
      window.location.reload();
    }

    showNotification(message) {
      const notification = document.createElement("div");
      notification.className = "notification success";
      notification.textContent = message;

      document.body.appendChild(notification);

      setTimeout(() => {
        notification.remove();
      }, 3000);
    }
  }

  // Initialize when DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    window.widgetCustomizer = new WidgetCustomizer();
  });
})();
