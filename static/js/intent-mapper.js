/** TRAXORA Intent Mapping System
 *
 * This module analyzes user behavior to determine likely intents and usage patterns.
 * It creates invisible tags for user actions and maps them to higher-level intents
 * that can be used for personalization and adaptive UI.
 */
class IntentMapper {
  constructor() {
    this.actions = this.loadActions();
    this.intents = {
      reporting: {
        score: 0,
        threshold: 3,
        actions: ["view_report", "export_report", "filter_report"],
      },
      monitoring: {
        score: 0,
        threshold: 3,
        actions: ["view_dashboard", "check_status", "view_alerts"],
      },
      managing: {
        score: 0,
        threshold: 4,
        actions: [
          "edit_record",
          "create_record",
          "assign_task",
          "update_settings",
        ],
      },
      analyzing: {
        score: 0,
        threshold: 3,
        actions: ["filter_data", "sort_data", "search_records", "view_details"],
      },
      planning: {
        score: 0,
        threshold: 3,
        actions: ["view_calendar", "schedule_event", "view_forecast"],
      },
    };
    this.currentIntent = this.loadCurrentIntent();
    this.sessionStart = new Date();
    this.lastActivity = new Date();
    this.pageViews = {};
    this.init();
  }
  init() {
    this.setupActionTracking();
    this.trackSession();
    this.analyzeActions();
    this.adaptUIToIntent();
  }
  loadActions() {
    const savedActions = localStorage.getItem("traxora_user_actions");
    return savedActions ? JSON.parse(savedActions) : [];
  }
  saveActions() {
    if (this.actions.length > 100) {
      this.actions = this.actions.slice(-100);
    }
    localStorage.setItem("traxora_user_actions", JSON.stringify(this.actions));
  }
  loadCurrentIntent() {
    const savedIntent = localStorage.getItem("traxora_current_intent");
    return savedIntent || "general";
  }
  saveCurrentIntent() {
    localStorage.setItem("traxora_current_intent", this.currentIntent);
  }
  setupActionTracking() {
    this.trackAction("page_view", {
      url: window.location.pathname,
      title: document.title,
    });
    document
      .querySelectorAll(".navbar-nav .nav-link, .nav-item .dropdown-item")
      .forEach((link) => {
        link.addEventListener("click", () => {
          const action = this.inferActionFromNavigation(link);
          this.trackAction(action, {
            element: link.textContent.trim(),
            url: link.getAttribute("href"),
          });
        });
      });
    document
      .querySelectorAll(
        "button:not([data-bs-dismiss]), .btn:not([data-bs-dismiss])",
      )
      .forEach((button) => {
        button.addEventListener("click", () => {
          if (
            button.classList.contains("btn-close") ||
            button.classList.contains("close")
          ) {
            return;
          }
          const action =
            button.dataset.action || this.inferActionFromButton(button);
          this.trackAction(action, {
            element: button.textContent.trim(),
            id: button.id || null,
            class: button.className,
          });
        });
      });
    document.querySelectorAll("form").forEach((form) => {
      form.addEventListener("submit", () => {
        const action = form.dataset.action || this.inferActionFromForm(form);
        this.trackAction(action, {
          form: form.id || form.className,
          action: form.getAttribute("action"),
        });
      });
    });
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach((trigger) => {
      trigger.addEventListener("click", () => {
        const targetId = trigger.getAttribute("data-bs-target");
        const modal = document.querySelector(targetId);
        if (modal) {
          const action = "view_modal";
          const modalTitle =
            modal.querySelector(".modal-title")?.textContent.trim() || "";
          this.trackAction(action, {
            modal: targetId,
            title: modalTitle,
          });
        }
      });
    });
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach((tab) => {
      tab.addEventListener("shown.bs.tab", (e) => {
        const action = "select_tab";
        this.trackAction(action, {
          tab: e.target.textContent.trim(),
          previousTab: e.relatedTarget
            ? e.relatedTarget.textContent.trim()
            : null,
        });
      });
    });
    document
      .querySelectorAll('input[type="search"], .search-form input[type="text"]')
      .forEach((search) => {
        search.form?.addEventListener("submit", () => {
          if (search.value.trim()) {
            this.trackAction("search_records", {
              query: search.value.trim(),
              searchField: search.name || search.id,
            });
          }
        });
      });
    document
      .querySelectorAll(
        'select.filter-select, input.filter-input, [data-filter="true"]',
      )
      .forEach((filter) => {
        filter.addEventListener("change", () => {
          this.trackAction("filter_data", {
            filter: filter.name || filter.id,
            value: filter.type === "checkbox" ? filter.checked : filter.value,
          });
        });
      });
    document
      .querySelectorAll('[data-sort="true"], .sort-select')
      .forEach((sort) => {
        sort.addEventListener("change", () => {
          this.trackAction("sort_data", {
            column: sort.value,
            element: sort.name || sort.id,
          });
        });
      });
    document
      .querySelectorAll(
        'a[href*="export"], a[href*="download"], button[data-action="export"]',
      )
      .forEach((link) => {
        link.addEventListener("click", () => {
          let format = "unknown";
          if (link.href) {
            if (link.href.includes("pdf")) format = "pdf";
            else if (link.href.includes("csv")) format = "csv";
            else if (link.href.includes("excel") || link.href.includes("xlsx"))
              format = "excel";
          }
          this.trackAction("export_report", {
            format: format,
            element: link.textContent.trim(),
          });
        });
      });
  }
  inferActionFromNavigation(element) {
    const text = element.textContent.toLowerCase().trim();
    const url = element.getAttribute("href") || "";
    if (url === "/" || url === "#" || url.includes("dashboard")) {
      return "view_dashboard";
    }
    if (text.includes("report") || url.includes("report")) {
      return "view_report";
    }
    if (text.includes("setting") || url.includes("setting")) {
      return "update_settings";
    }
    if (text.includes("alert") || url.includes("alert")) {
      return "view_alerts";
    }
    return "navigate";
  }
  inferActionFromButton(button) {
    const text = button.textContent.toLowerCase().trim();
    if (
      text.includes("add") ||
      text.includes("create") ||
      text.includes("new")
    ) {
      return "create_record";
    }
    if (text.includes("edit") || text.includes("update")) {
      return "edit_record";
    }
    if (text.includes("delete") || text.includes("remove")) {
      return "delete_record";
    }
    if (text.includes("save")) {
      return "save_record";
    }
    if (text.includes("export") || text.includes("download")) {
      return "export_report";
    }
    if (text.includes("filter") || text.includes("apply")) {
      return "filter_data";
    }
    if (text.includes("search")) {
      return "search_records";
    }
    if (text.includes("assign")) {
      return "assign_task";
    }
    if (button.classList.contains("btn-primary")) {
      return "primary_action";
    }
    return "button_click";
  }
  inferActionFromForm(form) {
    const formId = form.id || "";
    const formAction = form.getAttribute("action") || "";
    if (formId.includes("search") || formAction.includes("search")) {
      return "search_records";
    }
    if (formId.includes("filter") || formAction.includes("filter")) {
      return "filter_data";
    }
    if (
      formId.includes("create") ||
      formAction.includes("create") ||
      formAction.includes("new")
    ) {
      return "create_record";
    }
    if (
      formId.includes("edit") ||
      formAction.includes("edit") ||
      formAction.includes("update")
    ) {
      return "edit_record";
    }
    if (formId.includes("login")) {
      return "user_login";
    }
    const submitButton = form.querySelector(
      'button[type="submit"], input[type="submit"]',
    );
    if (submitButton) {
      const buttonText = submitButton.value || submitButton.textContent || "";
      if (buttonText.toLowerCase().includes("search")) {
        return "search_records";
      }
      if (buttonText.toLowerCase().includes("filter")) {
        return "filter_data";
      }
      if (
        buttonText.toLowerCase().includes("create") ||
        buttonText.toLowerCase().includes("add")
      ) {
        return "create_record";
      }
      if (
        buttonText.toLowerCase().includes("update") ||
        buttonText.toLowerCase().includes("save")
      ) {
        return "edit_record";
      }
    }
    return "form_submit";
  }
  trackAction(action, details = {}) {
    this.lastActivity = new Date();
    const actionData = {
      action: action,
      details: details,
      timestamp: new Date().toISOString(),
      page: window.location.pathname,
      sessionTime: Math.floor((this.lastActivity - this.sessionStart) / 1000),
    };
    this.actions.push(actionData);
    if (action === "page_view") {
      const page = details.url || window.location.pathname;
      this.pageViews[page] = (this.pageViews[page] || 0) + 1;
    }
    this.saveActions();
    this.analyzeAction(actionData);
    this.checkIntent();
  }
  trackSession() {
    window.addEventListener("beforeunload", () => {
      const timeOnPage = Math.floor((new Date() - this.lastActivity) / 1000);
      if (timeOnPage > 5) {
        // Only track if spent more than 5 seconds
        this.trackAction("page_exit", {
          timeOnPage: timeOnPage,
          url: window.location.pathname,
        });
      }
    });
    setInterval(() => {
      const now = new Date();
      const inactiveTime = Math.floor((now - this.lastActivity) / 1000);
      if (inactiveTime > 300) {
        this.sessionStart = now;
        this.lastActivity = now;
        this.trackAction("session_resume", {
          inactiveTime: inactiveTime,
        });
      }
    }, 60000); // Check every minute
  }
  analyzeAction(actionData) {
    const action = actionData.action;
    Object.keys(this.intents).forEach((intent) => {
      const intentData = this.intents[intent];
      if (intentData.actions.includes(action)) {
        intentData.score += 1;
        intentData.score *= 0.95;
      }
    });
  }
  analyzeActions() {
    Object.keys(this.intents).forEach((intent) => {
      this.intents[intent].score = 0;
    });
    const recentActions = this.actions.slice(-20);
    const actionCounts = {};
    recentActions.forEach((actionData) => {
      const action = actionData.action;
      actionCounts[action] = (actionCounts[action] || 0) + 1;
    });
    Object.keys(this.intents).forEach((intent) => {
      const intentData = this.intents[intent];
      intentData.actions.forEach((action) => {
        if (actionCounts[action]) {
          intentData.score += actionCounts[action];
        }
      });
    });
    this.checkIntent();
  }
  checkIntent() {
    let highestScore = 0;
    let highestIntent = "general";
    Object.keys(this.intents).forEach((intent) => {
      const intentData = this.intents[intent];
      if (
        intentData.score > highestScore &&
        intentData.score >= intentData.threshold
      ) {
        highestScore = intentData.score;
        highestIntent = intent;
      }
    });
    if (this.currentIntent !== highestIntent) {
      this.currentIntent = highestIntent;
      this.saveCurrentIntent();
      this.adaptUIToIntent();
    }
  }
  adaptUIToIntent() {
    if (!document.querySelector("[data-intent-adapt]")) {
      return;
    }
    document.querySelectorAll("[data-intent-adapt]").forEach((element) => {
      const intents = element.dataset.intentAdapt
        .split(",")
        .map((i) => i.trim());
      if (intents.includes(this.currentIntent) || intents.includes("all")) {
        element.style.display = ""; // Show this element
        element.classList.remove("d-none");
      } else {
        element.style.display = "none"; // Hide this element
        element.classList.add("d-none");
      }
    });
    document.querySelectorAll("[data-intent-nav]").forEach((navItem) => {
      const intents = navItem.dataset.intentNav.split(",").map((i) => i.trim());
      if (intents.includes(this.currentIntent)) {
        navItem.classList.add("intent-highlight"); // Highlight this nav item
      } else {
        navItem.classList.remove("intent-highlight");
      }
    });
    document.querySelectorAll("[data-intent-emphasis]").forEach((content) => {
      const intentEmphasis = content.dataset.intentEmphasis;
      if (intentEmphasis === this.currentIntent) {
        content.classList.add("intent-emphasized"); // Emphasize this content
      } else {
        content.classList.remove("intent-emphasized");
      }
    });
    this.triggerIntentHandlers();
  }
  triggerIntentHandlers() {
    const event = new CustomEvent("intentChanged", {
      detail: {
        intent: this.currentIntent,
        intents: this.intents,
      },
    });
    document.dispatchEvent(event);
    if (typeof window[`on${this.currentIntent}Intent`] === "function") {
      window[`on${this.currentIntent}Intent`](this.intents[this.currentIntent]);
    }
  }
  getCurrentIntent() {
    return this.currentIntent;
  }
  getIntentScores() {
    const scores = {};
    Object.keys(this.intents).forEach((intent) => {
      scores[intent] = this.intents[intent].score;
    });
    return scores;
  }
  getFrequentPages(limit = 5) {
    return Object.entries(this.pageViews)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map((entry) => ({
        url: entry[0],
        count: entry[1],
      }));
  }
  getRecentActionsByType(actionType, limit = 5) {
    return this.actions
      .filter((action) => action.action === actionType)
      .slice(-limit)
      .reverse();
  }
  exportBehaviorData() {
    return {
      currentIntent: this.currentIntent,
      intents: this.intents,
      pageViews: this.pageViews,
      recentActions: this.actions.slice(-20),
    };
  }
  clearAllData() {
    localStorage.removeItem("traxora_user_actions");
    localStorage.removeItem("traxora_current_intent");
    this.actions = [];
    this.pageViews = {};
    this.currentIntent = "general";
    Object.keys(this.intents).forEach((intent) => {
      this.intents[intent].score = 0;
    });
  }
}
document.addEventListener("DOMContentLoaded", function () {
  window.intentMapper = new IntentMapper();
  window.getCurrentUserIntent = function () {
    return window.intentMapper.getCurrentIntent();
  };
  window.getIntentScores = function () {
    return window.intentMapper.getIntentScores();
  };
  window.getTopVisitedPages = function () {
    return window.intentMapper.getFrequentPages();
  };
  document.dispatchEvent(new Event("intentMapperReady"));
});
const style = document.createElement("style");
style.textContent = `
.intent-highlight {
font-weight: bold !important;
position: relative;
}
.intent-highlight::after {
content: '';
position: absolute;
bottom: -2px;
left: 0;
width: 100%;
height: 2px;
background-color: var(--bs-primary);
animation: pulse 2s infinite;
}
.intent-emphasized {
border-left: 3px solid var(--bs-primary) !important;
padding-left: 15px !important;
background-color: rgba(var(--bs-primary-rgb), 0.05) !important;
}
@keyframes pulse {
0% { opacity: 0.6; }
50% { opacity: 1; }
100% { opacity: 0.6; }
}
`;
document.head.appendChild(style);
