* TRAXOVO Contextual Help Bubble System
* Provides intuitive guidance and performance tooltips
*/
class ContextualHelpSystem {
constructor() {
this.helpBubbles = new Map();
this.isActive = true;
this.animationDuration = 300;
this.init();
}
init() {
this.createHelpContainer();
this.registerHelpPoints();
this.bindEvents();
this.loadUserPreferences();
}
createHelpContainer() {
if (!document.getElementById('help-bubble-container')) {
const container = document.createElement('div');
container.id = 'help-bubble-container';
container.style.cssText = `
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
pointer-events: none;
z-index: 10000;
`;
document.body.appendChild(container);
}
}
registerHelpPoints() {
this.addHelpPoint('.metric-card', {
title: 'Fleet Metrics',
content: 'Real-time fleet performance data from your Gauge API. Click for detailed breakdown.',
position: 'top',
trigger: 'hover',
delay: 500
});
this.addHelpPoint('[data-metric="assets"]', {
title: 'Asset Count',
content: 'Total: 717 assets | Active: 614 (85.6% utilization)',
position: 'bottom',
trigger: 'hover',
delay: 300
});
this.addHelpPoint('[data-metric="revenue"]', {
title: 'Revenue Analytics',
content: 'Live revenue calculations based on equipment categories and billing rates',
position: 'top',
trigger: 'hover',
delay: 300
});
this.addHelpPoint('.nav-link', {
title: 'Navigation',
content: 'Access different modules of your fleet management system',
position: 'right',
trigger: 'hover',
delay: 700
});
this.addHelpPoint('.status-indicator', {
title: 'System Status',
content: 'Real-time connection status to external APIs and services',
position: 'top',
trigger: 'hover',
delay: 200
});
this.addHelpPoint('#refreshDashboard', {
title: 'Refresh Data',
content: 'Manually refresh all dashboard data from connected APIs',
position: 'bottom',
trigger: 'hover',
delay: 400
});
}
addHelpPoint(selector, config) {
this.helpBubbles.set(selector, {
...config,
id: this.generateId()
});
}
bindEvents() {
document.addEventListener('mouseover', (e) => this.handleMouseOver(e));
document.addEventListener('mouseout', (e) => this.handleMouseOut(e));
document.addEventListener('click', (e) => this.handleClick(e));
document.addEventListener('keydown', (e) => {
if (e.key === 'F1') {
e.preventDefault();
this.showGlobalHelp();
}
if (e.key === 'Escape') {
this.hideAllBubbles();
}
});
}
handleMouseOver(e) {
if (!this.isActive) return;
for (const [selector, config] of this.helpBubbles) {
if (e.target.matches(selector) || e.target.parentElement&&.parentElement.querySelector(selector)) {
if (config.trigger === 'hover') {
this.showBubbleDelayed(e.target, config);
}
break;
}
}
}
handleMouseOut(e) {
this.hideCurrentBubble();
}
handleClick(e) {
for (const [selector, config] of this.helpBubbles) {
if (e.target.matches(selector) || e.target.parentElement&&.parentElement.querySelector(selector)) {
if (config.trigger === 'click') {
this.showBubble(e.target, config);
}
break;
}
}
}
showBubbleDelayed(element, config) {
clearTimeout(this.delayTimer);
this.delayTimer = setTimeout(() => {
this.showBubble(element, config);
}, config.delay || 500);
}
showBubble(element, config) {
this.hideCurrentBubble();
const bubble = this.createBubble(config);
const container = document.getElementById('help-bubble-container');
container.appendChild(bubble);
this.positionBubble(bubble, element, config.position);
this.animateIn(bubble);
this.currentBubble = bubble;
}
createBubble(config) {
const bubble = document.createElement('div');
bubble.className = 'help-bubble';
bubble.innerHTML = `
<div class="help-bubble-content">
<div class="help-bubble-title">${config.title}</div>
<div class="help-bubble-text">${config.content}</div>
<div class="help-bubble-arrow"></div>
</div>
`;
bubble.style.cssText = `
position: absolute;
background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
color: #f9fafb;
padding: 12px 16px;
border-radius: 8px;
box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
max-width: 280px;
z-index: 10001;
pointer-events: auto;
opacity: 0;
transform: scale(0.8) translateY(10px);
transition: all ${this.animationDuration}ms cubic-bezier(0.34, 1.56, 0.64, 1);
border: 1px solid rgba(99, 102, 241, 0.3);
backdrop-filter: blur(10px);
`;
const title = bubble.querySelector('.help-bubble-title');
title.style.cssText = `
font-weight: 600;
font-size: 14px;
margin-bottom: 6px;
color: #6366f1;
`;
const text = bubble.querySelector('.help-bubble-text');
text.style.cssText = `
font-size: 13px;
line-height: 1.4;
color: #d1d5db;
`;
return bubble;
}
positionBubble(bubble, element, position = 'top') {
const rect = element.getBoundingClientRect();
const bubbleRect = bubble.getBoundingClientRect();
let top, left;
switch (position) {
case 'top':
top = rect.top - bubbleRect.height - 10;
left = rect.left + (rect.width / 2) - (bubbleRect.width / 2);
break;
case 'bottom':
top = rect.bottom + 10;
left = rect.left + (rect.width / 2) - (bubbleRect.width / 2);
break;
case 'left':
top = rect.top + (rect.height / 2) - (bubbleRect.height / 2);
left = rect.left - bubbleRect.width - 10;
break;
case 'right':
top = rect.top + (rect.height / 2) - (bubbleRect.height / 2);
left = rect.right + 10;
break;
}
const viewport = {
width: window.innerWidth,
height: window.innerHeight
};
left = Math.max(10, Math.min(left, viewport.width - bubbleRect.width - 10));
top = Math.max(10, Math.min(top, viewport.height - bubbleRect.height - 10));
bubble.style.left = left + 'px';
bubble.style.top = top + 'px';
}
animateIn(bubble) {
requestAnimationFrame(() => {
bubble.style.opacity = '1';
bubble.style.transform = 'scale(1) translateY(0)';
});
}
animateOut(bubble) {
bubble.style.opacity = '0';
bubble.style.transform = 'scale(0.8) translateY(10px)';
setTimeout(() => {
if (bubble.parentNode) {
bubble.parentNode.removeChild(bubble);
}
}, this.animationDuration);
}
hideCurrentBubble() {
clearTimeout(this.delayTimer);
if (this.currentBubble) {
this.animateOut(this.currentBubble);
this.currentBubble = null;
}
}
hideAllBubbles() {
const container = document.getElementById('help-bubble-container');
if (container) {
const bubbles = container.querySelectorAll('.help-bubble');
bubbles.forEach(bubble => this.animateOut(bubble));
}
this.currentBubble = null;
}
showGlobalHelp() {
const helpOverlay = document.createElement('div');
helpOverlay.id = 'global-help-overlay';
helpOverlay.innerHTML = `
<div class="global-help-content">
<h2>TRAXOVO Help Guide</h2>
<div class="help-sections">
<div class="help-section">
<h3>Navigation</h3>
<p>Use the sidebar to access different modules. Hover over items for quick help.</p>
</div>
<div class="help-section">
<h3>Keyboard Shortcuts</h3>
<ul>
<li><kbd>F1</kbd> - Show this help</li>
<li><kbd>Esc</kbd> - Close help bubbles</li>
<li><kbd>Ctrl+R</kbd> - Refresh dashboard</li>
</ul>
</div>
<div class="help-section">
<h3>Data Status</h3>
<p>All metrics show real-time data from your Gauge API connection.</p>
</div>
</div>
<button onclick="helpSystem.hideGlobalHelp()" class="help-close-btn">Close</button>
</div>
`;
helpOverlay.style.cssText = `
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0, 0, 0, 0.8);
z-index: 10002;
display: flex;
align-items: center;
justify-content: center;
backdrop-filter: blur(5px);
`;
document.body.appendChild(helpOverlay);
}
hideGlobalHelp() {
const overlay = document.getElementById('global-help-overlay');
if (overlay) {
overlay.remove();
}
}
toggle() {
this.isActive = !this.isActive;
if (!this.isActive) {
this.hideAllBubbles();
}
}
loadUserPreferences() {
const prefs = localStorage.getItem('traxovo-help-prefs');
if (prefs) {
const parsed = JSON.parse(prefs);
this.isActive = parsed.active !== false;
}
}
saveUserPreferences() {
localStorage.setItem('traxovo-help-prefs', JSON.stringify({
active: this.isActive
}));
}
generateId() {
return 'help_' + Math.random().toString(36).substr(2, 9);
}
}
class PerformanceTooltips {
constructor() {
this.metrics = {};
this.updateInterval = 5000; // 5 seconds
this.init();
}
init() {
this.collectMetrics();
setInterval(() => this.collectMetrics(), this.updateInterval);
this.attachToElements();
}
collectMetrics() {
this.metrics = {
loadTime: performance.now(),
memoryUsage: this.getMemoryInfo(),
networkLatency: this.measureLatency(),
renderTime: this.getRenderTime(),
timestamp: new Date().toLocaleTimeString()
};
}
getMemoryInfo() {
if (performance.memory) {
return {
used: Math.round(performance.memory.usedJSHeapSize / 1048576),
total: Math.round(performance.memory.totalJSHeapSize / 1048576),
limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
};
}
return null;
}
measureLatency() {
const start = performance.now();
return Math.round(performance.now() - start);
}
getRenderTime() {
const navigation = performance.getEntriesByType('navigation')[0];
if (navigation) {
return Math.round(navigation.loadEventEnd - navigation.loadEventStart);
}
return 0;
}
attachToElements() {
document.querySelectorAll('.metric-card').forEach(card => {
card.addEventListener('mouseenter', (e) => {
this.showPerformanceTooltip(e.target);
});
});
}
showPerformanceTooltip(element) {
const tooltip = document.createElement('div');
tooltip.className = 'performance-tooltip';
tooltip.innerHTML = this.generateTooltipContent();
tooltip.style.cssText = `
position: absolute;
background: #0f172a;
color: #64ff4b;
padding: 8px 12px;
border-radius: 6px;
font-family: 'Courier New', monospace;
font-size: 11px;
z-index: 10003;
border: 1px solid #22c55e;
box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
white-space: nowrap;
`;
document.body.appendChild(tooltip);
const rect = element.getBoundingClientRect();
tooltip.style.left = (rect.right + 10) + 'px';
tooltip.style.top = rect.top + 'px';
setTimeout(() => {
if (tooltip.parentNode) {
tooltip.remove();
}
}, 3000);
}
generateTooltipContent() {
const mem = this.metrics.memoryUsage;
return `
<div>⚡ Performance Snapshot</div>
<div>Load: ${this.metrics.loadTime.toFixed(1)}ms</div>
${mem ? `<div>Memory: ${mem.used}MB/${mem.total}MB</div>` : ''}
<div>Updated: ${this.metrics.timestamp}</div>
`;
}
}
document.addEventListener('DOMContentLoaded', () => {
window.helpSystem = new ContextualHelpSystem();
window.performanceTooltips = new PerformanceTooltips();
});
window.ContextualHelpSystem = ContextualHelpSystem;
window.PerformanceTooltips = PerformanceTooltips;