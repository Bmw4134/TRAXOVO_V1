* TRAXOVO Dashboard Widget Customization System
* Allows users to personalize their dashboard layout and widget preferences
*/
class DashboardCustomizer {
constructor() {
this.widgets = new Map();
this.userPreferences = this.loadUserPreferences();
this.gridSystem = null;
this.customizationMode = false;
this.initializeCustomization();
}
initializeCustomization() {
this.applyUserPreferences();
this.createCustomizationToolbar();
this.initializeDragAndDrop();
this.setupWidgetControls();
}
createCustomizationToolbar() {
const toolbar = document.createElement('div');
toolbar.className = 'dashboard-customization-toolbar';
toolbar.innerHTML = `
<div class="customization-controls">
<button class="btn btn-secondary" id="customizeBtn">
<i class="fas fa-cog"></i> Customize Dashboard
</button>
<button class="btn btn-primary d-none" id="saveLayoutBtn">
<i class="fas fa-save"></i> Save Layout
</button>
<button class="btn btn-outline-secondary d-none" id="resetLayoutBtn">
<i class="fas fa-undo"></i> Reset to Default
</button>
<button class="btn btn-success d-none" id="doneCustomizingBtn">
<i class="fas fa-check"></i> Done
</button>
</div>
<div class="widget-size-controls d-none">
<label>Widget Size:</label>
<select id="widgetSizeSelect" class="form-select form-select-sm">
<option value="small">Small</option>
<option value="medium">Medium</option>
<option value="large">Large</option>
<option value="full">Full Width</option>
</select>
</div>
`;
const dashboardContainer = document.querySelector('.dashboard-container') || document.querySelector('.container-fluid');
if (dashboardContainer) {
dashboardContainer.insertBefore(toolbar, dashboardContainer.firstChild);
}
this.setupToolbarEvents();
}
setupToolbarEvents() {
document.getElementById('customizeBtn')?.addEventListener('click', () => {
this.enterCustomizationMode();
});
document.getElementById('saveLayoutBtn')?.addEventListener('click', () => {
this.saveUserPreferences();
this.showNotification('Dashboard layout saved!', 'success');
});
document.getElementById('resetLayoutBtn')?.addEventListener('click', () => {
this.resetToDefault();
});
document.getElementById('doneCustomizingBtn')?.addEventListener('click', () => {
this.exitCustomizationMode();
});
document.getElementById('widgetSizeSelect')?.addEventListener('change', (e) => {
this.changeSelectedWidgetSize(e.target.value);
});
}
enterCustomizationMode() {
this.customizationMode = true;
document.body.classList.add('dashboard-customizing');
document.querySelectorAll('.d-none').forEach(el => {
if (el.closest('.customization-controls') || el.closest('.widget-size-controls')) {
el.classList.remove('d-none');
}
});
document.getElementById('customizeBtn')?.classList.add('d-none');
this.addWidgetControls();
this.enableSorting();
this.showNotification('Customization mode enabled. Drag widgets to rearrange, click controls to modify.', 'info');
}
exitCustomizationMode() {
this.customizationMode = false;
document.body.classList.remove('dashboard-customizing');
document.querySelectorAll('.customization-controls .d-none, .widget-size-controls').forEach(el => {
el.classList.add('d-none');
});
document.getElementById('customizeBtn')?.classList.remove('d-none');
this.removeWidgetControls();
this.disableSorting();
this.showNotification('Customization complete!', 'success');
}
addWidgetControls() {
const widgets = document.querySelectorAll('.metric-card, .chart-container, .widget');
widgets.forEach((widget, index) => {
if (widget.querySelector('.widget-controls')) return; // Already has controls
const controls = document.createElement('div');
controls.className = 'widget-controls';
controls.innerHTML = `
<div class="widget-control-buttons">
<button class="btn btn-sm btn-outline-primary widget-resize" title="Resize Widget">
<i class="fas fa-expand-arrows-alt"></i>
</button>
<button class="btn btn-sm btn-outline-warning widget-settings" title="Widget Settings">
<i class="fas fa-cog"></i>
</button>
<button class="btn btn-sm btn-outline-danger widget-hide" title="Hide Widget">
<i class="fas fa-eye-slash"></i>
</button>
</div>
<div class="widget-drag-handle" title="Drag to reorder">
<i class="fas fa-grip-vertical"></i>
</div>
`;
widget.style.position = 'relative';
widget.appendChild(controls);
widget.dataset.widgetId = index;
this.setupWidgetControlEvents(widget, controls);
});
}
setupWidgetControlEvents(widget, controls) {
controls.querySelector('.widget-hide')?.addEventListener('click', () => {
this.toggleWidgetVisibility(widget);
});
controls.querySelector('.widget-settings')?.addEventListener('click', () => {
this.openWidgetSettings(widget);
});
controls.querySelector('.widget-resize')?.addEventListener('click', () => {
this.selectWidget(widget);
});
}
removeWidgetControls() {
document.querySelectorAll('.widget-controls').forEach(control => {
control.remove();
});
}
initializeDragAndDrop() {
this.sortableInstances = [];
}
enableSorting() {
const containers = document.querySelectorAll('.row, .dashboard-row');
containers.forEach(container => {
if (container.children.length > 1) {
const sortable = new Sortable(container, {
animation: 150,
handle: '.widget-drag-handle',
ghostClass: 'widget-ghost',
chosenClass: 'widget-chosen',
dragClass: 'widget-drag',
onEnd: (evt) => {
this.handleWidgetReorder(evt);
}
});
this.sortableInstances.push(sortable);
}
});
}
disableSorting() {
this.sortableInstances.forEach(sortable => {
sortable.destroy();
});
this.sortableInstances = [];
}
handleWidgetReorder(evt) {
const widget = evt.item;
const newIndex = evt.newIndex;
const oldIndex = evt.oldIndex;
const widgetId = widget.dataset.widgetId;
if (widgetId && this.userPreferences.widgetOrder) {
const order = this.userPreferences.widgetOrder;
const movedWidget = order.splice(oldIndex, 1)[0];
order.splice(newIndex, 0, movedWidget);
}
this.showNotification(`Widget moved from position ${oldIndex + 1} to ${newIndex + 1}`, 'info');
}
toggleWidgetVisibility(widget) {
const widgetId = widget.dataset.widgetId;
const isHidden = widget.classList.contains('widget-hidden');
if (isHidden) {
widget.classList.remove('widget-hidden');
widget.style.display = '';
this.userPreferences.hiddenWidgets = this.userPreferences.hiddenWidgets.filter(id => id !== widgetId);
this.showNotification('Widget shown', 'success');
} else {
widget.classList.add('widget-hidden');
widget.style.display = 'none';
this.userPreferences.hiddenWidgets.push(widgetId);
this.showNotification('Widget hidden', 'warning');
}
}
selectWidget(widget) {
document.querySelectorAll('.widget-selected').forEach(w => {
w.classList.remove('widget-selected');
});
widget.classList.add('widget-selected');
const currentSize = this.getWidgetSize(widget);
document.getElementById('widgetSizeSelect').value = currentSize;
document.querySelector('.widget-size-controls')?.classList.remove('d-none');
}
getWidgetSize(widget) {
if (widget.classList.contains('col-12')) return 'full';
if (widget.classList.contains('col-lg-8') || widget.classList.contains('col-md-8')) return 'large';
if (widget.classList.contains('col-lg-6') || widget.classList.contains('col-md-6')) return 'medium';
return 'small';
}
changeSelectedWidgetSize(newSize) {
const selectedWidget = document.querySelector('.widget-selected');
if (!selectedWidget) return;
selectedWidget.classList.remove('col-12', 'col-lg-8', 'col-lg-6', 'col-lg-4', 'col-md-8', 'col-md-6', 'col-md-4');
switch (newSize) {
case 'full':
selectedWidget.classList.add('col-12');
break;
case 'large':
selectedWidget.classList.add('col-lg-8', 'col-md-8');
break;
case 'medium':
selectedWidget.classList.add('col-lg-6', 'col-md-6');
break;
case 'small':
selectedWidget.classList.add('col-lg-4', 'col-md-4');
break;
}
const widgetId = selectedWidget.dataset.widgetId;
this.userPreferences.widgetSizes[widgetId] = newSize;
this.showNotification(`Widget resized to ${newSize}`, 'success');
}
openWidgetSettings(widget) {
const widgetId = widget.dataset.widgetId;
const widgetTitle = widget.querySelector('.card-title, h5, h6')?.textContent || 'Widget';
const modal = document.createElement('div');
modal.className = 'modal fade';
modal.innerHTML = `
<div class="modal-dialog">
<div class="modal-content">
<div class="modal-header">
<h5 class="modal-title">Settings for ${widgetTitle}</h5>
<button type="button" class="btn-close" data-bs-dismiss="modal"></button>
</div>
<div class="modal-body">
<div class="form-group mb-3">
<label>Widget Title:</label>
<input type="text" class="form-control" id="widgetTitleInput" value="${widgetTitle}">
</div>
<div class="form-group mb-3">
<label>Refresh Rate:</label>
<select class="form-select" id="widgetRefreshRate">
<option value="30">30 seconds</option>
<option value="60" selected>1 minute</option>
<option value="300">5 minutes</option>
<option value="600">10 minutes</option>
</select>
</div>
<div class="form-check">
<input type="checkbox" class="form-check-input" id="widgetAutoRefresh" checked>
<label class="form-check-label">Auto-refresh widget data</label>
</div>
</div>
<div class="modal-footer">
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
<button type="button" class="btn btn-primary" id="saveWidgetSettings">Save Settings</button>
</div>
</div>
</div>
`;
document.body.appendChild(modal);
const modalInstance = new bootstrap.Modal(modal);
modalInstance.show();
modal.querySelector('#saveWidgetSettings')?.addEventListener('click', () => {
this.saveWidgetSettings(widgetId, modal);
modalInstance.hide();
});
modal.addEventListener('hidden.bs.modal', () => {
modal.remove();
});
}
saveWidgetSettings(widgetId, modal) {
const settings = {
title: modal.querySelector('#widgetTitleInput').value,
refreshRate: parseInt(modal.querySelector('#widgetRefreshRate').value),
autoRefresh: modal.querySelector('#widgetAutoRefresh').checked
};
this.userPreferences.widgetSettings[widgetId] = settings;
this.showNotification('Widget settings saved!', 'success');
}
loadUserPreferences() {
const saved = localStorage.getItem('traxovo_dashboard_preferences');
if (saved) {
return JSON.parse(saved);
}
return {
widgetOrder: [],
hiddenWidgets: [],
widgetSizes: {},
widgetSettings: {},
theme: 'default'
};
}
saveUserPreferences() {
localStorage.setItem('traxovo_dashboard_preferences', JSON.stringify(this.userPreferences));
}
applyUserPreferences() {
this.userPreferences.hiddenWidgets.forEach(widgetId => {
const widget = document.querySelector(`[data-widget-id="${widgetId}"]`);
if (widget) {
widget.classList.add('widget-hidden');
widget.style.display = 'none';
}
});
Object.entries(this.userPreferences.widgetSizes).forEach(([widgetId, size]) => {
const widget = document.querySelector(`[data-widget-id="${widgetId}"]`);
if (widget) {
this.applyWidgetSize(widget, size);
}
});
}
applyWidgetSize(widget, size) {
widget.classList.remove('col-12', 'col-lg-8', 'col-lg-6', 'col-lg-4', 'col-md-8', 'col-md-6', 'col-md-4');
switch (size) {
case 'full':
widget.classList.add('col-12');
break;
case 'large':
widget.classList.add('col-lg-8', 'col-md-8');
break;
case 'medium':
widget.classList.add('col-lg-6', 'col-md-6');
break;
case 'small':
widget.classList.add('col-lg-4', 'col-md-4');
break;
}
}
resetToDefault() {
if (confirm('Reset dashboard to default layout? This will remove all customizations.')) {
this.userPreferences = {
widgetOrder: [],
hiddenWidgets: [],
widgetSizes: {},
widgetSettings: {},
theme: 'default'
};
document.querySelectorAll('.widget-hidden, .widget-selected').forEach(widget => {
widget.classList.remove('widget-hidden', 'widget-selected');
widget.style.display = '';
});
document.querySelectorAll('[data-widget-id]').forEach(widget => {
widget.classList.remove('col-12', 'col-lg-8', 'col-lg-6', 'col-lg-4', 'col-md-8', 'col-md-6', 'col-md-4');
widget.classList.add('col-lg-6', 'col-md-6'); // Default size
});
this.saveUserPreferences();
this.showNotification('Dashboard reset to default layout!', 'success');
}
}
showNotification(message, type = 'info') {
const notification = document.createElement('div');
notification.className = `alert alert-${type} dashboard-notification`;
notification.innerHTML = `
<i class="fas fa-${type === 'success' ? 'check' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
${message}
`;
document.body.appendChild(notification);
setTimeout(() => notification.classList.add('show'), 100);
setTimeout(() => {
notification.classList.remove('show');
setTimeout(() => notification.remove(), 300);
}, 3000);
}
}
document.addEventListener('DOMContentLoaded', () => {
if (document.querySelector('.dashboard-container') ||
document.querySelector('.metric-card') ||
window.location.pathname === '/dashboard') {
if (typeof Sortable === 'undefined') {
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js';
script.onload = () => {
window.dashboardCustomizer = new DashboardCustomizer();
};
document.head.appendChild(script);
} else {
window.dashboardCustomizer = new DashboardCustomizer();
}
}
});