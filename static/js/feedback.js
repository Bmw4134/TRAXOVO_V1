/** TRAXORA Event-Driven Feedback System
*
* This module provides smart, contextual feedback to users based on their actions.
* It tracks user interactions, displays appropriate feedback, and helps build
* a foundation for adaptive UX behavior.
*/
class SmartFeedback {
constructor() {
this.toastContainer = null;
this.userPrefs = this.loadUserPreferences();
this.actionHistory = [];
this.init();
}
init() {
if (!document.querySelector('.toast-container')) {
this.toastContainer = document.createElement('div');
this.toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
document.body.appendChild(this.toastContainer);
} else {
this.toastContainer = document.querySelector('.toast-container');
}
this.setupEventListeners();
this.applyUserPreferences();
}
setupEventListeners() {
document.querySelectorAll('form').forEach(form => {
form.addEventListener('submit', e => {
if (form.classList.contains('login-form') || form.classList.contains('search-form')) return;
const formPurpose = form.dataset.purpose || this.inferFormPurpose(form);
const formAction = form.getAttribute('action') || '';
this.recordAction('form_submit', {
purpose: formPurpose,
action: formAction,
timestamp: new Date().toISOString()
});
});
});
document.querySelectorAll('.column-toggle').forEach(toggle => {
toggle.addEventListener('change', e => {
const columnName = e.target.dataset.column;
const isVisible = e.target.checked;
this.saveColumnPreference(columnName, isVisible);
this.recordAction('column_toggle', {
column: columnName,
visible: isVisible,
timestamp: new Date().toISOString()
});
});
});
document.querySelectorAll('.filter-select, .filter-input').forEach(filter => {
filter.addEventListener('change', e => {
const filterName = e.target.name || e.target.id;
const filterValue = e.target.value;
this.saveFilterPreference(filterName, filterValue);
this.recordAction('filter_change', {
filter: filterName,
value: filterValue,
timestamp: new Date().toISOString()
});
});
});
document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
tab.addEventListener('shown.bs.tab', e => {
const tabId = e.target.getAttribute('href');
const pagePath = window.location.pathname;
this.saveTabPreference(pagePath, tabId);
this.recordAction('tab_select', {
tab: tabId,
page: pagePath,
timestamp: new Date().toISOString()
});
});
});
document.querySelectorAll('a[href*="export"], a[href*="download"]').forEach(link => {
link.addEventListener('click', e => {
const href = link.getAttribute('href');
const format = this.inferExportFormat(href);
this.showToast('Export Started', `Preparing ${format} export...`, 'info');
this.recordAction('export_click', {
format: format,
url: href,
timestamp: new Date().toISOString()
});
});
});
}
showToast(title, message, type = 'success', autohide = true, delay = 3000) {
const toastId = 'toast-' + Date.now();
const toastHtml = `
<div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
<div class="toast-header bg-${type} text-white">
<i class="bi ${this.getIconForType(type)} me-2"></i>
<strong class="me-auto">${title}</strong>
<small>${this.getTimeString()}</small>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
</div>
<div class="toast-body">
${message}
</div>
</div>
`;
this.toastContainer.insertAdjacentHTML('beforeend', toastHtml);
const toastElement = document.getElementById(toastId);
const toast = new bootstrap.Toast(toastElement, {
autohide: autohide,
delay: delay
});
toast.show();
toastElement.addEventListener('hidden.bs.toast', () => {
toastElement.remove();
});
return toast;
}
showBanner(message, type = 'info', dismissible = true, autoHide = true, delay = 5000) {
const bannerId = 'banner-' + Date.now();
const bannerHtml = `
<div id="${bannerId}" class="alert alert-${type} alert-dismissible fade show mb-0 banner-notification" role="alert">
<div class="container d-flex align-items-center">
<i class="bi ${this.getIconForType(type)} me-2 fs-5"></i>
<div>${message}</div>
${dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}
</div>
</div>
`;
const mainElement = document.querySelector('main');
if (mainElement) {
mainElement.insertAdjacentHTML('afterbegin', bannerHtml);
const bannerElement = document.getElementById(bannerId);
if (autoHide) {
setTimeout(() => {
const banner = new bootstrap.Alert(bannerElement);
banner.close();
}, delay);
}
return bannerElement;
}
return null;
}
getIconForType(type) {
switch (type) {
case 'success': return 'bi-check-circle-fill';
case 'danger': return 'bi-exclamation-triangle-fill';
case 'warning': return 'bi-exclamation-circle-fill';
case 'info': return 'bi-info-circle-fill';
default: return 'bi-bell-fill';
}
}
getTimeString() {
const now = new Date();
return `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
}
inferFormPurpose(form) {
const action = form.getAttribute('action') || '';
const id = form.getAttribute('id') || '';
if (action.includes('upload') || form.querySelector('input[type="file"]')) {
return 'upload';
} else if (action.includes('filter') || id.includes('filter')) {
return 'filter';
} else if (action.includes('create') || id.includes('create')) {
return 'create';
} else if (action.includes('edit') || id.includes('edit')) {
return 'edit';
} else if (action.includes('delete') || id.includes('delete')) {
return 'delete';
} else if (action.includes('search') || id.includes('search')) {
return 'search';
}
return 'form_submission';
}
inferExportFormat(url) {
if (url.includes('pdf')) return 'PDF';
if (url.includes('csv')) return 'CSV';
if (url.includes('excel') || url.includes('xlsx') || url.includes('xls')) return 'Excel';
if (url.includes('json')) return 'JSON';
return 'file';
}
recordAction(action, details) {
this.actionHistory.push({
action,
details,
timestamp: new Date().toISOString()
});
if (this.actionHistory.length > 100) {
this.actionHistory.shift();
}
localStorage.setItem('traxora_action_history', JSON.stringify(this.actionHistory));
}
sendActionToServer(action, details) {
fetch('/api/log-action', {
method: 'POST',
headers: {
'Content-Type': 'application/json'
},
body: JSON.stringify({
action,
details
})
});
*/
}
loadUserPreferences() {
const prefs = localStorage.getItem('traxora_user_prefs');
return prefs ? JSON.parse(prefs) : {
columns: {},
filters: {},
tabs: {},
theme: 'dark',
densityLevel: 'default'
};
}
saveUserPreferences() {
localStorage.setItem('traxora_user_prefs', JSON.stringify(this.userPrefs));
}
saveColumnPreference(columnName, isVisible) {
if (!this.userPrefs.columns) {
this.userPrefs.columns = {};
}
this.userPrefs.columns[columnName] = isVisible;
this.saveUserPreferences();
}
saveFilterPreference(filterName, value) {
if (!this.userPrefs.filters) {
this.userPrefs.filters = {};
}
this.userPrefs.filters[filterName] = value;
this.saveUserPreferences();
}
saveTabPreference(pagePath, tabId) {
if (!this.userPrefs.tabs) {
this.userPrefs.tabs = {};
}
this.userPrefs.tabs[pagePath] = tabId;
this.saveUserPreferences();
}
applyUserPreferences() {
if (this.userPrefs.columns) {
Object.entries(this.userPrefs.columns).forEach(([column, visible]) => {
const toggle = document.querySelector(`.column-toggle[data-column="${column}"]`);
if (toggle) {
toggle.checked = visible;
const tableColumn = document.querySelectorAll(`.${column}-column, [data-column="${column}"]`);
tableColumn.forEach(el => {
el.style.display = visible ? '' : 'none';
});
}
});
}
if (this.userPrefs.filters) {
Object.entries(this.userPrefs.filters).forEach(([filter, value]) => {
const filterElement = document.querySelector(`#${filter}, [name="${filter}"]`);
if (filterElement && filterElement.value !== value) {
filterElement.value = value;
filterElement.dispatchEvent(new Event('change', { bubbles: true }));
}
});
}
if (this.userPrefs.tabs) {
const pagePath = window.location.pathname;
const activeTabId = this.userPrefs.tabs[pagePath];
if (activeTabId) {
const tabLink = document.querySelector(`[data-bs-toggle="tab"][href="${activeTabId}"]`);
if (tabLink) {
const tab = new bootstrap.Tab(tabLink);
tab.show();
}
}
}
}
analyzeUserIntent() {
const recentActions = this.actionHistory.slice(-10);
const hasViewedReports = recentActions.some(a => a.action === 'tab_select' && a.details.tab.includes('report'));
const hasExported = recentActions.some(a => a.action === 'export_click');
if (hasViewedReports && hasExported) {
return 'reporting';
}
const hasFormsSubmitted = recentActions.filter(a => a.action === 'form_submit').length > 2;
if (hasFormsSubmitted) {
return 'data_entry';
}
return 'browsing';
}
generateRecommendations() {
const intent = this.analyzeUserIntent();
switch (intent) {
case 'reporting':
return [
{ text: 'View Driver Attendance Trends', url: '/attendance_dashboard', priority: 'high' },
{ text: 'Set up automated exports', url: '#', priority: 'medium' }
];
case 'data_entry':
return [
{ text: 'Use bulk import for faster entry', url: '#', priority: 'high' },
{ text: 'View recently added data', url: '#', priority: 'medium' }
];
default:
return [];
}
}
}
document.addEventListener('DOMContentLoaded', function() {
window.traxoraFeedback = new SmartFeedback();
document.querySelectorAll('form:not(.login-form):not(.search-form)').forEach(form => {
form.addEventListener('submit', function(e) {
const formType = form.dataset.formType || 'form';
const actionText = form.dataset.actionText || 'Processing...';
const successText = form.dataset.successText || 'Success!';
window.traxoraFeedback.showToast('Action in Progress', actionText, 'info');
if (form.classList.contains('demo-form')) {
e.preventDefault();
setTimeout(() => {
window.traxoraFeedback.showToast('Success', successText, 'success');
}, 1500);
}
});
});
document.querySelectorAll('[data-feedback]').forEach(el => {
el.addEventListener('click', function(e) {
const feedbackType = this.dataset.feedback;
const message = this.dataset.message || 'Action completed';
if (feedbackType === 'toast') {
const title = this.dataset.title || 'Notification';
const type = this.dataset.type || 'info';
window.traxoraFeedback.showToast(title, message, type);
} else if (feedbackType === 'banner') {
const type = this.dataset.type || 'info';
window.traxoraFeedback.showBanner(message, type);
}
if (!this.dataset.allowDefault) {
e.preventDefault();
}
});
});
});
function showFeedback(title, message, type = 'success') {
if (window.traxoraFeedback) {
window.traxoraFeedback.showToast(title, message, type);
} else {
console.warn('Feedback system not initialized');
}
}
function recordUserAction(action, details) {
if (window.traxoraFeedback) {
window.traxoraFeedback.recordAction(action, details);
} else {
console.warn('Feedback system not initialized');
}
}