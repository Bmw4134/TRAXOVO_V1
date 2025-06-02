// TRAXOVO Drill-Down Analytics - Enterprise Intelligence
class DrillDownAnalytics {
  constructor() {
    this.currentLevel = 0;
    this.breadcrumbs = [];
    this.init();
  }

  init() {
    this.setupInteractiveElements();
    this.bindEvents();
  }

  setupInteractiveElements() {
    const metrics = document.querySelectorAll(
      ".metric-card, .analytics-widget",
    );
    metrics.forEach((metric) => {
      metric.style.cursor = "pointer";
      metric.addEventListener("click", (e) => {
        const dataType = e.target.dataset.drillType || "general";
        this.drillDown(dataType, e.target);
      });
    });
  }

  drillDown(type, element) {
    this.currentLevel++;
    this.breadcrumbs.push(type);

    // Show detailed view
    const detailPanel = this.createDetailPanel(type);
    document.body.appendChild(detailPanel);

    // Animate the transition
    element.style.transform = "scale(0.95)";
    setTimeout(() => {
      element.style.transform = "scale(1)";
    }, 200);
  }

  createDetailPanel(type) {
    const panel = document.createElement("div");
    panel.className = "drill-down-panel";
    panel.innerHTML = `
            <div class="panel-header">
                <h4>${type.charAt(0).toUpperCase() + type.slice(1)} Analytics</h4>
                <button class="btn btn-sm btn-outline-secondary" onclick="drillDownAnalytics.goBack()">
                    <i class="bi bi-arrow-left"></i> Back
                </button>
            </div>
            <div class="panel-content">
                <div class="analytics-grid">
                    <div class="metric-detail">
                        <label>Current Period:</label>
                        <span class="value">Real-time data loading...</span>
                    </div>
                    <div class="metric-detail">
                        <label>Trend Analysis:</label>
                        <span class="value">Calculating...</span>
                    </div>
                </div>
            </div>
        `;

    panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 2000;
            min-width: 400px;
            max-width: 600px;
        `;

    return panel;
  }

  goBack() {
    const panel = document.querySelector(".drill-down-panel");
    if (panel) {
      panel.remove();
    }
    this.currentLevel = Math.max(0, this.currentLevel - 1);
    this.breadcrumbs.pop();
  }

  bindEvents() {
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.goBack();
      }
    });
  }
}

const drillDownAnalytics = new DrillDownAnalytics();
