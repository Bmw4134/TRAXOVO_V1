* TRAXOVO Contextual Navigation Wizard
* Intelligent navigation guidance based on user context and role
*/
class ContextualNavigationWizard {
constructor() {
this.currentPath = window.location.pathname;
this.userRole = this.detectUserRole();
this.sessionContext = this.loadSessionContext();
this.wizardActive = false;
this.init();
}
init() {
this.createWizardInterface();
this.bindEvents();
this.analyzeCurrentContext();
}
detectUserRole() {
const roleMap = {
'admin': ['admin', 'system-admin'],
'executive': ['executive', 'dashboard'],
'controller': ['billing', 'revenue', 'financial'],
'estimating': ['project', 'job-sites'],
'equipment': ['asset', 'fleet', 'equipment'],
'payroll': ['attendance', 'driver'],
'viewer': ['reports', 'analytics']
};
for (const [role, keywords] of Object.entries(roleMap)) {
if (keywords.some(keyword => this.currentPath.includes(keyword))) {
return role;
}
}
return 'viewer'; // default role
}
loadSessionContext() {
return {
lastVisited: localStorage.getItem('lastVisitedModules') ?
JSON.parse(localStorage.getItem('lastVisitedModules')) : [],
preferences: localStorage.getItem('navigationPreferences') ?
JSON.parse(localStorage.getItem('navigationPreferences')) : {},
completedTasks: localStorage.getItem('completedTasks') ?
JSON.parse(localStorage.getItem('completedTasks')) : []
};
}
createWizardInterface() {
const wizardHTML = `
<div id="navigation-wizard" class="navigation-wizard" style="display: none;">
<div class="wizard-header">
<h5><i class="fas fa-compass me-2"></i>Navigation Assistant</h5>
<button class="btn btn-sm btn-outline-light wizard-close" onclick="navigationWizard.hideWizard()">
<i class="fas fa-times"></i>
</button>
</div>
<div class="wizard-content">
<div id="wizard-suggestions" class="wizard-suggestions"></div>
<div id="wizard-quickstart" class="wizard-quickstart"></div>
</div>
<div class="wizard-footer">
<button class="btn btn-sm btn-primary" onclick="navigationWizard.showQuickTour()">
<i class="fas fa-route me-1"></i>Quick Tour
</button>
<button class="btn btn-sm btn-outline-primary" onclick="navigationWizard.showShortcuts()">
<i class="fas fa-keyboard me-1"></i>Shortcuts
</button>
</div>
</div>
<button id="wizard-trigger" class="wizard-trigger" onclick="navigationWizard.toggleWizard()" title="Navigation Help">
<i class="fas fa-question-circle"></i>
</button>
`;
document.body.insertAdjacentHTML('beforeend', wizardHTML);
this.addWizardStyles();
}
addWizardStyles() {
const styles = `
<style>
.navigation-wizard {
position: fixed;
top: 80px;
right: 20px;
width: 320px;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
border-radius: 12px;
box-shadow: 0 10px 30px rgba(0,0,0,0.3);
z-index: 1050;
color: white;
animation: slideInRight 0.3s ease-out;
}
.wizard-header {
padding: 15px 20px 10px;
border-bottom: 1px solid rgba(255,255,255,0.2);
display: flex;
justify-content: space-between;
align-items: center;
}
.wizard-content {
padding: 15px 20px;
max-height: 400px;
overflow-y: auto;
}
.wizard-footer {
padding: 10px 20px 15px;
border-top: 1px solid rgba(255,255,255,0.2);
display: flex;
gap: 10px;
}
.wizard-suggestion {
background: rgba(255,255,255,0.1);
border-radius: 8px;
padding: 12px;
margin-bottom: 10px;
cursor: pointer;
transition: all 0.2s ease;
}
.wizard-suggestion:hover {
background: rgba(255,255,255,0.2);
transform: translateX(5px);
}
.wizard-suggestion-title {
font-weight: 600;
margin-bottom: 5px;
}
.wizard-suggestion-desc {
font-size: 0.9em;
opacity: 0.9;
}
.wizard-trigger {
position: fixed;
bottom: 30px;
right: 30px;
width: 50px;
height: 50px;
border-radius: 50%;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
border: none;
color: white;
font-size: 20px;
box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
cursor: pointer;
transition: all 0.3s ease;
z-index: 1000;
}
.wizard-trigger:hover {
transform: scale(1.1);
box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}
.quickstart-item {
display: flex;
align-items: center;
padding: 8px 0;
border-bottom: 1px solid rgba(255,255,255,0.1);
cursor: pointer;
}
.quickstart-item:hover {
background: rgba(255,255,255,0.05);
border-radius: 4px;
}
.quickstart-icon {
width: 30px;
text-align: center;
margin-right: 10px;
}
@keyframes slideInRight {
from { transform: translateX(100%); opacity: 0; }
to { transform: translateX(0); opacity: 1; }
}
@media (max-width: 768px) {
.navigation-wizard {
width: 300px;
right: 10px;
top: 60px;
}
.wizard-trigger {
bottom: 20px;
right: 20px;
}
}
</style>
`;
document.head.insertAdjacentHTML('beforeend', styles);
}
analyzeCurrentContext() {
const contextSuggestions = this.generateContextualSuggestions();
this.updateWizardContent(contextSuggestions);
}
generateContextualSuggestions() {
const suggestions = [];
const path = this.currentPath;
if (this.userRole === 'admin') {
suggestions.push({
title: 'System Overview',
description: 'Monitor system health and user activity',
action: 'navigateTo',
target: '/admin',
icon: 'fas fa-cogs'
});
}
if (this.userRole === 'controller' || path.includes('billing')) {
suggestions.push({
title: 'Master Billing Dashboard',
description: 'View $552K RAGLE revenue and billing analytics',
action: 'navigateTo',
target: '/master-billing/',
icon: 'fas fa-calculator'
});
}
if (this.userRole === 'payroll' || path.includes('attendance')) {
suggestions.push({
title: 'Master Attendance System',
description: 'Track 92 drivers with GPS validation',
action: 'navigateTo',
target: '/master-attendance/',
icon: 'fas fa-clipboard-check'
});
}
if (path === '/dashboard' || path === '/') {
suggestions.push({
title: 'Fleet Analytics',
description: 'Analyze 717 assets performance and utilization',
action: 'navigateTo',
target: '/fleet-analytics',
icon: 'fas fa-chart-line'
});
}
if (path.includes('asset')) {
suggestions.push({
title: 'Asset Map View',
description: 'Real-time GPS tracking of fleet assets',
action: 'navigateTo',
target: '/fleet-map',
icon: 'fas fa-map-marked-alt'
});
}
const currentHour = new Date().getHours();
if (currentHour >= 6 && currentHour <= 10) {
suggestions.push({
title: 'Daily Driver Report',
description: 'Morning attendance and dispatch overview',
action: 'navigateTo',
target: '/daily-driver-report',
icon: 'fas fa-calendar-day'
});
}
suggestions.push({
title: 'AI Fleet Assistant',
description: 'Get intelligent insights about your fleet data',
action: 'navigateTo',
target: '/ai-assistant',
icon: 'fas fa-robot'
});
return suggestions;
}
updateWizardContent(suggestions) {
const suggestionsContainer = document.getElementById('wizard-suggestions');
const quickstartContainer = document.getElementById('wizard-quickstart');
suggestionsContainer.innerHTML = suggestions.map(suggestion => `
<div class="wizard-suggestion" onclick="navigationWizard.executeSuggestion('${suggestion.action}', '${suggestion.target}')">
<div class="wizard-suggestion-title">
<i class="${suggestion.icon} me-2"></i>${suggestion.title}
</div>
<div class="wizard-suggestion-desc">${suggestion.description}</div>
</div>
`).join('');
const quickstartItems = this.getQuickstartItems();
quickstartContainer.innerHTML = `
<h6 class="mb-3">Quick Actions</h6>
${quickstartItems.map(item => `
<div class="quickstart-item" onclick="navigationWizard.executeSuggestion('${item.action}', '${item.target}')">
<div class="quickstart-icon"><i class="${item.icon}"></i></div>
<div>${item.title}</div>
</div>
`).join('')}
`;
}
getQuickstartItems() {
const baseItems = [
{ title: 'Dashboard Home', icon: 'fas fa-home', action: 'navigateTo', target: '/dashboard' },
{ title: 'Asset Overview', icon: 'fas fa-truck', action: 'navigateTo', target: '/asset-manager' },
{ title: 'Fleet Map', icon: 'fas fa-map', action: 'navigateTo', target: '/fleet-map' }
];
const roleSpecificItems = {
'admin': [
{ title: 'User Management', icon: 'fas fa-users', action: 'navigateTo', target: '/admin' },
{ title: 'System Health', icon: 'fas fa-heartbeat', action: 'navigateTo', target: '/system-health' }
],
'controller': [
{ title: 'Billing Reports', icon: 'fas fa-file-invoice', action: 'navigateTo', target: '/master-billing/' },
{ title: 'Revenue Analytics', icon: 'fas fa-chart-pie', action: 'navigateTo', target: '/billing' }
],
'payroll': [
{ title: 'Attendance Matrix', icon: 'fas fa-calendar-check', action: 'navigateTo', target: '/master-attendance/' },
{ title: 'Driver Reports', icon: 'fas fa-id-card', action: 'navigateTo', target: '/driver-management' }
]
};
return [...baseItems, ...(roleSpecificItems[this.userRole] || [])];
}
executeSuggestion(action, target) {
if (action === 'navigateTo') {
this.trackNavigation(target);
window.location.href = target;
}
this.hideWizard();
}
trackNavigation(target) {
let visited = this.sessionContext.lastVisited;
if (!visited.includes(target)) {
visited.unshift(target);
if (visited.length > 10) visited.pop();
localStorage.setItem('lastVisitedModules', JSON.stringify(visited));
}
}
toggleWizard() {
const wizard = document.getElementById('navigation-wizard');
if (wizard.style.display === 'none') {
this.showWizard();
} else {
this.hideWizard();
}
}
showWizard() {
const wizard = document.getElementById('navigation-wizard');
wizard.style.display = 'block';
this.wizardActive = true;
this.analyzeCurrentContext(); // Refresh suggestions
}
hideWizard() {
const wizard = document.getElementById('navigation-wizard');
wizard.style.display = 'none';
this.wizardActive = false;
}
showQuickTour() {
const tourSteps = [
{ element: '.sidebar', content: 'Navigate between modules using this sidebar' },
{ element: '.dashboard-metrics', content: 'Key performance indicators are displayed here' },
{ element: '.data-refresh', content: 'Use this to refresh your real-time data' }
];
this.startGuidedTour(tourSteps);
}
showShortcuts() {
const shortcuts = [
{ key: 'Alt + D', action: 'Go to Dashboard' },
{ key: 'Alt + B', action: 'Open Billing' },
{ key: 'Alt + A', action: 'Open Attendance' },
{ key: 'Alt + M', action: 'Open Fleet Map' },
{ key: 'Alt + ?', action: 'Toggle Navigation Help' }
];
const shortcutHTML = shortcuts.map(shortcut =>
`<div class="shortcut-item">
<kbd>${shortcut.key}</kbd> - ${shortcut.action}
</div>`
).join('');
document.getElementById('wizard-suggestions').innerHTML = `
<h6>Keyboard Shortcuts</h6>
<div class="shortcuts-list">${shortcutHTML}</div>
`;
}
startGuidedTour(steps) {
console.log('Starting guided tour with steps:', steps);
this.hideWizard();
}
bindEvents() {
document.addEventListener('keydown', (e) => {
if (e.altKey) {
switch(e.key) {
case 'd':
e.preventDefault();
window.location.href = '/dashboard';
break;
case 'b':
e.preventDefault();
window.location.href = '/master-billing/';
break;
case 'a':
e.preventDefault();
window.location.href = '/master-attendance/';
break;
case 'm':
e.preventDefault();
window.location.href = '/fleet-map';
break;
case '?':
e.preventDefault();
this.toggleWizard();
break;
}
}
});
document.addEventListener('click', (e) => {
const wizard = document.getElementById('navigation-wizard');
const trigger = document.getElementById('wizard-trigger');
if (this.wizardActive &&
!wizard.contains(e.target) &&
!trigger.contains(e.target)) {
this.hideWizard();
}
});
}
}
let navigationWizard;
document.addEventListener('DOMContentLoaded', function() {
navigationWizard = new ContextualNavigationWizard();
});