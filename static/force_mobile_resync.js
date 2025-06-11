// 🛡 Force Desktop Layout and Touch Restore on iPhone
(function() {
  try {
    // Aggressive cache and storage clearing
    localStorage.clear();
    sessionStorage.clear();
    if ('caches' in window) {
      caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
    }

    // Force viewport override
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute("content", "width=1024, initial-scale=0.3, maximum-scale=1, user-scalable=yes");
    }

    // Apply desktop mode styling
    document.body.style.zoom = "0.3";
    document.body.style.transform = "scale(0.3)";
    document.body.style.transformOrigin = "top left";
    document.body.classList.add("force-desktop-mode");

    // Safety sweep for rogue overlays or dev sheets
    setTimeout(() => {
      document.querySelectorAll("iframe, div").forEach(el => {
        const content = el.innerText || "";
        const src = el.src || "";
        const computedStyle = window.getComputedStyle(el);
        
        // Remove problematic elements
        if (content.includes("React App") || 
            src.includes(":3000") || 
            parseInt(computedStyle.zIndex) > 1000 ||
            el.classList.contains("development-overlay")) {
          el.remove();
        }
      });
    }, 500);

    console.log("✅ Mobile resync and override enforced.");
  } catch (e) {
    console.error("❌ Resync script failed", e);
  }
})();

// Visual confirmation marker
const marker = document.createElement("div");
marker.innerText = "✅ MOBILE OVERRIDE ACTIVE";
marker.style.cssText = `
  position: fixed; top: 0; right: 0;
  background: #00ff00; color: #000000;
  z-index: 99999; font-size: 12px;
  padding: 4px 8px; font-family: monospace;
  border-radius: 0 0 0 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
`;

// Add marker after DOM is ready
if (document.body) {
  document.body.appendChild(marker);
} else {
  document.addEventListener('DOMContentLoaded', () => {
    document.body.appendChild(marker);
  });
}

// Auto-remove marker after 3 seconds
setTimeout(() => {
  if (marker && marker.parentNode) {
    marker.remove();
  }
}, 3000);