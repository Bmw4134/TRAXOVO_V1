* TRAXOVO Performance Optimization Engine
* Executive-grade user experience with instant response times
*/
class TRAXOVOPerformanceEngine {
constructor() {
this.activeRequests = new Map();
this.chartInstances = new Map();
this.navigationQueue = [];
this.isNavigating = false;
this.initializePerformanceOptimization();
}
initializePerformanceOptimization() {
this.fixExpandingCharts();
this.setupInstantNavigation();
this.optimizeResourceAllocation();
this.setupPreemptiveLoading();
}
fixExpandingCharts() {
document.addEventListener('DOMContentLoaded', () => {
const chartContainers = document.querySelectorAll('.chart-container, canvas, [id*="chart"], [class*="Chart"]');
chartContainers.forEach(container => {
if (container.tagName === 'CANVAS') {
container.style.maxWidth = '100%';
container.style.maxHeight = '400px';
container.style.width = '100%';
container.style.height = '400px';
}
if (!container.parentElement.classList.contains('chart-wrapper')) {
const wrapper = document.createElement('div');
wrapper.className = 'chart-wrapper';
wrapper.style.cssText = 'width: 100%; height: 400px; overflow: hidden; position: relative;';
container.parentElement.insertBefore(wrapper, container);
wrapper.appendChild(container);
}
});
if (window.Chart && window.Chart.instances) {
Object.values(window.Chart.instances).forEach(chart => {
if (chart && chart.destroy) {
chart.destroy();
}
});
}
});
}
setupInstantNavigation() {
document.addEventListener('click', (e) => {
const link = e.target.closest('a[href], button[onclick]');
if (!link) return;
this.showInstantFeedback(link);
this.prioritizeNavigation();
}, true);
}
showInstantFeedback(element) {
element.style.transform = 'scale(0.95)';
element.style.transition = 'transform 0.1s ease';
setTimeout(() => {
element.style.transform = 'scale(1)';
}, 100);
this.showLoadingIndicator();
}
prioritizeNavigation() {
this.activeRequests.forEach((request, key) => {
if (request.priority !== 'critical') {
request.controller.abort();
this.activeRequests.delete(key);
}
});
this.pauseBackgroundProcesses();
}
pauseBackgroundProcesses() {
const intervals = ['autoRefreshInterval', 'metricsUpdateInterval', 'chartUpdateInterval'];
intervals.forEach(intervalName => {
if (window[intervalName]) {
clearInterval(window[intervalName]);
}
});
document.querySelectorAll('.animated, [class*="animate"]').forEach(el => {
el.style.animationPlayState = 'paused';
});
}
setupPreemptiveLoading() {
const criticalRoutes = [
'/april-billing/',
'/ai-assistant',
'/kaizen',
'/master-attendance',
'/fleet-map'
];
criticalRoutes.forEach(route => {
this.preloadRoute(route);
});
}
preloadRoute(route) {
fetch(route, {
method: 'HEAD',
priority: 'low'
}).catch(() => {
});
}
showLoadingIndicator() {
const existingLoader = document.getElementById('traxovo-loader');
if (existingLoader) return;
const loader = document.createElement('div');
loader.id = 'traxovo-loader';
loader.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';
loader.style.cssText = `
position: fixed;
top: 20px;
right: 20px;
z-index: 9999;
background: white;
padding: 10px;
border-radius: 4px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
`;
document.body.appendChild(loader);
setTimeout(() => {
if (loader.parentElement) {
loader.remove();
}
}, 3000);
}
optimizeResourceAllocation() {
const images = document.querySelectorAll('img[data-src]');
const imageObserver = new IntersectionObserver((entries) => {
entries.forEach(entry => {
if (entry.isIntersecting) {
const img = entry.target;
img.src = img.dataset.src;
img.removeAttribute('data-src');
imageObserver.unobserve(img);
}
});
});
images.forEach(img => imageObserver.observe(img));
this.optimizeTableRendering();
}
optimizeTableRendering() {
const largeTables = document.querySelectorAll('table tbody tr');
if (largeTables.length > 50) {
this.virtualizeTable(largeTables[0].closest('table'));
}
}
virtualizeTable(table) {
const rows = Array.from(table.querySelectorAll('tbody tr'));
const visibleRows = 25;
let currentStart = 0;
const showRows = (start) => {
rows.forEach((row, index) => {
row.style.display = (index >= start && index < start + visibleRows) ? '' : 'none';
});
};
showRows(0);
this.addTablePagination(table, rows.length, visibleRows, showRows);
}
addTablePagination(table, totalRows, visibleRows, showRowsCallback) {
const pagination = document.createElement('div');
pagination.className = 'table-pagination mt-2';
pagination.innerHTML = `
<button class="btn btn-sm btn-outline-primary" onclick="window.traxovoPerf.previousPage(this)">Previous</button>
<span class="mx-2">Page <span class="current-page">1</span> of <span class="total-pages">${Math.ceil(totalRows / visibleRows)}</span></span>
<button class="btn btn-sm btn-outline-primary" onclick="window.traxovoPerf.nextPage(this)">Next</button>
`;
table.parentElement.appendChild(pagination);
pagination.dataset.totalRows = totalRows;
pagination.dataset.visibleRows = visibleRows;
pagination.dataset.currentPage = 1;
pagination.showRowsCallback = showRowsCallback;
}
previousPage(button) {
const pagination = button.parentElement;
const currentPage = parseInt(pagination.dataset.currentPage);
if (currentPage > 1) {
const newPage = currentPage - 1;
pagination.dataset.currentPage = newPage;
pagination.querySelector('.current-page').textContent = newPage;
const start = (newPage - 1) * parseInt(pagination.dataset.visibleRows);
pagination.showRowsCallback(start);
}
}
nextPage(button) {
const pagination = button.parentElement;
const currentPage = parseInt(pagination.dataset.currentPage);
const totalPages = Math.ceil(parseInt(pagination.dataset.totalRows) / parseInt(pagination.dataset.visibleRows));
if (currentPage < totalPages) {
const newPage = currentPage + 1;
pagination.dataset.currentPage = newPage;
pagination.querySelector('.current-page').textContent = newPage;
const start = (newPage - 1) * parseInt(pagination.dataset.visibleRows);
pagination.showRowsCallback(start);
}
}
}
const chartFixCSS = `
<style>
.chart-wrapper {
width: 100% !important;
height: 400px !important;
overflow: hidden !important;
position: relative !important;
}
.chart-container, canvas[id*="chart"] {
max-width: 100% !important;
max-height: 400px !important;
width: 100% !important;
height: 400px !important;
}
.card .chart-container {
height: 350px !important;
overflow: hidden !important;
}
.btn, .card, .nav-link {
transition: all 0.15s ease !important;
}
.btn:hover {
transform: translateY(-1px) !important;
box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
}
.loading {
opacity: 0.7 !important;
pointer-events: none !important;
}
</style>
`;
document.head.insertAdjacentHTML('beforeend', chartFixCSS);
window.traxovoPerf = new TRAXOVOPerformanceEngine();
console.log('TRAXOVO Performance Engine: Executive optimization active');