* TRAXORA User Preferences System
*
* This module tracks and applies user preferences across the application,
* creating a personalized experience based on past behavior.
*/
class UserPreferences {
constructor() {
this.preferences = this.loadPreferences();
this.fieldHistory = this.loadFieldHistory();
this.currentPage = window.location.pathname;
this.initializeFormTracking();
}
loadPreferences() {
const savedPrefs = localStorage.getItem('traxora_preferences');
return savedPrefs ? JSON.parse(savedPrefs) : {
filters: {},
columns: {},
sorts: {},
pageSize: {},
viewMode: {},
recentSearches: {},
lastAccessed: {}
};
}
savePreferences() {
localStorage.setItem('traxora_preferences', JSON.stringify(this.preferences));
}
loadFieldHistory() {
const savedHistory = localStorage.getItem('traxora_field_history');
return savedHistory ? JSON.parse(savedHistory) : {};
}
saveFieldHistory() {
localStorage.setItem('traxora_field_history', JSON.stringify(this.fieldHistory));
}
applyPreferencesToPage() {
this.applyFilterPreferences();
this.applyColumnPreferences();
this.applySortPreferences();
this.applyViewModePreferences();
this.setupFieldAutoComplete();
this.updateLastAccessed();
}
updateLastAccessed() {
this.preferences.lastAccessed[this.currentPage] = new Date().toISOString();
this.savePreferences();
}
applyFilterPreferences() {
const pageFilters = this.preferences.filters[this.currentPage];
if (!pageFilters) return;
Object.keys(pageFilters).forEach(filterId => {
const filterElement = document.getElementById(filterId);
if (!filterElement) return;
const savedValue = pageFilters[filterId];
if (filterElement.tagName === 'SELECT') {
filterElement.value = savedValue;
filterElement.dispatchEvent(new Event('change'));
}
else if (filterElement.tagName === 'INPUT') {
if (filterElement.type === 'checkbox') {
filterElement.checked = savedValue === 'true' || savedValue === true;
} else if (filterElement.type === 'radio') {
const radio = document.querySelector(`input[name="${filterElement.name}"][value="${savedValue}"]`);
if (radio) radio.checked = true;
} else {
filterElement.value = savedValue;
}
}
});
}
applyColumnPreferences() {
const pageColumns = this.preferences.columns[this.currentPage];
if (!pageColumns) return;
Object.keys(pageColumns).forEach(columnId => {
const isVisible = pageColumns[columnId];
const columnToggle = document.querySelector(`[data-column-toggle="${columnId}"]`);
if (columnToggle) {
if (columnToggle.type === 'checkbox') {
columnToggle.checked = isVisible;
}
document.querySelectorAll(`[data-column="${columnId}"], .${columnId}-column`).forEach(col => {
col.style.display = isVisible ? '' : 'none';
});
}
});
}
applySortPreferences() {
const pageSorts = this.preferences.sorts[this.currentPage];
if (!pageSorts) return;
Object.keys(pageSorts).forEach(tableId => {
const sortInfo = pageSorts[tableId];
const sortSelect = document.querySelector(`#${tableId}-sort-field, [data-sort-table="${tableId}"]`);
const directionSelect = document.querySelector(`#${tableId}-sort-direction, [data-sort-direction="${tableId}"]`);
if (sortSelect && sortInfo.field) {
sortSelect.value = sortInfo.field;
sortSelect.dispatchEvent(new Event('change'));
}
if (directionSelect && sortInfo.direction) {
directionSelect.value = sortInfo.direction;
directionSelect.dispatchEvent(new Event('change'));
}
});
}
applyViewModePreferences() {
const viewMode = this.preferences.viewMode[this.currentPage];
if (!viewMode) return;
const viewButton = document.querySelector(`[data-view-mode="${viewMode}"]`);
if (viewButton) {
viewButton.click();
}
}
setupFieldAutoComplete() {
document.querySelectorAll('input[type="text"], input[type="email"], textarea').forEach(field => {
if (field.classList.contains('no-autocomplete') || field.autocomplete === 'off') return;
const fieldId = field.id || field.name;
if (!fieldId) return;
field.addEventListener('change', () => {
this.saveFieldInputHistory(fieldId, field.value);
});
if (this.fieldHistory[fieldId] && this.fieldHistory[fieldId].length > 0) {
const datalistId = `history-${fieldId}`;
let datalist = document.getElementById(datalistId);
if (!datalist) {
datalist = document.createElement('datalist');
datalist.id = datalistId;
document.body.appendChild(datalist);
field.setAttribute('list', datalistId);
}
datalist.innerHTML = '';
this.fieldHistory[fieldId].forEach(value => {
const option = document.createElement('option');
option.value = value;
datalist.appendChild(option);
});
}
});
}
initializeFormTracking() {
document.querySelectorAll('.data-filter, [data-filter="true"]').forEach(filter => {
const filterId = filter.id;
if (!filterId) return;
filter.addEventListener('change', () => {
this.saveFilterPreference(filterId, filter.type === 'checkbox' ? filter.checked : filter.value);
});
});
document.querySelectorAll('[data-column-toggle]').forEach(toggle => {
const columnId = toggle.dataset.columnToggle;
toggle.addEventListener('change', () => {
const isVisible = toggle.type === 'checkbox' ? toggle.checked : toggle.value === 'true';
this.saveColumnPreference(columnId, isVisible);
document.querySelectorAll(`[data-column="${columnId}"], .${columnId}-column`).forEach(col => {
col.style.display = isVisible ? '' : 'none';
});
});
});
document.querySelectorAll('[data-sort-table]').forEach(sortSelect => {
const tableId = sortSelect.dataset.sortTable;
sortSelect.addEventListener('change', () => {
const directionSelect = document.querySelector(`[data-sort-direction="${tableId}"]`);
const direction = directionSelect ? directionSelect.value : 'asc';
this.saveSortPreference(tableId, {
field: sortSelect.value,
direction: direction
});
});
});
document.querySelectorAll('[data-sort-direction]').forEach(directionSelect => {
const tableId = directionSelect.dataset.sortDirection;
directionSelect.addEventListener('change', () => {
const sortSelect = document.querySelector(`[data-sort-table="${tableId}"]`);
const field = sortSelect ? sortSelect.value : null;
if (field) {
this.saveSortPreference(tableId, {
field: field,
direction: directionSelect.value
});
}
});
});
document.querySelectorAll('[data-view-mode]').forEach(viewButton => {
const viewMode = viewButton.dataset.viewMode;
viewButton.addEventListener('click', () => {
this.saveViewModePreference(viewMode);
});
});
document.querySelectorAll('.search-form, [data-search="true"]').forEach(searchForm => {
searchForm.addEventListener('submit', (e) => {
const searchInput = searchForm.querySelector('input[type="search"], input[type="text"]');
if (searchInput && searchInput.value.trim()) {
this.saveSearchQuery(searchInput.value.trim());
}
});
});
}
saveFilterPreference(filterId, value) {
if (!this.preferences.filters[this.currentPage]) {
this.preferences.filters[this.currentPage] = {};
}
this.preferences.filters[this.currentPage][filterId] = value;
this.savePreferences();
}
saveColumnPreference(columnId, isVisible) {
if (!this.preferences.columns[this.currentPage]) {
this.preferences.columns[this.currentPage] = {};
}
this.preferences.columns[this.currentPage][columnId] = isVisible;
this.savePreferences();
}
saveSortPreference(tableId, sortInfo) {
if (!this.preferences.sorts[this.currentPage]) {
this.preferences.sorts[this.currentPage] = {};
}
this.preferences.sorts[this.currentPage][tableId] = sortInfo;
this.savePreferences();
}
saveViewModePreference(viewMode) {
this.preferences.viewMode[this.currentPage] = viewMode;
this.savePreferences();
}
saveSearchQuery(query) {
if (!this.preferences.recentSearches[this.currentPage]) {
this.preferences.recentSearches[this.currentPage] = [];
}
this.preferences.recentSearches[this.currentPage] =
this.preferences.recentSearches[this.currentPage].filter(q => q !== query);
this.preferences.recentSearches[this.currentPage].unshift(query);
if (this.preferences.recentSearches[this.currentPage].length > 10) {
this.preferences.recentSearches[this.currentPage].pop();
}
this.savePreferences();
}
saveFieldInputHistory(fieldId, value) {
if (!value.trim()) return;
if (!this.fieldHistory[fieldId]) {
this.fieldHistory[fieldId] = [];
}
this.fieldHistory[fieldId] = this.fieldHistory[fieldId].filter(v => v !== value);
this.fieldHistory[fieldId].unshift(value);
if (this.fieldHistory[fieldId].length > 10) {
this.fieldHistory[fieldId].pop();
}
this.saveFieldHistory();
}
getRecentSearches() {
return this.preferences.recentSearches[this.currentPage] || [];
}
getFrequentPages(limit = 5) {
const pages = Object.keys(this.preferences.lastAccessed)
.map(page => ({
url: page,
lastAccessed: new Date(this.preferences.lastAccessed[page])
}))
.sort((a, b) => b.lastAccessed - a.lastAccessed);
return pages.slice(0, limit);
}
clearAllPreferences() {
localStorage.removeItem('traxora_preferences');
localStorage.removeItem('traxora_field_history');
this.preferences = this.loadPreferences();
this.fieldHistory = this.loadFieldHistory();
}
}
document.addEventListener('DOMContentLoaded', function() {
window.userPreferences = new UserPreferences();
window.userPreferences.applyPreferencesToPage();
const recentSearchesContainer = document.querySelector('.recent-searches-container');
if (recentSearchesContainer) {
const recentSearches = window.userPreferences.getRecentSearches();
if (recentSearches.length > 0) {
let html = '<h6 class="dropdown-header">Recent Searches</h6>';
recentSearches.forEach(search => {
html += `<a class="dropdown-item" href="?search=${encodeURIComponent(search)}">${search}</a>`;
});
recentSearchesContainer.innerHTML = html;
}
}
});