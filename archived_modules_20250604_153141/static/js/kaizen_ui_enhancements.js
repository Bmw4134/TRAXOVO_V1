function initializeSimulateButton() {
  const existingButton = document.getElementById("simulateData");
  if (!existingButton) {
    const button = document.createElement("button");
    button.id = "simulateData";
    button.innerHTML = "Simulate Live Metrics";
    button.style.cssText = `
margin: 1rem;
padding: 0.5rem 1rem;
background-color: #4caf50;
color: white;
border: none;
border-radius: 5px;
cursor: pointer;
position: fixed;
top: 80px;
right: 20px;
z-index: 1000;
display: none;
`;
    if (window.innerWidth > 768) {
      button.style.display = "block";
    }
    button.onclick = () => {
      document.querySelectorAll(".metric-card.placeholder").forEach((card) => {
        const percent = Math.floor(Math.random() * 100) + "%";
        const valueNode = card.querySelector("p, h3");
        if (valueNode) {
          valueNode.innerText = percent;
          card.style.animation = "pulse 0.5s ease-in-out";
        }
      });
    };
    document.body.appendChild(button);
  }
}
function initializePlaceholderTooltips() {
  const style = document.createElement("style");
  style.textContent = `
.hover-note {
position: absolute;
background: rgba(255, 204, 0, 0.95);
padding: 6px 10px;
border-radius: 6px;
top: 4px;
right: 4px;
font-size: 12px;
z-index: 9999;
pointer-events: none;
box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.metric-card {
position: relative;
}
.metric-card.placeholder {
border-left: 4px solid #ffc107 !important;
}
.metric-card[data-auth="false"] {
opacity: 0.8;
border-left: 4px solid #ff9800 !important;
}
.metric-card[data-auth="false"]:hover {
opacity: 1;
}
@keyframes pulse {
0% { transform: scale(1); }
50% { transform: scale(1.05); }
100% { transform: scale(1); }
}
`;
  document.head.appendChild(style);
  document
    .querySelectorAll(
      '.metric-card.placeholder, .metric-card[data-auth="false"]',
    )
    .forEach((card) => {
      card.addEventListener("mouseenter", () => {
        if (!card.querySelector(".hover-note")) {
          const note = document.createElement("div");
          note.className = "hover-note";
          note.innerText = "Demo Value: Not using authentic data";
          card.appendChild(note);
        }
      });
      card.addEventListener("mouseleave", () => {
        const note = card.querySelector(".hover-note");
        if (note) card.removeChild(note);
      });
    });
}
function markPlaceholderCards() {
  document.querySelectorAll(".metric-card").forEach((card) => {
    const textContent = card.textContent.toLowerCase();
    if (
      textContent.includes("demo") ||
      textContent.includes("placeholder") ||
      textContent.includes("sample") ||
      card.dataset.auth === "false"
    ) {
      card.classList.add("placeholder");
      if (!card.dataset.auth) {
        card.dataset.auth = "false";
      }
    }
  });
}
function addDataSourceIndicators() {
  document.querySelectorAll(".metric-card").forEach((card) => {
    if (!card.querySelector(".data-source-indicator")) {
      const indicator = document.createElement("div");
      indicator.className = "data-source-indicator";
      indicator.style.cssText = `
display: flex; align-items: center; justify-content: center;
width: 8px;
height: 8px;
border-radius: 50%;
background-color: ${card.dataset.auth === "false" ? "#ffc107" : "#28a745"};
`;
      card.appendChild(indicator);
    }
  });
}
document.addEventListener("DOMContentLoaded", function () {
  markPlaceholderCards();
  initializePlaceholderTooltips();
  addDataSourceIndicators();
  initializeSimulateButton();
});
window.KaizenUI = {
  markPlaceholderCards,
  initializePlaceholderTooltips,
  addDataSourceIndicators,
  initializeSimulateButton,
};
