/**
 * Watson Organizational Ideas Management System
 * Front-end interface for capturing and managing organizational ideas
 */

class WatsonIdeasManager {
  constructor() {
    this.apiBase = "";
    this.currentIdeas = [];
    this.initializeInterface();
    this.loadRecentIdeas();
  }

  initializeInterface() {
    // Create the organizational ideas interface
    this.createIdeasInterface();

    // Set up event listeners
    this.setupEventListeners();

    // Load ASI goals if available
    this.loadASIGoals();
  }

  createIdeasInterface() {
    const watsonSection = document.getElementById("watson-ideas-section");
    if (!watsonSection) return;

    watsonSection.innerHTML = `
            <div class="card border-success mb-4">
                <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-lightbulb"></i> Watson Organizational Ideas & ASI Controls
                    </h5>
                    <div>
                        <button class="btn btn-light btn-sm me-2" onclick="watsonIdeas.openASIEditor()">
                            <i class="fas fa-robot"></i> Edit ASI Goals
                        </button>
                        <button class="btn btn-light btn-sm" onclick="watsonIdeas.triggerASIDebug()">
                            <i class="fas fa-sync-alt"></i> Run ASI Debug
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <!-- ASI Goals Overview -->
                    <div class="row mb-4" id="asi-goals-overview">
                        <div class="col-12">
                            <h6>ASI Goals Status:</h6>
                            <div id="goals-status-grid" class="row">
                                <!-- Goals loaded dynamically -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Organizational Ideas Input -->
                    <div class="organizational-ideas-input">
                        <h6>Submit Organizational Ideas:</h6>
                        <div class="row">
                            <div class="col-md-8">
                                <textarea class="form-control mb-3" id="orgIdeasInput" rows="4" 
                                          placeholder="Enter organizational ideas, system enhancements, or modifications here...
Examples:
• Integrate new GAUGE API features
• Enhance confidence algorithms
• Add predictive maintenance modules
• Improve user interface elements"></textarea>
                            </div>
                            <div class="col-md-4">
                                <div class="form-group mb-2">
                                    <label for="ideaCategory">Category:</label>
                                    <select class="form-select" id="ideaCategory">
                                        <option value="Enhancement">Enhancement</option>
                                        <option value="Bug Fix">Bug Fix</option>
                                        <option value="New Feature">New Feature</option>
                                        <option value="Security">Security</option>
                                        <option value="Performance">Performance</option>
                                        <option value="UI/UX">UI/UX</option>
                                        <option value="Data Integration">Data Integration</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary w-100" onclick="watsonIdeas.submitIdea()">
                                    <i class="fas fa-paper-plane"></i> Submit to Watson
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recent Ideas Display -->
                    <div class="recent-ideas mt-4">
                        <h6>Recent Organizational Ideas:</h6>
                        <div id="recentIdeasContainer" class="ideas-container">
                            <!-- Recent ideas loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  setupEventListeners() {
    // Auto-save drafts
    const textArea = document.getElementById("orgIdeasInput");
    if (textArea) {
      textArea.addEventListener("input", () => {
        localStorage.setItem("watson_idea_draft", textArea.value);
      });

      // Load saved draft
      const draft = localStorage.getItem("watson_idea_draft");
      if (draft) {
        textArea.value = draft;
      }
    }

    // Enter key shortcut
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.key === "Enter") {
        this.submitIdea();
      }
    });
  }

  async loadASIGoals() {
    try {
      const response = await fetch("/api/daily_goals");
      const data = await response.json();

      if (data.goals) {
        this.displayGoalsOverview(data.goals);
      }
    } catch (error) {
      console.error("Error loading ASI goals:", error);
    }
  }

  displayGoalsOverview(goals) {
    const container = document.getElementById("goals-status-grid");
    if (!container) return;

    container.innerHTML = goals
      .map(
        (goal) => `
            <div class="col-md-4 mb-2">
                <div class="goal-status-card p-2 border rounded">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="goal-title">${goal.title}</span>
                        <span class="badge badge-${this.getPriorityColor(goal.priority_level)}">
                            ${goal.completion_percentage.toFixed(1)}%
                        </span>
                    </div>
                    <div class="progress mt-1" style="height: 4px;">
                        <div class="progress-bar bg-${this.getPriorityColor(goal.priority_level)}" 
                             style="width: ${goal.completion_percentage}%"></div>
                    </div>
                </div>
            </div>
        `,
      )
      .join("");
  }

  getPriorityColor(priority) {
    switch (priority.toLowerCase()) {
      case "high":
        return "danger";
      case "medium":
        return "warning";
      case "low":
        return "success";
      default:
        return "info";
    }
  }

  async submitIdea() {
    const textarea = document.getElementById("orgIdeasInput");
    const category = document.getElementById("ideaCategory");

    if (!textarea || !textarea.value.trim()) {
      this.showNotification(
        "Please enter an idea before submitting",
        "warning",
      );
      return;
    }

    const ideaData = {
      title: this.extractTitle(textarea.value),
      description: textarea.value.trim(),
      category: category ? category.value : "General",
    };

    try {
      const response = await fetch("/api/submit_organizational_idea", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(ideaData),
      });

      const result = await response.json();

      if (result.success) {
        this.showNotification(
          "Idea submitted successfully to Watson module!",
          "success",
        );
        textarea.value = "";
        localStorage.removeItem("watson_idea_draft");
        this.loadRecentIdeas();

        // Show ASI analysis if available
        if (result.asi_analysis) {
          this.displayASIAnalysis(result.asi_analysis);
        }
      } else {
        this.showNotification(
          "Error submitting idea: " + result.error,
          "error",
        );
      }
    } catch (error) {
      console.error("Submission error:", error);
      this.showNotification("Network error submitting idea", "error");
    }
  }

  extractTitle(description) {
    // Extract first sentence or first 50 characters as title
    const firstSentence = description.split(".")[0];
    return firstSentence.length > 50
      ? firstSentence.substring(0, 47) + "..."
      : firstSentence;
  }

  async loadRecentIdeas() {
    try {
      const response = await fetch("/api/get_organizational_ideas");
      const data = await response.json();

      if (data.ideas) {
        this.currentIdeas = data.ideas;
        this.displayRecentIdeas(data.ideas);
      }
    } catch (error) {
      console.error("Error loading recent ideas:", error);
    }
  }

  displayRecentIdeas(ideas) {
    const container = document.getElementById("recentIdeasContainer");
    if (!container) return;

    if (ideas.length === 0) {
      container.innerHTML = '<p class="text-muted">No ideas submitted yet.</p>';
      return;
    }

    container.innerHTML = ideas
      .slice(0, 5)
      .map(
        (idea) => `
            <div class="idea-card border rounded p-3 mb-2">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${idea.title}</h6>
                    <div>
                        <span class="badge bg-${this.getPriorityColor(idea.priority)}">${idea.priority}</span>
                        <span class="badge bg-secondary ms-1">${idea.category}</span>
                    </div>
                </div>
                <p class="mb-2 small">${idea.description.substring(0, 150)}${idea.description.length > 150 ? "..." : ""}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        Submitted: ${new Date(idea.timestamp).toLocaleString()}
                    </small>
                    <div>
                        <button class="btn btn-sm btn-outline-primary" onclick="watsonIdeas.viewIdeaDetails('${idea.id}')">
                            View Details
                        </button>
                        ${
                          idea.status === "submitted"
                            ? `
                        <button class="btn btn-sm btn-outline-success ms-1" onclick="watsonIdeas.approveIdea('${idea.id}')">
                            Approve
                        </button>
                        `
                            : ""
                        }
                    </div>
                </div>
            </div>
        `,
      )
      .join("");
  }

  displayASIAnalysis(analysis) {
    const analysisHtml = `
            <div class="asi-analysis-popup" style="position: fixed; top: 20px; right: 20px; 
                 background: white; border: 2px solid #28a745; border-radius: 8px; 
                 padding: 20px; max-width: 400px; z-index: 9999; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
                <h6><i class="fas fa-robot text-success"></i> ASI Analysis Complete</h6>
                <div class="analysis-content">
                    <p><strong>Feasibility:</strong> ${analysis.feasibility_score}%</p>
                    <p><strong>Impact:</strong> ${analysis.impact_score}%</p>
                    <p><strong>Recommendation:</strong> ${analysis.asi_recommendation}</p>
                    <p><strong>Timeline:</strong> ${analysis.estimated_implementation_time}</p>
                </div>
                <button class="btn btn-sm btn-success" onclick="this.parentElement.remove()">
                    Got it!
                </button>
            </div>
        `;

    document.body.insertAdjacentHTML("beforeend", analysisHtml);

    // Auto-remove after 10 seconds
    setTimeout(() => {
      const popup = document.querySelector(".asi-analysis-popup");
      if (popup) popup.remove();
    }, 10000);
  }

  async approveIdea(ideaId) {
    try {
      const response = await fetch("/api/update_idea_status", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          idea_id: ideaId,
          status: "approved",
          notes: "Approved by Watson",
        }),
      });

      const result = await response.json();

      if (result.success) {
        this.showNotification("Idea approved successfully", "success");
        this.loadRecentIdeas();
      }
    } catch (error) {
      console.error("Error approving idea:", error);
    }
  }

  openASIEditor() {
    // Create modal for ASI goal editing
    const modal = `
            <div class="modal fade" id="asiEditorModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">ASI Goals Editor</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Direct ASI goal modification interface:</p>
                            <div id="asi-goals-editor">
                                <!-- Goals editor will be populated here -->
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="watsonIdeas.saveASIGoals()">
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

    document.body.insertAdjacentHTML("beforeend", modal);
    new bootstrap.Modal(document.getElementById("asiEditorModal")).show();
  }

  async triggerASIDebug() {
    try {
      this.showNotification("Triggering ASI debug cycle...", "info");

      const response = await fetch("/api/trigger_debug_cycle");
      const result = await response.json();

      if (result.status === "debug_cycle_completed") {
        this.showNotification(
          "ASI debug cycle completed successfully",
          "success",
        );
        this.loadASIGoals(); // Refresh goals
      }
    } catch (error) {
      console.error("Error triggering ASI debug:", error);
      this.showNotification("Error running ASI debug cycle", "error");
    }
  }

  showNotification(message, type) {
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-white bg-${type === "error" ? "danger" : type} border-0`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 5000);
  }

  viewIdeaDetails(ideaId) {
    const idea = this.currentIdeas.find((i) => i.id === ideaId);
    if (!idea) return;

    // Create detailed view modal
    const modal = `
            <div class="modal fade" id="ideaDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${idea.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-8">
                                    <h6>Description:</h6>
                                    <p>${idea.description}</p>
                                    
                                    <h6>ASI Analysis:</h6>
                                    <ul>
                                        <li>Feasibility: ${idea.asi_analysis.feasibility_score}%</li>
                                        <li>Impact: ${idea.asi_analysis.impact_score}%</li>
                                        <li>Recommendation: ${idea.asi_analysis.asi_recommendation}</li>
                                        <li>Timeline: ${idea.asi_analysis.estimated_implementation_time}</li>
                                    </ul>
                                </div>
                                <div class="col-md-4">
                                    <h6>Details:</h6>
                                    <p><strong>Category:</strong> ${idea.category}</p>
                                    <p><strong>Priority:</strong> ${idea.priority}</p>
                                    <p><strong>Status:</strong> ${idea.status}</p>
                                    <p><strong>Submitted:</strong> ${new Date(idea.timestamp).toLocaleString()}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

    document.body.insertAdjacentHTML("beforeend", modal);
    new bootstrap.Modal(document.getElementById("ideaDetailsModal")).show();
  }
}

// Initialize Watson Ideas Manager
let watsonIdeas;
document.addEventListener("DOMContentLoaded", function () {
  watsonIdeas = new WatsonIdeasManager();
});

// Global function for easy access
window.watsonIdeas = watsonIdeas;
