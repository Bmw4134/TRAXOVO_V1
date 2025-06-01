* Interactive Data Drill-Down Analytics
* Provides detailed breakdowns and visualizations for all modules
*/
class DrillDownAnalytics {
constructor() {
this.charts = {};
this.currentModule = null;
this.initializeChartLibrary();
}
initializeChartLibrary() {
if (typeof Chart === 'undefined') {
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
script.onload = () => this.setupEventListeners();
document.head.appendChild(script);
} else {
this.setupEventListeners();
}
}
setupEventListeners() {
document.addEventListener('click', (e) => {
const metricCard = e.target.closest('.metric-card, .card');
if (metricCard && metricCard.dataset.drilldown) {
this.openDrillDown(metricCard.dataset.drilldown, metricCard);
}
});
this.setupBillingDrillDowns();
this.setupFleetDrillDowns();
this.setupAttendanceDrillDowns();
}
setupBillingDrillDowns() {
const billingCards = document.querySelectorAll('[data-module="billing"]');
billingCards.forEach(card => {
card.style.cursor = 'pointer';
card.addEventListener('click', () => {
this.showBillingDrillDown(card.dataset.period);
});
});
}
setupFleetDrillDowns() {
const fleetCards = document.querySelectorAll('[data-module="fleet"]');
fleetCards.forEach(card => {
card.style.cursor = 'pointer';
card.addEventListener('click', () => {
this.showFleetDrillDown(card.dataset.category);
});
});
}
setupAttendanceDrillDowns() {
const attendanceCards = document.querySelectorAll('[data-module="attendance"]');
attendanceCards.forEach(card => {
card.style.cursor = 'pointer';
card.addEventListener('click', () => {
this.showAttendanceDrillDown(card.dataset.type);
});
});
}
async showBillingDrillDown(period) {
const modal = this.createDrillDownModal(`${period} Billing Analytics`);
try {
const response = await fetch(`/api/billing/drilldown/${period}`);
const data = await response.json();
if (data.success) {
this.renderBillingCharts(modal, data.analytics);
} else {
this.showError(modal, 'Unable to load billing analytics');
}
} catch (error) {
this.showError(modal, 'Error loading billing data');
}
}
async showFleetDrillDown(category) {
const modal = this.createDrillDownModal(`${category} Fleet Analytics`);
try {
const response = await fetch(`/api/fleet/drilldown/${category}`);
const data = await response.json();
if (data.success) {
this.renderFleetCharts(modal, data.analytics);
} else {
this.showError(modal, 'Unable to load fleet analytics');
}
} catch (error) {
this.showError(modal, 'Error loading fleet data');
}
}
async showAttendanceDrillDown(type) {
const modal = this.createDrillDownModal(`${type} Attendance Analytics`);
try {
const response = await fetch(`/api/attendance/drilldown/${type}`);
const data = await response.json();
if (data.success) {
this.renderAttendanceCharts(modal, data.analytics);
} else {
this.showError(modal, 'Unable to load attendance analytics');
}
} catch (error) {
this.showError(modal, 'Error loading attendance data');
}
}
createDrillDownModal(title) {
const modalId = 'drillDownModal';
const existingModal = document.getElementById(modalId);
if (existingModal) {
existingModal.remove();
}
const modal = document.createElement('div');
modal.id = modalId;
modal.className = 'modal fade';
modal.innerHTML = `
<div class="modal-dialog modal-xl">
<div class="modal-content">
<div class="modal-header">
<h5 class="modal-title">${title}</h5>
<button type="button" class="btn-close" data-bs-dismiss="modal"></button>
</div>
<div class="modal-body">
<div class="row">
<div class="col-12 text-center">
<div class="spinner-border text-primary" role="status">
<span class="visually-hidden">Loading analytics...</span>
</div>
<p class="mt-2">Loading detailed analytics...</p>
</div>
</div>
</div>
</div>
</div>
`;
document.body.appendChild(modal);
const bootstrapModal = new bootstrap.Modal(modal);
bootstrapModal.show();
return modal;
}
renderBillingCharts(modal, data) {
const modalBody = modal.querySelector('.modal-body');
modalBody.innerHTML = `
<div class="row">
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Revenue Breakdown</h6>
</div>
<div class="card-body">
<canvas id="revenueChart"></canvas>
</div>
</div>
</div>
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Asset Category Performance</h6>
</div>
<div class="card-body">
<canvas id="categoryChart"></canvas>
</div>
</div>
</div>
<div class="col-12 mt-3">
<div class="card">
<div class="card-header">
<h6>Monthly Trend Analysis</h6>
</div>
<div class="card-body">
<canvas id="trendChart"></canvas>
</div>
</div>
</div>
<div class="col-12 mt-3">
<div class="card">
<div class="card-header">
<h6>Detailed Breakdown</h6>
</div>
<div class="card-body">
<div class="table-responsive">
<table class="table table-striped">
<thead>
<tr>
<th>Asset Category</th>
<th>Hours</th>
<th>Rate</th>
<th>Revenue</th>
<th>% of Total</th>
</tr>
</thead>
<tbody id="billingDetailTable">
</tbody>
</table>
</div>
</div>
</div>
</div>
</div>
`;
this.createRevenueChart(data.revenue_breakdown);
this.createCategoryChart(data.category_performance);
this.createTrendChart(data.trend_analysis);
this.populateBillingTable(data.detailed_breakdown);
}
renderFleetCharts(modal, data) {
const modalBody = modal.querySelector('.modal-body');
modalBody.innerHTML = `
<div class="row">
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Asset Utilization</h6>
</div>
<div class="card-body">
<canvas id="utilizationChart"></canvas>
</div>
</div>
</div>
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Status Distribution</h6>
</div>
<div class="card-body">
<canvas id="statusChart"></canvas>
</div>
</div>
</div>
<div class="col-12 mt-3">
<div class="card">
<div class="card-header">
<h6>Performance Metrics</h6>
</div>
<div class="card-body">
<canvas id="performanceChart"></canvas>
</div>
</div>
</div>
</div>
`;
this.createUtilizationChart(data.utilization);
this.createStatusChart(data.status_distribution);
this.createPerformanceChart(data.performance_metrics);
}
renderAttendanceCharts(modal, data) {
const modalBody = modal.querySelector('.modal-body');
modalBody.innerHTML = `
<div class="row">
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Attendance Patterns</h6>
</div>
<div class="card-body">
<canvas id="attendanceChart"></canvas>
</div>
</div>
</div>
<div class="col-md-6">
<div class="card">
<div class="card-header">
<h6>Driver Performance</h6>
</div>
<div class="card-body">
<canvas id="driverChart"></canvas>
</div>
</div>
</div>
<div class="col-12 mt-3">
<div class="card">
<div class="card-header">
<h6>Weekly Trends</h6>
</div>
<div class="card-body">
<canvas id="weeklyChart"></canvas>
</div>
</div>
</div>
</div>
`;
this.createAttendanceChart(data.patterns);
this.createDriverChart(data.driver_performance);
this.createWeeklyChart(data.weekly_trends);
}
createRevenueChart(data) {
const ctx = document.getElementById('revenueChart').getContext('2d');
new Chart(ctx, {
type: 'doughnut',
data: {
labels: data.labels,
datasets: [{
data: data.values,
backgroundColor: [
'#007bff', '#28a745', '#ffc107', '#dc3545',
'#17a2b8', '#6f42c1', '#fd7e14', '#20c997'
]
}]
},
options: {
responsive: true,
plugins: {
legend: {
position: 'bottom'
}
}
}
});
}
createCategoryChart(data) {
const ctx = document.getElementById('categoryChart').getContext('2d');
new Chart(ctx, {
type: 'bar',
data: {
labels: data.labels,
datasets: [{
label: 'Revenue',
data: data.values,
backgroundColor: '#007bff'
}]
},
options: {
responsive: true,
scales: {
y: {
beginAtZero: true
}
}
}
});
}
createTrendChart(data) {
const ctx = document.getElementById('trendChart').getContext('2d');
new Chart(ctx, {
type: 'line',
data: {
labels: data.labels,
datasets: [{
label: 'Monthly Revenue',
data: data.values,
borderColor: '#007bff',
backgroundColor: 'rgba(0, 123, 255, 0.1)',
fill: true
}]
},
options: {
responsive: true,
scales: {
y: {
beginAtZero: true
}
}
}
});
}
populateBillingTable(data) {
const tbody = document.getElementById('billingDetailTable');
tbody.innerHTML = data.map(row => `
<tr>
<td>${row.category}</td>
<td>${row.hours.toLocaleString()}</td>
<td>$${row.rate}/hr</td>
<td>$${row.revenue.toLocaleString()}</td>
<td>${row.percentage}%</td>
</tr>
`).join('');
}
showError(modal, message) {
const modalBody = modal.querySelector('.modal-body');
modalBody.innerHTML = `
<div class="alert alert-danger" role="alert">
<strong>Error:</strong> ${message}
</div>
`;
}
}
document.addEventListener('DOMContentLoaded', () => {
new DrillDownAnalytics();
});