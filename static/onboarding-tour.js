/**
 * TRAXOVO Interactive Onboarding Tour
 * Smooth guided experience for new users
 */

class TRAXOVOOnboardingTour {
  constructor() {
    this.currentStep = 0;
    this.steps = [
      {
        target: ".navbar-brand",
        title: "Welcome to TRAXOVO",
        content:
          "Your enterprise fleet intelligence platform with 717 assets and 92 drivers under management.",
        position: "bottom",
      },
      {
        target: '[data-tour="fleet-overview"]',
        title: "Fleet Overview",
        content:
          "Monitor your active fleet status with real-time telematic data from GAUGE API integration.",
        position: "bottom",
      },
      {
        target: '[data-tour="attendance-matrix"]',
        title: "Attendance Intelligence",
        content:
          "Automated attendance tracking with May 2025 report processing and overtime calculations.",
        position: "right",
      },
      {
        target: '[data-tour="billing-automation"]',
        title: "Billing Automation",
        content:
          "Automated billing with authentic RAGLE data processing for equipment management.",
        position: "left",
      },
      {
        target: '[data-tour="ai-intelligence"]',
        title: "AI Intelligence Center",
        content:
          "Fortune 500-grade predictive analytics with machine learning insights.",
        position: "top",
      },
      {
        target: '[data-tour="voice-commands"]',
        title: "Voice Commands",
        content:
          'Use Alt+V or click the microphone for hands-free navigation. Try saying "dashboard" or "billing".',
        position: "bottom",
      },
    ];
    this.overlay = null;
    this.tooltip = null;
    this.isActive = false;
  }

  start() {
    // Check if user has already seen the tour
    if (localStorage.getItem("traxovo-tour-completed") === "true") {
      return;
    }

    this.isActive = true;
    this.currentStep = 0;
    this.createOverlay();
    this.showStep(0);

    // Track tour start
    this.trackEvent("tour_started");
  }

  createOverlay() {
    this.overlay = document.createElement("div");
    this.overlay.className = "onboarding-overlay";
    this.overlay.innerHTML = `
            <style>
                .onboarding-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 9999;
                    pointer-events: none;
                }
                
                .onboarding-spotlight {
                    position: absolute;
                    background: transparent;
                    border-radius: 8px;
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5),
                                0 0 0 9999px rgba(0, 0, 0, 0.7);
                    pointer-events: auto;
                    transition: all 0.3s ease;
                }
                
                .onboarding-tooltip {
                    position: absolute;
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    max-width: 350px;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
                                0 10px 10px -5px rgba(0, 0, 0, 0.04);
                    z-index: 10001;
                    pointer-events: auto;
                    border: 1px solid #e5e7eb;
                }
                
                /* Mobile Optimizations */
                @media (max-width: 768px) {
                    .onboarding-tooltip {
                        max-width: 300px;
                        padding: 16px;
                        font-size: 14px;
                        margin: 10px;
                    }
                    
                    .onboarding-tooltip h3 {
                        font-size: 16px;
                        margin-bottom: 8px;
                    }
                    
                    .onboarding-tooltip p {
                        font-size: 13px;
                        line-height: 1.4;
                        margin-bottom: 16px;
                    }
                    
                    .onboarding-buttons {
                        flex-direction: column;
                        gap: 8px;
                    }
                    
                    .onboarding-btn {
                        width: 100%;
                        padding: 12px 16px;
                        font-size: 14px;
                        text-align: center;
                    }
                    
                    .onboarding-controls {
                        flex-direction: column;
                        gap: 12px;
                        align-items: center;
                    }
                    
                    .onboarding-progress {
                        order: 2;
                    }
                    
                    .onboarding-buttons {
                        order: 1;
                        width: 100%;
                    }
                }
                
                .onboarding-tooltip h3 {
                    margin: 0 0 12px 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #1f2937;
                }
                
                .onboarding-tooltip p {
                    margin: 0 0 20px 0;
                    color: #6b7280;
                    line-height: 1.5;
                }
                
                .onboarding-controls {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .onboarding-progress {
                    display: flex;
                    gap: 6px;
                }
                
                .onboarding-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #d1d5db;
                    transition: background 0.2s;
                }
                
                .onboarding-dot.active {
                    background: #3b82f6;
                }
                
                .onboarding-buttons {
                    display: flex;
                    gap: 8px;
                }
                
                .onboarding-btn {
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: 1px solid #d1d5db;
                    background: white;
                    color: #6b7280;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s;
                }
                
                .onboarding-btn:hover {
                    background: #f9fafb;
                }
                
                .onboarding-btn.primary {
                    background: #3b82f6;
                    color: white;
                    border-color: #3b82f6;
                }
                
                .onboarding-btn.primary:hover {
                    background: #2563eb;
                }
                
                @media (max-width: 768px) {
                    .onboarding-tooltip {
                        max-width: 280px;
                        padding: 20px;
                    }
                }
            </style>
        `;
    document.body.appendChild(this.overlay);
  }

  showStep(stepIndex) {
    if (stepIndex >= this.steps.length) {
      this.complete();
      return;
    }

    const step = this.steps[stepIndex];
    const target = document.querySelector(step.target);

    if (!target) {
      // Skip missing elements and go to next step
      this.showStep(stepIndex + 1);
      return;
    }

    // Create spotlight
    this.createSpotlight(target);

    // Create tooltip
    this.createTooltip(step, target, stepIndex);

    // Smooth scroll to element
    target.scrollIntoView({
      behavior: "smooth",
      block: "center",
      inline: "center",
    });

    this.currentStep = stepIndex;
  }

  createSpotlight(target) {
    // Remove existing spotlight
    const existing = this.overlay.querySelector(".onboarding-spotlight");
    if (existing) existing.remove();

    const rect = target.getBoundingClientRect();
    const spotlight = document.createElement("div");
    spotlight.className = "onboarding-spotlight";

    // Add padding around the element
    const padding = 8;
    spotlight.style.left = rect.left - padding + "px";
    spotlight.style.top = rect.top - padding + "px";
    spotlight.style.width = rect.width + padding * 2 + "px";
    spotlight.style.height = rect.height + padding * 2 + "px";

    this.overlay.appendChild(spotlight);
  }

  createTooltip(step, target, stepIndex) {
    // Remove existing tooltip
    if (this.tooltip) this.tooltip.remove();

    this.tooltip = document.createElement("div");
    this.tooltip.className = "onboarding-tooltip";

    this.tooltip.innerHTML = `
            <h3>${step.title}</h3>
            <p>${step.content}</p>
            <div class="onboarding-controls">
                <div class="onboarding-progress">
                    ${this.steps
                      .map(
                        (_, i) =>
                          `<div class="onboarding-dot ${i === stepIndex ? "active" : ""}"></div>`,
                      )
                      .join("")}
                </div>
                <div class="onboarding-buttons">
                    ${stepIndex > 0 ? '<button class="onboarding-btn" onclick="tour.previous()">Previous</button>' : ""}
                    <button class="onboarding-btn" onclick="tour.skip()">Skip Tour</button>
                    <button class="onboarding-btn primary" onclick="tour.next()">
                        ${stepIndex === this.steps.length - 1 ? "Finish" : "Next"}
                    </button>
                </div>
            </div>
        `;

    // Position tooltip
    this.positionTooltip(target, step.position);
    document.body.appendChild(this.tooltip);
  }

  positionTooltip(target, position) {
    const rect = target.getBoundingClientRect();
    const tooltipRect = { width: 350, height: 200 }; // Estimated size

    let left, top;

    switch (position) {
      case "top":
        left = rect.left + rect.width / 2 - tooltipRect.width / 2;
        top = rect.top - tooltipRect.height - 12;
        break;
      case "bottom":
        left = rect.left + rect.width / 2 - tooltipRect.width / 2;
        top = rect.bottom + 12;
        break;
      case "left":
        left = rect.left - tooltipRect.width - 12;
        top = rect.top + rect.height / 2 - tooltipRect.height / 2;
        break;
      case "right":
        left = rect.right + 12;
        top = rect.top + rect.height / 2 - tooltipRect.height / 2;
        break;
      default:
        left = rect.left;
        top = rect.bottom + 12;
    }

    // Keep tooltip within viewport
    const padding = 20;
    left = Math.max(
      padding,
      Math.min(left, window.innerWidth - tooltipRect.width - padding),
    );
    top = Math.max(
      padding,
      Math.min(top, window.innerHeight - tooltipRect.height - padding),
    );

    this.tooltip.style.left = left + "px";
    this.tooltip.style.top = top + "px";
  }

  next() {
    this.trackEvent("tour_step_completed", { step: this.currentStep });
    this.showStep(this.currentStep + 1);
  }

  previous() {
    if (this.currentStep > 0) {
      this.showStep(this.currentStep - 1);
    }
  }

  skip() {
    this.trackEvent("tour_skipped", { step: this.currentStep });
    this.complete();
  }

  complete() {
    this.isActive = false;
    localStorage.setItem("traxovo-tour-completed", "true");

    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
    }

    if (this.tooltip) {
      this.tooltip.remove();
      this.tooltip = null;
    }

    // Show completion message
    this.showCompletionMessage();
    this.trackEvent("tour_completed");
  }

  showCompletionMessage() {
    const message = document.createElement("div");
    message.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            font-weight: 500;
            animation: slideIn 0.3s ease;
        `;

    message.innerHTML = `
            <style>
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            </style>
            🎉 Welcome to TRAXOVO! You're ready to manage your fleet with enterprise intelligence.
        `;

    document.body.appendChild(message);

    setTimeout(() => {
      message.style.animation = "slideIn 0.3s ease reverse";
      setTimeout(() => message.remove(), 300);
    }, 3000);
  }

  trackEvent(event, data = {}) {
    // Track user engagement for analytics
    console.log(`Tour Event: ${event}`, data);

    // Send to analytics if available
    if (window.gtag) {
      window.gtag("event", event, {
        event_category: "onboarding",
        ...data,
      });
    }
  }

  reset() {
    localStorage.removeItem("traxovo-tour-completed");
    this.complete();
  }
}

// Initialize tour system
const tour = new TRAXOVOOnboardingTour();

// Auto-start tour for new users
document.addEventListener("DOMContentLoaded", function () {
  // Small delay to ensure page is fully loaded
  setTimeout(() => {
    tour.start();
  }, 1000);
});

// Add restart tour button for users who want to see it again
function addTourRestartButton() {
  const restartBtn = document.createElement("button");
  restartBtn.innerHTML = "🎯 Restart Tour";
  restartBtn.className = "btn btn-sm btn-outline-primary";
  restartBtn.style.cssText =
    "position: fixed; bottom: 20px; right: 20px; z-index: 1000;";
  restartBtn.onclick = () => {
    tour.reset();
    setTimeout(() => tour.start(), 500);
  };

  // Only show if tour was completed
  if (localStorage.getItem("traxovo-tour-completed") === "true") {
    document.body.appendChild(restartBtn);
  }
}

// Add restart button after DOM is loaded
document.addEventListener("DOMContentLoaded", addTourRestartButton);
