// TRAXOVO Smooth Transitions - Enterprise UI Enhancement
class SmoothTransitions {
  constructor() {
    this.init();
  }

  init() {
    this.setupPageTransitions();
    this.setupButtonAnimations();
    this.setupCardHovers();
  }

  setupPageTransitions() {
    document.addEventListener("DOMContentLoaded", () => {
      document.body.style.opacity = "0";
      document.body.style.transition = "opacity 0.3s ease";
      setTimeout(() => {
        document.body.style.opacity = "1";
      }, 100);
    });
  }

  setupButtonAnimations() {
    const buttons = document.querySelectorAll(".btn, button");
    buttons.forEach((btn) => {
      btn.addEventListener("click", function (e) {
        const ripple = document.createElement("span");
        ripple.classList.add("ripple");
        ripple.style.left = e.offsetX + "px";
        ripple.style.top = e.offsetY + "px";
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
      });
    });
  }

  setupCardHovers() {
    const cards = document.querySelectorAll(".card, .enterprise-card");
    cards.forEach((card) => {
      card.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";
    });
  }
}

new SmoothTransitions();
